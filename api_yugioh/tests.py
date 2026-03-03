from django.test import TestCase, RequestFactory
from django.urls import reverse, resolve
from unittest.mock import patch, MagicMock
from requests.exceptions import ConnectionError, Timeout
from api_yugioh.views import (
    get_cards_from_api, card_info_view, home, search_cards, random_card, login
)
from api_yugioh.models import Card, CardSet, CardImage, CardPrice, BanlistInfo
from api_yugioh.templatetags.custom_filters import filtrar_valor


# ─── Datos de ejemplo simulando la respuesta de la API ───────────────────────

SAMPLE_CARD = {
    "id": 46986414,
    "name": "Dark Magician",
    "type": "Normal Monster",
    "desc": "The ultimate wizard in terms of attack and defense.",
    "atk": 2500,
    "def": 2100,
    "level": 7,
    "race": "Spellcaster",
    "attribute": "DARK",
    "archetype": "Dark Magician",
    "card_sets": [
        {
            "set_name": "Legend of Blue Eyes White Dragon",
            "set_code": "LOB-005",
            "set_rarity": "Ultra Rare",
            "set_price": "85.95"
        }
    ],
    "card_images": [
        {
            "id": 46986414,
            "image_url": "https://images.ygoprodeck.com/images/cards/46986414.jpg",
            "image_url_small": "https://images.ygoprodeck.com/images/cards_small/46986414.jpg"
        }
    ],
    "card_prices": [
        {
            "tcgplayer_price": "1.50",
            "cardmarket_price": "0.80"
        }
    ]
}

SAMPLE_CARD_2 = {
    "id": 89631139,
    "name": "Blue-Eyes White Dragon",
    "type": "Normal Monster",
    "desc": "This legendary dragon is a powerful engine of destruction.",
    "atk": 3000,
    "def": 2500,
    "level": 8,
    "race": "Dragon",
    "attribute": "LIGHT",
    "card_images": [
        {
            "id": 89631139,
            "image_url": "https://images.ygoprodeck.com/images/cards/89631139.jpg",
            "image_url_small": "https://images.ygoprodeck.com/images/cards_small/89631139.jpg"
        }
    ],
    "card_prices": [
        {
            "tcgplayer_price": "2.00",
            "cardmarket_price": "1.20"
        }
    ]
}

API_RESPONSE_LIST = {"data": [SAMPLE_CARD, SAMPLE_CARD_2]}
API_RESPONSE_SINGLE = SAMPLE_CARD  # randomcard devuelve un solo dict, sin wrapper "data"


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Tests para get_cards_from_api
# ═══════════════════════════════════════════════════════════════════════════════

class GetCardsFromApiTests(TestCase):
    """Tests unitarios para la función get_cards_from_api."""

    @patch('api_yugioh.views.requests.get')
    def test_returns_list_when_data_key_present(self, mock_get):
        """Cuando la API devuelve {'data': [...]}, retorna la lista interna."""
        mock_response = MagicMock()
        mock_response.json.return_value = API_RESPONSE_LIST
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = get_cards_from_api('https://fake-url.com')

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['name'], 'Dark Magician')
        self.assertEqual(result[1]['name'], 'Blue-Eyes White Dragon')

    @patch('api_yugioh.views.requests.get')
    def test_returns_single_card_wrapped_in_list(self, mock_get):
        """Cuando la API devuelve un dict sin 'data' (randomcard), lo envuelve en lista."""
        mock_response = MagicMock()
        mock_response.json.return_value = API_RESPONSE_SINGLE
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = get_cards_from_api('https://fake-url.com/randomcard')

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'Dark Magician')

    @patch('api_yugioh.views.requests.get')
    def test_returns_empty_list_on_connection_error(self, mock_get):
        """Si hay un error de conexión, retorna lista vacía."""
        mock_get.side_effect = ConnectionError("No connection")

        result = get_cards_from_api('https://fake-url.com')

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    @patch('api_yugioh.views.requests.get')
    def test_returns_empty_list_on_timeout(self, mock_get):
        """Si hay timeout, retorna lista vacía."""
        mock_get.side_effect = Timeout("Request timed out")

        result = get_cards_from_api('https://fake-url.com')

        self.assertEqual(result, [])

    @patch('api_yugioh.views.requests.get')
    def test_passes_timeout_parameter(self, mock_get):
        """Verifica que la llamada a requests.get incluye timeout=10."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": []}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        get_cards_from_api('https://fake-url.com')

        mock_get.assert_called_once_with('https://fake-url.com', timeout=10)


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Tests para las vistas
# ═══════════════════════════════════════════════════════════════════════════════

class HomeViewTests(TestCase):
    """Tests para la vista home."""

    def test_home_status_code_200(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_home_uses_correct_template(self):
        response = self.client.get(reverse('home'))
        self.assertTemplateUsed(response, 'index.html')


class LoginViewTests(TestCase):
    """Tests para la vista login."""

    def test_login_status_code_200(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_login_uses_correct_template(self):
        response = self.client.get(reverse('login'))
        self.assertTemplateUsed(response, 'login.html')


class RandomCardViewTests(TestCase):
    """Tests para la vista random_card."""

    @patch('api_yugioh.views.get_cards_from_api')
    def test_random_card_renders_card(self, mock_api):
        """Cuando la API devuelve una carta, la vista la pasa al template."""
        mock_api.return_value = [SAMPLE_CARD]

        response = self.client.get(reverse('random_card'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'random_card.html')
        self.assertEqual(response.context['card']['name'], 'Dark Magician')

    @patch('api_yugioh.views.get_cards_from_api')
    def test_random_card_shows_error_on_empty_response(self, mock_api):
        """Cuando la API no devuelve cartas, muestra error."""
        mock_api.return_value = []

        response = self.client.get(reverse('random_card'))

        self.assertEqual(response.status_code, 200)
        self.assertIn('error', response.context)

    @patch('api_yugioh.views.get_cards_from_api')
    def test_random_card_calls_random_api_url(self, mock_api):
        """Verifica que usa el endpoint de carta aleatoria."""
        mock_api.return_value = [SAMPLE_CARD]

        self.client.get(reverse('random_card'))

        mock_api.assert_called_once_with('https://db.ygoprodeck.com/api/v7/randomcard.php')

    @patch('api_yugioh.views.get_cards_from_api')
    def test_random_card_context_contains_card_attributes(self, mock_api):
        """Verifica que el contexto contiene los atributos principales de la carta."""
        mock_api.return_value = [SAMPLE_CARD]

        response = self.client.get(reverse('random_card'))
        card = response.context['card']

        self.assertEqual(card['atk'], 2500)
        self.assertEqual(card['def'], 2100)
        self.assertEqual(card['level'], 7)
        self.assertEqual(card['attribute'], 'DARK')
        self.assertEqual(card['race'], 'Spellcaster')


class SearchCardsViewTests(TestCase):
    """Tests para la vista search_cards."""

    @patch('api_yugioh.views.get_cards_from_api')
    def test_search_with_query_returns_cards(self, mock_api):
        """Cuando se busca un nombre, devuelve las cartas encontradas."""
        mock_api.return_value = [SAMPLE_CARD]

        response = self.client.get(reverse('search_cards'), {'q': 'Dark Magician'})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'search_card.html')
        self.assertEqual(len(response.context['cards']), 1)
        self.assertEqual(response.context['query'], 'Dark Magician')

    @patch('api_yugioh.views.get_cards_from_api')
    def test_search_builds_correct_api_url(self, mock_api):
        """Verifica que construye la URL con fname y encode."""
        mock_api.return_value = []

        self.client.get(reverse('search_cards'), {'q': 'Dark Magician'})

        mock_api.assert_called_once_with(
            'https://db.ygoprodeck.com/api/v7/cardinfo.php?fname=Dark%20Magician'
        )

    def test_search_without_query_returns_empty_list(self):
        """Si no se pasa query, no llama a la API y devuelve lista vacía."""
        response = self.client.get(reverse('search_cards'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['cards'], [])
        self.assertIsNone(response.context['query'])

    def test_search_with_empty_query_returns_empty_list(self):
        """Si el query es solo espacios, no llama a la API."""
        response = self.client.get(reverse('search_cards'), {'q': '   '})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['cards'], [])

    @patch('api_yugioh.views.get_cards_from_api')
    def test_search_encodes_special_characters(self, mock_api):
        """Verifica que los caracteres especiales se encodean correctamente."""
        mock_api.return_value = []

        self.client.get(reverse('search_cards'), {'q': 'D/D/D'})

        mock_api.assert_called_once_with(
            'https://db.ygoprodeck.com/api/v7/cardinfo.php?fname=D/D/D'
        )


class CardInfoViewTests(TestCase):
    """Tests para la vista card_info_view (listado paginado)."""

    @patch('api_yugioh.views.get_cards_from_api')
    @patch('api_yugioh.views.requests.get')
    def test_card_info_view_returns_cards(self, mock_requests_get, mock_api):
        """Verifica que trae cartas y las pasa al template."""
        mock_meta_response = MagicMock()
        mock_meta_response.json.return_value = {
            'data': [SAMPLE_CARD],
            'meta': {'total_rows': 100}
        }
        mock_meta_response.raise_for_status.return_value = None
        mock_requests_get.return_value = mock_meta_response

        mock_api.return_value = [SAMPLE_CARD, SAMPLE_CARD_2]

        response = self.client.get(reverse('card_info_view'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'base_main.html')
        self.assertEqual(len(response.context['cards']), 2)

    @patch('api_yugioh.views.get_cards_from_api')
    @patch('api_yugioh.views.requests.get')
    def test_card_info_view_handles_api_error(self, mock_requests_get, mock_api):
        """Si la API falla, muestra mensaje de error."""
        mock_requests_get.side_effect = ConnectionError("API down")

        response = self.client.get(reverse('card_info_view'))

        self.assertEqual(response.status_code, 200)
        self.assertIn('error', response.context)


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Tests para las URLs
# ═══════════════════════════════════════════════════════════════════════════════

class URLTests(TestCase):
    """Verifica que las URLs resuelven a las vistas correctas."""

    def test_home_url_resolves(self):
        resolver = resolve('/')
        self.assertEqual(resolver.func, home)

    def test_cards_info_url_resolves(self):
        resolver = resolve('/cards_info/')
        self.assertEqual(resolver.func, card_info_view)

    def test_random_card_url_resolves(self):
        resolver = resolve('/random_card/')
        self.assertEqual(resolver.func, random_card)

    def test_search_cards_url_resolves(self):
        resolver = resolve('/search-cards/')
        self.assertEqual(resolver.func, search_cards)

    def test_login_url_resolves(self):
        resolver = resolve('/login/')
        self.assertEqual(resolver.func, login)


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Tests para template tags
# ═══════════════════════════════════════════════════════════════════════════════

class CustomFiltersTests(TestCase):
    """Tests para el template tag filtrar_valor."""

    def test_filtrar_valor_encuentra_valor(self):
        arreglo = [
            {'valorBuscar': 'A', 'otro': 1},
            {'valorBuscar': 'B', 'otro': 2},
        ]
        result = filtrar_valor(arreglo, 'A')
        self.assertEqual(result, "Valor encontrado: A")

    def test_filtrar_valor_no_encuentra_valor(self):
        arreglo = [
            {'valorBuscar': 'A', 'otro': 1},
        ]
        result = filtrar_valor(arreglo, 'Z')
        self.assertEqual(result, "Valor no encontrado")

    def test_filtrar_valor_lista_vacia(self):
        result = filtrar_valor([], 'A')
        self.assertEqual(result, "Valor no encontrado")


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Tests de integración: estructura JSON de la API
# ═══════════════════════════════════════════════════════════════════════════════

class APIDataStructureTests(TestCase):
    """
    Tests que verifican que el código accede correctamente a la
    estructura de datos de la API de YGOProDeck.
    """

    def test_card_has_card_sets_with_set_code(self):
        """Verifica que set_code está dentro de card_sets, NO en el nivel raíz."""
        card = SAMPLE_CARD
        self.assertNotIn('set_code', card)
        self.assertIn('card_sets', card)
        self.assertEqual(card['card_sets'][0]['set_code'], 'LOB-005')

    def test_card_images_accessible_by_index(self):
        """Las imágenes se acceden con card_images[0].image_url."""
        card = SAMPLE_CARD
        self.assertIn('card_images', card)
        self.assertIn('image_url', card['card_images'][0])

    def test_card_prices_accessible_by_index(self):
        """Los precios se acceden con card_prices[0].tcgplayer_price."""
        card = SAMPLE_CARD
        self.assertIn('card_prices', card)
        self.assertEqual(card['card_prices'][0]['tcgplayer_price'], '1.50')

    def test_card_without_card_sets(self):
        """Algunas cartas (tokens) no tienen card_sets."""
        card = SAMPLE_CARD_2
        self.assertNotIn('card_sets', card)

    @patch('api_yugioh.views.get_cards_from_api')
    def test_search_template_does_not_render_set_code_at_root(self, mock_api):
        """
        El template search_card.html usa {{ card.set_code }}, pero ese campo
        NO existe a nivel raíz. Debería usar {{ card.card_sets.0.set_code }}.
        Este test documenta el bug actual.
        """
        mock_api.return_value = [SAMPLE_CARD]

        response = self.client.get(reverse('search_cards'), {'q': 'Dark Magician'})
        content = response.content.decode()

        # El set_code 'LOB-005' NO aparece porque el template accede a
        # card.set_code (inexistente) en vez de card.card_sets.0.set_code
        self.assertNotIn('LOB-005', content,
            "Si este test falla, significa que el bug de set_code fue corregido. "
            "Actualiza este test para verificar que SÍ aparece."
        )


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Tests para los modelos Django (BD)
# ═══════════════════════════════════════════════════════════════════════════════

class CardModelTests(TestCase):
    """Tests para el modelo Card."""

    def setUp(self):
        """Crear cartas de prueba."""
        self.monster = Card.objects.create(
            card_id=46986414,
            name='Dark Magician',
            type='Normal Monster',
            human_readable_card_type='Normal Monster',
            frame_type='normal',
            desc='The ultimate wizard in terms of attack and defense.',
            race='Spellcaster',
            atk=2500,
            defense=2100,
            level=7,
            attribute='DARK',
            archetype='Dark Magician',
            ygoprodeck_url='https://ygoprodeck.com/card/dark-magician-4003',
            typeline=['Spellcaster', 'Normal'],
        )
        self.spell = Card.objects.create(
            card_id=55144522,
            name='Pot of Greed',
            type='Spell Card',
            human_readable_card_type='Normal Spell',
            frame_type='spell',
            desc='Draw 2 cards.',
            race='Normal',
            archetype='Greed',
        )
        self.link = Card.objects.create(
            card_id=1861629,
            name='Decode Talker',
            type='Link Monster',
            frame_type='link',
            desc='2+ Effect Monsters',
            race='Cyberse',
            atk=2300,
            defense=None,
            level=0,
            attribute='DARK',
            linkval=3,
            linkmarkers=['Top', 'Bottom-Left', 'Bottom-Right'],
        )
        self.pendulum = Card.objects.create(
            card_id=16178681,
            name='Odd-Eyes Pendulum Dragon',
            type='Pendulum Effect Monster',
            frame_type='effect_pendulum',
            desc='Full description',
            race='Dragon',
            atk=2500,
            defense=2000,
            level=7,
            attribute='DARK',
            scale=4,
            pend_desc='Pendulum effect text',
            monster_desc='Monster effect text',
        )

    def test_card_str(self):
        self.assertEqual(str(self.monster), 'Dark Magician (46986414)')

    def test_is_monster(self):
        self.assertTrue(self.monster.is_monster)
        self.assertFalse(self.spell.is_monster)

    def test_is_spell(self):
        self.assertTrue(self.spell.is_spell)
        self.assertFalse(self.monster.is_spell)

    def test_is_trap(self):
        self.assertFalse(self.spell.is_trap)

    def test_is_link(self):
        self.assertTrue(self.link.is_link)
        self.assertFalse(self.monster.is_link)

    def test_is_pendulum(self):
        self.assertTrue(self.pendulum.is_pendulum)
        self.assertFalse(self.monster.is_pendulum)

    def test_card_count(self):
        self.assertEqual(Card.objects.count(), 4)

    def test_card_ordering(self):
        """Las cartas se ordenan alfabéticamente por nombre."""
        names = list(Card.objects.values_list('name', flat=True))
        self.assertEqual(names, sorted(names))

    def test_link_monster_has_null_defense(self):
        self.assertIsNone(self.link.defense)

    def test_pendulum_has_scale(self):
        self.assertEqual(self.pendulum.scale, 4)

    def test_link_has_markers(self):
        self.assertEqual(self.link.linkmarkers, ['Top', 'Bottom-Left', 'Bottom-Right'])

    def test_card_search_by_name(self):
        results = Card.objects.filter(name__icontains='magician')
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().name, 'Dark Magician')


class CardSetModelTests(TestCase):
    """Tests para el modelo CardSet."""

    def setUp(self):
        self.card = Card.objects.create(
            card_id=46986414,
            name='Dark Magician',
            type='Normal Monster',
        )
        self.card_set = CardSet.objects.create(
            card=self.card,
            set_name='Legend of Blue Eyes White Dragon',
            set_code='LOB-005',
            set_rarity='Ultra Rare',
            set_rarity_code='(UR)',
            set_price=46.71,
        )

    def test_card_set_str(self):
        self.assertEqual(
            str(self.card_set),
            'LOB-005 - Legend of Blue Eyes White Dragon (Ultra Rare)'
        )

    def test_card_set_relation(self):
        self.assertEqual(self.card.card_sets.count(), 1)
        self.assertEqual(self.card.card_sets.first().set_code, 'LOB-005')

    def test_multiple_sets_per_card(self):
        CardSet.objects.create(
            card=self.card,
            set_name='Starter Deck: Yugi',
            set_code='SDY-006',
            set_rarity='Ultra Rare',
            set_rarity_code='(UR)',
            set_price=9.96,
        )
        self.assertEqual(self.card.card_sets.count(), 2)

    def test_cascade_delete(self):
        """Al eliminar la carta, se eliminan sus sets."""
        self.card.delete()
        self.assertEqual(CardSet.objects.count(), 0)


class CardImageModelTests(TestCase):
    """Tests para el modelo CardImage."""

    def setUp(self):
        self.card = Card.objects.create(
            card_id=46986414,
            name='Dark Magician',
            type='Normal Monster',
        )
        self.image = CardImage.objects.create(
            card=self.card,
            image_id=46986414,
            image_url='https://images.ygoprodeck.com/images/cards/46986414.jpg',
            image_url_small='https://images.ygoprodeck.com/images/cards_small/46986414.jpg',
            image_url_cropped='https://images.ygoprodeck.com/images/cards_cropped/46986414.jpg',
        )

    def test_card_image_str(self):
        self.assertIn('Dark Magician', str(self.image))

    def test_card_image_relation(self):
        self.assertEqual(self.card.card_images.count(), 1)

    def test_multiple_images_per_card(self):
        """Una carta puede tener múltiples artworks."""
        CardImage.objects.create(
            card=self.card,
            image_id=46986415,
            image_url='https://images.ygoprodeck.com/images/cards/46986415.jpg',
        )
        self.assertEqual(self.card.card_images.count(), 2)


class CardPriceModelTests(TestCase):
    """Tests para el modelo CardPrice."""

    def setUp(self):
        self.card = Card.objects.create(
            card_id=46986414,
            name='Dark Magician',
            type='Normal Monster',
        )
        self.price = CardPrice.objects.create(
            card=self.card,
            tcgplayer_price=0.22,
            cardmarket_price=0.02,
            ebay_price=0.99,
            amazon_price=14.45,
            coolstuffinc_price=0.39,
        )

    def test_card_price_str(self):
        self.assertIn('Dark Magician', str(self.price))

    def test_card_price_values(self):
        self.assertAlmostEqual(float(self.price.tcgplayer_price), 0.22, places=2)
        self.assertAlmostEqual(float(self.price.amazon_price), 14.45, places=2)

    def test_card_price_relation(self):
        self.assertEqual(self.card.card_prices.count(), 1)


class BanlistInfoModelTests(TestCase):
    """Tests para el modelo BanlistInfo."""

    def setUp(self):
        self.card = Card.objects.create(
            card_id=55144522,
            name='Pot of Greed',
            type='Spell Card',
        )
        self.banlist = BanlistInfo.objects.create(
            card=self.card,
            ban_tcg='Forbidden',
            ban_ocg='Forbidden',
            ban_goat='Limited',
        )

    def test_banlist_str(self):
        result = str(self.banlist)
        self.assertIn('Pot of Greed', result)
        self.assertIn('TCG: Forbidden', result)

    def test_banlist_one_to_one(self):
        """banlist_info es una relación OneToOne."""
        self.assertEqual(self.card.banlist_info.ban_tcg, 'Forbidden')

    def test_cascade_delete(self):
        self.card.delete()
        self.assertEqual(BanlistInfo.objects.count(), 0)

    def test_card_without_banlist(self):
        """No todas las cartas tienen banlist_info."""
        free_card = Card.objects.create(
            card_id=46986414,
            name='Dark Magician',
            type='Normal Monster',
        )
        self.assertFalse(hasattr(free_card, 'banlist_info') and
                         BanlistInfo.objects.filter(card=free_card).exists())
