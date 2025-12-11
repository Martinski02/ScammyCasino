# slot_1/slot_1.py
# Bereinigte, vollständige Version — upgrades.py angebunden, Scatter + Freespin-State,
# stabile ASCII-Box (wcwidth), saubere Animation, keine Syntaxfehler.
#
# Voraussetzungen:
#  - wcwidth installiert (wcswidth)
#  - slot_1.symbols, slot_1.lines, slot_1.upgrades existieren wie in deinem Projekt
#
# Hinweis: Freespin-Modus ist als funktionaler Placeholder implementiert — es läuft
# durch X Freespins, nutzt dieselbe Gewinnlogik; später kannst du Sticky-Wilds / Multipliers ergänzen.

import random
import time
import sys

from wcwidth import wcswidth

# ---------------------------------------------------------
# IMPORTS AUS DEM PROJEKT
# ---------------------------------------------------------
from slot_1.symbols import (
    SYMBOLS,
    BASE_WEIGHTS,
    SYMBOL_BASE_MULTI,
    BONUS_MULTI,
    SCATTER,
    SCATTER_REWARD,
    WILD,
    init_symbol_unlock_state,
)

from slot_1.lines import (
    init_line_state,
    get_active_lines,
)

# ausgelagertes Upgrade-System
from slot_1.upgrades import apply_upgrade, get_upgrades_for_menu

# Farbe (optional)
try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
    GREEN = Fore.GREEN
    RED = Fore.RED
    YELLOW = Fore.YELLOW
    CYAN = Fore.CYAN
    MAGENTA = Fore.MAGENTA
    RESET = Style.RESET_ALL
except Exception:
    GREEN = RED = YELLOW = CYAN = MAGENTA = RESET = ""


# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------
def clear_screen():
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


# ---------------------------------------------------------
# STATE FACTORY
# ---------------------------------------------------------
def make_slot_state(start_guthaben_cent: int = 0):
    """Erzeugt zentrales slot_state dict."""
    return {
        # Guthaben
        "guthaben": int(start_guthaben_cent),

        # Einsatz (Cent)
        "bet": 10,

        # Slot-Multiplikator (zukunft)
        "slot_multiplier": 1,

        # Symboldaten (kopierbar, veränderbar)
        "symbols": SYMBOLS[:],
        "weights": BASE_WEIGHTS[:],
        "symbol_state": init_symbol_unlock_state(),

        # Scatter / Wild
        "scatter": SCATTER,
        "scatter_reward": SCATTER_REWARD,  # Coins (not cent)
        "scatter_p": 0.05,  # Startchance pro Walze, genau ein Scatter zu setzen
        "wild": WILD,

        # Linien
        "line_state": init_line_state(),

        # Feld-Boosts
        "field_boosts": {},

        # Animation
        "spin_total_duration": 5.0,
        "spin_speed_upgrades": 0,

        # Upgrade-level container (wird von upgrades.py benutzt)
        "upgrade_levels": {},

        # Spielmodus / Freespins
        "mode": None,  # None | "freespins"
        "freespins": None,  # wenn mode == "freespins", dict mit keys below
    }


# ---------------------------------------------------------
# SYMBOL-UTILS
# ---------------------------------------------------------
def unlocked_symbols(state):
    return state["symbol_state"]["unlocked"]


# ---------------------------------------------------------
# REEL SPIN (mit Scatter-Mechanik)
# ---------------------------------------------------------
def spin_reels(state):
    """
    Für jede Walze:
      - mit Wahrscheinlichkeit state['scatter_p'] platzieren wir genau 1 Scatter an einer zufälligen Zeile (0..2)
      - sonst normale Walze: 3 Symbole per reel drawn using state['weights']
    Symbole (inkl. Wild) werden unabhängig gezogen; Display & Gewinn-Logik
    entscheidet später, ob locked Symbole zählen.
    """
    reels = []
    p = float(state.get("scatter_p", 0.05))
    scatter = state["scatter"]

    symbols = state["symbols"]
    weights = state["weights"]

    for col in range(5):
        if random.random() < p:
            # Diese Walze bekommt genau einen Scatter an random row
            pos = random.randint(0, 2)
            # Ziehe normale Symbole, aber ohne Scatter (sonst können 2+ Scatter auf einer Walze entstehen)
            allowed = [s for s in symbols if s != scatter]
            allowed_w = [w for s, w in zip(symbols, weights) if s != scatter]
            col_syms = random.choices(allowed, weights=allowed_w, k=3)
            col_syms[pos] = scatter
            reels.append(col_syms)
        else:
            # Normale Walze (Scatter kann nicht mehrfach pro Walze entstehen)
            reels.append(random.choices(symbols, weights=weights, k=3))

    return reels


# ---------------------------------------------------------
# ASCII-BOX (verwendet wcswidth für korrekte Zentrierung)
# ---------------------------------------------------------
def _visible_width(text: str) -> int:
    w = wcswidth(str(text))
    return w if w >= 0 else len(str(text))


def _pad_display(sym: str, width: int) -> str:
    s = str(sym)
    vis = _visible_width(s)
    if vis >= width:
        # Symbol breiter oder gleich: minimal einrücken, vermeide Trunkierung
        return " " + s
    pad_total = width - vis
    left = pad_total // 2
    right = pad_total - left
    return (" " * left) + s + (" " * right)


def print_slot_box(state, reels):
    """Zeichnet die 5x3 Box; nicht-freigeschaltete Symbole werden als 🔒 angezeigt."""
    CELL_WIDTH = 9
    TOP = "╔" + ("═" * CELL_WIDTH + "╦") * 4 + "═" * CELL_WIDTH + "╗"
    MID = "╠" + ("═" * CELL_WIDTH + "╬") * 4 + "═" * CELL_WIDTH + "╣"
    BOTTOM = "╚" + ("═" * CELL_WIDTH + "╩") * 4 + "═" * CELL_WIDTH + "╝"

    us = unlocked_symbols(state)

    print(YELLOW + TOP)
    for row in range(3):
        line = "║"
        for col in range(5):
            sym = reels[col][row]
            display = sym if sym in us else "🔒"
            line += _pad_display(display, CELL_WIDTH) + "║"
        print(YELLOW + line)
        if row < 2:
            print(YELLOW + MID)
    print(YELLOW + BOTTOM + RESET)


# ---------------------------------------------------------
# ANIMATION
# ---------------------------------------------------------
def spin_animation(state, final_reels):
    total = max(0.5, float(state.get("spin_total_duration", 5.0)))
    baseline_frames = 12
    frames = max(6, int(round(baseline_frames * (total / 5.0))))
    step = max(1, int(round(frames / 6)))
    SYMS = state["symbols"]

    for frame in range(frames):
        current = []
        for col in range(5):
            threshold = frames - 1 - ((4 - col) * step)
            if frame < threshold:
                current.append([random.choice(SYMS) for _ in range(3)])
            else:
                current.append(final_reels[col])

        clear_screen()
        print(MAGENTA + "SPINNING...\n" + RESET)
        print_slot_box(state, current)
        time.sleep(total / frames)


# ---------------------------------------------------------
# FREESPIN-ENGINE (Trigger + Lauf)
# ---------------------------------------------------------
def start_freespins(state, trigger_count):
    """
    Setzt Freespins im state. trigger_count ist Anzahl Scatters (3/4/5).
    Wir legen aktuelle Freespins in state['freespins'] ab und set mode.
    """
    mapping = {3: 10, 4: 15, 5: 20}
    amount = mapping.get(trigger_count, 10)
    state["freespins"] = {
        "remaining": amount,
        "trigger_count": trigger_count,
        "sticky_wilds": [],  # placeholder: future sticky wild implementation
    }
    state["mode"] = "freespins"
    print(GREEN + f"FREISPIELE: {amount} gestartet (aus {trigger_count} Scatters)!" + RESET)


def run_freespin_mode(state):
    """
    Ausführung der Freespins: simple placeholder implementation.
    Führt so viele Spins durch wie state['freespins']['remaining'] und kehrt dann zurück.
    """
    if not state.get("freespins"):
        print("Keine Freespins aktiv.")
        state["mode"] = None
        return

    print(GREEN + "\n=== FREISPIELE MODUS ===" + RESET)
    while state["freespins"]["remaining"] > 0:
        rem = state["freespins"]["remaining"]
        print(CYAN + f"Freispins übrig: {rem}" + RESET)
        input("Press Enter to spin a Freespin...")

        reels = spin_reels(state)
        try:
            spin_animation(state, reels)
        except Exception:
            pass

        clear_screen()
        print_slot_box(state, reels)
        # In Freespins normale Gewinne gelten; later: apply sticky wilds, multipliers etc.
        check_and_apply_wins(state, reels)

        state["freespins"]["remaining"] -= 1
        time.sleep(0.2)

    print(GREEN + "=== FREISPIELE BEENDET ===\n" + RESET)
    state["freespins"] = None
    state["mode"] = None


# ---------------------------------------------------------
# GEWINNPRÜFUNG (Lines + Scatter)
# ---------------------------------------------------------
def check_and_apply_wins(state, reels):
    """
    Prüft:
      - Scatter Instant-Rewards & Freespin-Trigger (nur wenn Scatter freigeschaltet)
      - Linien (nur freigeschaltete Symbole zählen; Scatter ausgeschlossen)
    Alle internen Werte in Cent.
    """
    total = 0
    active_lines = get_active_lines(state["line_state"])
    us = unlocked_symbols(state)

    # --- Scatter Count (unabhängig von Linien) ---
    scatter = state["scatter"]
    scatter_count = sum(col.count(scatter) for col in reels)

    if scatter in us and scatter_count >= 3:
        # Sofortgewinn (Coins -> Cent)
        rewards = {3: 50, 4: 150, 5: 500}
        reward_coins = rewards.get(scatter_count, 500)
        print(GREEN + f"{scatter_count}x SCATTER! Sofortgewinn +{reward_coins} Coins" + RESET)
        total += int(reward_coins * 100)

        # Freespin-Trigger (auch wenn bereits im Freespin-Modus, set/start)
        # start_freespins setzt state mode -> der Aufrufer entscheidet, wann run_freespin_mode ausgeführt wird
        start_freespins(state, scatter_count)

    # --- Linien prüfen ---
    for line in active_lines:
        # Bestimme Startsymbol: reels[0][line[0]]
        start = reels[0][line[0]]

        # Startsymbol muss freigeschaltet und kein Scatter sein
        if start not in us:
            continue
        if start == scatter:
            continue

        # Zähle sich fortsetzende gleiche Symbole (links->rechts)
        count = 1
        for w in range(1, 5):
            if reels[w][line[w]] == start:
                count += 1
            else:
                break

        if count >= 3:
            base_multi = SYMBOL_BASE_MULTI.get(start)
            if base_multi is None:
                # mapping fehlt => skip
                continue

            bonus = BONUS_MULTI.get(count, 1)

            boosts = sum(state["field_boosts"].get((c, line[c]), 0) for c in range(5))
            field_multi = 1 + 0.5 * boosts

            # Gewinn in Cent
            win = int(state["bet"] * count * base_multi * bonus * field_multi * state["slot_multiplier"])
            total += win

            fm = f" | Feld×{field_multi:.1f}" if boosts else ""
            print(GREEN + f"Linie {line}: {count}x {start} | Bonus×{bonus}{fm} → +{win/100:.2f} Coins" + RESET)

    # Ausgabe Gesamt
    if total == 0:
        print(RED + "Kein Gewinn.\n" + RESET)
    else:
        print(GREEN + f"\nTOTAL GEWINN: +{total/100:.2f} Coins\n" + RESET)

    state["guthaben"] += total
    return state["guthaben"]


# ---------------------------------------------------------
# SPIN MODE (normal)
# ---------------------------------------------------------
def slot_spin(state):
    print(MAGENTA + "\n=== SPIN MODUS ===" + RESET)
    print(CYAN + "Enter = Spin | q = zurück" + RESET)

    while True:
        cmd = input("> ")
        if cmd.lower() == "q":
            return state["guthaben"]

        reels = spin_reels(state)

        try:
            spin_animation(state, reels)
        except Exception:
            pass

        clear_screen()
        print_slot_box(state, reels)
        check_and_apply_wins(state, reels)

        print(CYAN + f"Guthaben: {state['guthaben']/100:.2f} Coins\n" + RESET)


# ---------------------------------------------------------
# UPGRADE MENU -> benutzt upgrades.py
# ---------------------------------------------------------
def slot_upgrade_menu(state):
    while True:
        print("\n=== UPGRADES ===")

        items = get_upgrades_for_menu(state)
        for i, u in enumerate(items):
            print(f"{i+1}) {u['name']} (Lv {u['level']})")
            if u["maxed"]:
                print("   MAXED OUT")
            else:
                print(f"   Preis: {u['price_cent']/100:.2f} Coins")

        print(f"{len(items)+1}) Zurück")
        choice = input("> ")

        if not choice.isdigit():
            print("Ungültige Eingabe.")
            continue

        choice = int(choice)
        if choice == len(items) + 1:
            return state["guthaben"]

        if not (1 <= choice <= len(items)):
            print("Ungültige Auswahl.")
            continue

        item = items[choice - 1]
        key = item["key"]

        state["guthaben"] = apply_upgrade(
            key,
            state["guthaben"],
            state,
            state["symbol_state"],
            state["line_state"],
            state["weights"]
        )


# ---------------------------------------------------------
# SLOT ENTRY (called by game.py)
# ---------------------------------------------------------
def slot_1(guthaben):
    """
    Entry function used by your game.main
    Accepts guthaben in Cent (int). Returns ("main", updated_guthaben).
    """
    state = make_slot_state(start_guthaben_cent=guthaben)

    while True:
        # If freespin-mode has been set by a previous spin, run it immediately
        if state.get("mode") == "freespins":
            run_freespin_mode(state)
            # after freespins return to menu loop (don't autopick another action)
            continue

        print("\n=== SLOT 1 ===")
        print("Freigeschaltet:", ", ".join(unlocked_symbols(state)))
        num_lines = len(get_active_lines(state["line_state"]))
        print(f"Einsatz: {state['bet']/100:.2f} | Linien: {num_lines} | Spin-Time: {state['spin_total_duration']:.2f}s")
        print("1) Spin")
        print("2) Upgrades")
        print("3) Zurück")

        choice = input("> ")
        if choice == "1":
            state["guthaben"] = slot_spin(state)
        elif choice == "2":
            state["guthaben"] = slot_upgrade_menu(state)
        elif choice == "3":
            return "main", state["guthaben"]
        else:
            print("Ungültige Eingabe.")
