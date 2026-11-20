"""The WhatsApp bot of the Goa Grievance Tracker.

A citizen chats with the portal's WhatsApp number. The bot does what the website does, and the WhatsApp number
itself proves who the citizen is (WhatsApp checks the phone), so there is no login:

  1  register a complaint (kind, category, description, place, photos, check, submit)
  2  track a complaint by its ID        3  list my complaints
  4  confirm that a problem is fixed (or say it is not: the complaint then moves up)
  5  a login code for the website       6  switch between English and Konkani

A citizen can also just describe the problem in their own words. With ANTHROPIC_API_KEY set, Claude works out the kind
and category (wa_ai.py), so the bot only asks for what is missing. Without a key, a few keywords decide and the bot
asks the rest. Everything the bot says comes from the fixed texts below, in English or Konkani, never from a model.

The other direction: when the portal sends a follow-up to a citizen who has written to the bot (registered, reminded,
escalated, marked resolved), it is also pushed to their WhatsApp (see deliver()). WhatsApp allows free-form messages
only within 24 hours of the person's last message, so later ones are kept in the portal log only (or sent through an
approved template when the Meta provider has one).

The Konkani texts are a first draft and should be read by a Konkani speaker before real use.
"""

import base64
import json
import threading
import time
import traceback
from collections import OrderedDict, deque
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional, Tuple

from complaint_portal import messages as texts
from complaint_portal.categories import (
    CIVIC, EMERGENCY, KIND_LABELS, MAX_PHOTO_BYTES, PHOTO_TYPES, PHOTOS_REQUIRED, POLICE, POLICE_NOTICE,
    available_kinds, categories_for, category_label,
)
from complaint_portal.language import detect_language
from complaint_portal.rules import AWAITING, CLOSED, OPEN, STATUS_TEXT
from complaint_portal.whatsapp import Inbound, Media, chunks
from complaint_portal.wa_ai import keyword_understanding
from complaint_portal.workflow import PortalError, iso, utcnow

WINDOW = timedelta(hours=23)      # WhatsApp: free-form replies are allowed for 24 hours after the person's message
STATE_MAX_AGE = timedelta(hours=12)   # a half-finished chat is forgotten after this long without a message
RATE_LIMIT = (20, 60.0)           # at most this many messages from one number per this many seconds
SEEN_LIMIT = 2000
LIST_LIMIT = 6
MIN_COMPLAINT_CHARS = 10
MAX_COMPLAINT_CHARS = 2000

YES = {"1", "yes", "y", "ok", "okay", "yeah", "haan", "होय", "हय", "व्हय", "submit"}
NO = {"2", "no", "n", "nahi", "ना", "न्ही", "न्हय"}
HOME = {"0", "menu", "cancel", "back", "stop", "मेनू", "रद्द", "फाटीं"}

KIND_KOK = {EMERGENCY: "आणीबाणी", CIVIC: "आणीबाणी न्हय (दिसाची नागरी समस्या)", POLICE: "पोलीस तक्रार"}
CATEGORY_KOK = {
    "emergency_rescue": "आणीबाणी सुटका",
    "fire_smoke": "आग आनी धूर",
    "ambulance_medical": "रुग्णवाहिका आनी वैद्यकीय आणीबाणी",
    "lpg_leak": "एलपीजी गॅस गळती",
    "hazardous_gas": "धोकादायक गॅस वा रसायन गळती",
    "flood_rescue": "पूर सुटका",
    "building_collapse": "इमारत कोसळप",
    "electrical_hazard": "वीज धोको, पडिल्ली तार",
    "road_accident": "सुटका जाय आशिल्लो रस्ते अपघात",
    "lift_trapped": "लिफ्टांत अडकप",
    "tree_fall": "रूख पडप",
    "drowning": "बुडप",
    "landslide": "दरड कोसळप",
    "water_supply": "उदक पुरवण",
    "drainage_sewerage": "गटारां आनी सांडपाणी",
    "garbage_sanitation": "कचरो आनी स्वच्छताय",
    "roads_footpaths": "रस्ते आनी पदपथ",
    "streetlights": "रस्त्यावयले दिवे",
    "flooding_waterlogging": "पूर आनी उदक सांचप",
    "public_health_strays": "सार्वजनीक आरोग्य आनी भटकीं जनावरां",
    "parks_infrastructure": "उद्यानां आनी सार्वजनीक सुविधा",
    "municipal_services_taxes": "नगरपालिका सेवा आनी कर",
    "other_civic": "हेर तक्रारी",
    "cybercrime": "सायबर गुन्हो आनी ऑनलायन फसवणूक",
    "financial_fraud": "आर्थिक फसवणूक",
    "lost_property": "हरयिल्ली वस्तू",
    "traffic_safety": "सार्वजनीक सुरक्षा आनी वाहतूक",
    "complaint_individuals": "व्यक्तींविशीं तक्रार",
}
POLICE_NOTICE_KOK = ("ही यंत्रणा फकत तुमची तक्रार नोंद करता आनी तिचो मागोवो घेता. गुन्हो घडलो काय आनी एफआयआर नोंद करपाक जाय काय हें फकत अधिकृत पोलीस अधिकारीच थारायतात.")
STATUS_KOK = {OPEN: "उक्ती. कारवाय चालू आसा.",
             AWAITING: "सुटली अशें नोंद केल्ली आसा. तुमच्या खात्रीची वाट पळयता.",
             CLOSED: "बंद केली. समस्या सुटली अशें तुमी खात्री केल्या."}

S: Dict[str, Dict[str, str]] = {
    "menu": {
        "en": "*Goa Grievance Tracker*\nReply with a number:\n1 - Register a complaint\n2 - Track a complaint\n3 - My complaints\n4 - Tell us a problem is fixed\n5 - Login code for the website\n6 - कोंकणी\n\nOr just write your problem in your own words. Send *0* any time to come back to this menu.\n_Student demo with invented data. Not an official government service._",
        "kok": "*गोंय तक्रार मागोवो*\nएका क्रमांकान जाप दियात:\n1 - तक्रार नोंद करात\n2 - तक्रारीचो मागोवो\n3 - म्हज्यो तक्रारी\n4 - समस्या सुटली अशें सांगात\n5 - वेबसायटीखातीर लॉगिन कोड\n6 - English\n\nवा तुमची समस्या तुमच्या स्वताच्या उतरांनी बरयात. ह्या मेनूंत परतपाक केन्नाय *0* धाडात.\n_कल्पीत म्हायतीचो विद्यार्थी डेमो. ही सरकारी अधिकृत सेवा न्हय._",
    },
    "send_text_first": {
        "en": "Thank you. To register a complaint, first write what the problem is (or send 1). I will ask for photos at the end.",
        "kok": "धन्यवाद. तक्रार नोंद करपाक पयलीं समस्या कितली तें बरयात (वा 1 धाडात). निमाणें फोटो विचारतलों.",
    },
    "cancelled": {
        "en": "Cancelled.",
        "kok": "रद्द केलें.",
    },
    "unclear": {
        "en": "I did not understand that. Here is the menu.",
        "kok": "तें म्हाका समजलें ना. हो मेनू.",
    },
    "oops": {
        "en": "Something went wrong on our side. Please try again. Send 0 for the menu.",
        "kok": "आमच्या वटेन कांय चुकलें. कृपा करून परत यत्न करात. मेनूखातीर 0 धाडात.",
    },
    "language_set": {
        "en": "Language set to English.",
        "kok": "भास कोंकणी केली.",
    },
    "need_account": {
        "en": "To register a complaint I need a few details about you first. This takes four short questions.\nWhat is your name?",
        "kok": "तक्रार नोंद करपाक पयलीं तुमची थोडी म्हायती जाय. चार नान्या प्रस्नांनी जाता.\nतुमचें नांव कितें?",
    },
    "bad_name": {
        "en": "Please send your name (2 to 100 letters).",
        "kok": "कृपा करून तुमचें नांव धाडात (2 ते 100 अक्षरां).",
    },
    "ask_taluk": {
        "en": "Thank you, {name}. Which taluka do you live in? Reply with a number:\n{list}",
        "kok": "धन्यवाद, {name}. तुमी कोणे तालुक्यांत रावतात? क्रमांकान जाप दियात:\n{list}",
    },
    "bad_choice": {
        "en": "Please reply with one of the numbers shown.",
        "kok": "कृपा करून दाखयल्ल्या क्रमांकां मदलो एक धाडात.",
    },
    "ask_ward": {
        "en": "Which ward do you live in? Send the ward number ({low} to {high}).",
        "kok": "तुमी कोणे वॉर्डांत रावतात? वॉर्ड क्रमांक धाडात ({low} ते {high}).",
    },
    "bad_ward": {
        "en": "That ward number is not in this taluka. Send a number from {low} to {high}.",
        "kok": "तो वॉर्ड क्रमांक ह्या तालुक्यांत ना. {low} ते {high} मदलो क्रमांक धाडात.",
    },
    "ask_home": {
        "en": "Last one: your home address, with street and area (at least 10 characters).",
        "kok": "निमाणें: तुमचो घराचो पत्तो, रस्तो आनी वाठारासयत (उणें तितलें 10 अक्षरां).",
    },
    "bad_address": {
        "en": "Please give the address in more detail, with street and area (10 to 300 characters).",
        "kok": "कृपा करून पत्तो रस्तो आनी वाठारासयत चड तपशिलान दियात (10 ते 300 अक्षरां).",
    },
    "account_ready": {
        "en": "Thank you, you are set up.",
        "kok": "धन्यवाद, तुमचें खातें तयार जालां.",
    },
    "ask_kind": {
        "en": "What kind of complaint is it? Reply with a number:\n{list}",
        "kok": "ही कसल्या प्रकारची तक्रार? क्रमांकान जाप दियात:\n{list}",
    },
    "ask_category": {
        "en": "Which type? Reply with a number:\n{list}",
        "kok": "कोणो प्रकार? क्रमांकान जाप दियात:\n{list}",
    },
    "emergency_note": {
        "en": "If anyone is in danger right now, call *112* first. This service cannot send help instantly.",
        "kok": "आत्तां कोणूय धोक्यांत आसल्यार पयलीं *112* वयर फोन करात. ही सेवा तात्काळ मदत धाडूंक शकना.",
    },
    "ask_text": {
        "en": "Describe the problem in a few words (at least 10 characters).",
        "kok": "समस्या थोडेच उतरांनी सांगात (उणें तितलें 10 अक्षरां).",
    },
    "bad_text": {
        "en": "Please describe the problem in 10 to 2000 characters.",
        "kok": "कृपा करून समस्या 10 ते 2000 अक्षरांनी सांगात.",
    },
    "ask_place": {
        "en": "Where is the problem? Send the street and area, or share a location pin. Send *same* to use your home address.",
        "kok": "समस्या खंय आसा? रस्तो आनी वाठार धाडात वा लोकेशन पिन शेअर करात. तुमचो घराचो पत्तो वापरपाक *same* धाडात.",
    },
    "ask_photos_civic": {
        "en": "Photos are optional. You may send up to {n} photos of the problem. Send *done* when finished, or *skip* to go without. ({have} of {n} received)",
        "kok": "फोटो ऐच्छीक. तुमी समस्येचे {n} मेरेन फोटो धाडूंक शकतात. जाल्यार *done*, नाका जाल्यार *skip* धाडात. ({have}/{n} मेळ्ळे)",
    },
    "ask_photos_police": {
        "en": "You may send up to {n} photos or PDF documents. Send *done* when finished, or *skip* to go without. ({have} of {n} received)",
        "kok": "तुमी {n} मेरेन फोटो वा PDF कागद धाडूंक शकतात. जाल्यार *done*, नाका जाल्यार *skip* धाडात. ({have}/{n} मेळ्ळे)",
    },
    "photo_got": {
        "en": "Got it ({have} of {n}).",
        "kok": "मेळ्ळो ({have}/{n}).",
    },
    "photo_need": {
        "en": "I still need {left} more photo(s).",
        "kok": "अजून {left} फोटो जाय.",
    },
    "photo_bad": {
        "en": "I could not use that file. Photos must be JPEG, PNG or WebP pictures (documents: PDF), under 4 MB.",
        "kok": "ती फायल वापरूंक जालें ना. फोटो JPEG, PNG वा WebP जावंक जाय (कागद: PDF), 4 MB भितर.",
    },
    "photo_wait": {
        "en": "Please send a photo (or *0* to cancel).",
        "kok": "कृपा करून फोटो धाडात (वा रद्द करपाक *0*).",
    },
    "check": {
        "en": "Please check your complaint:\nKind: {kind}\nType: {category}\nProblem: {text}\nPlace: {place}\nFiles: {files}\n\nReply *1* to submit or *2* to cancel.",
        "kok": "कृपा करून तुमची तक्रार तपासात:\nप्रकार: {kind}\nवर्ग: {category}\nसमस्या: {text}\nजाय: {place}\nफायली: {files}\n\nसादर करपाक *1*, रद्द करपाक *2* धाडात.",
    },
    "registered": {
        "en": "Complaint registered.\nID: *{id}*\nType: {label}\nSent to: {office}\nAction expected by: {due}\nI will message you here at each step. Send the ID any time to see the status.",
        "kok": "तक्रार नोंद जाली.\nक्रमांक: *{id}*\nवर्ग: {label}\nधाडल्लें कार्यालय: {office}\nकारवायेची अपेक्षा: {due}\nदर पावलार हांगाच संदेश धाडटलों. स्थिती पळोवपाक केन्नाय क्रमांक धाडात.",
    },
    "files_none": {
        "en": "none",
        "kok": "ना",
    },
    "files_n": {
        "en": "{n} attached",
        "kok": "{n} जोडले",
    },
    "ask_id": {
        "en": "Send your complaint ID (it looks like CMP-20261110-1234).",
        "kok": "तुमचो तक्रार क्रमांक धाडात (उदाहरण CMP-20261110-1234).",
    },
    "no_such": {
        "en": "I could not find a complaint with that ID for this mobile number. Check the ID, or send 3 to see your complaints.",
        "kok": "ह्या मोबायल क्रमांकाखातीर तो क्रमांक आशिल्ली तक्रार मेळ्ळी ना. क्रमांक तपासात, वा तुमच्यो तक्रारी पळोवपाक 3 धाडात.",
    },
    "track": {
        "en": "*{id}* - {label}\nStatus: {status}\nWith: {office}\n{due}Latest update (in English): {latest}",
        "kok": "*{id}* - {label}\nस्थिती: {status}\nसध्या हांगा: {office}\n{due}निमाणी म्हायती (इंग्रजींत): {latest}",
    },
    "due": {
        "en": "Action due by: {due}\n",
        "kok": "कारवाय जावपाची वेळ: {due}\n",
    },
    "list_head": {
        "en": "Your complaints (newest first):\n{list}\n\nSend a number to see one, or 0 for the menu.",
        "kok": "तुमच्यो तक्रारी (नवी पयली):\n{list}\n\nएक पळोवपाक क्रमांक धाडात, मेनूखातीर 0.",
    },
    "list_none": {
        "en": "You have no complaints yet. Send 1 to register one.",
        "kok": "तुमकां अजून एकूय तक्रार ना. नोंद करपाक 1 धाडात.",
    },
    "fix_none": {
        "en": "No complaint of yours is waiting for your confirmation right now.",
        "kok": "आत्तां तुमची एकूय तक्रार तुमच्या खात्रीची वाट पळयना.",
    },
    "fix_pick": {
        "en": "Which complaint? Reply with a number:\n{list}",
        "kok": "कोणती तक्रार? क्रमांकान जाप दियात:\n{list}",
    },
    "fix_ask": {
        "en": "*{id}* ({label}) was marked resolved. Is the problem fixed?\n1 - Yes, it is fixed\n2 - No, it is not fixed",
        "kok": "*{id}* ({label}) सुटली अशें नोंद केल्ली आसा. समस्या सुटली?\n1 - होय, सुटली\n2 - ना, सुटूंक ना",
    },
    "fix_code_shown": {
        "en": "Thank you. To close the complaint, reply with this code: *{code}* (valid {minutes} minutes).",
        "kok": "धन्यवाद. तक्रार बंद करपाक हो कोड धाडात: *{code}* ({minutes} मिनटां वैध).",
    },
    "fix_code_sent": {
        "en": "Thank you. {note} Reply with the 6-digit code to close the complaint.",
        "kok": "धन्यवाद. {note} तक्रार बंद करपाक 6 आंकड्यांचो कोड धाडात.",
    },
    "fix_closed": {
        "en": "Complaint {id} is closed. Thank you for confirming.",
        "kok": "तक्रार {id} बंद केली. खात्री केल्ल्याखातीर धन्यवाद.",
    },
    "fix_escalated": {
        "en": "Sorry the problem is not fixed. Complaint {id} is with {office} now.",
        "kok": "समस्या सुटूंक ना जाल्ल्याखातीर माफ करात. तक्रार {id} आत्तां {office} कडेन आसा.",
    },
    "code_bad": {
        "en": "Send the 6-digit code, or 0 to cancel.",
        "kok": "6 आंकड्यांचो कोड धाडात, वा रद्द करपाक 0.",
    },
    "login_code": {
        "en": "Your website login code is *{code}*. It lasts {minutes} minutes. Do not share it.",
        "kok": "तुमचो वेबसायट लॉगिन कोड *{code}*. तो {minutes} मिनटां वैध. कोणाकूय सांगूं नाकात.",
    },
    "login_sent": {
        "en": "{note}",
        "kok": "{note}",
    },
    "login_need": {
        "en": "You have no account yet. Send 1 to register a complaint, and I will set up your account.",
        "kok": "तुमकां अजून खातें ना. तक्रार नोंद करपाक 1 धाडात, तुमचें खातें हांव तयार करतलों.",
    },
}


def T(key: str, lang: str, **values: Any) -> str:
    options = S[key]
    return options.get(lang, options["en"]).format(**values)


def kind_label(kind: str, lang: str) -> str:
    return KIND_KOK[kind] if lang == "kok" else KIND_LABELS[kind]


def cat_label(kind: str, key: str, lang: str) -> str:
    return CATEGORY_KOK.get(key, category_label(kind, key)) if lang == "kok" else category_label(kind, key)


def _numbered(items: List[str]) -> str:
    return "\n".join(f"{number} - {item}" for number, item in enumerate(items, start=1))


def _number(text: str) -> Optional[int]:
    text = text.strip()
    return int(text) if text.isdigit() and len(text) < 6 else None


class Chat:
    """One incoming message being handled: who, their language, their saved place in a conversation, and the replies."""

    def __init__(self, mobile: str, lang: str, state: Dict[str, Any], now: datetime) -> None:
        self.mobile, self.lang, self.state, self.now = mobile, lang, state, now
        self.replies: List[str] = []

    def say(self, key: str, **values: Any) -> None:
        self.replies.append(T(key, self.lang, **values))

    @property
    def step(self) -> Optional[str]:
        return self.state.get("step")

    @property
    def data(self) -> Dict[str, Any]:
        return self.state.setdefault("d", {})

    def go(self, step: Optional[str]) -> None:
        self.state["step"] = step


class WhatsAppBot:
    """Handles one citizen message at a time (process) and pushes portal messages to WhatsApp (deliver)."""

    def __init__(self, portal: Any, channel: Any, understanding: Any = None, clock=utcnow,
                 background: bool = True) -> None:
        self.portal = portal
        self.channel = channel
        self.understanding = understanding
        self.clock = clock
        self.background = background
        self._locks: Dict[str, threading.Lock] = {}
        self._guard = threading.Lock()
        self._seen: "OrderedDict[str, bool]" = OrderedDict()
        self._recent: Dict[str, Deque[float]] = {}

    # ------------------------------------------------------------------ entry points

    def handle_async(self, messages: List[Inbound]) -> None:
        """Answer in the background, so the provider's webhook gets its 200 at once."""
        def work() -> None:
            for message in messages:
                try:
                    for reply in self.process(message):
                        sent, detail = self.channel.send_text(message.mobile, reply)
                        if not sent:
                            print(f"WhatsApp reply failed: {detail}")
                except Exception:
                    traceback.print_exc()
        threading.Thread(target=work, daemon=True).start()

    def process(self, message: Inbound) -> List[str]:
        """Work out the replies to one message. Safe to call from several threads."""
        with self._lock_for(message.mobile):
            if self._duplicate(message.message_id) or self._too_fast(message.mobile):
                return []
            now = self.clock()
            store = self.portal.store
            contact = store.wa_touch(message.mobile, iso(now), detect_language(message.text))
            try:
                state = json.loads(contact["state"] or "{}")
            except ValueError:
                state = {}
            # A conversation left alone for a long time starts again from the menu.
            last = state.get("at")
            if last and now - datetime.fromisoformat(last) > STATE_MAX_AGE:
                self._clear_files(state)
                state = {}
            chat = Chat(message.mobile, contact["language"], state, now)
            try:
                self._dispatch(chat, message)
            except PortalError as error:
                chat.replies.append(error.message)
            except Exception:
                traceback.print_exc()
                self._clear_files(chat.state)
                chat.state = {}
                chat.say("oops")
            chat.state["at"] = iso(now)
            store.wa_save(message.mobile, chat.lang, json.dumps(chat.state))
            return chat.replies

    def deliver(self, mobile: str, text: str) -> str:
        """Push a portal message to this citizen's WhatsApp. Returns "whatsapp" if one is on its way, else "portal"."""
        contact = self.portal.store.wa_get(mobile)
        if not contact:
            return "portal"
        inside = self.clock() - datetime.fromisoformat(contact["last_inbound"]) < WINDOW
        templated = hasattr(self.channel, "send_update_template") and bool(getattr(self.channel, "update_template", ""))
        if not inside and not templated:
            return "portal"

        def send() -> None:
            if inside:
                sent, detail = self.channel.send_text(mobile, text)
            else:
                sent, detail = self.channel.send_update_template(mobile, text)
            if not sent:
                print(f"WhatsApp push to {mobile[:2]}XXXXXX{mobile[-2:]} failed: {detail}")

        if self.background:
            threading.Thread(target=send, daemon=True).start()
        else:
            send()
        return "whatsapp"

    # ------------------------------------------------------------------ guards

    def _lock_for(self, mobile: str) -> threading.Lock:
        with self._guard:
            return self._locks.setdefault(mobile, threading.Lock())

    def _duplicate(self, message_id: str) -> bool:
        """Providers repeat a message when we are slow. Each ID is handled once."""
        if not message_id:
            return False
        with self._guard:
            if message_id in self._seen:
                return True
            self._seen[message_id] = True
            while len(self._seen) > SEEN_LIMIT:
                self._seen.popitem(last=False)
        return False

    def _too_fast(self, mobile: str) -> bool:
        limit, seconds = RATE_LIMIT
        now = time.monotonic()
        with self._guard:
            queue = self._recent.setdefault(mobile, deque())
            while queue and now - queue[0] > seconds:
                queue.popleft()
            if len(queue) >= limit:
                return True
            queue.append(now)
        return False

    # ------------------------------------------------------------------ conversation

    def _dispatch(self, chat: Chat, message: Inbound) -> None:
        text = message.text.strip()
        low = text.lower()
        if low in HOME and not message.media:
            was_busy = chat.step is not None
            self._clear_files(chat.state)
            chat.state = {}
            if was_busy and low not in ("0", "menu", "मेनू"):
                chat.say("cancelled")
            chat.say("menu")
            return
        step = chat.step
        if step:
            handler = getattr(self, f"_step_{step}", None)
            if handler is None:
                chat.state = {}
                chat.say("menu")
                return
            handler(chat, message)
            return
        self._idle(chat, message)

    def _idle(self, chat: Chat, message: Inbound) -> None:
        text = message.text.strip()
        number = _number(text)
        if message.media or message.location:
            # A photo or pin with no complaint open: it would be lost, so say how to start.
            chat.say("send_text_first")
            return
        if number is not None and 1 <= number <= 6:
            {1: lambda: self._start_registration(chat, {}), 2: lambda: self._ask_for_id(chat),
             3: lambda: self._show_list(chat), 4: lambda: self._start_fix(chat),
             5: lambda: self._send_login_code(chat), 6: lambda: self._toggle_language(chat)}[number]()
            return
        answer = None
        if self.understanding is not None:
            answer = self.understanding.understand(text, "no conversation open")
        if answer is None:
            answer = keyword_understanding(text)
        if answer.get("language") in ("en", "kok") and answer["intent"] != "show_menu":
            chat.lang = answer["language"]
        intent = answer["intent"]
        if intent == "register_complaint":
            chat.lang = answer.get("language") or chat.lang
            self._start_registration(chat, {"text": text, "kind": answer.get("kind"), "category": answer.get("category")})
        elif intent == "track_complaint":
            if answer.get("complaint_id"):
                self._show_one(chat, answer["complaint_id"])
            else:
                self._ask_for_id(chat)
        elif intent == "my_complaints":
            self._show_list(chat)
        elif intent == "confirm_fix":
            self._start_fix(chat)
        elif intent == "login_code":
            self._send_login_code(chat)
        elif intent == "change_language":
            wanted = "kok" if "कोंकणी" in text or "konkani" in text.lower() else "en" if "english" in text.lower() else None
            if wanted:
                chat.lang = wanted
                chat.say("language_set")
                chat.say("menu")
            else:
                self._toggle_language(chat)
        elif intent == "show_menu":
            chat.say("menu")
        else:
            chat.say("unclear")
            chat.say("menu")

    def _toggle_language(self, chat: Chat) -> None:
        chat.lang = "en" if chat.lang == "kok" else "kok"
        chat.say("language_set")
        chat.say("menu")

    # ---- sign-up (only for someone who has no account yet)

    def _citizen(self, chat: Chat) -> Optional[Dict[str, Any]]:
        return self.portal.store.get_citizen(chat.mobile)

    def _step_signup_name(self, chat: Chat, message: Inbound) -> None:
        name = " ".join(message.text.split())
        if not 2 <= len(name) <= 100:
            chat.say("bad_name")
            return
        chat.data["name"] = name
        zones = self.portal.locations.tree()["zones"]
        names = texts._konkani_names() if chat.lang == "kok" else {}
        chat.say("ask_taluk", name=name.split(" ")[0],
                 list=_numbered([names.get(zone["name"], zone["name"]) for zone in zones]))
        chat.go("signup_taluk")

    def _step_signup_taluk(self, chat: Chat, message: Inbound) -> None:
        zones = self.portal.locations.tree()["zones"]
        number = _number(message.text)
        if number is None or not 1 <= number <= len(zones):
            chat.say("bad_choice")
            return
        zone = zones[number - 1]
        wards = [ward["number"] for ward in zone["wards"]]
        chat.data["zone"] = zone["number"]
        if len(wards) == 1:
            chat.data["ward"] = wards[0]
            chat.say("ask_home")
            chat.go("signup_home")
        else:
            chat.say("ask_ward", low=min(wards), high=max(wards))
            chat.go("signup_ward")

    def _step_signup_ward(self, chat: Chat, message: Inbound) -> None:
        zone = next(item for item in self.portal.locations.tree()["zones"] if item["number"] == chat.data["zone"])
        wards = [ward["number"] for ward in zone["wards"]]
        number = _number(message.text)
        if number is None or number not in wards:
            chat.say("bad_ward", low=min(wards), high=max(wards))
            return
        chat.data["ward"] = number
        chat.say("ask_home")
        chat.go("signup_home")

    def _step_signup_home(self, chat: Chat, message: Inbound) -> None:
        address = " ".join(message.text.split())
        if not 10 <= len(address) <= 300:
            chat.say("bad_address")
            return
        self.portal.sign_up_citizen(chat.data["name"], chat.mobile, address, chat.data["ward"], now=chat.now)
        chat.say("account_ready")
        chat.data.pop("name", None), chat.data.pop("zone", None), chat.data.pop("ward", None)
        chat.data.pop("after", None)
        chat.go(None)
        self._advance_registration(chat)

    # ---- registering a complaint

    def _start_registration(self, chat: Chat, prefill: Dict[str, Any]) -> None:
        chat.state = {"d": {key: value for key, value in prefill.items() if value}}
        written = chat.data.get("text")
        if written is not None:
            written = " ".join(written.split())[:MAX_COMPLAINT_CHARS]
            if len(written) < MIN_COMPLAINT_CHARS:
                chat.data.pop("text")
            else:
                chat.data["text"] = written
        if self._citizen(chat) is None:
            chat.data["after"] = "register"
            chat.say("need_account")
            chat.go("signup_name")
            return
        self._advance_registration(chat)

    def _advance_registration(self, chat: Chat) -> None:
        """Ask for the next thing the complaint still needs."""
        data = chat.data
        kinds = list(available_kinds())
        if data.get("kind") not in kinds:
            data.pop("kind", None)
            data.pop("category", None)
        if "kind" not in data:
            chat.say("ask_kind", list=_numbered([kind_label(kind, chat.lang) for kind in kinds]))
            chat.go("reg_kind")
            return
        kind = data["kind"]
        keys = [key for key, _ in categories_for(kind)]
        if data.get("category") not in keys:
            data.pop("category", None)
        if "category" not in data:
            if kind == EMERGENCY:
                chat.say("emergency_note")
            if kind == POLICE:
                chat.replies.append(POLICE_NOTICE_KOK if chat.lang == "kok" else POLICE_NOTICE)
            chat.say("ask_category", list=_numbered([cat_label(kind, key, chat.lang) for key in keys]))
            chat.go("reg_category")
            return
        if "text" not in data:
            chat.say("ask_text")
            chat.go("reg_text")
            return
        if "place" not in data:
            chat.say("ask_place")
            chat.go("reg_place")
            return
        photos = data.get("photos", [])
        if kind == CIVIC and not data.get("photos_done"):
            chat.say("ask_photos_civic", n=PHOTOS_REQUIRED, have=len(photos))
            chat.go("reg_photos")
            return
        if kind == POLICE and not data.get("photos_done"):
            chat.say("ask_photos_police", n=PHOTOS_REQUIRED, have=len(photos))
            chat.go("reg_photos")
            return
        files = len(data.get("photos", []))
        chat.say("check", kind=kind_label(kind, chat.lang), category=cat_label(kind, data["category"], chat.lang),
                 text=self._short(data["text"]), place=self._short(data["place"], 120),
                 files=T("files_n", chat.lang, n=files) if files else T("files_none", chat.lang))
        chat.go("reg_check")

    @staticmethod
    def _short(text: str, limit: int = 300) -> str:
        text = " ".join(text.split())
        return text if len(text) <= limit else text[: limit - 1] + "…"

    def _step_reg_kind(self, chat: Chat, message: Inbound) -> None:
        kinds = list(available_kinds())
        number = _number(message.text)
        if number is None or not 1 <= number <= len(kinds):
            chat.say("bad_choice")
            return
        chat.data["kind"] = kinds[number - 1]
        chat.data.pop("category", None)
        self._advance_registration(chat)

    def _step_reg_category(self, chat: Chat, message: Inbound) -> None:
        keys = [key for key, _ in categories_for(chat.data["kind"])]
        number = _number(message.text)
        if number is None or not 1 <= number <= len(keys):
            chat.say("bad_choice")
            return
        chat.data["category"] = keys[number - 1]
        self._advance_registration(chat)

    def _step_reg_text(self, chat: Chat, message: Inbound) -> None:
        text = " ".join(message.text.split())
        if not MIN_COMPLAINT_CHARS <= len(text) <= MAX_COMPLAINT_CHARS:
            chat.say("bad_text")
            return
        chat.data["text"] = text
        self._advance_registration(chat)

    @staticmethod
    def _place_from_pin(location: Tuple[float, float, str]) -> str:
        latitude, longitude, label = location
        base = f"Pinned location {latitude:.5f}, {longitude:.5f}"
        return f"{label.strip()[:150]} ({base})" if label.strip() else base

    def _step_reg_place(self, chat: Chat, message: Inbound) -> None:
        if message.location:
            chat.data["place"] = self._place_from_pin(message.location)
        elif message.text.strip().lower() in ("same", "home", "तेंच", "घर"):
            citizen = self._citizen(chat)
            chat.data["place"] = citizen["address"] if citizen else ""
        else:
            place = " ".join(message.text.split())
            if not 10 <= len(place) <= 300:
                chat.say("bad_address")
                return
            chat.data["place"] = place
        self._advance_registration(chat)

    def _step_reg_photos(self, chat: Chat, message: Inbound) -> None:
        data = chat.data
        kind = data["kind"]
        photos = data.setdefault("photos", [])
        if message.media:
            for item in message.media:
                if len(photos) >= PHOTOS_REQUIRED:
                    break
                saved = self._save_media(chat.mobile, item, len(photos))
                if saved is None:
                    chat.say("photo_bad")
                    continue
                photos.append(saved)
                chat.say("photo_got", have=len(photos), n=PHOTOS_REQUIRED)
            if len(photos) >= PHOTOS_REQUIRED:
                data["photos_done"] = True
                self._advance_registration(chat)
            return
        word = message.text.strip().lower()
        if kind in (CIVIC, POLICE) and word in ("done", "skip", "no", "जालें", "नाका"):
            data["photos_done"] = True
            self._advance_registration(chat)
            return
        chat.say("photo_wait")

    def _step_reg_check(self, chat: Chat, message: Inbound) -> None:
        word = message.text.strip().lower()
        if word in NO:
            self._clear_files(chat.state)
            chat.state = {}
            chat.say("cancelled")
            chat.say("menu")
            return
        if word not in YES:
            chat.say("bad_choice")
            return
        data = chat.data
        citizen = self._citizen(chat)
        urls = []
        for name, mime in data.get("photos", []):
            raw = self._temp_folder() / name
            urls.append(f"data:{mime};base64," + base64.b64encode(raw.read_bytes()).decode("ascii"))
        with self.portal.muted():
            try:
                view = self.portal.register(
                    citizen["name"], chat.mobile, data["text"], ward_number=citizen["ward_number"], use_llm=False,
                    now=chat.now, address=data["place"], kind=data["kind"], category=data["category"],
                    photos=urls if data["kind"] in (CIVIC, POLICE) else None)
            except PortalError as error:
                # Most likely a photo the portal refused: ask for the photos again and say why.
                self._clear_files(chat.state)
                data.pop("photos", None)
                data.pop("photos_done", None)
                chat.replies.append(error.message)
                self._advance_registration(chat)
                return
        self._clear_files(chat.state)
        chat.state = {}
        due = texts.when_text(view["deadline"])
        reply = T("registered", chat.lang, id=view["id"], label=self._type_label(view, chat.lang),
                  office=self._office(view["current_office"], chat.lang), due=due)
        if data["kind"] == EMERGENCY:
            reply += "\n\n" + T("emergency_note", chat.lang)
        if view.get("police_notice"):
            reply += "\n\n" + (POLICE_NOTICE_KOK if chat.lang == "kok" else view["police_notice"])
        chat.replies.append(reply)

    # ---- photos kept on disk while the chat is going on

    def _temp_folder(self) -> Path:
        folder = Path(self.portal.store.path).parent / "wa_tmp"
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    def _save_media(self, mobile: str, item: Media, index: int) -> Optional[List[str]]:
        try:
            raw, mime = self.channel.fetch_media(item)
        except Exception as error:
            print(f"WhatsApp media download failed: {error}")
            return None
        mime = (mime or item.mime or "").split(";")[0].strip().lower()
        if mime not in PHOTO_TYPES or not raw or len(raw) > MAX_PHOTO_BYTES:
            return None
        name = f"{mobile}-{index + 1}-{int(time.time() * 1000) % 100000}.bin"
        (self._temp_folder() / name).write_bytes(raw)
        return [name, mime]

    def _clear_files(self, state: Dict[str, Any]) -> None:
        for name, _ in (state.get("d") or {}).get("photos", []):
            try:
                (self._temp_folder() / name).unlink(missing_ok=True)
            except OSError:
                pass

    # ---- tracking

    def _ask_for_id(self, chat: Chat) -> None:
        chat.state = {}
        chat.say("ask_id")
        chat.go("track_id")

    def _step_track_id(self, chat: Chat, message: Inbound) -> None:
        found = keyword_understanding(message.text).get("complaint_id")
        if not found:
            chat.say("ask_id")
            return
        chat.state = {}
        self._show_one(chat, found)

    def _show_one(self, chat: Chat, complaint_id: str) -> None:
        try:
            view = self.portal.track(complaint_id, chat.mobile)
        except PortalError:
            chat.say("no_such")
            return
        status = view["status_text"]
        if chat.lang == "kok" and status == STATUS_TEXT.get(view["status"]):
            status = STATUS_KOK[view["status"]]
        due = T("due", chat.lang, due=texts.when_text(view["deadline"])) if view["status"] == OPEN and view["deadline"] else ""
        events = view.get("events") or []
        chat.say("track", id=view["id"], label=self._type_label(view, chat.lang), status=status,
                 office=self._office(view["current_office"], chat.lang), due=due,
                 latest=self._short(events[-1]["message"], 250) if events else "-")

    def _show_list(self, chat: Chat) -> None:
        chat.state = {}
        rows = self.portal.citizen_complaints(chat.mobile)[:LIST_LIMIT]
        if not rows:
            chat.say("list_none")
            return
        lines = []
        for number, row in enumerate(rows, start=1):
            status = (STATUS_KOK if chat.lang == "kok" else {OPEN: "Open", AWAITING: "Resolved, please confirm",
                                                           CLOSED: "Closed"})[row["status"]]
            lines.append(f"{number} - {row['id']} - {self._type_label(row, chat.lang)} - {status.split('.')[0]}")
        chat.say("list_head", list="\n".join(lines))
        chat.data["ids"] = [row["id"] for row in rows]
        chat.go("pick_complaint")

    def _step_pick_complaint(self, chat: Chat, message: Inbound) -> None:
        ids = chat.data.get("ids", [])
        number = _number(message.text)
        found = keyword_understanding(message.text).get("complaint_id")
        if number is not None and 1 <= number <= len(ids):
            found = ids[number - 1]
        if not found:
            chat.say("bad_choice")
            return
        chat.state = {}
        self._show_one(chat, found)

    # ---- confirming a fix

    def _start_fix(self, chat: Chat) -> None:
        chat.state = {}
        waiting = [row for row in self.portal.citizen_complaints(chat.mobile) if row["status"] == AWAITING]
        if not waiting:
            chat.say("fix_none")
            return
        chat.data["ids"] = [row["id"] for row in waiting]
        chat.data["labels"] = {row["id"]: self._type_label(row, chat.lang) for row in waiting}
        if len(waiting) == 1:
            self._ask_fixed(chat, waiting[0]["id"])
        else:
            chat.say("fix_pick", list="\n".join(f"{n} - {row['id']} - {self._type_label(row, chat.lang)}"
                                                for n, row in enumerate(waiting, start=1)))
            chat.go("fix_pick")

    def _step_fix_pick(self, chat: Chat, message: Inbound) -> None:
        ids = chat.data.get("ids", [])
        number = _number(message.text)
        if number is None or not 1 <= number <= len(ids):
            chat.say("bad_choice")
            return
        self._ask_fixed(chat, ids[number - 1])

    def _ask_fixed(self, chat: Chat, complaint_id: str) -> None:
        chat.data["id"] = complaint_id
        chat.say("fix_ask", id=complaint_id, label=chat.data.get("labels", {}).get(complaint_id, ""))
        chat.go("fix_answer")

    def _step_fix_answer(self, chat: Chat, message: Inbound) -> None:
        word = message.text.strip().lower()
        complaint_id = chat.data["id"]
        if word in YES:
            view = self.portal.confirm(complaint_id, chat.mobile, True, now=chat.now)
            if view.get("demo_code"):
                chat.say("fix_code_shown", code=view["demo_code"], minutes=view.get("demo_code_minutes", 10))
            else:
                chat.say("fix_code_sent", note=view.get("code_note", ""))
            chat.state = {"d": {"id": complaint_id}}
            chat.go("fix_code")
        elif word in NO:
            view = self.portal.confirm(complaint_id, chat.mobile, False, "Said on WhatsApp.", now=chat.now)
            chat.state = {}
            chat.say("fix_escalated", id=complaint_id, office=self._office(view["current_office"], chat.lang))
        else:
            chat.say("bad_choice")

    def _step_fix_code(self, chat: Chat, message: Inbound) -> None:
        code = "".join(ch for ch in message.text if ch.isdigit())
        if len(code) != 6:
            chat.say("code_bad")
            return
        complaint_id = chat.data["id"]
        self.portal.confirm_code(complaint_id, chat.mobile, code, now=chat.now)
        chat.state = {}
        chat.say("fix_closed", id=complaint_id)

    # ---- login code for the website

    def _send_login_code(self, chat: Chat) -> None:
        chat.state = {}
        if self._citizen(chat) is None:
            chat.say("login_need")
            return
        result = self.portal.start_citizen_login(chat.mobile, now=chat.now)
        if result.get("code"):   # no code provider is set up, and this chat proves the number, so the code goes here
            chat.say("login_code", code=result["code"], minutes=result["minutes"])
        else:
            chat.say("login_sent", note=result["note"])

    # ---- small helpers

    def _type_label(self, view: Dict[str, Any], lang: str) -> str:
        label = view.get("complaint_label", "")
        return texts._konkani_names().get(label, label) if lang == "kok" else label

    def _office(self, office: str, lang: str) -> str:
        return texts._konkani_names().get(office, office) if lang == "kok" else office
