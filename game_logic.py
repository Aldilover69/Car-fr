"""
Reine Spiellogik für PyMon Abenteuer.

Enthält KEINE Netzwerkzugriffe - nur Berechnungen (Statuswerte, Schaden,
Fangchance, Erfahrungspunkte, Typen-Effektivität). Dadurch lässt sich dieses
Modul unabhängig testen und ist unabhängig von PokéAPI/Streamlit.
"""
import math
import random

# ---------------------------------------------------------------------------
# Typen: Farben (für Badges) und deutsche Bezeichnungen
# ---------------------------------------------------------------------------

TYPE_COLORS = {
    "normal": "#A8A878", "fire": "#F08030", "water": "#6890F0", "electric": "#F8D030",
    "grass": "#78C850", "ice": "#98D8D8", "fighting": "#C03028", "poison": "#A040A0",
    "ground": "#E0C068", "flying": "#A890F0", "psychic": "#F85888", "bug": "#A8B820",
    "rock": "#B8A038", "ghost": "#705898", "dragon": "#7038F8", "dark": "#705848",
    "steel": "#B8B8D0", "fairy": "#EE99AC",
}

TYPE_NAMES_DE = {
    "normal": "Normal", "fire": "Feuer", "water": "Wasser", "electric": "Elektro",
    "grass": "Pflanze", "ice": "Eis", "fighting": "Kampf", "poison": "Gift",
    "ground": "Boden", "flying": "Flug", "psychic": "Psycho", "bug": "Käfer",
    "rock": "Gestein", "ghost": "Geist", "dragon": "Drache", "dark": "Unlicht",
    "steel": "Stahl", "fairy": "Fee",
}

# Angreifender Typ -> {verteidigender Typ: Multiplikator} (nur Abweichungen von 1.0)
TYPE_CHART = {
    "normal":   {"rock": 0.5, "ghost": 0.0, "steel": 0.5},
    "fire":     {"fire": 0.5, "water": 0.5, "grass": 2.0, "ice": 2.0, "bug": 2.0,
                 "rock": 0.5, "dragon": 0.5, "steel": 2.0},
    "water":    {"fire": 2.0, "water": 0.5, "grass": 0.5, "ground": 2.0, "rock": 2.0, "dragon": 0.5},
    "electric": {"water": 2.0, "electric": 0.5, "grass": 0.5, "ground": 0.0, "flying": 2.0, "dragon": 0.5},
    "grass":    {"fire": 0.5, "water": 2.0, "grass": 0.5, "poison": 0.5, "ground": 2.0,
                 "flying": 0.5, "bug": 0.5, "rock": 2.0, "dragon": 0.5, "steel": 0.5},
    "ice":      {"fire": 0.5, "water": 0.5, "grass": 2.0, "ice": 0.5, "ground": 2.0,
                 "flying": 2.0, "dragon": 2.0, "steel": 0.5},
    "fighting": {"normal": 2.0, "ice": 2.0, "poison": 0.5, "flying": 0.5, "psychic": 0.5,
                 "bug": 0.5, "rock": 2.0, "ghost": 0.0, "dark": 2.0, "steel": 2.0, "fairy": 0.5},
    "poison":   {"grass": 2.0, "poison": 0.5, "ground": 0.5, "rock": 0.5, "ghost": 0.5,
                 "steel": 0.0, "fairy": 2.0},
    "ground":   {"fire": 2.0, "electric": 2.0, "grass": 0.5, "poison": 2.0, "flying": 0.0,
                 "bug": 0.5, "rock": 2.0, "steel": 2.0},
    "flying":   {"electric": 0.5, "grass": 2.0, "fighting": 2.0, "bug": 2.0, "rock": 0.5, "steel": 0.5},
    "psychic":  {"fighting": 2.0, "poison": 2.0, "psychic": 0.5, "dark": 0.0, "steel": 0.5},
    "bug":      {"fire": 0.5, "grass": 2.0, "fighting": 0.5, "poison": 0.5, "flying": 0.5,
                 "psychic": 2.0, "ghost": 0.5, "dark": 2.0, "steel": 0.5, "fairy": 0.5},
    "rock":     {"fire": 2.0, "ice": 2.0, "fighting": 0.5, "ground": 0.5, "flying": 2.0,
                 "bug": 2.0, "steel": 0.5},
    "ghost":    {"normal": 0.0, "psychic": 2.0, "ghost": 2.0, "dark": 0.5},
    "dragon":   {"dragon": 2.0, "steel": 0.5, "fairy": 0.0},
    "dark":     {"fighting": 0.5, "psychic": 2.0, "ghost": 2.0, "dark": 0.5, "fairy": 0.5},
    "steel":    {"fire": 0.5, "water": 0.5, "electric": 0.5, "ice": 2.0, "rock": 2.0,
                 "steel": 0.5, "fairy": 2.0},
    "fairy":    {"fire": 0.5, "fighting": 2.0, "poison": 0.5, "dragon": 2.0, "dark": 2.0, "steel": 0.5},
}


def type_effectiveness(move_type: str, defender_types: list) -> float:
    """Multipliziert die Effektivität über alle Typen des Verteidigers."""
    multiplier = 1.0
    chart = TYPE_CHART.get(move_type, {})
    for t in defender_types:
        multiplier *= chart.get(t, 1.0)
    return multiplier


# ---------------------------------------------------------------------------
# Statuswerte (vereinfachte, aber an die echten Spiele angelehnte Formel:
# IV=31, EV=0, neutrale Nature)
# ---------------------------------------------------------------------------

def calculate_stat(base: int, level: int, is_hp: bool = False) -> int:
    if is_hp:
        return math.floor(((2 * base + 31) * level) / 100) + level + 10
    return math.floor(((2 * base + 31) * level) / 100) + 5


def calculate_all_stats(base_stats: dict, level: int) -> dict:
    return {
        "hp": calculate_stat(base_stats.get("hp", 50), level, is_hp=True),
        "atk": calculate_stat(base_stats.get("atk", 50), level),
        "def": calculate_stat(base_stats.get("def", 50), level),
        "spa": calculate_stat(base_stats.get("spa", 50), level),
        "spd": calculate_stat(base_stats.get("spd", 50), level),
        "spe": calculate_stat(base_stats.get("spe", 50), level),
    }


# ---------------------------------------------------------------------------
# Erfahrungspunkte
# ---------------------------------------------------------------------------

def xp_for_level(level: int) -> int:
    """Benötigte Gesamt-EP, um dieses Level zu erreichen (mittelschnelle Kurve)."""
    return level ** 3


def xp_gain(opponent_level: int) -> int:
    return opponent_level * 6 + random.randint(5, 15)


# ---------------------------------------------------------------------------
# Schaden
# ---------------------------------------------------------------------------

def calculate_damage(attacker_level: int, move: dict, attacker_stats: dict,
                      defender_stats: dict, attacker_types: list, defender_types: list):
    """Gibt (schaden, effektivitäts_multiplikator) zurück."""
    power = move.get("power") or 40
    if move.get("damage_class") == "special":
        atk_stat, def_stat = attacker_stats["spa"], defender_stats["spd"]
    else:
        atk_stat, def_stat = attacker_stats["atk"], defender_stats["def"]

    stab = 1.5 if move.get("type") in attacker_types else 1.0
    eff = type_effectiveness(move.get("type"), defender_types)

    if eff == 0:
        return 0, eff

    base = (((2 * attacker_level / 5) + 2) * power * (atk_stat / max(1, def_stat)) / 50) + 2
    random_factor = random.uniform(0.85, 1.0)
    damage = base * stab * eff * random_factor
    return max(1, math.floor(damage)), eff


# ---------------------------------------------------------------------------
# Fangchance (vereinfachte Version der Gen-3+-Formel)
# ---------------------------------------------------------------------------

def try_catch(current_hp: int, max_hp: int, capture_rate: int, ball_bonus: float = 1.0):
    """Gibt (gefangen: bool, chance: float 0..1) zurück."""
    max_hp = max(1, max_hp)
    a = ((3 * max_hp - 2 * max(0, current_hp)) * capture_rate * ball_bonus) / (3 * max_hp)
    chance = min(1.0, max(0.02, a / 255))
    return random.random() < chance, chance
