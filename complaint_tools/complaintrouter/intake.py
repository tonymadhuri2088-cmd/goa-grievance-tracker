"""Classifies a citizen complaint into a charter complaint type and subtype.

This is a keyword classifier, not a trained model. It returns notes whenever a
subtype or timeline had to be assumed, so a human can confirm before action.
"""

import json
from typing import Any, Dict, List

try:
    from neuro_san.interfaces.coded_tool import CodedTool
except ImportError:  # the web portal runs without Neuro-SAN installed; only the agent network needs it
    class CodedTool:  # pylint: disable=too-few-public-methods
        """Stand-in so the tools still import when Neuro-SAN is not installed."""

from .common import district, load_charter

# Specific types. "general_grievance" is used only when none of these match.
TYPE_KEYWORDS = {
    "unsafe_cleaning": ["manual scavenging", "unsafe cleaning", "cleaning sewer without", "died while cleaning", "without safety gear"],
    "water_leakage": ["leak", "pipe burst", "pipeline burst", "water wastage", "water flowing on the road", "water flowing on road"],
    "water_pollution": ["contaminated", "dirty water", "polluted", "muddy water", "smelly water", "sewage in water", "water quality", "discoloured water", "discolored water"],
    "no_water_supply": ["no water", "no supply", "water not coming", "water supply stopped", "defective water supply", "defective supply"],
    "defective_meter": ["water meter", "meter defective", "meter faulty", "meter not working", "meter stopped"],
    "handpump_repair": ["hand pump", "handpump", "india mark"],
    "sewer_main_blockage": ["sewer main", "main sewer", "sewer blocked", "sewer blockage", "manhole overflow", "sewage overflow", "sewer overflow"],
    "house_sewer_blockage": ["house sewer", "house drain", "toilet blocked", "drain blocked at home", "toilet not flushing"],
    "damaged_sewer_line": ["sewer line damaged", "damaged sewer", "broken sewer", "sewer pipe broken", "sewer line broken"],
    "tax_charges": ["water bill", "tax", "charges", "arrears", "bill is wrong", "payment not reflected", "excess bill"],
    "tanker_supply": ["tanker", "water lorry"],
    "new_connection_delay": ["new connection", "connection not given", "application pending", "connection pending"],
    "street_water_no_piped": ["no piped", "public tap", "street water", "no pipe connection", "standpipe"],
    "septic_tank_clearance": ["septic", "desludging", "tank clearance", "tank cleaning"],
}

# Types of the Goa pack (data/charter_goa.json). Each list has English and Konkani words.
# Only the types the active charter has are used. The Konkani words should be reviewed by a Konkani speaker.
GOA_TYPE_KEYWORDS = {
    "cybercrime": ["cyber", "online fraud", "otp", "phishing", "hacked", "fake call", "upi fraud", "social media", "सायबर", "ऑनलायन फसवणूक", "ओटीपी", "बनावट कॉल", "फिशिंग"],
    "financial_fraud": ["fraud", "cheated", "cheating", "scam", "money taken", "loan fraud", "bank fraud", "फसवणूक", "फसयलो", "फसयलें", "पयशे फसवणूक", "आर्थिक फसवणूक"],
    "lost_property": ["lost my", "lost phone", "lost wallet", "lost mobile", "lost property", "missing phone", "stolen", "theft", "robbery", "हरयलें", "हरयल्लो", "हरयल्ली", "चोरी", "चोरयलो", "चोरयलें", "फोन हरयलो"],
    "traffic_safety": ["traffic", "accident", "rash driving", "signal", "illegal parking", "drunk driving", "unsafe road", "वाहतूक", "अपघात", "ट्रॅफीक", "पार्किंग", "बेदरकार वाहन"],
    "complaint_individuals": ["threat", "threatening", "harass", "harassment", "neighbour", "neighbor", "assault", "धमकी", "त्रास", "भांडण", "हल्लो", "शेजारी"],
    "hospital_service": ["hospital", "doctor", "medicine", "no beds", "nurse", "ward boy", "phc", "health centre", "health center", "ambulance", "इस्पितळ", "डॉक्टर", "दवा", "खाट", "नर्स", "आरोग्य केंद्र", "रुग्णवाहिका"],
    "no_water_supply": ["no water", "no supply", "water not coming", "water supply stopped", "drinking water", "उदक येना", "उदक ना", "उदक येवंक ना", "उदक पुरवण", "पियेवेचें उदक", "नळाक उदक ना"],
    "water_leakage": ["leak", "pipe burst", "pipeline burst", "water wastage", "गळती", "पायप फुटलो", "पायप फुटला", "उदक वाया"],
    "water_pollution": ["contaminated", "dirty water", "polluted water", "muddy water", "smelly water", "घाण उदक", "दुखावलें उदक", "दुर्गंधी उदक", "गोबरें उदक"],
    "handpump_repair": ["hand pump", "handpump", "borewell", "bore well", "हातपंप", "बोरवेल", "बोअरवेल", "विहीर"],
    "road_damage": ["pothole", "road damaged", "bad road", "broken road", "road repair", "खळगो", "खळगे", "रस्तो मोडलो", "रस्तो खराब", "रस्ता दुरुस्ती", "रस्तो दुरुस्ती"],
    "streetlight_fault": ["street light", "streetlight", "street lamp", "light not working", "रस्त्यावयलो दिवो", "रस्त्यावयली बत्ती", "स्ट्रीटलाईट", "दिवो चालू ना", "बत्ती बंद"],
    "garbage_sanitation": ["garbage", "rubbish", "waste not collected", "dustbin", "dumping", "mosquito", "कचरो", "कचरा", "घाण", "स्वच्छताय", "डास"],
    "drainage_blockage": ["drain", "drainage", "sewage", "sewer", "gutter", "manhole", "गटार", "सांडपाणी", "मॅनहोल", "गटार तुबलां", "गटार बंद"],
    "property_tax_billing": ["property tax", "tax", "water bill", "bill is wrong", "excess bill", "कर", "बिल", "घरपट्टी", "वीज बिल", "उदक बिल"],
}

GENERAL_KEYWORDS = ["complaint", "grievance", "vigilance", "corruption", "employee", "rude", "तक्रार", "भ्रष्टाचार", "लांच"]

URGENT_TERMS = [
    "died", "death", "collapse", "child", "injury", "injured", "electrocut", "sick",
    "hospital", "fever", "diarrhoea", "diarrhea", "vomit", "contaminated", "unsafe",
    "manhole", "ambulance", "threat", "धमकी", "मरण", "जखम", "ताप"]


def _keywords_for(charter: Dict[str, Any]) -> Dict[str, List[str]]:
    """The keyword lists for the types the active charter has. The Chennai pack keeps its original lists."""
    merged: Dict[str, List[str]] = {}
    sources = (TYPE_KEYWORDS,) if district() == "chennai" else (TYPE_KEYWORDS, GOA_TYPE_KEYWORDS)
    for source in sources:
        for complaint_type, terms in source.items():
            if complaint_type in charter["complaint_types"]:
                merged.setdefault(complaint_type, [])
                merged[complaint_type] += [term for term in terms if term not in merged[complaint_type]]
    return merged


def _subtype(complaint_type: str, text: str) -> Dict[str, Any]:
    """Pick a subtype from the text. Report whether it was stated or assumed."""
    lowered = text.lower()
    if complaint_type == "water_leakage":
        if "transmission" in lowered:
            return {"subtype": "transmission_main", "stated": True}
        if "distribution" in lowered or " main" in lowered:
            return {"subtype": "distribution_main", "stated": True}
        if "service" in lowered:
            return {"subtype": "service_line", "stated": True}
        return {"subtype": "service_line", "stated": False}
    if complaint_type == "water_pollution":
        if any(term in lowered for term in ["not identified", "unknown source", "cannot find", "source unknown"]):
            return {"subtype": "not_identified", "stated": True}
        if any(term in lowered for term in ["at the tap", "from the tap", "pipe", "tank"]):
            return {"subtype": "identified_point", "stated": True}
        return {"subtype": "identified_point", "stated": False}
    if complaint_type == "handpump_repair":
        if "india mark" in lowered:
            return {"subtype": "india_mark_pump", "stated": True}
        return {"subtype": "hand_pump", "stated": "hand pump" in lowered or "handpump" in lowered}
    return {"subtype": None, "stated": True}


def classify_complaint(text: str) -> Dict[str, Any]:
    """Return the complaint type, subtype, urgency, and any notes for a human."""
    charter = load_charter()
    lowered = text.lower()
    urgent_hits = [term for term in URGENT_TERMS if term in lowered]
    matches: Dict[str, List[str]] = {}
    for complaint_type, terms in _keywords_for(charter).items():
        hits = [term for term in terms if term in lowered]
        if hits:
            matches[complaint_type] = hits

    notes: List[str] = []
    if not matches:
        general = [term for term in GENERAL_KEYWORDS if term in lowered]
        if general:
            complaint_type, hits = "general_grievance", general
        else:
            return {
                "complaint_type": "unclassified", "subtype": None, "urgent": bool(urgent_hits),
                "matched_terms": [], "needs_human_review": True,
                "notes": ["No charter complaint type matched."],
            }
    else:
        ranked = sorted(matches.items(), key=lambda item: len(item[1]), reverse=True)
        complaint_type, hits = ranked[0]
        if len(ranked) > 1 and len(ranked[1][1]) == len(hits):
            notes.append(f"Tie between {complaint_type} and {ranked[1][0]}; confirm the type.")

    entry = charter["complaint_types"][complaint_type]
    subtype_info = _subtype(complaint_type, text) if entry.get("subtypes") else {"subtype": None, "stated": True}
    subtype = subtype_info["subtype"]
    if entry.get("subtypes") and not subtype_info["stated"]:
        notes.append(f"Subtype not stated; defaulted to {subtype}. Confirm before relying on the deadline.")
    if complaint_type == "water_leakage" and not subtype_info["stated"]:
        notes.append("Leak location not stated. The shortest deadline (service line) is used.")

    urgent = bool(urgent_hits) or bool(entry.get("always_urgent"))
    return {
        "complaint_type": complaint_type,
        "subtype": subtype,
        "urgent": urgent,
        "matched_terms": hits,
        "needs_human_review": bool(notes) or urgent,
        "notes": notes,
    }


class ComplaintIntake(CodedTool):
    """CodedTool that classifies one complaint."""

    async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> str:
        return json.dumps(classify_complaint(str(args.get("complaint_text", ""))))
