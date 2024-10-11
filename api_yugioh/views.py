import requests
import random
from django.shortcuts import render
from requests.exceptions import RequestException

api_url = 'https://db.ygoprodeck.com/api/v7/cardinfo.php'

def get_cards_from_api(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Lanza un error si el código de estado es 4xx o 5xx
        return response.json().get('data', [])
    except RequestException as e:
        print(f'Error al hacer la solicitud a la API: {e}')
        return []

def card_info_view(request):
    cards = get_cards_from_api(api_url)
    
    if cards:
        random_cards = random.sample(cards, 40)
        context = {'cards': random_cards}
    else:
        context = {'error': 'No se pudieron obtener las cartas de la API'}

    return render(request, 'base_main.html', context)

def home(request):
    return render(request, 'index.html')

def card_info(request, card_name):
    return render(request, 'card_info.html', {'card_name': card_name})

def search_cards(request):
    query = request.GET.get('q')
    cards = []
    
    if query:
        # Limpieza básica del input
        query = query.strip()
        
        if query:
            api_query_url = f'{api_url}?name={query}'
            cards = get_cards_from_api(api_query_url)

    context = {'cards': cards, 'query': query}
    return render(request, 'search_card.html', context)

def random_card(request):
    cards = get_cards_from_api(api_url)
    
    if cards:
        random_card = random.choice(cards)
        context = {'card': random_card}
    else:
        context = {'error': 'No se pudieron obtener las cartas de la API'}
    
    return render(request, 'random_card.html', context)

def login(request):
    return render(request, 'login.html')