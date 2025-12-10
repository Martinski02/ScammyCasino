# main.py
from slot_1.slot_1 import slot_1


def title_screen(game_name):
    print(game_name + "\n")
    input("Press Enter to start...")

def main_menu():
    print(f"\n=== Scammy Casino === \n")
    instruction = "\nChoose an option 1-6: "
    options = ["Gamble", "Shop", "Profil", "Social", "Settings", "Quit"]

    for i in range(len(options)):
        print(f"{i + 1}) {options[i]}")

    choice = input(instruction)

    if choice.isdigit():
        choice = int(choice)
        if 1 <= choice <= 6:
            return choice

    print("Invalid selection. Please press 1-6.")
    return None

def menu_gamble(guthaben):
    """
    Ruft slot_1(guthaben) auf.
    Erwartet, dass slot_1 entweder
      - ("main", updated_guthaben) zurückgibt
      - oder nur updated_guthaben zurückgibt
    -> Passt das Format automatisch an.
    """
    result = slot_1(guthaben)

    # Wenn slot_1 ein Tuple ("main", guthaben) zurückgibt -> return as-is
    if isinstance(result, tuple) and len(result) == 2:
        return result

    # Wenn nur guthaben zurückgegeben wurde, packe es sauber ein
    return "main", result

def menu_shop():
    print("\n=== Shop ===")
    input("Press Enter to return...")
    return "main", None

def menu_profile():
    print("\n=== Profile ===")
    input("Press Enter to return...")
    return "main", None

def menu_social():
    print("\n=== Social ===")
    input("Press Enter to return...")
    return "main", None

def menu_settings():
    print("\n=== Settings ===")
    input("Press Enter to return...")
    return "main", None

def game_loop():
    title_screen("===Scammy Casino===")

    guthaben = 0   # Startguthaben in Cent (zB 100.00 Coins); setz sinnvollen Startwert
    state = "main"

    while True:
        if state == "main":
            selection = main_menu()
            if selection == 1:
                # wechsel in gamble: menu_gamble gibt (state, guthaben) zurück
                state, maybe_guthaben = menu_gamble(guthaben)
                if maybe_guthaben is not None:
                    guthaben = maybe_guthaben
            elif selection == 2:
                state, _ = menu_shop()
            elif selection == 3:
                state, _ = menu_profile()
            elif selection == 4:
                state, _ = menu_social()
            elif selection == 5:
                state, _ = menu_settings()
            elif selection == 6:
                print("Goodbye!")
                break
            else:
                state = "main"

if __name__ == "__main__":
    game_loop()