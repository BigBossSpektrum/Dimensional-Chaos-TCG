import os
import requests
from urllib.parse import quote

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ATTRIBUTES = ["DARK", "DIVINE", "EARTH", "FIRE", "LIGHT", "WATER", "WIND"]

RACES_MONSTER = [
    "Aqua", "Beast", "Beast-Warrior", "Creator-God", "Cyberse",
    "Dinosaur", "Divine-Beast", "Dragon", "Fairy", "Fiend", "Fish",
    "Insect", "Machine", "Plant", "Psychic", "Pyro", "Reptile",
    "Rock", "Sea Serpent", "Spellcaster", "Thunder", "Warrior",
    "Winged Beast", "Wyrm", "Zombie", "Illusion"
]

RACES_SPELL_TRAP = [
    "Normal", "Continuous", "Counter", "Equip", "Field", "Quick-Play", "Ritual"
]


def download_image(url, save_path):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, 'wb') as f:
                f.write(response.content)
            print(f"OK: {os.path.basename(save_path)}")
            return True
        else:
            return False
    except Exception as e:
        print(f"ERROR: {url} -> {e}")
        return False


def main():
    attr_dir = os.path.join(BASE_DIR, "static", "img", "attributes")
    race_dir = os.path.join(BASE_DIR, "static", "img", "races")

    # Atributos: icons/attributes/{ATTR}.jpg (ya descargados)
    for attr in ATTRIBUTES:
        save_path = os.path.join(attr_dir, f"{attr}.png")
        if os.path.exists(save_path):
            print(f"SKIP: {attr}.png (exists)")
            continue
        url = f"https://images.ygoprodeck.com/images/cards/icons/attributes/{attr}.jpg"
        download_image(url, save_path)

    # Razas de monstruos: icons/race/{Race}.png (singular 'race')
    for race in RACES_MONSTER:
        save_path = os.path.join(race_dir, f"{race}.png")
        if os.path.exists(save_path):
            print(f"SKIP: {race}.png (exists)")
            continue
        encoded = quote(race)
        url = f"https://images.ygoprodeck.com/images/cards/icons/race/{encoded}.png"
        download_image(url, save_path)

    # Subtipos de Spell/Trap (mismos iconos, misma ruta)
    for race in RACES_SPELL_TRAP:
        save_path = os.path.join(race_dir, f"{race}.png")
        if os.path.exists(save_path):
            print(f"SKIP: {race}.png (exists)")
            continue
        encoded = quote(race)
        url = f"https://images.ygoprodeck.com/images/cards/icons/race/{encoded}.png"
        download_image(url, save_path)

    print("\nDescarga completada!")


if __name__ == "__main__":
    main()
