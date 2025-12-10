# symbols.py
# ------------------------------------------
# SYMBOLDATEN, GEWICHTUNGEN, MULTIPLIKATOREN
# UND FREISCHALT-SYSTEM
# ------------------------------------------

# 🔣 Alle Symbole der Slot
SYMBOLS = [
    "🍒", "🍋", "🍊", "🍉", "⭐", "🍇", "7️⃣", "🃏"
]

# 🎲 Basisgewichtungen – bestimmen Seltenheit
BASE_WEIGHTS = [
20, 20, 15, 15, 1, 10, 7, 5
]

# 💰 Multiplikatoren pro Symbol
SYMBOL_BASE_MULTI = {
    "🍒": 1,
    "🍋": 1,
    "🍊": 2,
    "🍉": 2,
    "⭐": None,  # Scatter Sonderfall
    "🍇": 3,
    "7️⃣": 7,
    "🃏": 10,
}

# Nicht-lineare Boni für 3,4,5 Treffer
BONUS_MULTI = {
    3: 1,
    4: 10,
    5: 100,
}

# Scatter Belohnung (Coins, nicht Cent!)
SCATTER = "⭐"
SCATTER_REWARD = 50

WILD = "🃏"


# ------------------------------------------
# SYMBOL-FREISCHALTUNG
# ------------------------------------------

def init_symbol_unlock_state():
    order = SYMBOLS[:]  # Vollständige Reihenfolge
    unlocked = [order[0]]  # Nur 🍒 am Anfang aktiv
    next_index = 1  # zeigt auf 🍋 als nächstes Symbol

    return {
        "order": order,
        "unlocked": unlocked,
        "next_index": next_index
    }


def unlock_next_symbol(state):
    """
    Schaltet EIN Symbol nach Reihenfolge frei.
    """
    if state["next_index"] >= len(state["order"]):
        return None

    sym = state["order"][state["next_index"]]
    state["unlocked"].append(sym)
    state["next_index"] += 1
    return sym
