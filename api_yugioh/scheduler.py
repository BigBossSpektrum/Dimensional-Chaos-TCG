import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

import requests
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

CHECK_URL = 'https://db.ygoprodeck.com/api/v7/checkdbver.php'
STATE_FILE = Path(__file__).resolve().parent.parent / '.yugioh_sync_state.json'

_scheduler = None


def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save_state(state: dict) -> None:
    try:
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f)
    except OSError as e:
        logger.error(f'No se pudo guardar el estado de sincronización: {e}')


def _get_api_version() -> str | None:
    try:
        response = requests.get(CHECK_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data and isinstance(data, list):
            return data[0].get('database_version')
    except Exception as e:
        logger.warning(f'No se pudo obtener la versión de la API: {e}')
    return None


def sync_cards() -> None:
    """
    Comprueba la versión de la API de YGOProDeck y sincroniza la base de datos
    solo si hay cambios respecto a la última sincronización.
    """
    from django.core.management import call_command

    logger.info('Comprobando versión de la API de YGOProDeck...')
    api_version = _get_api_version()
    state = _load_state()
    last_version = state.get('database_version')

    if api_version and api_version == last_version:
        logger.info(f'Sin cambios en la API (versión {api_version}). Sincronización omitida.')
        return

    if api_version:
        logger.info(f'Nueva versión detectada: {api_version} (anterior: {last_version or "ninguna"}).')
    else:
        logger.info('No se pudo obtener la versión; sincronizando de todos modos...')

    try:
        call_command('fetch_all_cards')
        _save_state({
            'database_version': api_version,
            'last_sync': datetime.now(timezone.utc).isoformat(),
        })
        logger.info('Sincronización completada correctamente.')
    except Exception as e:
        logger.error(f'Error durante la sincronización automática: {e}')


def start() -> None:
    global _scheduler
    if _scheduler is not None:
        return

    _scheduler = BackgroundScheduler(timezone='UTC')
    _scheduler.add_job(
        sync_cards,
        trigger=IntervalTrigger(hours=24),
        id='sync_yugioh_cards',
        name='Sincronizar cartas YGOProDeck',
        replace_existing=True,
        misfire_grace_time=3600,
        next_run_time=datetime.now(timezone.utc),  # comprueba cambios al arrancar
    )
    _scheduler.start()
    logger.info('Scheduler iniciado: sincronización automática de cartas cada 24 horas.')
