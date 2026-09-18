"""JSON-LD structured data + the </script>-breakout guard in the share injector.

These give crawlers machine-readable content the client-rendered shell lacks;
the escaping check matters because item names are free text from the DB."""

import json

from app import _event_fields, _inject_share_meta, _jsonld_script


def _parse(s: str) -> dict:
    return json.loads(s[s.index(">") + 1 : s.rindex("<")].replace("<\\/", "</"))


def _extract_jsonld(html: str) -> dict:
    start = html.index('<script type="application/ld+json">') + len(
        '<script type="application/ld+json">'
    )
    end = html.index("</script>", start)
    # Reverse the </ -> <\/ guard so json can parse it back.
    return json.loads(html[start:end].replace("<\\/", "</"))


def test_jsonld_has_context_type_name_url():
    # A non-Event type only needs name/url/image — no event fields required.
    s = _jsonld_script("SportsTeam", {"title": "A"}, "https://x/team/5/", "https://x/i.png")
    obj = _parse(s)
    assert obj["@context"] == "https://schema.org"
    assert obj["@type"] == "SportsTeam"
    assert obj["name"] == "A"
    assert obj["url"] == "https://x/team/5/"
    assert obj["image"] == "https://x/i.png"


def test_event_type_without_event_data_is_omitted():
    # A SportsEvent needs startDate + location; with none, emit nothing rather than
    # an invalid Event (which Search Console flags as a critical error).
    assert _jsonld_script("SportsEvent", {"title": "A vs B"}, "https://x/match/5/", "") == ""


def test_event_jsonld_carries_required_and_recommended_fields():
    from datetime import datetime

    meta = {
        "title": "A vs B",
        "event": _event_fields(
            datetime(2026, 9, 18, 16, 0),
            location="ملعب القاهرة",
            location_url="https://maps/x",
            end=datetime(2026, 9, 18, 18, 0),
            status="scheduled",
            competitors=["A", "B"],
            organizer="Youth Cup",
        ),
    }
    obj = _parse(_jsonld_script("SportsEvent", meta, "https://x/match/5/", "https://x/i.png"))
    assert obj["startDate"] == "2026-09-18T16:00:00"
    assert obj["endDate"] == "2026-09-18T18:00:00"
    assert obj["location"]["@type"] == "Place"
    assert obj["location"]["name"] == "ملعب القاهرة"
    assert obj["location"]["url"] == "https://maps/x"
    assert obj["eventStatus"] == "https://schema.org/EventScheduled"
    assert [t["name"] for t in obj["performer"]] == ["A", "B"]
    assert [t["name"] for t in obj["competitor"]] == ["A", "B"]
    assert obj["organizer"]["name"] == "Youth Cup"


def test_event_fields_empty_without_start_date():
    # A TBD fixture (no date) produces no event dict at all.
    assert _event_fields(None, location="ملعب") == {}


def test_jsonld_omits_missing_description_and_image():
    s = _jsonld_script("Person", {"title": "لاعب"}, "https://x/player/1/", "")
    obj = json.loads(s[s.index(">") + 1 : s.rindex("<")].replace("<\\/", "</"))
    assert "image" not in obj and "description" not in obj
    assert obj["name"] == "لاعب"  # Arabic kept readable (ensure_ascii=False)


def test_script_breakout_is_neutralised():
    # A hostile item name must not be able to close the script tag early.
    s = _jsonld_script("Person", {"title": "</script><script>alert(1)</script>"},
                       "https://x/player/1/", "")
    # No raw </script> before our own closing tag.
    inner = s[: s.rindex("</script>")]
    assert "</script>" not in inner
    assert "<\\/script>" in inner


def test_inject_adds_jsonld_when_schema_type_given():
    html = "<html><head><title>x</title><meta name=\"description\" content=\"\"/></head><body></body></html>"
    out = _inject_share_meta(
        html, {"title": "Team A", "description": "u17"}, "https://x/team/3/",
        "https://x/logo.png", og_type="website", schema_type="SportsTeam",
    )
    obj = _extract_jsonld(out)
    assert obj["@type"] == "SportsTeam"
    assert obj["name"] == "Team A"
    assert obj["description"] == "u17"
    # OG tags still present.
    assert 'property="og:title"' in out


def test_inject_skips_jsonld_when_no_schema_type():
    html = "<html><head><title>x</title></head><body></body></html>"
    out = _inject_share_meta(
        html, {"title": "Team A"}, "https://x/", "https://x/i.png",
    )
    assert "application/ld+json" not in out
