# slot_1/slot_1.py
# Vollständig korrigiert, sauber formatiert, upgrades.py integriert,
# Freespins + Scatter-P-Wahrscheinlichkeit + Wild-Engine (WL1/S1)

import random
import time
import sys
from wcwidth import wcswidth

# ---------------------------------------------------------
# IMPORTS (Projekt)
# ---------------------------------------------------------
from slot_1.symbols import (
    SYMBOLS, BASE_WEIGHTS, SYMBOL_BASE_MULTI, BONUS_MULTI,
    SCATTER, SCATTER_REWARD, WILD, init_symbol_unlock_state
)
from slot_1.lines import init_line_state, get_active_lines
from slot_1.upgrades import apply_upgrade, get_upgrades_for_menu

# Farben
try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
    GREEN = Fore.GREEN; RED = Fore.RED
    YELLOW = Fore.YELLOW; CYAN = Fore.CYAN
    MAGENTA = Fore.MAGENTA; RESET = Style.RESET_ALL
except Exception:
    GREEN = RED = YELLOW = CYAN = MAGENTA = RESET = ""

# ---------------------------------------------------------
# NUMBER FORMATING
# ---------------------------------------------------------
def format_number(value: float | int, max_decimals: int = 3) -> str:
    value = float(value)

    # Kleine Werte normal anzeigen
    if value < 1:
        return f"{value:.2f}".rstrip("0").rstrip(".")

    suffixes = [
        (1_000_000_000, "b"),
        (1_000_000, "m"),
        (1_000, "k"),
    ]

    for threshold, suffix in suffixes:
        if value >= threshold:
            num = value / threshold
            formatted = f"{num:.{max_decimals}f}".rstrip("0").rstrip(".")
            return f"{formatted}{suffix}"

    # 1–999: max 2 Dezimalstellen, keine Fake-Rundung
    return f"{value:.2f}".rstrip("0").rstrip(".")


# ---------------------------------------------------------
# SCREEN HELPER
# ---------------------------------------------------------
def clear_screen():
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


# ---------------------------------------------------------
# STATE FACTORY
# ---------------------------------------------------------
def make_slot_state(start_guthaben_cent: int = 0):
    return {
        "guthaben": int(start_guthaben_cent),
        "bet": 10,
        "slot_multiplier": 1,

        # Symbole
        "symbols": SYMBOLS[:],
        "weights": BASE_WEIGHTS[:],
        "symbol_state": init_symbol_unlock_state(),

        # Scatter/Wild
        "scatter": SCATTER,
        "scatter_reward": SCATTER_REWARD,
        "scatter_p": 0.05,
        "wild": WILD,

        # Linien
        "line_state": init_line_state(),

        # Feldboosts
        "field_boosts": {},

        # Spin anim
        "spin_total_duration": 5.0,
        "spin_speed_upgrades": 0,

        # Upgrades
        "upgrade_levels": {},

        # Freespins
        "mode": None,
        "freespins": None,
        "freespin_trigger": None,
    }


# ---------------------------------------------------------
# UTILS
# ---------------------------------------------------------
def unlocked_symbols(state):
    return state["symbol_state"]["unlocked"]


# ---------------------------------------------------------
# SPIN REELS (mit Scatter-P pro Walze)
# ---------------------------------------------------------
def spin_reels(state):
    p = float(state["scatter_p"])
    scatter = state["scatter"]
    symbols = state["symbols"]
    weights = state["weights"]

    reels = []
    for _ in range(5):
        if random.random() < p:
            pos = random.randint(0, 2)
            allowed = [s for s in symbols if s != scatter]
            allowed_w = [w for s, w in zip(symbols, weights) if s != scatter]
            col = random.choices(allowed, weights=allowed_w, k=3)
            col[pos] = scatter
        else:
            col = random.choices(symbols, weights=weights, k=3)
        reels.append(col)
    return reels


# ---------------------------------------------------------
# ASCII BOX (wcwidth)
# ---------------------------------------------------------
def _visible_width(t):
    w = wcswidth(str(t))
    return w if w >= 0 else len(str(t))

def _pad_display(sym, width):
    s = str(sym)
    vis = _visible_width(s)
    if vis >= width:
        return " " + s
    pad = width - vis
    L = pad // 2
    R = pad - L
    return " " * L + s + " " * R

def print_slot_box(state, reels):
    CELL = 9
    TOP = "╔" + ("═"*CELL + "╦")*4 + "═"*CELL + "╗"
    MID = "╠" + ("═"*CELL + "╬")*4 + "═"*CELL + "╣"
    BOT = "╚" + ("═"*CELL + "╩")*4 + "═"*CELL + "╝"

    unlocked = set(unlocked_symbols(state))

    print(YELLOW + TOP)
    for r in range(3):
        line = "║"
        for c in range(5):
            sym = reels[c][r]
            disp = sym if sym in unlocked else "🔒"
            line += _pad_display(disp, CELL) + "║"
        print(YELLOW + line)
        if r < 2:
            print(YELLOW + MID)
    print(YELLOW + BOT + RESET)


# ---------------------------------------------------------
# ANIMATION
# ---------------------------------------------------------
def spin_animation(state, final_reels):
    total = max(0.5, float(state["spin_total_duration"]))
    base_frames = 12
    frames = max(6, int(round(base_frames * (total / 5.0))))
    step = max(1, frames // 6)
    SYMS = state["symbols"]

    for f in range(frames):
        current = []
        for col in range(5):
            thr = frames - 1 - ((4 - col) * step)
            if f < thr:
                current.append([random.choice(SYMS) for _ in range(3)])
            else:
                current.append(final_reels[col])
        clear_screen()
        print(MAGENTA + "SPINNING...\n" + RESET)
        print_slot_box(state, current)
        time.sleep(total / frames)


# ---------------------------------------------------------
# WILD ENGINE (WL1/S1)
# ---------------------------------------------------------
def evaluate_line_with_wilds(reels, line, state):
    WILD = state["wild"]
    SCATTER = state["scatter"]
    unlocked = set(state["symbol_state"]["unlocked"])

    def s_at(c):
        return reels[c][line[c]]

    # 1) Startsymbol suchen (erstes Nicht-Wild, Nicht-Scatter, unlocked)
    start = None
    for c in range(5):
        s = s_at(c)
        if s == WILD:
            continue
        if s == SCATTER:
            return 0, None, False
        if s not in unlocked:
            return 0, None, False
        start = s
        break

    # 2) Pure Wild Line
    if start is None:
        if WILD not in unlocked:
            return 0, None, False
        count = 0
        for c in range(5):
            if s_at(c) == WILD:
                count += 1
            else:
                break
        return count, WILD, True

    # 3) Normale Linie mit Wild als Joker
    count = 0
    for c in range(5):
        s = s_at(c)
        if s == SCATTER:
            break
        if s == start:
            count += 1
            continue
        if s == WILD and WILD in unlocked:
            count += 1
            continue
        break

    return count, start, False


# ---------------------------------------------------------
# GEWINNLOGIK + SCATTER-TRIGGER
# ---------------------------------------------------------
def check_and_apply_wins(state, reels):
    total = 0
    unlocked = set(unlocked_symbols(state))
    SCATTER = state["scatter"]

    # --- Scatter ---
    scat_count = sum(col.count(SCATTER) for col in reels)
    if SCATTER in unlocked and scat_count >= 3:
        rewards = {3: 50, 4: 150, 5: 500}
        reward = rewards.get(scat_count, 500)
        print(GREEN + f"{scat_count}x Scatter → +{format_number(reward)} Coins" + RESET)
        total += reward * 100
        state["freespin_trigger"] = scat_count
    else:
        state["freespin_trigger"] = None

    # --- Linien ---
    for line in get_active_lines(state["line_state"]):
        count, sym, is_w = evaluate_line_with_wilds(reels, line, state)
        if count < 3 or sym is None:
            continue

        base = SYMBOL_BASE_MULTI[sym]
        bonus = BONUS_MULTI[count]
        boosts = sum(state["field_boosts"].get((c, line[c]), 0) for c in range(5))
        field_multi = 1 + 0.5 * boosts

        win = int(state["bet"] * count * base * bonus * field_multi * state["slot_multiplier"])
        total += win

        fm = f" | Feld×{field_multi:.1f}" if boosts else ""
        print(GREEN + f"Linie {line}: {count}x {sym} | Bonus×{bonus}{fm} → +{format_number(win/100)} Coins" + RESET)

    # --- Ergebnis ---
    if total == 0:
        print(RED + "Kein Gewinn.\n" + RESET)
    else:
        print(GREEN + f"TOTAL: +{format_number(total/100)} Coins\n" + RESET)

    state["guthaben"] += total
    return state["guthaben"]


# ---------------------------------------------------------
# FREESPIN ENGINE
# ---------------------------------------------------------
def start_freespins(state, n):
    mapping = {3: 10, 4: 15, 5: 20}
    amount = mapping[n]
    print(GREEN + f"FREISPIELE START: {amount}" + RESET)

    state["mode"] = "freespins"
    state["freespins"] = {
        "remaining": amount,
        "trigger": n,
        "sticky_wilds": [],
    }

def run_freespin_mode(state):
    fs = state["freespins"]
    if not fs:
        state["mode"] = None
        return

    print(GREEN + "\n=== FREISPIELE ===" + RESET)

    while fs["remaining"] > 0:
        print(CYAN + f"FS übrig: {fs['remaining']}" + RESET)
        input("Enter = Freispin")

        reels = spin_reels(state)
        spin_animation(state, reels)
        clear_screen()
        print_slot_box(state, reels)
        check_and_apply_wins(state, reels)

        fs["remaining"] -= 1

    print(GREEN + "=== FREISPIELE ENDE ===" + RESET)
    state["mode"] = None
    state["freespins"] = None


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
        spin_animation(state, reels)
        clear_screen()
        print_slot_box(state, reels)
        check_and_apply_wins(state, reels)

        # Freespin Trigger?
        t = state.get("freespin_trigger")
        if t:
            start_freespins(state, t)
            run_freespin_mode(state)

        coins = state["guthaben"] / 100
        print(CYAN + f"Guthaben: {format_number(coins)} Coins" + RESET)


# ---------------------------------------------------------
# UPGRADE MENU
# ---------------------------------------------------------
def slot_upgrade_menu(state):
    while True:
        print("\n=== UPGRADES ===")
        items = get_upgrades_for_menu(state)

        for i, u in enumerate(items):
            line = f"{i+1}) {u['name']} (Lv {u['level']})"

            if u["maxed"]:
                line += " [MAX]"
                print(line)
                continue

            if u["purchasable"]:
                line += f"  → {format_number(u['price_cent']/100)} Coins"
                print(GREEN + line + RESET)
                continue

            # sichtbar, aber gesperrt
            line += " 🔒"
            print(YELLOW + line + RESET)

            if u["locked_reason"]:
                for reason in u["locked_reason"]:
                    print(f"     └─ benötigt: {reason}")
            else:
                price = format_number(u['price_cent']/100)
                print(f"     └─ benötigt: {price} Coins")


        print(f"{len(items)+1}) Zurück")
        ch = input("> ")

        if not ch.isdigit():
            print("Ungültig.")
            continue
        ch = int(ch)

        if ch == len(items) + 1:
            return state["guthaben"]
        if not (1 <= ch <= len(items)):
            print("Ungültig.")
            continue

        item = items[ch - 1]

        if item["maxed"]:
            print(RED + "❌ Dieses Upgrade ist bereits MAXED." + RESET)
            continue

        if not item["purchasable"]:
            print(RED + "❌ Dieses Upgrade ist gesperrt." + RESET)
            if item["locked_reason"]:
                for r in item["locked_reason"]:
                    print(f"   - benötigt: {r}")
            continue

        # ✅ nur hier darf gekauft werden
        state["guthaben"] = apply_upgrade(
            item["key"],
            state["guthaben"],
            state,
            state["symbol_state"],
            state["line_state"],
            state["weights"]
)


# ---------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------
def slot_1(guthaben):
    state = make_slot_state(start_guthaben_cent=guthaben)

    while True:
        if state.get("mode") == "freespins":
            run_freespin_mode(state)
            continue

        print("\n=== SLOT 1 ===")
        print("Freigeschaltet:", ", ".join(unlocked_symbols(state)))
        n = len(get_active_lines(state["line_state"]))
        print(f"Einsatz: {format_number(state['bet']/100)} | Linien: {n} | Spin: {state['spin_total_duration']:.2f}s")
        print("1) Spin")
        print("2) Upgrades")
        print("3) Zurück")

        ch = input("> ")

        if ch == "1":
            state["guthaben"] = slot_spin(state)
        elif ch == "2":
            state["guthaben"] = slot_upgrade_menu(state)
        elif ch == "3":
            return "main", state["guthaben"]
        else:
            print("Ungültige Eingabe.")
