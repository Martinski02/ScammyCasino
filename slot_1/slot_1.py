# slot_1.py
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
    unlock_next_symbol
)

from slot_1.lines import (
    init_line_state,
    get_active_lines,
    upgrade_palindrom,
    upgrade_spiegel,
)

# ---------------------------------------------------------
# FARBEN (Fallback ohne colorama)
# ---------------------------------------------------------
try:
    from colorama import Fore, Style, init
    init(autoreset=True)
    GREEN = Fore.GREEN
    RED   = Fore.RED
    YELLOW = Fore.YELLOW
    CYAN = Fore.CYAN
    MAGENTA = Fore.MAGENTA
    RESET = Style.RESET_ALL
except Exception:
    GREEN = RED = YELLOW = CYAN = MAGENTA = RESET = ""


# ---------------------------------------------------------
# SPIELZUSTAND
# ---------------------------------------------------------
bet = 10  # 10 Cent
slot_level_multiplier = 1
field_boosts = {}

symbols = SYMBOLS
weights = BASE_WEIGHTS[:]

symbol_state = init_symbol_unlock_state()
unlocked_symbols = symbol_state["unlocked"]

line_state = init_line_state()

spin_speed_upgrades = 0
spin_speed = 5.0 / 12  # 12 Frames → 5 Sekunden


# ---------------------------------------------------------
# UPGRADE-EFFEKTE
# ---------------------------------------------------------
def effect_unlock_symbol():
    new = unlock_next_symbol(symbol_state)
    if new:
        print(GREEN + f"Neues Symbol freigeschaltet: {new}" + RESET)
    else:
        print("Alle Symbole freigeschaltet!")


def effect_increase_bet():
    global bet
    bet *= 2
    print(CYAN + f"Einsatz erhöht → {bet/100:.2f} Coins" + RESET)


def effect_increase_spin_speed():
    global spin_speed_upgrades, spin_speed

    spin_speed_upgrades += 1
    total = max(0.5, 5.0 - spin_speed_upgrades * 0.1)
    spin_speed = total / 12

    print(CYAN + f"Spin-Speed verbessert → {total:.2f}s" + RESET)


def effect_improve_symbol_chance():
    global weights
    new = weights[:]

    # verbessere seltene Symbole leicht
    for i in range(len(new)-1, max(-1, len(new)-4), -1):
        new[i] += 2

    weights[:] = new
    print(CYAN + "Seltene Symbole verstärkt." + RESET)


def effect_field_upgrade():
    col = random.randint(0, 4)
    row = random.randint(0, 2)
    field_boosts[(col, row)] = field_boosts.get((col, row), 0) + 1
    print(CYAN + f"Feld ({col},{row}) verbessert." + RESET)


def effect_palindrom_upgrade():
    msg = upgrade_palindrom(line_state)
    print(GREEN + msg + RESET)


def effect_spiegel_upgrade():
    msg = upgrade_spiegel(line_state)
    print(GREEN + msg + RESET)


# ---------------------------------------------------------
# UPGRADE-DATENBANK
# ---------------------------------------------------------
upgrades = {
    "symbol_unlock": {
        "name": "Symbol freischalten",
        "level": 1,
        "prices": [1,5,25,100,500,2500,10000,50000,250000],
        "effect": effect_unlock_symbol
    },
    "bet": {
        "name": "Höhere Einsätze",
        "level": 1,
        "prices": [5,50,500,5000,50000],
        "effect": effect_increase_bet
    },
    "spin_speed": {
        "name": "Schnellere Spins",
        "level": 1,
        "prices": [10,25,100,500],
        "effect": effect_increase_spin_speed
    },
    "symbol_chance": {
        "name": "Bessere Symbolchancen",
        "level": 1,
        "prices": [15,75,300,1200],
        "effect": effect_improve_symbol_chance
    },
    "palindrom": {
        "name": "Palindrom-Linien erweitern",
        "level": 1,
        "prices": [50, 250],
        "effect": effect_palindrom_upgrade
    },
    "spiegel": {
        "name": "Spiegelpaare freischalten",
        "level": 1,
        "prices": [10] * 200,
        "effect": effect_spiegel_upgrade
    },
    "field": {
        "name": "Feld Upgrade",
        "level": 1,
        "prices": [40,200,1000],
        "effect": effect_field_upgrade
    }
}


# ---------------------------------------------------------
# REEL SPIN
# ---------------------------------------------------------
def spin_reels():
    return [
        random.choices(symbols, weights=weights, k=3)
        for _ in range(5)
    ]


# ---------------------------------------------------------
# ASCII SLOT-BOX (OHNE Bildschirm löschen)
# ---------------------------------------------------------
def print_slot_box(reels):
    CELL_WIDTH = 9

    def pad(sym):
        return str(sym).center(CELL_WIDTH)

    TOP    = "╔" + ("═" + "═"*CELL_WIDTH + "╦")*4 + "═" + "═"*CELL_WIDTH + "╗"
    MID    = "╠" + ("═" + "═"*CELL_WIDTH + "╬")*4 + "═" + "═"*CELL_WIDTH + "╣"
    BOTTOM = "╚" + ("═" + "═"*CELL_WIDTH + "╩")*4 + "═" + "═"*CELL_WIDTH + "╝"

    print(YELLOW + TOP)
    for row in range(3):
        line = "║"
        for col in range(5):
            sym = reels[col][row]
            # Anzeige NUR wenn freigeschaltet
            if sym in unlocked_symbols:
                display = sym
            else:
                display = "🔒"
            line += pad(display) + "║"
        print(YELLOW + line)
        if row < 2:
            print(YELLOW + MID)
    print(YELLOW + BOTTOM + RESET)

# ---------------------------------------------------------
# ANIMATION
# ---------------------------------------------------------
def spin_animation(final_reels):
    frames = 12
    step = 2

    for frame in range(frames - 1):
        current = []
        for col in range(5):

            threshold = frames - 1 - ((4 - col) * step)
            if frame < threshold:
                current.append([random.choice(symbols) for _ in range(3)])
            else:
                current.append(final_reels[col])

        sys.stdout.write("\033[2J\033[H")  # Nur hier löschen!
        sys.stdout.flush()

        print(MAGENTA + "SPINNING...\n" + RESET)
        print_slot_box(current)
        time.sleep(spin_speed)


# ---------------------------------------------------------
# GEWINNPRÜFUNG
# ---------------------------------------------------------
def check_and_apply_wins(reels, guthaben):
    total = 0
    active_lines = get_active_lines(line_state)

    # -------- SCATTER --------
    scatter_count = sum(
        1 for col in reels for sym in col
        if sym == SCATTER and sym in unlocked_symbols
    )

    if scatter_count >= 3:
        print(GREEN + f"SCATTER BONUS! +{SCATTER_REWARD} Coins" + RESET)
        total += SCATTER_REWARD * 100  # in Cent


    # -------- LINIEN --------
    for line in active_lines:
        start = reels[0][line[0]]

        # kein Gewinnsymbol
        if start not in unlocked_symbols:
            continue

        # Scatter zählt NICHT auf Linien
        if start == SCATTER:
            continue

        count = 1
        for w in range(1, 5):
            sym = reels[w][line[w]]

            # Wild ersetzt Symbol (aber nicht Scatter)
            if sym == start or sym == WILD:
                count += 1
            else:
                break

        if count >= 3:
            base = SYMBOL_BASE_MULTI[start]  # Coins
            bonus = BONUS_MULTI[count]

            boosts = sum(field_boosts.get((c, line[c]), 0) for c in range(5))
            field_multi = 1 + 0.5 * boosts

            win_coins = bet * base * count * bonus * field_multi * slot_level_multiplier
            win = int(win_coins)

            total += win

            print(
                GREEN +
                f"Linie {line}: {count}x {start} | Bonus x{bonus} | Feld x{field_multi:.1f} → +{win/100:.2f} Coins"
                + RESET
            )

    # TOTAL
    if total == 0:
        print(RED + "Kein Gewinn.\n" + RESET)
    else:
        print(GREEN + f"\nTOTAL GEWINN: +{total/100:.2f} Coins\n" + RESET)

    return guthaben + total


# ---------------------------------------------------------
# SPIN-MODUS
# ---------------------------------------------------------
def slot_spin(guthaben):
    print(MAGENTA + "\n=== SPIN MODUS ===")
    print(CYAN + "Enter = Spin | q = zurück" + RESET)

    while True:
        cmd = input("> ")
        if cmd.lower() == "q":
            return guthaben

        reels = spin_reels()
        spin_animation(reels)

        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()

        print_slot_box(reels)
        guthaben = check_and_apply_wins(reels, guthaben)
        print(CYAN + f"Guthaben: {guthaben/100:.2f} Coins\n" + RESET)


# ---------------------------------------------------------
# UPGRADE-MENÜ
# ---------------------------------------------------------
def slot_upgrade_menu(guthaben):
    while True:
        print("\n=== UPGRADES ===")

        keys = list(upgrades.keys())

        for i, key in enumerate(keys):
            u = upgrades[key]
            print(f"{i+1}) {u['name']} (Lv {u['level']})")

            if u["level"] > len(u["prices"]):
                print("   MAXED OUT")
            else:
                price = u["prices"][u["level"] - 1] * 100
                print(f"   Preis: {price/100:.2f} Coins")

        print(f"{len(keys)+1}) Zurück")

        choice = input("> ")
        if not choice.isdigit():
            print("Ungültig.")
            continue

        choice = int(choice)

        if choice == len(keys) + 1:
            return guthaben

        key = keys[choice - 1]
        u = upgrades[key]

        if u["level"] > len(u["prices"]):
            print("MAXED")
            continue

        price = u["prices"][u["level"] - 1] * 100
        if guthaben < price:
            print("Nicht genug Coins!")
            continue

        guthaben -= price
        u["effect"]()
        u["level"] += 1

        print(GREEN + "Upgrade gekauft!" + RESET)


# ---------------------------------------------------------
# SLOT-HAUPTMENÜ
# ---------------------------------------------------------
def slot_1(guthaben):
    while True:
        print("\n=== SLOT 1 ===")
        print("Freigeschaltet:", ", ".join(unlocked_symbols))
        print(f"Einsatz: {bet/100:.2f} | Linien: {len(get_active_lines(line_state))} | Speed: {spin_speed*12:.2f}s")
        print("1) Spin")
        print("2) Upgrades")
        print("3) Zurück")

        choice = input("> ")
        if choice == "1":
            guthaben = slot_spin(guthaben)
        elif choice == "2":
            guthaben = slot_upgrade_menu(guthaben)
        elif choice == "3":
            return "main", guthaben
        else:
            print("Ungültige Eingabe.")