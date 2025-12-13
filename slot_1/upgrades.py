# slot_1/upgrades.py
"""
Upgrade-System – stabil & konsistent

Enthält:
- Upgrade-Definitionen (UPGRADE_DEFS)
- Upgrade-Visibility + Requirement-System (Schritt 4.5 Teil 1)
- apply_upgrade(...)
- get_upgrades_for_menu(...)

Statuslogik:
KAUFBAR:
    Coins >= Preis
    UND alle Requirements erfüllt

SICHTBAR:
    Coins >= Preis
    ODER mindestens ein Requirement erfüllt

UNSICHTBAR:
    Coins < Preis
    UND keine Requirements erfüllt
"""

from typing import Dict, Any, Optional
import random

# ---------------------------------------------------------
# IMPORTS (optional, aber vorhanden im Projekt)
# ---------------------------------------------------------
try:
    from slot_1.symbols import unlock_next_symbol
except Exception:
    unlock_next_symbol = None

try:
    from slot_1.lines import upgrade_palindrom, upgrade_spiegel
except Exception:
    upgrade_palindrom = None
    upgrade_spiegel = None


# ---------------------------------------------------------
# EFFECTS
# ---------------------------------------------------------
def _effect_unlock_symbol(slot_state, symbol_state, line_state, weights=None):
    if unlock_next_symbol:
        new = unlock_next_symbol(symbol_state)
        if new:
            print(f"Neues Symbol freigeschaltet: {new}")
        else:
            print("Alle Symbole bereits freigeschaltet!")
        return


def _effect_increase_bet(slot_state, symbol_state, line_state, weights=None):
    slot_state["bet"] *= 2
    print(f"Einsatz erhöht → {slot_state['bet']/100:.2f} Coins")


def _effect_increase_spin_speed(slot_state, symbol_state, line_state, weights=None):
    upgrades = slot_state.get("spin_speed_upgrades", 0) + 1
    slot_state["spin_speed_upgrades"] = upgrades
    slot_state["spin_total_duration"] = max(0.5, 5.0 - upgrades * 0.1)

    print(
        f"Spin-Speed verbessert → {slot_state['spin_total_duration']:.2f}s "
        f"(Upgrades: {upgrades})"
    )

    if slot_state["spin_total_duration"] <= 0.5:
        slot_state["spin_speed_maxed"] = True


def _effect_field_boost(slot_state, symbol_state, line_state, weights=None):
    col = random.randint(0, 4)
    row = random.randint(0, 2)
    fb = slot_state.setdefault("field_boosts", {})
    fb[(col, row)] = fb.get((col, row), 0) + 1
    print(f"Feld ({col},{row}) verbessert (+50%).")


def _effect_palindrom_upgrade(slot_state, symbol_state, line_state, weights=None):
    if upgrade_palindrom:
        print(upgrade_palindrom(line_state))


def _effect_spiegel_upgrade(slot_state, symbol_state, line_state, weights=None):
    if upgrade_spiegel:
        print(upgrade_spiegel(line_state))


def _effect_scatter_chance(slot_state, symbol_state, line_state, weights=None):
    old = slot_state.get("scatter_p", 0.05)
    new = min(0.20, old + 0.01)
    slot_state["scatter_p"] = new
    print(f"Scatter-Chance erhöht: {old:.3f} → {new:.3f}")


# ---------------------------------------------------------
# UPGRADE DEFINITIONS
# ---------------------------------------------------------
UPGRADE_DEFS = {
    "symbol_unlock": {
        "name": "Symbol freischalten",
        "prices": [1, 2, 4, 8, 16, 32, 64],
        "effect": _effect_unlock_symbol,
    },
    "bet": {
        "name": "Höhere Einsätze",
        "prices": [10, 50, 500, 5000],
        "effect": _effect_increase_bet,
    },
    "spin_speed": {
        "name": "Schnellere Spins",
        "prices": [2.5, 5, 10, 20, 50, 100],
        "effect": _effect_increase_spin_speed,
    },
    "field": {
        "name": "Feld-Upgrade",
        "prices": [10] * 999,
        "effect": _effect_field_boost,
    },
    "palindrom": {
        "name": "Palindrom-Linien",
        "prices": [10, 1000],
        "effect": _effect_palindrom_upgrade,
    },
    "spiegel": {
        "name": "Spiegelpaare",
        "prices": [100] * 200,
        "effect": _effect_spiegel_upgrade,
    },
    "scatter_chance": {
        "name": "Scatter-Wahrscheinlichkeit",
        "prices": [50, 500, 5000, 50000],
        "effect": _effect_scatter_chance,
    },
}


# ---------------------------------------------------------
# REQUIREMENTS (Schritt 4.5 Teil 1)
# ---------------------------------------------------------
UPGRADE_REQUIREMENTS = {
    "bet": {
        "requires_upgrade": "symbol_unlock",
    },
    "spin_speed": {
        "requires_upgrade": "symbol_unlock",
    },
    "field": {
        "requires_upgrade": "symbol_unlock",
    },
    "palindrom": {
        "requires_upgrade": "bet",
    },
    "spiegel": {
        "requires_upgrade": "palindrom",
    },
    "scatter_chance": {
        "requires_symbol": "⭐",
    },
}


# ---------------------------------------------------------
# REQUIREMENT CHECKER
# ---------------------------------------------------------
def check_requirements(key: str, slot_state: Dict[str, Any]) -> list[str]:
    """
    Gibt eine Liste fehlender Requirements zurück.
    Leere Liste = alle erfüllt.
    """
    missing = []
    levels = slot_state.get("upgrade_levels", {})
    unlocked_symbols = slot_state["symbol_state"]["unlocked"]

    req = UPGRADE_REQUIREMENTS.get(key, {})

    if "requires_upgrade" in req:
        req_key = req["requires_upgrade"]
        if levels.get(req_key, 1) <= 1:
            missing.append(f"Upgrade '{req_key}'")

    if "requires_symbol" in req:
        sym = req["requires_symbol"]
        if sym not in unlocked_symbols:
            missing.append(f"Symbol {sym}")

    return missing


# ---------------------------------------------------------
# APPLY UPGRADE
# ---------------------------------------------------------
def apply_upgrade(
    key: str,
    guthaben_cent: int,
    slot_state: Dict[str, Any],
    symbol_state: Dict[str, Any],
    line_state: Dict[str, Any],
    weights: Optional[list] = None,
) -> int:

    if key not in UPGRADE_DEFS:
        print("Ungültiges Upgrade.")
        return guthaben_cent

    levels = slot_state.setdefault("upgrade_levels", {})
    lvl = levels.get(key, 1)
    prices = UPGRADE_DEFS[key]["prices"]

    if lvl > len(prices):
        print("Upgrade bereits MAXED.")
        return guthaben_cent

    cost_cent = int(prices[lvl - 1] * 100)
    if guthaben_cent < cost_cent:
        print("Nicht genug Coins.")
        return guthaben_cent

    missing = check_requirements(key, slot_state)
    if missing:
        print("Upgrade gesperrt. Fehlend:", ", ".join(missing))
        return guthaben_cent

    # bezahlen
    guthaben_cent -= cost_cent

    # Effekt
    UPGRADE_DEFS[key]["effect"](slot_state, symbol_state, line_state, weights)

    # Level erhöhen
    levels[key] = lvl + 1

    print(f"{UPGRADE_DEFS[key]['name']} gekauft! (Lv {levels[key]})")
    return guthaben_cent


# ---------------------------------------------------------
# MENU HELPER
# ---------------------------------------------------------
def get_upgrades_for_menu(slot_state: Dict[str, Any]) -> list[dict]:
    """
    Liefert alle Upgrades mit Status:
    - sichtbar
    - kaufbar
    - maxed
    - locked_reason
    """
    out = []
    levels = slot_state.get("upgrade_levels", {})
    coins = slot_state["guthaben"]

    for key, meta in UPGRADE_DEFS.items():
        lvl = levels.get(key, 1)
        prices = meta["prices"]
        maxed = lvl > len(prices)

        price_cent = None if maxed else int(prices[lvl - 1] * 100)
        missing = check_requirements(key, slot_state)

        # Sichtbarkeit
        visible = False
        if not missing:
            visible = True
        elif price_cent is not None and coins >= price_cent:
            visible = True

        if not visible:
            continue

        purchasable = (
            not maxed
            and price_cent is not None
            and coins >= price_cent
            and not missing
        )

        out.append({
            "key": key,
            "name": meta["name"],
            "level": lvl,
            "price_cent": price_cent,
            "maxed": maxed,
            "purchasable": purchasable,
            "locked_reason": missing,
        })

    return out