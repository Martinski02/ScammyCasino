# slot_1/upgrades.py
"""
Upgrade-System (Option B - strukturierter slot_state)
- Definiert Upgrade-Metadaten (name, prices, effect)
- Bietet apply_upgrade(key, guthaben, slot_state, symbol_state, line_state, weights=None)
- Bietet helper get_upgrades_for_menu(slot_state) zur Anzeige
"""

import random
from typing import Optional, Dict, Any

# Wir benutzen vorhandene Line/Symbol-Funktionen falls vorhanden.
# Diese Importe sind optional — wenn du lokale Funktionen nutzt, können
# sie entfallen. Falls lines.unlock/... an anderer Stelle sind,
# kannst du die Effekte anpassen.
try:
    from slot_1.symbols import unlock_next_symbol
except Exception:
    # Fallback: wenn nicht importierbar, upgrades.py nutzt symbol_state direkt.
    unlock_next_symbol = None

try:
    from slot_1.lines import upgrade_palindrom as lines_upgrade_palindrom
    from slot_1.lines import upgrade_spiegel as lines_upgrade_spiegel
except Exception:
    lines_upgrade_palindrom = None
    lines_upgrade_spiegel = None


# -------------------------
# Hilfs-Funktionen / Effekte
# -------------------------
def _effect_unlock_symbol(slot_state: Dict[str, Any], symbol_state: Dict[str, Any], line_state: Dict[str, Any], weights: Optional[list] = None):
    """
    Schaltet das nächste Symbol frei. Erwartet symbol_state mit
    { 'order': [...], 'unlocked': [...], 'next_index': int }.
    Wenn slot_1.symbols.unlock_next_symbol importierbar ist, verwenden wir das.
    """
    if unlock_next_symbol:
        new = unlock_next_symbol(symbol_state)
        if new:
            print(f"Neues Symbol freigeschaltet: {new}")
            return
        else:
            print("Alle Symbole bereits freigeschaltet!")
            return

    # Fallback - manuelle Manipulation
    if symbol_state["next_index"] >= len(symbol_state["order"]):
        print("Alle Symbole bereits freigeschaltet!")
        return

    sym = symbol_state["order"][symbol_state["next_index"]]
    symbol_state["unlocked"].append(sym)
    symbol_state["next_index"] += 1
    print(f"Neues Symbol freigeschaltet: {sym}")


def _effect_increase_bet(slot_state: Dict[str, Any], symbol_state: Dict[str, Any], line_state: Dict[str, Any], weights: Optional[list] = None):
    slot_state["bet"] = int(slot_state["bet"] * 2)
    print(f"Einsatz erhöht → {slot_state['bet']/100:.2f} Coins")


def _effect_increase_spin_speed(slot_state: Dict[str, Any], symbol_state: Dict[str, Any], line_state: Dict[str, Any], weights: Optional[list] = None):
    # expect slot_state keys: 'spin_upgrades','spin_frames','base_spinspeed','spin_speed'
    slot_state["spin_upgrades"] = slot_state.get("spin_upgrades", 0) + 1
    base = slot_state.get("base_spinspeed", 5.0)
    frames = slot_state.get("spin_frames", 12)
    total_duration = max(0.5, base - slot_state["spin_upgrades"] * 0.1)
    slot_state["spin_speed"] = total_duration / frames
    print(f"Spin-Speed verbessert → Gesamtdauer: {total_duration:.2f}s")

    # Wenn wir das Max erreicht haben, setze das upgrade level auf max (der Aufrufer macht das UI)
    if total_duration <= 0.5:
        slot_state["spin_speed_maxed"] = True


def _effect_improve_symbol_chance(slot_state: Dict[str, Any], symbol_state: Dict[str, Any], line_state: Dict[str, Any], weights: Optional[list] = None):
    if weights is None:
        print("Fehler: weights müssen übergeben werden, um Symbolwahrscheinlichkeiten zu verbessern.")
        return
    # erhöhe die Gewichte der seltensten 3 Symbole leicht
    idxs = sorted(range(len(weights)), key=lambda i: weights[i])[:3]
    for i in idxs:
        weights[i] += 2
    print("Seltenere Symbole etwas häufiger gemacht.")


def _effect_field_boost(slot_state: Dict[str, Any], symbol_state: Dict[str, Any], line_state: Dict[str, Any], weights: Optional[list] = None):
    col = random.randint(0, 4)
    row = random.randint(0, 2)
    fb = slot_state.setdefault("field_boosts", {})
    fb[(col, row)] = fb.get((col, row), 0) + 1
    print(f"Feld ({col},{row}) verbessert (+50%).")


def _effect_palindrom_upgrade(slot_state: Dict[str, Any], symbol_state: Dict[str, Any], line_state: Dict[str, Any], weights: Optional[list] = None):
    # prefer lines module method if present
    if lines_upgrade_palindrom:
        msg = lines_upgrade_palindrom(line_state)
        print(msg)
        return
    # fallback: manipulate line_state directly if structure known
    pal = line_state.get("pal_step", 1)
    if pal == 1:
        # append group2 if present on line_state (expecting constants somewhere else)
        if "PALINDROM_GROUP_2" in line_state:
            line_state["active"].extend(line_state["PALINDROM_GROUP_2"])
        line_state["pal_step"] = 2
        print("Palindrom-Gruppe 2 freigeschaltet!")
        return
    if pal == 2:
        if "PALINDROM_GROUP_3" in line_state:
            line_state["active"].extend(line_state["PALINDROM_GROUP_3"])
        line_state["pal_step"] = 3
        print("Palindrom-Gruppe 3 freigeschaltet!")
        return
    print("Alle Palindrom-Linien bereits freigeschaltet!")

def _effect_scatter_chance(slot_state, symbol_state, line_state, weights=None):
    """
    Erhöht die Wahrscheinlichkeit pro Walze, dass EIN Scatter entsteht.
    Maximal sinnvoll ~0.20 (20%)
    """
    old = slot_state.get("scatter_p", 0.05)

    # sanft erhöhen: +0.01 pro Upgrade
    new = min(0.20, old + 0.01)

    slot_state["scatter_p"] = new
    print(f"Scatter-Chance erhöht: {old:.3f} → {new:.3f}")


def _effect_spiegel_upgrade(slot_state: Dict[str, Any], symbol_state: Dict[str, Any], line_state: Dict[str, Any], weights: Optional[list] = None):
    if lines_upgrade_spiegel:
        msg = lines_upgrade_spiegel(line_state)
        print(msg)
        return
    # fallback: if line_state stores a list of pairs, use pair_index
    idx = line_state.get("pair_index", 0)
    pairs = line_state.get("SPIEGEL_PAARE", [])
    if idx < len(pairs):
        a, b = pairs[idx]
        line_state["active"].append(a)
        line_state["active"].append(b)
        line_state["pair_index"] = idx + 1
        print(f"Spiegelpaar {idx+1} freigeschaltet!")
        return
    print("Alle Spiegelpaare bereits freigeschaltet!")


# -------------------------
# Upgrade-DB (metadaten)
# -------------------------
# Preise sind in COINS (lesbar), apply_upgrade multipliziert *100 für CENT
UPGRADE_DEFS = {
    "symbol_unlock": {
        "name": "Symbol freischalten",
        "prices": [1, 5, 25, 100, 500, 2500, 10000],
        "effect": _effect_unlock_symbol
    },
    "bet": {
        "name": "Höhere Einsätze",
        "prices": [5, 50, 500, 5000],
        "effect": _effect_increase_bet
    },
    "spin_speed": {
        "name": "Schnellere Spins",
        "prices": [10, 25, 100, 500],
        "effect": _effect_increase_spin_speed
    },
    "field": {
        "name": "Feld Upgrade",
        "prices": [40, 200, 1000],
        "effect": _effect_field_boost
    },
    "palindrom": {
        "name": "Palindrom-Linien erweitern",
        "prices": [50, 250],
        "effect": _effect_palindrom_upgrade
    },
    "spiegel": {
        "name": "Spiegelpaare freischalten",
        # viele günstige Schritte ok
        "prices": [10] * 200,
        "effect": _effect_spiegel_upgrade
    },
    "scatter_chance": {
    "name": "Scatter Wahrscheinlichkeit erhöhen",
    "prices": [50, 150, 300, 600, 1200],
    "effect": _effect_scatter_chance
},
    # "symbol_chance": {
    #     "name": "Bessere Symbolchancen",
    #     "prices": [15, 75, 300, 1200],
    #     "effect": _effect_improve_symbol_chance
    # },    
}


# -------------------------
# Core: apply_upgrade()
# -------------------------
def apply_upgrade(key: str,
                  guthaben_cent: int,
                  slot_state: Dict[str, Any],
                  symbol_state: Dict[str, Any],
                  line_state: Dict[str, Any],
                  weights: Optional[list] = None) -> int:
    """
    Führt ein Upgrade aus:
    - key: upgrade-key (siehe UPGRADE_DEFS)
    - guthaben_cent: aktuelles Guthaben in CENT
    - slot_state, symbol_state, line_state: state-Objekte (dictionaries)
    - weights: falls das Upgrade die Wahrscheinlichkeiten anpasst (symbol-chance)

    Liefert aktualisiertes guthaben (in CENT) zurück.
    """

    if key not in UPGRADE_DEFS:
        print("Ungültiges Upgrade:", key)
        return guthaben_cent

    # initialisiere levels-Container
    levels = slot_state.setdefault("upgrade_levels", {})
    lvl = levels.get(key, 1)

    prices = UPGRADE_DEFS[key]["prices"]
    # maxed check
    if lvl > len(prices):
        print("Dieses Upgrade ist bereits MAXED OUT.")
        return guthaben_cent

    cost_coins = prices[lvl - 1]
    cost_cent = int(cost_coins * 100)

    if guthaben_cent < cost_cent:
        print("Nicht genug Coins!")
        return guthaben_cent

    # bezahle
    guthaben_cent -= cost_cent

    # effektausführung
    try:
        effect_fn = UPGRADE_DEFS[key]["effect"]
        # some effect functions need weights; we always pass them
        effect_fn(slot_state, symbol_state, line_state, weights)
    except Exception as e:
        print(f"Fehler beim Anwenden des Effekts: {e}")

    # level erhöhen
    levels[key] = lvl + 1

    # special: if spin_speed reached max, reflect in levels (optional)
    if slot_state.get("spin_speed_maxed", False) and key == "spin_speed":
        levels[key] = len(prices) + 1

    print(f"{UPGRADE_DEFS[key]['name']} gekauft! (neu: Level {levels[key]})")
    return guthaben_cent


# -------------------------
# UI Helper
# -------------------------
def get_upgrades_for_menu(slot_state: Dict[str, Any]) -> list:
    """
    Gibt eine Liste von dicts zurück, die im Upgrade-Menü gezeichnet werden können:
    [{ 'key':..., 'name':..., 'level':..., 'price_cent':..., 'maxed':... }, ...]
    """
    out = []
    levels = slot_state.get("upgrade_levels", {})
    for key, meta in UPGRADE_DEFS.items():
        lvl = levels.get(key, 1)
        prices = meta["prices"]
        maxed = lvl > len(prices)
        price_cent = None if maxed else int(prices[lvl - 1] * 100)
        out.append({
            "key": key,
            "name": meta["name"],
            "level": lvl,
            "price_cent": price_cent,
            "maxed": maxed
        })
    return out