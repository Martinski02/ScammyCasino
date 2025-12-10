# slot_1/slot_1.py
import random
import time
import sys

# ---------------------------------------------------------
# IMPORTS
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

# Neu: ausgelagertes Upgrade-System
from slot_1.upgrades import apply_upgrade, get_upgrades_for_menu

# Farbe (fallback ohne colorama)
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
# HELPER
# ---------------------------------------------------------
def clear_screen():
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


# ---------------------------------------------------------
# SLOT STATE FACTORY
# ---------------------------------------------------------
def make_slot_state(start_guthaben_cent: int = 0):
    return {
        "guthaben": int(start_guthaben_cent),

        # Einsatz
        "bet": 10,  # 10 Cent

        # Multiplikator
        "slot_multiplier": 1,

        # Symboldaten
        "symbols": SYMBOLS[:],
        "weights": BASE_WEIGHTS[:],
        "symbol_state": init_symbol_unlock_state(),

        # Scatter / Wild
        "scatter": SCATTER,
        "scatter_reward": SCATTER_REWARD,
        "wild": WILD,

        # Linien
        "line_state": init_line_state(),

        # Feldboosts
        "field_boosts": {},

        # Spin Animation
        "spin_total_duration": 5.0,
        "spin_speed_upgrades": 0,

        # Upgrade-Level werden von upgrades.py verwendet
        "upgrade_levels": {}
    }


# ---------------------------------------------------------
# SYMBOL-UTILS
# ---------------------------------------------------------
def unlocked_symbols(state):
    return state["symbol_state"]["unlocked"]


# ---------------------------------------------------------
# REEL SPIN
# ---------------------------------------------------------
def spin_reels(state):
    return [
        random.choices(state["symbols"], weights=state["weights"], k=3)
        for _ in range(5)
    ]


# ---------------------------------------------------------
# ASCII SLOT BOX (sauber, ohne Fallback – wcwidth zwingend)
# ---------------------------------------------------------
from wcwidth import wcswidth

def print_slot_box(state, reels):
    """
    Zeichnet die Slot-Box. Emoji und Unicode werden sauber über wcwidth
    gemessen und exakt in der Mitte der Zellbreite zentriert.
    """

    CELL_WIDTH = 9  # sichtbare Breite jeder Zelle

    def visible_width(text: str) -> int:
        """Sichtbare Terminal-Breite (immer korrekt, da wcwidth existiert)."""
        w = wcswidth(str(text))
        return w if w >= 0 else 1  # wcwidth gibt -1 für unprintbare zurück

    def pad_display(sym: str, width: int) -> str:
        """
        Zentriert ein Symbol basierend auf wcswidth().
        Schneidet nichts ab, auch wenn Emoji breiter wirken.
        """
        s = str(sym)
        vis = visible_width(s)

        if vis >= width:
            # Wenn das Symbol breiter ist als die Zelle: etwas einrücken
            return " " + s

        pad_total = width - vis
        left = pad_total // 2
        right = pad_total - left
        return (" " * left) + s + (" " * right)

    # Rahmen
    TOP    = "╔" + ("═" * CELL_WIDTH + "╦") * 4 + "═" * CELL_WIDTH + "╗"
    MID    = "╠" + ("═" * CELL_WIDTH + "╬") * 4 + "═" * CELL_WIDTH + "╣"
    BOTTOM = "╚" + ("═" * CELL_WIDTH + "╩") * 4 + "═" * CELL_WIDTH + "╝"

    unlocked = state["symbol_state"]["unlocked"]

    print(YELLOW + TOP)
    for row in range(3):
        line = "║"
        for col in range(5):
            sym = reels[col][row]
            display = sym if sym in unlocked else "🔒"
            line += pad_display(display, CELL_WIDTH) + "║"
        print(YELLOW + line)

        if row < 2:
            print(YELLOW + MID)
    print(YELLOW + BOTTOM + RESET)


# ---------------------------------------------------------
# ANIMATION
# ---------------------------------------------------------
def spin_animation(state, final_reels):
    total = max(0.5, float(state["spin_total_duration"]))
    baseline_frames = 12
    frames = max(6, int(baseline_frames * (total / 5.0)))
    step = max(1, int(frames / 6))
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
# GEWINNPRÜFUNG
# ---------------------------------------------------------
def check_and_apply_wins(state, reels):
    total = 0
    active_lines = get_active_lines(state["line_state"])
    unlocked = unlocked_symbols(state)

    # --- Scatter Check ---
    scatter_count = sum(col.count(state["scatter"]) for col in reels)
    if state["scatter"] in unlocked and scatter_count >= 3:
        print(GREEN + f"SCATTER BONUS! +{state['scatter_reward']} Coins" + RESET)
        total += int(state["scatter_reward"] * 100)

    # --- Liniengewinne ---
    for line in active_lines:
        start = reels[0][line[0]]

        if start not in unlocked:
            continue
        if start == state["scatter"]:
            continue

        count = 1
        for w in range(1, 5):
            if reels[w][line[w]] == start:
                count += 1
            else:
                break

        if count >= 3:
            base_multi = SYMBOL_BASE_MULTI.get(start)
            bonus = BONUS_MULTI.get(count, 1)

            boosts = sum(state["field_boosts"].get((c, line[c]), 0) for c in range(5))
            field_multi = 1 + 0.5 * boosts

            win = int(state["bet"] * count * base_multi * bonus * field_multi * state["slot_multiplier"])
            total += win

            fm = f" | Feld×{field_multi:.1f}" if boosts else ""
            print(GREEN + f"Linie {line}: {count}x {start} | Bonus×{bonus}{fm} → +{win/100:.2f} Coins" + RESET)

    if total == 0:
        print(RED + "Kein Gewinn.\n" + RESET)
    else:
        print(GREEN + f"\nTOTAL GEWINN: +{total/100:.2f} Coins\n" + RESET)

    state["guthaben"] += total
    return state["guthaben"]


# ---------------------------------------------------------
# SPIN MODE
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
        except:
            pass

        clear_screen()
        print_slot_box(state, reels)
        check_and_apply_wins(state, reels)

        print(CYAN + f"Guthaben: {state['guthaben']/100:.2f} Coins\n" + RESET)


# ---------------------------------------------------------
# UPGRADE MENU → benutzt upgrades.py
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

        if not 1 <= choice <= len(items):
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
# SLOT MAIN MENU
# ---------------------------------------------------------
def slot_1(guthaben):
    state = make_slot_state(start_guthaben_cent=guthaben)

    while True:
        print("\n=== SLOT 1 ===")
        print("Freigeschaltet:", ", ".join(unlocked_symbols(state)))
        print(f"Einsatz: {state['bet']/100:.2f} | Linien: {len(get_active_lines(state['line_state']))} | Spin: {state['spin_total_duration']:.2f}s")
        print("1) Spin")
        print("2) Upgrades")
        print("3) Zurück")

        choice = input("> ")
        if choice == "1":
            slot_spin(state)
        elif choice == "2":
            slot_upgrade_menu(state)
        elif choice == "3":
            return "main", state["guthaben"]
        else:
            print("Ungültige Eingabe.")
