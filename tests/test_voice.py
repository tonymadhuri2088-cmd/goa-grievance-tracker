"""Tests for the phone helpline: what is understood from speech, what is spoken back, a whole call, and the two entries
(the call page's API and the Twilio phone webhook). No internet and no model are used. These run on the Goa pack."""

import http.client
import importlib.util
import json
import re
import sys
import threading
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "complaint_tools"))

# pylint: disable=wrong-import-position
from complaint_portal.auth import Sessions, hash_password  # noqa: E402
from complaint_portal.rules import DISTRICT_HEAD, FIELDS  # noqa: E402
from complaint_portal.store import Store  # noqa: E402
from complaint_portal.voice import (  # noqa: E402
    MAX_SILENCES, MAX_TURNS, Turn, VoiceHelpline, complaint_id_from_speech, spoken_number, speakable, twiml_for,
    understood,
)
from complaint_portal.whatsapp import TwilioChannel  # noqa: E402
from complaint_portal.workflow import Portal, utcnow  # noqa: E402

_spec = importlib.util.spec_from_file_location("portal_server_voice", ROOT / "portal" / "server.py")
portal_server = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(portal_server)

MOBILE = "9876543210"
HASH = hash_password("portal-test-pass")
PROBLEM = "There is no water in our street for three days"


@pytest.fixture
def portal(goa, tmp_path):
    store = Store(tmp_path / "portal.db")
    for field in FIELDS:
        for level in ("depot", "deputy_ae", "area_engineer", "superintendent_engineer"):
            store.insert_officer(f"{field}.{level}", f"{FIELDS[field]} {level}", field, level, HASH)
    store.insert_officer("district.head", "Collectorate", "all", DISTRICT_HEAD, HASH)
    return Portal(store)


@pytest.fixture
def helpline(portal):
    return VoiceHelpline(portal, None, clock=lambda: datetime(2026, 11, 10, 9, 0, tzinfo=timezone.utc))


def talk(helpline, *sentences, mobile=MOBILE, call="call-0001"):
    last = None
    for sentence in sentences:
        last = helpline.turn(mobile, call, sentence)
    return last


# ------------------------------------------------------------------ what the caller said
@pytest.mark.parametrize("heard, number", [
    ("five", "5"), ("Five.", "5"), ("option two", "2"), ("twenty three", "23"), ("thirty", "30"),
    ("two zero two six", "2026"), ("12", "12"), ("ward number nineteen", "19"), ("to", "2"),
])
def test_spoken_numbers_become_digits(heard, number):
    assert spoken_number(heard) == number


@pytest.mark.parametrize("heard", ["", "water", "five taps are broken", "hello there"])
def test_other_speech_is_not_a_number(heard):
    assert spoken_number(heard) is None


def test_a_complaint_id_can_be_spoken_letter_by_letter():
    assert complaint_id_from_speech("C M P 2 0 2 6 1 1 2 0 4 3 7 1") == "CMP-20261120-4371"
    assert complaint_id_from_speech("complaint id 202611204371") == "CMP-20261120-4371"
    assert complaint_id_from_speech("two zero two six one one two zero four three seven one") == "CMP-20261120-4371"
    assert complaint_id_from_speech("C M P 2 0 2 6") is None
    assert complaint_id_from_speech("the water is gone") is None


def test_yes_and_no_are_read_where_the_bot_expects_a_choice():
    assert understood("Yes please", "reg_check") == "1"
    assert understood("no thanks", "reg_check") == "2"
    assert understood("okay", "fix_answer") == "1"
    assert understood("same as my home", "reg_place") == "same"
    assert understood("go back", "reg_text") == "0"
    # Outside those steps the words are left alone, so a complaint that starts with "no water" is not turned into 2.
    assert understood("no water in our street", None) == "no water in our street"
    assert understood("one", None) == "1"


def test_what_the_caller_said_is_cut_to_a_safe_length():
    assert len(understood("water " * 500, None)) <= 600


# ------------------------------------------------------------------ what is said back
def test_lists_and_ids_are_made_to_sound_right_when_read_out():
    spoken = speakable("*Pick one:*\n1 - Emergency\n2 - Not emergency\nSend 0 any time to come back to this menu.")
    assert "For Emergency, say 1." in spoken and "For Not emergency, say 2." in spoken
    assert "*" not in spoken and "Send" not in spoken
    said = speakable("Registered. ID: CMP-20261120-4371")
    assert "C M P. 2 0 2 6 1 1 2 0. 4 3 7 1." in said
    assert "CMP-" not in said


def test_the_whatsapp_only_lines_are_not_read_out():
    spoken = speakable("Done.\nI will message you here at each step. Send the ID any time to see the status.")
    assert "message you here" not in spoken and "website" in spoken
    assert "(" not in speakable("Send your complaint ID (for example CMP-20261110-1234).")


def test_the_time_limit_is_said_in_days_not_as_a_clock_time():
    assert "Action expected by" not in speakable("Done.\nAction expected by: 13 Nov 2026, 5:30 PM\nMore.")
    now = datetime(2026, 11, 10, 9, 0, tzinfo=timezone.utc)
    from complaint_portal.voice import days_left
    assert days_left("2026-11-13T12:00:00+00:00", now) == 4      # a part of a day counts as a day
    assert days_left("2026-11-11T09:00:00+00:00", now) == 1
    assert days_left("2026-11-01T09:00:00+00:00", now) == 0 and days_left(None, now) is None


# ------------------------------------------------------------------ a whole call
def test_a_new_caller_registers_a_complaint_by_talking(helpline, portal):
    greeting = helpline.start(MOBILE, "call-0001")
    assert greeting.end is False and "AI assistant" in greeting.lines[0] and "not a government officer" in greeting.lines[0]
    reply = talk(helpline, PROBLEM)
    assert "name" in " ".join(reply.lines).lower()
    for said in ("Ravi Kumar", "one", "five"):                    # name, Panaji City, ward 5
        reply = talk(helpline, said)
    reply = talk(helpline, "Station Road near Jagat Circle Panaji")   # home address
    assert "kind of complaint" in " ".join(reply.lines)
    reply = talk(helpline, "two", "one")                          # not an emergency, water supply
    assert "Where is the problem" in " ".join(reply.lines)
    reply = talk(helpline, "same as home")
    # The photos step was answered for the caller: the next thing said is the check, not a request for photos.
    text = " ".join(reply.lines)
    assert "check your complaint" in text and "photo" not in text.lower()
    reply = talk(helpline, "yes")
    text = " ".join(reply.lines)
    assert "Complaint registered" in text and "C M P." in text and "Is there anything else" in text
    complaints = portal.citizen_complaints(MOBILE)
    assert len(complaints) == 1 and complaints[0]["status"] == "open"
    assert "water" in json.dumps(complaints[0]).lower()
    # The caller is told how long it should take, and the page gets the complaint for its side panel.
    assert re.search(r"resolved within \d+ days?, by \d+ \w+ 2026", text) and "Action expected by" not in text
    panel = reply.complaint
    assert panel["id"] == complaints[0]["id"] and panel["kind"] == "new" and panel["days"] >= 1
    assert "no water" in panel["problem"] and panel["type"] and panel["office"] and panel["due"]
    assert reply.as_dict()["complaint"]["id"] == panel["id"]
    assert talk(helpline, "goodbye").complaint is None


def test_the_caller_can_track_a_complaint_by_saying_its_id(helpline, portal):
    helpline.start(MOBILE, "call-0001")
    talk(helpline, PROBLEM, "Ravi Kumar", "one", "five", "Station Road near Jagat Circle Panaji", "two", "one",
         "same as home", "yes")
    complaint_id = portal.citizen_complaints(MOBILE)[0]["id"]               # CMP-YYYYMMDD-NNNN
    digits = " ".join(re.sub(r"\D", "", complaint_id))
    reply = talk(helpline, "track")
    assert "complaint ID" in " ".join(reply.lines)
    reply = talk(helpline, f"C M P {digits}")
    assert "Drinking water" in " ".join(reply.lines) or "water" in " ".join(reply.lines).lower()
    assert "C M P." in " ".join(reply.lines)
    assert reply.complaint["kind"] == "track" and reply.complaint["id"] == complaint_id
    assert not any("resolved within" in line for line in reply.lines)   # tracking is not a new promise


def test_goodbye_ends_the_call(helpline):
    helpline.start(MOBILE, "call-0001")
    reply = talk(helpline, "goodbye")
    assert reply.end is True and "Goodbye" in reply.lines[0]


def test_silence_is_met_with_a_second_chance_and_then_a_hang_up(helpline):
    helpline.start(MOBILE, "call-0001")
    first = talk(helpline, "")
    assert first.end is False and "did not hear" in first.lines[0]
    for _ in range(MAX_SILENCES - 2):
        talk(helpline, None)
    last = talk(helpline, "")
    assert last.end is True


def test_speaking_resets_the_silence_count(helpline):
    helpline.start(MOBILE, "call-0001")
    talk(helpline, "", "")
    talk(helpline, "menu")
    assert talk(helpline, "").end is False


def test_a_very_long_call_is_ended(helpline):
    helpline.start(MOBILE, "call-0001")
    last = None
    for _ in range(MAX_TURNS + 1):
        last = talk(helpline, "menu")
    assert last.end is True


def test_a_call_is_tied_to_its_caller(helpline):
    helpline.start(MOBILE, "call-0001")
    stranger = helpline.turn("9123456780", "call-0001", "menu")
    assert "Welcome" in stranger.lines[0]      # a different number cannot continue someone else's call: it starts afresh


def test_a_call_never_sends_a_whatsapp_message(helpline, portal):
    sent = []
    helpline.bot.channel.send_text = lambda mobile, text: sent.append(text) or (True, "")
    helpline.start(MOBILE, "call-0001")
    talk(helpline, PROBLEM, "Ravi Kumar", "one", "five", "Station Road near Jagat Circle Panaji", "two", "one",
         "same as home", "yes")
    assert sent == []


# ------------------------------------------------------------------ the phone provider's answer
def test_the_twilio_answer_speaks_then_listens():
    xml = twiml_for(Turn(["Hello & welcome", "Say <track>"]), "/api/voice/twilio", "en-IN").decode()
    assert xml.startswith("<?xml") and "<Gather" in xml and 'input="speech dtmf"' in xml
    assert "Hello &amp; welcome" in xml and "&lt;track&gt;" in xml
    assert 'action="/api/voice/twilio"' in xml and "<Hangup/>" not in xml


def test_the_twilio_answer_hangs_up_at_the_end_and_reads_konkani_with_a_hindi_voice():
    assert "<Hangup/>" in twiml_for(Turn(["Goodbye"], end=True), "/api/voice/twilio").decode()
    xml = twiml_for(Turn(["धन्यवाद"], lang="kok"), "/api/voice/twilio").decode()
    assert 'language="hi-IN"' in xml and "धन्यवाद" in xml


# ------------------------------------------------------------------ over HTTP
@pytest.fixture
def server(portal, monkeypatch):
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "secret-token")
    monkeypatch.setenv("PUBLIC_URL", "https://demo.example")
    sessions = Sessions(portal.store, "citizen")
    voice = VoiceHelpline(portal, None)
    httpd = portal_server.make_server("127.0.0.1", 0, portal, Sessions(), sessions, voice=voice)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield httpd.server_address[1], sessions
    httpd.shutdown()
    httpd.server_close()


def request(port, method, path, body=None, headers=None):
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    connection.request(method, path, body, headers or {})
    response = connection.getresponse()
    return response.status, response.read()


def web_turn(port, payload, cookie=None):
    headers = {"Content-Type": "application/json"}
    if cookie:
        headers["Cookie"] = f"citizen_session={cookie}"
    return request(port, "POST", "/api/voice/turn", json.dumps(payload), headers)


def test_the_call_page_is_served_and_says_it_is_on(server):
    port, _ = server
    status, body = request(port, "GET", "/call")
    assert status == 200 and b"AI helpline" in body
    info = json.loads(request(port, "GET", "/api/voice/info")[1])
    assert info["web"] is True and info["language"] == "en-IN"


def test_only_a_logged_in_citizen_can_use_the_call_api(server):
    port, _ = server
    assert web_turn(port, {"call_id": "abcdefgh1234", "start": True})[0] == 401


def test_a_logged_in_citizen_can_make_a_call_from_the_page(server, portal):
    port, sessions = server
    portal.sign_up_citizen("Ravi Kumar", MOBILE, "Station Road, Jagat Circle, Panaji", 5)
    cookie = sessions.create(MOBILE, utcnow(), utcnow().replace(year=utcnow().year + 1))
    status, body = web_turn(port, {"call_id": "abcdefgh1234", "start": True}, cookie)
    first = json.loads(body)
    assert status == 200 and first["end"] is False and "AI assistant" in first["say"][0]
    status, body = web_turn(port, {"call_id": "abcdefgh1234", "heard": "goodbye"}, cookie)
    assert json.loads(body)["end"] is True
    assert web_turn(port, {"call_id": "x", "heard": "hi"}, cookie)[0] == 400
    assert web_turn(port, {"call_id": "abcdefgh1234", "heard": 5}, cookie)[0] == 400


def signed_call(port, params, token="secret-token"):
    channel = TwilioChannel("", token, "", "https://demo.example")
    signature = channel.expected_signature("https://demo.example/api/voice/twilio", params)
    return request(port, "POST", "/api/voice/twilio", urllib.parse.urlencode(params),
                   {"Content-Type": "application/x-www-form-urlencoded", "X-Twilio-Signature": signature})


def test_a_phone_call_from_twilio_is_answered_with_a_greeting(server):
    port, _ = server
    status, body = signed_call(port, {"CallSid": "CA1234567890abcdef", "From": "+919876543210"})
    assert status == 200 and b"<Gather" in body and b"AI assistant" in body
    status, body = signed_call(port, {"CallSid": "CA1234567890abcdef", "From": "+919876543210",
                                      "SpeechResult": "goodbye"})
    assert status == 200 and b"<Hangup/>" in body


def test_a_phone_call_with_a_wrong_signature_is_refused(server):
    port, _ = server
    assert signed_call(port, {"CallSid": "CA1234567890abcdef", "From": "+919876543210"}, token="other")[0] == 403
    assert request(port, "POST", "/api/voice/twilio", "From=%2B919876543210",
                   {"Content-Type": "application/x-www-form-urlencoded"})[0] == 403


def test_a_caller_from_another_country_is_told_so_and_hung_up_on(server):
    port, _ = server
    status, body = signed_call(port, {"CallSid": "CA1234567890abcdef", "From": "+14155550000"})
    assert status == 200 and b"Indian mobile numbers" in body and b"<Hangup/>" in body


def test_the_phone_route_is_absent_without_a_twilio_token(portal, monkeypatch):
    monkeypatch.delenv("TWILIO_AUTH_TOKEN", raising=False)
    httpd = portal_server.make_server("127.0.0.1", 0, portal, Sessions(), voice=VoiceHelpline(portal, None))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        assert request(httpd.server_address[1], "POST", "/api/voice/twilio", "x=1")[0] == 404
    finally:
        httpd.shutdown()
        httpd.server_close()
