# lines.py
# ------------------------------------------------------------
# LINIENSYSTEM FÜR SLOT 1
# Jetzt mit:
#   - Palindrom-Upgrade (eigenes Upgrade)
#   - Spiegelpaar-Upgrade (eigenes Upgrade)
# ------------------------------------------------------------

# ------------------------------------------------------------
# 1) PALINDROM-GRUPPEN
# ------------------------------------------------------------

PALINDROM_GROUP_1 = [
[0,0,0,0,0],
[1,1,1,1,1],
[2,2,2,2,2],
[0,1,2,1,0],
[2,1,0,1,2],
[1,0,0,0,1],
[1,2,2,2,1],
[0,0,1,0,0],
[2,2,1,2,2]
]

PALINDROM_GROUP_2 = [
[0,1,0,1,0],
[0,1,1,1,0],
[1,0,1,0,1],
[1,1,0,1,1],
[1,1,2,1,1],
[1,2,1,2,1],
[2,1,1,1,2],
[2,1,2,1,2]
]

PALINDROM_GROUP_3 = [
[0,0,2,0,0],
[0,2,0,2,0],
[0,2,1,2,0],
[0,2,2,2,0],
[1,0,2,0,1],
[1,2,0,2,1],
[2,0,0,0,2],
[2,0,1,0,2],
[2,0,2,0,2],
[2,2,0,2,2]
]


# ------------------------------------------------------------
# 2) SPIEGELPAAR-GENERIERUNG
# ------------------------------------------------------------

def generate_all_lines():
    """Erzeugt alle 243 möglichen Linien (3^5)."""
    all_lines = []
    for a in range(3):
        for b in range(3):
            for c in range(3):
                for d in range(3):
                    for e in range(3):
                        all_lines.append([a,b,c,d,e])
    return all_lines


def is_palindrom(line):
    return line == list(reversed(line))


def generate_spiegel_paare():
    """Erzeugt alle Spiegelpaare, jedes Paar nur einmal."""
    all_lines = generate_all_lines()

    seen = set()
    pairs = []

    for line in all_lines:
        t = tuple(line)
        if t in seen:
            continue

        rev = tuple(reversed(line))

        # Palindrom überspringen
        if list(t) == list(rev):
            continue

        pairs.append((list(t), list(rev)))

        seen.add(t)
        seen.add(rev)

    return pairs


SPIEGEL_PAARE = generate_spiegel_paare()


# ------------------------------------------------------------
# 3) STATE INITIALISIERUNG
# ------------------------------------------------------------

def init_line_state():
    """
    'pal_step': 1..3    → welche Palindromgruppe aktiv
    'pair_index': Index der nächsten Spiegel-Freischaltung
    'active': Liste aktiver Linien
    """
    return {
        "pal_step": 1,
        "pair_index": 0,
        "active": PALINDROM_GROUP_1[:]
    }


# ------------------------------------------------------------
# 4) AKTIVE LINIEN ABRUFEN
# ------------------------------------------------------------

def get_active_lines(state):
    return state["active"]


# ------------------------------------------------------------
# 5) UPGRADE: PALINDROM-LINIEN
# ------------------------------------------------------------

def upgrade_palindrom(state):
    """Schaltet Palindromgruppe 2 → 3 → MAX frei."""
    if state["pal_step"] == 1:
        state["active"].extend(PALINDROM_GROUP_2)
        state["pal_step"] = 2
        return "Palindrom-Gruppe 2 freigeschaltet!"

    if state["pal_step"] == 2:
        state["active"].extend(PALINDROM_GROUP_3)
        state["pal_step"] = 3
        return "Palindrom-Gruppe 3 freigeschaltet!"

    return "Alle Palindrom-Linien bereits freigeschaltet!"


# ------------------------------------------------------------
# 6) UPGRADE: SPIEGELPAARE
# ------------------------------------------------------------

def upgrade_spiegel(state):
    """Schaltet Spiegelpaare nacheinander frei."""
    if state["pair_index"] < len(SPIEGEL_PAARE):
        a, b = SPIEGEL_PAARE[state["pair_index"]]
        state["active"].append(a)
        state["active"].append(b)
        state["pair_index"] += 1
        return f"Spiegelpaar {state['pair_index']} freigeschaltet!"

    return "Alle Spiegelpaare bereits freigeschaltet!"
