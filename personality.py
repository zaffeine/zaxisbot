"""
Mjautomat's personality. Slightly hostile, slightly stupid, deeply
committed to nobody touching their sens. Import these into cogs instead
of hardcoding tone-specific strings elsewhere.
"""

YES_MESSAGES = [
    "Good kitty.",
    "Acceptable.",
    "Good. Do not touch it.",
    "Configuration stable. Good kitty.",
    "Sens incident avoided.",
    "Very good. Carry on.",
]

NO_MESSAGES = [
    "CHANGE IT BACK, RIGHT NYEOW!!!!",
    "What the fuck did I tell you.",
    "0 DAYS SINCE LAST SENS INCIDENT.",
    "PUT IT BACK.",
    "You had ONE job.",
    "Revert your settings immediately.",
]

# Escalating patience for repeated invalid answers. Index == current streak.
INVALID_ESCALATION = [
    "Please answer YES or NO.",
    "I said YES or NO.",
    "there are TWO OPTIONS",
    "u r gonk",
]
INVALID_ESCALATION_FINAL = "gonk"


def format_sens_question(user_row: dict) -> str:
    dpi = user_row.get("dpi")
    sens = user_row.get("sens")
    if dpi and sens:
        edpi = dpi * sens
        return f"Are you still running {dpi} DPI / {sens} in-game sens ({edpi:.0f} eDPI)? (reply yes or no)"
    return "Have you changed your settings? (reply yes or no)"


def format_no_reply(user_row: dict) -> str:
    import random

    dpi = user_row.get("dpi")
    sens = user_row.get("sens")
    base = random.choice(NO_MESSAGES)
    if dpi and sens:
        edpi = dpi * sens
        return f"{base} Get it back to {edpi:.0f} eDPI."
    return base
