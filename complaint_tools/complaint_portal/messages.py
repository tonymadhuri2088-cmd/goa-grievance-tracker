"""The texts of reminders and follow-up messages, in English and Konkani.

Officers always get English. Citizens get their message in the language their complaint was written in.
The Konkani texts should be read by a Konkani speaker before real use.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

IST = timezone(timedelta(hours=5, minutes=30))

# subject -> language -> text. Placeholders: {id} {label} {office} {due} {next_office} {previous}
TEMPLATES: Dict[str, Dict[str, str]] = {
    # To the officer
    "reminder_half": {
        "en": "Reminder: complaint {id} ({label}) at {office} has used half of its time limit. Please act by {due}.",
    },
    "reminder_final": {
        "en": "Final reminder: complaint {id} ({label}) is due by {due}. If it is not resolved, it moves to {next_office}.",
    },
    "reminder_final_last": {
        "en": "Final reminder: complaint {id} ({label}) is due by {due}. It is already with the last level.",
    },
    "escalated_to_you": {
        "en": "Complaint {id} ({label}) has moved to you ({office}): the time limit at {previous} passed.",
    },
    "no_officer": {
        "en": "Complaint {id} ({label}) has no officer at {office}. Please assign someone. It is due by {due}.",
    },
    # To the citizen
    "citizen_registered": {
        "en": "Your complaint {id} ({label}) is registered with {office}. Action is expected by {due}. "
              "Use your complaint ID to see its status.",
        "kok": "तुमची तक्रार {id} ({label}) {office} कडेन नोंद जाल्ली आसा. {due} पयलीं कारवाय जावपाची अपेक्षा आसा. "
              "स्थिती पळोवपाक तुमचो तक्रार क्रमांक वापरात.",
    },
    "citizen_reminded": {
        "en": "Update on complaint {id}: we have reminded {office}. Action is due by {due}.",
        "kok": "तक्रार {id} विशीं म्हायती: {office} क याद धाडल्ली आसा. {due} पयलीं कारवाय जावपाक जाय.",
    },
    "citizen_escalated": {
        "en": "Update on complaint {id}: it was not resolved in time and has moved to {office}.",
        "kok": "तक्रार {id} विशीं म्हायती: ठरिल्ल्या वेळार सुटली ना, म्हणून ती {office} कडेन धाडल्या.",
    },
    "citizen_resolved": {
        "en": "Complaint {id} ({label}) was marked resolved by {office}. If the problem is fixed, please confirm "
              "it (on WhatsApp, send 4). If it is not fixed, say so and it will move up.",
        "kok": "तक्रार {id} ({label}) {office} कडेन सुटली अशें नोंद केल्ली आसा. समस्या सुटली जाल्यार कृपा करून खात्री करात "
              "(वॉट्सॲपार 4 धाडात). सुटूंक ना जाल्यार तशें सांगात, ती वयल्या पातळेक वचतली.",
    },
}


def when_text(moment: Any) -> str:
    """A due time as text for a message, in India time, such as '9 Nov 2026, 5:30 PM'."""
    if not moment:
        return "the time limit"
    parsed = datetime.fromisoformat(moment) if isinstance(moment, str) else moment
    local = parsed.astimezone(IST)
    hour = local.hour % 12 or 12
    return f"{local.day} {local.strftime('%b %Y')}, {hour}:{local.minute:02d} {'AM' if local.hour < 12 else 'PM'}"


def render(subject: str, language: str, **values: Any) -> str:
    """Fill in a template. A language with no text for this subject falls back to English."""
    options = TEMPLATES[subject]
    if language == "kok":
        names = _konkani_names()
        values = {key: (names.get(value, value) if key in NAME_KEYS and isinstance(value, str) else value)
                  for key, value in values.items()}
    return options.get(language, options["en"]).format(**values)


# Values that are office, department or complaint type names. In Konkani text they are replaced by the charter's
# Konkani name when it has one.
NAME_KEYS = ("label", "office", "next_office")


def _konkani_names() -> Dict[str, str]:
    from complaintrouter.common import load_charter  # the charter of the active pack
    return load_charter().get("konkani_names", {})
