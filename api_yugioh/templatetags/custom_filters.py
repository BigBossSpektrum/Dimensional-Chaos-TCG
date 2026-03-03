from django import template

register = template.Library()

@register.filter
def filtrar_valor(arreglo, valor_deseado):
    """Filtra un arreglo de diccionarios buscando un valor específico."""
    resultado = list(filter(lambda obj: obj.get('valorBuscar') == valor_deseado, arreglo))
    if resultado:
        return f"Valor encontrado: {resultado[0]['valorBuscar']}"
    else:
        return "Valor no encontrado"
