"""Tests for the Goa pack: its data, the Konkani names and words, and the default district."""

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from complaint_portal.language import detect_language
from complaint_portal.locations import load_locations, match_zones
from complaintrouter import common

ROOT = Path(__file__).resolve().parents[1]
DEVANAGARI = re.compile("[ऀ-ॿ]")
KANNADA = re.compile("[ಀ-೿]")


def test_goa_is_the_default_district():
    code = ("import sys; sys.path.insert(0, 'complaint_tools'); "
            "from complaintrouter import common; print(common.district())")
    out = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, check=True,
                         env={"PATH": "/usr/bin:/bin"})
    assert out.stdout.strip() == "goa"
    assert "goa" in common.DISTRICTS


def test_the_goa_charter_names_goa_and_is_labelled_a_sample(goa):
    charter = common.load_charter()
    assert charter["state"] == "Goa"
    assert "Sample" in charter["label"] and "Goa" in charter["label"]
    assert "Kalaburagi" not in json.dumps(charter, ensure_ascii=False)
    assert not KANNADA.search(json.dumps(charter, ensure_ascii=False))


def test_every_label_has_a_konkani_name_in_devanagari(goa):
    charter = common.load_charter()
    names = charter["konkani_names"]
    labels = {entry["label"] for entry in charter["complaint_types"].values()}
    labels |= set(charter["fields"].values()) | set(charter["owners"].values()) | set(charter["stage_labels"].values())
    labels.add(charter["ward_office_label"])
    labels |= {zone.name for zone in load_locations().zones.values()}
    assert sorted(label for label in labels if label not in names) == []
    assert all(DEVANAGARI.search(value) for value in names.values())


def test_goa_has_twelve_talukas_and_the_panaji_wards(goa):
    data = load_locations()
    assert len(data.zones) == 12 and data.total == 41
    assert data.zone(1).name == "Panaji City" and data.zone(1).ward_to == 30
    assert data.ward(41).zone_name == "Dharbandora"


@pytest.mark.parametrize("address, zone", [
    ("Near the church, Calangute, Bardez", 2),
    ("Mapusa market", 2),
    ("Palolem beach road, Canacona", 11),
    ("Sanquelim bus stand", 4),
    ("Dabolim airport road", 7),
    ("Colva, Salcete", 8),
])
def test_goa_places_match_their_taluka(goa, address, zone):
    assert match_zones(address, load_locations())[0][0] == zone


@pytest.mark.parametrize("text, expected", [
    ("आमच्या रस्त्यार तीन दीस उदक येना", "no_water_supply"),
    ("रस्त्यार व्हडलो खळगो आसा", "road_damage"),
    ("रस्त्यावयलो दिवो चालू ना", "streetlight_fault"),
    ("आमच्या गल्लींत कचरो उखलूंक ना", "garbage_sanitation"),
    ("गटार तुबलां आनी सांडपाणी रस्त्यार येता", "drainage_blockage"),
])
def test_konkani_words_find_the_complaint_type(goa, text, expected):
    from complaintrouter.pipeline import run_complaint
    result = run_complaint(text, None, use_llm=False)
    assert result["classification"]["complaint_type"] == expected


def test_devanagari_text_is_detected_as_konkani(goa):
    assert detect_language("आमच्या रस्त्यार तीन दीस उदक येना") == "kok"
    assert detect_language("There is no water") == "en"


def test_no_page_or_script_still_shows_kannada_or_kalaburagi():
    leftovers = []
    for folder in ("portal", "complaint_tools/complaint_portal", "complaint_tools/complaintrouter", "data"):
        for path in (ROOT / folder).rglob("*"):
            if not path.is_file() or path.suffix not in (".py", ".js", ".html", ".json", ".csv", ".webmanifest"):
                continue
            if path.name in ("charter.json",) or "vendor" in path.parts or "data" in path.parts and path.name.startswith("chennai"):
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            if KANNADA.search(text) or "Kalaburagi" in text or "Kannada" in text:
                leftovers.append(str(path.relative_to(ROOT)))
    assert leftovers == []


def test_two_portals_can_share_one_database_with_their_own_table(monkeypatch):
    from complaint_portal import durable
    monkeypatch.delenv("SNAPSHOT_TABLE", raising=False)
    assert durable._table_name() == "portal_snapshot"          # Kalaburagi keeps its table
    monkeypatch.setenv("SNAPSHOT_TABLE", "goa_snapshot")
    assert durable._table_name() == "goa_snapshot"
    monkeypatch.setenv("SNAPSHOT_TABLE", "x; drop table y")
    with pytest.raises(ValueError):
        durable._table_name()


def test_the_goa_blueprint_shares_the_existing_free_database_in_its_own_table():
    text = (ROOT / "render.yaml").read_text()
    assert "databases:" not in text and "kalaburagi-data" in text and "goa_snapshot" in text
