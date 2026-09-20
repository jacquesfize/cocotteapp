"""Minimal RFC 5545 (iCalendar) generation for meal-plan entries."""

from datetime import datetime, timedelta, timezone

from .models import MealType

# Heure de début (locale « flottante ») et durée de chaque repas.
MEAL_START = {
    MealType.BREAKFAST: (8, 0),
    MealType.LUNCH: (12, 30),
    MealType.DINNER: (19, 30),
    MealType.SNACK: (16, 0),
}
MEAL_DURATION = timedelta(hours=1)
MEAL_LABEL = dict(MealType.choices)


def escape_text(value):
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\r\n", "\\n")
        .replace("\n", "\\n")
        .replace("\r", "\\n")
    )


def fold_line(line):
    """Fold to 75 octets per line, never splitting a multi-byte character."""
    if len(line.encode("utf-8")) <= 75:
        return line
    parts, current, size = [], "", 0
    limit = 75
    for char in line:
        n = len(char.encode("utf-8"))
        if size + n > limit:
            parts.append(current)
            current, size, limit = "", 0, 74  # continuation lines start with a space
        current += char
        size += n
    parts.append(current)
    return "\r\n ".join(parts)


def build_ics(entries, calendar_name="Cocotte"):
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Cocotte//Planning//FR",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{escape_text(calendar_name)}",
    ]
    for entry in entries:
        hour, minute = MEAL_START.get(entry.meal_type, (19, 30))
        start = datetime(entry.date.year, entry.date.month, entry.date.day, hour, minute)
        end = start + MEAL_DURATION
        meal = MEAL_LABEL.get(entry.meal_type, entry.meal_type)
        description = f"{meal} - {entry.servings} portion(s)"
        lines += [
            "BEGIN:VEVENT",
            f"UID:cocotte-mealplan-{entry.pk}@cocotte",
            f"DTSTAMP:{stamp}",
            f"DTSTART:{start.strftime('%Y%m%dT%H%M%S')}",
            f"DTEND:{end.strftime('%Y%m%dT%H%M%S')}",
            f"SUMMARY:{escape_text(entry.recipe.title)}",
            f"DESCRIPTION:{escape_text(description)}",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    return "\r\n".join(fold_line(line) for line in lines) + "\r\n"
