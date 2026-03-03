from django.contrib import admin
from .models import Card, CardSet, CardImage, CardPrice, BanlistInfo


class CardSetInline(admin.TabularInline):
    model = CardSet
    extra = 0


class CardImageInline(admin.TabularInline):
    model = CardImage
    extra = 0


class CardPriceInline(admin.TabularInline):
    model = CardPrice
    extra = 0


class BanlistInfoInline(admin.StackedInline):
    model = BanlistInfo
    extra = 0
    max_num = 1


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ('card_id', 'name', 'type', 'attribute', 'race', 'atk', 'defense', 'level')
    list_filter = ('type', 'attribute', 'race', 'frame_type')
    search_fields = ('name', 'archetype', 'desc')
    inlines = [CardSetInline, CardImageInline, CardPriceInline, BanlistInfoInline]


@admin.register(CardSet)
class CardSetAdmin(admin.ModelAdmin):
    list_display = ('set_code', 'set_name', 'set_rarity', 'set_price', 'card')
    list_filter = ('set_rarity',)
    search_fields = ('set_code', 'set_name', 'card__name')


@admin.register(CardImage)
class CardImageAdmin(admin.ModelAdmin):
    list_display = ('image_id', 'card', 'image_url')
    search_fields = ('card__name',)


@admin.register(CardPrice)
class CardPriceAdmin(admin.ModelAdmin):
    list_display = ('card', 'tcgplayer_price', 'cardmarket_price', 'ebay_price', 'amazon_price')
    search_fields = ('card__name',)


@admin.register(BanlistInfo)
class BanlistInfoAdmin(admin.ModelAdmin):
    list_display = ('card', 'ban_tcg', 'ban_ocg', 'ban_goat')
    list_filter = ('ban_tcg', 'ban_ocg')
    search_fields = ('card__name',)
