"""
Management command: fetch_all_cards
Descarga TODAS las cartas de la API de YGOProDeck y las guarda en la DB.

Uso:
    python manage.py fetch_all_cards
    python manage.py fetch_all_cards --clear   # Borra todo antes de importar
"""

import sys
import time
from decimal import Decimal, InvalidOperation

import requests
from django.core.management.base import BaseCommand
from django.db import transaction

from api_yugioh.models import Card, CardSet, CardImage, CardPrice, BanlistInfo

API_URL = 'https://db.ygoprodeck.com/api/v7/cardinfo.php'


class Command(BaseCommand):
    help = 'Descarga todas las cartas de la API de YGOProDeck y las guarda en la base de datos.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Borra todas las cartas existentes antes de importar.',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Borrando datos existentes...'))
            Card.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Datos borrados.'))

        self.stdout.write('Descargando todas las cartas de la API de YGOProDeck...')
        start_time = time.time()

        try:
            response = requests.get(API_URL, timeout=120)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            self.stderr.write(self.style.ERROR(f'Error al conectar con la API: {e}'))
            sys.exit(1)

        cards_data = data.get('data', [])
        total = len(cards_data)
        self.stdout.write(f'Se encontraron {total} cartas. Guardando en la base de datos...')

        created = 0
        updated = 0
        errors = 0

        # Procesar en lotes para mejor rendimiento
        BATCH_SIZE = 500
        for batch_start in range(0, total, BATCH_SIZE):
            batch = cards_data[batch_start:batch_start + BATCH_SIZE]
            try:
                with transaction.atomic():
                    for card_data in batch:
                        try:
                            was_created = self._save_card(card_data)
                            if was_created:
                                created += 1
                            else:
                                updated += 1
                        except Exception as e:
                            errors += 1
                            card_name = card_data.get('name', 'DESCONOCIDA')
                            self.stderr.write(
                                self.style.WARNING(f'  Error con "{card_name}": {e}')
                            )
            except Exception as e:
                self.stderr.write(
                    self.style.ERROR(f'Error en lote {batch_start}-{batch_start + len(batch)}: {e}')
                )
                errors += len(batch)

            # Progreso
            processed = min(batch_start + BATCH_SIZE, total)
            pct = processed / total * 100
            self.stdout.write(f'  Progreso: {processed}/{total} ({pct:.1f}%)')

        elapsed = time.time() - start_time
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'¡Importación completada en {elapsed:.1f}s!'
        ))
        self.stdout.write(f'  Creadas:      {created}')
        self.stdout.write(f'  Actualizadas: {updated}')
        if errors:
            self.stdout.write(self.style.WARNING(f'  Errores:      {errors}'))

    # ── Helpers ────────────────────────────────────────────────────────────

    def _save_card(self, data: dict) -> bool:
        """
        Guarda o actualiza una carta y todos sus modelos relacionados.
        Retorna True si fue creada, False si fue actualizada.
        """
        card_id = data['id']

        card_defaults = {
            'name': data.get('name', ''),
            'type': data.get('type', ''),
            'human_readable_card_type': data.get('humanReadableCardType', ''),
            'frame_type': data.get('frameType', ''),
            'desc': data.get('desc', ''),
            'race': data.get('race', ''),
            'archetype': data.get('archetype', ''),
            'ygoprodeck_url': data.get('ygoprodeck_url', ''),
            'atk': data.get('atk'),
            'defense': data.get('def'),
            'level': data.get('level'),
            'attribute': data.get('attribute', ''),
            'linkval': data.get('linkval'),
            'linkmarkers': data.get('linkmarkers'),
            'scale': data.get('scale'),
            'typeline': data.get('typeline'),
            'pend_desc': data.get('pend_desc', ''),
            'monster_desc': data.get('monster_desc', ''),
        }

        card, was_created = Card.objects.update_or_create(
            card_id=card_id,
            defaults=card_defaults,
        )

        # ── Card Sets ─────────────────────────────────────────────────
        if 'card_sets' in data and data['card_sets']:
            card.card_sets.all().delete()
            sets_to_create = []
            for s in data['card_sets']:
                sets_to_create.append(CardSet(
                    card=card,
                    set_name=s.get('set_name', ''),
                    set_code=s.get('set_code', ''),
                    set_rarity=s.get('set_rarity', ''),
                    set_rarity_code=s.get('set_rarity_code', ''),
                    set_price=self._to_decimal(s.get('set_price')),
                ))
            CardSet.objects.bulk_create(sets_to_create)

        # ── Card Images ───────────────────────────────────────────────
        if 'card_images' in data and data['card_images']:
            card.card_images.all().delete()
            images_to_create = []
            for img in data['card_images']:
                images_to_create.append(CardImage(
                    card=card,
                    image_id=img.get('id', 0),
                    image_url=img.get('image_url', ''),
                    image_url_small=img.get('image_url_small', ''),
                    image_url_cropped=img.get('image_url_cropped', ''),
                ))
            CardImage.objects.bulk_create(images_to_create)

        # ── Card Prices ───────────────────────────────────────────────
        if 'card_prices' in data and data['card_prices']:
            card.card_prices.all().delete()
            prices_to_create = []
            for p in data['card_prices']:
                prices_to_create.append(CardPrice(
                    card=card,
                    cardmarket_price=self._to_decimal(p.get('cardmarket_price')),
                    tcgplayer_price=self._to_decimal(p.get('tcgplayer_price')),
                    ebay_price=self._to_decimal(p.get('ebay_price')),
                    amazon_price=self._to_decimal(p.get('amazon_price')),
                    coolstuffinc_price=self._to_decimal(p.get('coolstuffinc_price')),
                ))
            CardPrice.objects.bulk_create(prices_to_create)

        # ── Banlist Info ──────────────────────────────────────────────
        if 'banlist_info' in data and data['banlist_info']:
            bl = data['banlist_info']
            BanlistInfo.objects.update_or_create(
                card=card,
                defaults={
                    'ban_tcg': bl.get('ban_tcg', ''),
                    'ban_ocg': bl.get('ban_ocg', ''),
                    'ban_goat': bl.get('ban_goat', ''),
                },
            )
        else:
            # Si la carta no tiene banlist_info, eliminar registro previo
            BanlistInfo.objects.filter(card=card).delete()

        return was_created

    @staticmethod
    def _to_decimal(value) -> Decimal | None:
        """Convierte un valor a Decimal de forma segura."""
        if value is None or value == '':
            return None
        try:
            d = Decimal(str(value))
            return d if d >= 0 else None
        except (InvalidOperation, ValueError):
            return None
