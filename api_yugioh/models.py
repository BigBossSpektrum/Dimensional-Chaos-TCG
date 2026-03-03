from django.db import models


# ═══════════════════════════════════════════════════════════════════════════════
# Modelo principal: Card
# Mapea los campos de nivel raíz de la API de YGOProDeck v7
# https://db.ygoprodeck.com/api/v7/cardinfo.php
# ═══════════════════════════════════════════════════════════════════════════════

class Card(models.Model):
    """
    Carta de Yu-Gi-Oh! con todos los atributos del JSON raíz de la API.

    Campos que varían según el tipo de carta:
    - Monstruos: atk, def, level, attribute, race (como tipo de monstruo)
    - Spell/Trap: race (como subtipo: Normal, Continuous, etc.)
    - Link: linkval, linkmarkers (sin def, level=0)
    - Pendulum: scale, pend_desc, monster_desc
    """

    # ── Identificación ────────────────────────────────────────────────────
    card_id = models.BigIntegerField(
        primary_key=True,
        help_text='ID único de la carta en la API de YGOProDeck'
    )
    name = models.CharField(max_length=255, db_index=True)
    ygoprodeck_url = models.URLField(max_length=500, blank=True, default='')

    # ── Clasificación ─────────────────────────────────────────────────────
    type = models.CharField(
        max_length=100,
        help_text='Tipo completo: "Normal Monster", "Spell Card", "Link Monster", etc.'
    )
    human_readable_card_type = models.CharField(
        max_length=100, blank=True, default='',
        help_text='Tipo legible: "Normal Monster", "Normal Spell", "Link Effect Monster"'
    )
    frame_type = models.CharField(
        max_length=50, blank=True, default='',
        help_text='Tipo de marco: normal, effect, spell, trap, link, xyz, synchro, fusion, effect_pendulum, etc.'
    )
    race = models.CharField(
        max_length=100, blank=True, default='',
        help_text='Tipo de monstruo (Spellcaster, Dragon) o subtipo de spell/trap (Normal, Continuous)'
    )
    archetype = models.CharField(
        max_length=255, blank=True, default='',
        help_text='Arquetipo al que pertenece la carta'
    )
    typeline = models.JSONField(
        blank=True, null=True,
        help_text='Array de strings con la línea de tipo: ["Dragon", "Pendulum", "Effect"]'
    )

    # ── Descripción ───────────────────────────────────────────────────────
    desc = models.TextField(
        blank=True, default='',
        help_text='Descripción/efecto completo de la carta'
    )
    pend_desc = models.TextField(
        blank=True, default='',
        help_text='Descripción del efecto péndulo (solo cartas Pendulum)'
    )
    monster_desc = models.TextField(
        blank=True, default='',
        help_text='Descripción del efecto de monstruo (solo cartas Pendulum)'
    )

    # ── Stats de monstruo ─────────────────────────────────────────────────
    atk = models.IntegerField(
        null=True, blank=True,
        help_text='Puntos de ataque (null para Spell/Trap)'
    )
    defense = models.IntegerField(
        null=True, blank=True,
        help_text='Puntos de defensa (null para Link y Spell/Trap)'
    )
    level = models.IntegerField(
        null=True, blank=True,
        help_text='Nivel/Rango del monstruo (0 para Link, null para Spell/Trap)'
    )
    attribute = models.CharField(
        max_length=20, blank=True, default='',
        help_text='Atributo: DARK, LIGHT, WATER, FIRE, EARTH, WIND, DIVINE'
    )

    # ── Stats exclusivos de Link ──────────────────────────────────────────
    linkval = models.IntegerField(
        null=True, blank=True,
        help_text='Valor de Link (solo monstruos Link)'
    )
    linkmarkers = models.JSONField(
        blank=True, null=True,
        help_text='Marcadores Link: ["Top", "Bottom-Left", "Bottom-Right"]'
    )

    # ── Stats exclusivos de Pendulum ──────────────────────────────────────
    scale = models.IntegerField(
        null=True, blank=True,
        help_text='Escala Péndulo (solo cartas Pendulum)'
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Carta'
        verbose_name_plural = 'Cartas'

    def __str__(self):
        return f'{self.name} ({self.card_id})'

    @property
    def is_monster(self):
        return 'Monster' in self.type

    @property
    def is_spell(self):
        return self.type == 'Spell Card'

    @property
    def is_trap(self):
        return self.type == 'Trap Card'

    @property
    def is_link(self):
        return 'Link' in self.type

    @property
    def is_pendulum(self):
        return 'Pendulum' in self.type


# ═══════════════════════════════════════════════════════════════════════════════
# Modelo: CardSet
# Mapea cada entrada del array "card_sets" de la API
# Una carta puede aparecer en muchos sets
# ═══════════════════════════════════════════════════════════════════════════════

class CardSet(models.Model):
    """Set/colección donde fue impresa una carta."""

    card = models.ForeignKey(
        Card, on_delete=models.CASCADE, related_name='card_sets'
    )
    set_name = models.CharField(max_length=255, help_text='Nombre del set')
    set_code = models.CharField(max_length=50, help_text='Código del set: LOB-005')
    set_rarity = models.CharField(max_length=100, help_text='Rareza: Ultra Rare, Common, etc.')
    set_rarity_code = models.CharField(
        max_length=20, blank=True, default='',
        help_text='Código de rareza: (UR), (C), (ScR)'
    )
    set_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text='Precio del set'
    )

    class Meta:
        ordering = ['set_name']
        verbose_name = 'Set de Carta'
        verbose_name_plural = 'Sets de Cartas'

    def __str__(self):
        return f'{self.set_code} - {self.set_name} ({self.set_rarity})'


# ═══════════════════════════════════════════════════════════════════════════════
# Modelo: CardImage
# Mapea cada entrada del array "card_images" de la API
# Una carta puede tener múltiples artworks/ediciones
# ═══════════════════════════════════════════════════════════════════════════════

class CardImage(models.Model):
    """Imagen/artwork de una carta. Una carta puede tener varios artworks."""

    card = models.ForeignKey(
        Card, on_delete=models.CASCADE, related_name='card_images'
    )
    image_id = models.BigIntegerField(
        help_text='ID de la imagen en la API'
    )
    image_url = models.URLField(
        max_length=500, help_text='URL de la imagen completa'
    )
    image_url_small = models.URLField(
        max_length=500, blank=True, default='',
        help_text='URL de la imagen en tamaño pequeño'
    )
    image_url_cropped = models.URLField(
        max_length=500, blank=True, default='',
        help_text='URL de la imagen recortada (solo el artwork)'
    )

    class Meta:
        verbose_name = 'Imagen de Carta'
        verbose_name_plural = 'Imágenes de Cartas'

    def __str__(self):
        return f'Imagen {self.image_id} de {self.card.name}'


# ═══════════════════════════════════════════════════════════════════════════════
# Modelo: CardPrice
# Mapea cada entrada del array "card_prices" de la API
# Precios de diferentes mercados
# ═══════════════════════════════════════════════════════════════════════════════

class CardPrice(models.Model):
    """Precios de una carta en diferentes mercados."""

    card = models.ForeignKey(
        Card, on_delete=models.CASCADE, related_name='card_prices'
    )
    cardmarket_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text='Precio en Cardmarket (EUR)'
    )
    tcgplayer_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text='Precio en TCGPlayer (USD)'
    )
    ebay_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text='Precio en eBay (USD)'
    )
    amazon_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text='Precio en Amazon (USD)'
    )
    coolstuffinc_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text='Precio en CoolStuffInc (USD)'
    )

    class Meta:
        verbose_name = 'Precio de Carta'
        verbose_name_plural = 'Precios de Cartas'

    def __str__(self):
        return f'Precios de {self.card.name} (TCG: ${self.tcgplayer_price})'


# ═══════════════════════════════════════════════════════════════════════════════
# Modelo: BanlistInfo
# Mapea el objeto "banlist_info" de la API (opcional, no todas las cartas lo tienen)
# ═══════════════════════════════════════════════════════════════════════════════

class BanlistInfo(models.Model):
    """Estado de una carta en las diferentes banlists."""

    BAN_STATUS_CHOICES = [
        ('Forbidden', 'Forbidden'),
        ('Limited', 'Limited'),
        ('Semi-Limited', 'Semi-Limited'),
    ]

    card = models.OneToOneField(
        Card, on_delete=models.CASCADE, related_name='banlist_info'
    )
    ban_tcg = models.CharField(
        max_length=20, blank=True, default='',
        choices=BAN_STATUS_CHOICES,
        help_text='Estado en la banlist TCG'
    )
    ban_ocg = models.CharField(
        max_length=20, blank=True, default='',
        choices=BAN_STATUS_CHOICES,
        help_text='Estado en la banlist OCG'
    )
    ban_goat = models.CharField(
        max_length=20, blank=True, default='',
        choices=BAN_STATUS_CHOICES,
        help_text='Estado en la banlist GOAT format'
    )

    class Meta:
        verbose_name = 'Info de Banlist'
        verbose_name_plural = 'Info de Banlists'

    def __str__(self):
        parts = []
        if self.ban_tcg:
            parts.append(f'TCG: {self.ban_tcg}')
        if self.ban_ocg:
            parts.append(f'OCG: {self.ban_ocg}')
        return f'{self.card.name} - {", ".join(parts)}' if parts else f'{self.card.name} - Sin restricciones'
