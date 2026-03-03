import requests
import random
from urllib.parse import quote
from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from requests.exceptions import RequestException
from .models import Card

api_url = 'https://db.ygoprodeck.com/api/v7/cardinfo.php'
api_random_url = 'https://db.ygoprodeck.com/api/v7/randomcard.php'

def get_cards_from_api(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        # La API puede devolver un solo objeto (randomcard) o una lista en 'data'
        if 'data' in data:
            return data['data']
        return [data] if isinstance(data, dict) else data
    except RequestException as e:
        print(f'Error al hacer la solicitud a la API: {e}')
        return []

def card_info_view(request):
    # Usar paginación de la API: traer solo 40 cartas con offset aleatorio
    try:
        # Primero obtener el total de cartas disponibles
        meta_url = f'{api_url}?num=1&offset=0'
        response = requests.get(meta_url, timeout=10)
        response.raise_for_status()
        meta = response.json().get('meta', {})
        total = meta.get('total_rows', 1000)
        
        # Elegir un offset aleatorio
        max_offset = max(0, total - 40)
        random_offset = random.randint(0, max_offset)
        
        paginated_url = f'{api_url}?num=40&offset={random_offset}'
        cards = get_cards_from_api(paginated_url)
        context = {'cards': cards}
    except (RequestException, Exception) as e:
        print(f'Error al obtener cartas: {e}')
        context = {'error': 'No se pudieron obtener las cartas de la API'}

    return render(request, 'base_main.html', context)

def home(request):
    return render(request, 'index.html')

def card_info(request, card_name):
    return render(request, 'card_info.html', {'card_name': card_name})

def search_cards(request):
    query = request.GET.get('q')
    cards = Card.objects.none()
    
    if query:
        query = query.strip()
        
        if query:
            # Buscar en la base de datos local por nombre, arquetipo, tipo o descripción
            cards = Card.objects.filter(
                Q(name__icontains=query) |
                Q(archetype__icontains=query) |
                Q(type__icontains=query) |
                Q(desc__icontains=query)
            ).prefetch_related(
                'card_images', 'card_prices', 'card_sets'
            ).select_related('banlist_info')[:40]

    context = {'cards': cards, 'query': query}
    return render(request, 'search_card.html', context)

def card_detail(request, card_id):
    """Vista de detalle de una carta desde la base de datos local."""
    card = get_object_or_404(
        Card.objects.prefetch_related(
            'card_images', 'card_prices', 'card_sets'
        ).select_related('banlist_info'),
        card_id=card_id
    )
    return render(request, 'card_detail.html', {'card': card})

def random_card(request):
    # Usar el endpoint dedicado para carta aleatoria (1 sola carta, no todo el catálogo)
    cards = get_cards_from_api(api_random_url)
    
    if cards:
        context = {'card': cards[0]}
    else:
        context = {'error': 'No se pudieron obtener las cartas de la API'}
    
    return render(request, 'random_card.html', context)

def login(request):
    return render(request, 'login.html')