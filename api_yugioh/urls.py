from django.urls import path
from . import views

urlpatterns = [
    # path('card/', views.get_card, name='get_card'),
    # path('card/<str:card_name>/', views.get_card, name='get_card'),
    # path('search/', views.search_card, name='search_card'),
    path('', views.home, name='home'),
    path('cards_info/', views.card_info_view, name='card_info_view'),
    path('random_card/', views.random_card, name='random_card'),
    path('card/<int:card_id>/', views.card_detail, name='card_detail'),
    path('search-cards/', views.search_cards, name='search_cards'),
    path('api/suggest-set-codes/', views.suggest_set_codes, name='suggest_set_codes'),
    path('login/', views.login, name='login'),
]