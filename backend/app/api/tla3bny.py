"""tla3bny (LeagueHub) API — served under /api/tla3bny, for the
tla3bny.youthscores.org subdomain.

A faithful port of the standalone `ug/` Flask routes onto the merged backend:
academy registration/approval, player rosters with document verification, match
scheduling and result entry, visual lineups, and auto-computed standings and
leaderboards. All reads are public; writes require the tla3bny login
(`services.tla3bny_auth`), which is independent of the youthscores admin auth.
"""

from __future__ import annotations

import os
import uuid
from collections import defaultdict
from datetime import datetime

from flask import Blueprint, current_app, jsonify, request
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import (
    Tla3bnyAgeCategory,
    Tla3bnyLineup,
    Tla3bnyLineupSlot,
    Tla3bnyMatch,
    Tla3bnyMatchEvent,
    Tla3bnyPlayer,
    Tla3bnyPlayerFile,
    Tla3bnyUser,
)
from app.services import tla3bny_auth as auth

tla3bny_bp = Blueprint("tla3bny", __name__, url_prefix="/api/tla3bny")


# ── uploads ─────────────────────────────────────────────────────────────────
def _allowed(filename: str, allowed_set: set[str]) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_set


def save_upload(file_storage, kind: str = "image") -> str | None:
    """Save an uploaded file and return its relative path (``uploads/<name>``).

    kind: "image", "pdf" or "document" (image or pdf). Returns None if no file
    was provided. Raises ValueError on a disallowed extension. The path is
    relative so the same /uploads/<name> route serves it as every other upload.
    """
    if file_storage is None or file_storage.filename == "":
        return None

    images = current_app.config["ALLOWED_IMAGE_EXTENSIONS"]
    pdfs = current_app.config["ALLOWED_PDF_EXTENSIONS"]
    if kind == "pdf":
        allowed = pdfs
    elif kind == "document":
        allowed = pdfs | images
    else:
        allowed = images

    if not _allowed(file_storage.filename, allowed):
        raise ValueError(f"File type not allowed for {file_storage.filename}")

    ext = file_storage.filename.rsplit(".", 1)[1].lower()
    safe = secure_filename(f"{uuid.uuid4().hex}.{ext}")
    folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(folder, exist_ok=True)
    file_storage.save(os.path.join(folder, safe))
    return f"uploads/{safe}"


def _read_payload():
    """Return (data, files) handling both multipart and JSON bodies."""
    if request.content_type and "multipart/form-data" in request.content_type:
        return request.form, request.files
    return (request.get_json(silent=True) or {}), None


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


# ── auth ────────────────────────────────────────────────────────────────────
@tla3bny_bp.post("/auth/register")
def register():
    """Register a new academy (multipart for a logo, or JSON)."""
    data, files = _read_payload()
    logo = files.get("logo") if files is not None else None

    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    phone = (data.get("phone") or "").strip()
    address = (data.get("address") or "").strip()

    if not name or not email or not password:
        return jsonify({"error": "name, email and password are required"}), 400
    if Tla3bnyUser.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 409

    logo_path = None
    if logo is not None:
        try:
            logo_path = save_upload(logo, kind="image")
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

    user = Tla3bnyUser(
        email=email,
        role="academy",
        status="pending",
        name=name,
        phone=phone,
        address=address,
        logo_path=logo_path,
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return (
        jsonify(
            {
                "message": "Registration submitted. Awaiting admin approval.",
                "token": auth.generate_token(user),
                "user": user.to_dict(),
            }
        ),
        201,
    )


@tla3bny_bp.post("/auth/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = Tla3bnyUser.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid email or password"}), 401

    return jsonify({"token": auth.generate_token(user), "user": user.to_dict()})


@tla3bny_bp.get("/auth/me")
@auth.login_required
def me():
    return jsonify({"user": auth.current_user().to_dict()})


# ── academies ───────────────────────────────────────────────────────────────
@tla3bny_bp.get("/academies")
def list_academies():
    """Public: approved academies only."""
    academies = (
        Tla3bnyUser.query.filter_by(role="academy", status="approved")
        .order_by(Tla3bnyUser.name.asc())
        .all()
    )
    return jsonify([a.to_dict(public=True) for a in academies])


@tla3bny_bp.get("/academies/manage")
@auth.role_required("super_admin")
def manage_academies():
    """Super admin: all academies, optionally filtered by status."""
    status = request.args.get("status")
    q = Tla3bnyUser.query.filter_by(role="academy")
    if status:
        q = q.filter_by(status=status)
    academies = q.order_by(Tla3bnyUser.created_at.desc()).all()
    return jsonify([a.to_dict() for a in academies])


@tla3bny_bp.get("/academies/<int:academy_id>")
def get_academy(academy_id: int):
    academy = Tla3bnyUser.query.filter_by(
        id=academy_id, role="academy"
    ).first_or_404()
    return jsonify(academy.to_dict(public=True))


@tla3bny_bp.post("/academies/<int:academy_id>/approve")
@auth.role_required("super_admin")
def approve_academy(academy_id: int):
    academy = Tla3bnyUser.query.filter_by(
        id=academy_id, role="academy"
    ).first_or_404()
    academy.status = "approved"
    academy.rejection_reason = None
    db.session.commit()
    return jsonify(academy.to_dict())


@tla3bny_bp.post("/academies/<int:academy_id>/reject")
@auth.role_required("super_admin")
def reject_academy(academy_id: int):
    academy = Tla3bnyUser.query.filter_by(
        id=academy_id, role="academy"
    ).first_or_404()
    data = request.get_json(silent=True) or {}
    academy.status = "rejected"
    academy.rejection_reason = (data.get("reason") or "").strip() or None
    db.session.commit()
    return jsonify(academy.to_dict())


@tla3bny_bp.post("/academies/<int:academy_id>/suspend")
@auth.role_required("super_admin")
def suspend_academy(academy_id: int):
    academy = Tla3bnyUser.query.filter_by(
        id=academy_id, role="academy"
    ).first_or_404()
    academy.status = "pending"
    db.session.commit()
    return jsonify(academy.to_dict())


@tla3bny_bp.put("/academies/me")
@auth.role_required("academy")
def update_own_profile():
    """Academy edits its own profile (name, phone, address, logo)."""
    academy = auth.current_user()
    data, files = _read_payload()
    logo = files.get("logo") if files is not None else None

    if data.get("name"):
        academy.name = data.get("name").strip()
    if data.get("phone") is not None:
        academy.phone = (data.get("phone") or "").strip()
    if data.get("address") is not None:
        academy.address = (data.get("address") or "").strip()

    if logo is not None:
        try:
            academy.logo_path = save_upload(logo, kind="image")
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

    db.session.commit()
    return jsonify(academy.to_dict())


# ── age categories ──────────────────────────────────────────────────────────
def _parse_required_files(data, default: int = 1) -> int:
    try:
        return max(0, int(data.get("required_files")))
    except (TypeError, ValueError):
        return default


@tla3bny_bp.get("/categories")
def list_categories():
    cats = Tla3bnyAgeCategory.query.order_by(Tla3bnyAgeCategory.label.asc()).all()
    return jsonify([c.to_dict() for c in cats])


@tla3bny_bp.post("/categories")
@auth.role_required("super_admin")
def create_category():
    data = request.get_json(silent=True) or {}
    label = (data.get("label") or "").strip()
    if not label:
        return jsonify({"error": "label is required"}), 400
    if Tla3bnyAgeCategory.query.filter_by(label=label).first():
        return jsonify({"error": "Category already exists"}), 409
    cat = Tla3bnyAgeCategory(label=label, required_files=_parse_required_files(data))
    db.session.add(cat)
    db.session.commit()
    return jsonify(cat.to_dict()), 201


@tla3bny_bp.put("/categories/<int:cat_id>")
@auth.role_required("super_admin")
def update_category(cat_id: int):
    cat = Tla3bnyAgeCategory.query.get_or_404(cat_id)
    data = request.get_json(silent=True) or {}
    label = (data.get("label") or "").strip()
    if not label:
        return jsonify({"error": "label is required"}), 400
    existing = Tla3bnyAgeCategory.query.filter_by(label=label).first()
    if existing and existing.id != cat_id:
        return jsonify({"error": "Category already exists"}), 409
    cat.label = label
    if "required_files" in data:
        cat.required_files = _parse_required_files(data, cat.required_files)
    db.session.commit()
    return jsonify(cat.to_dict())


@tla3bny_bp.delete("/categories/<int:cat_id>")
@auth.role_required("super_admin")
def delete_category(cat_id: int):
    cat = Tla3bnyAgeCategory.query.get_or_404(cat_id)
    db.session.delete(cat)
    db.session.commit()
    return jsonify({"message": "deleted"})


# ── players ─────────────────────────────────────────────────────────────────
def _parse_dob(value):
    return _parse_date(value)


def _save_documents(player: Tla3bnyPlayer, files) -> None:
    """Save uploaded documents (field 'documents', multiple; plus legacy
    single 'papers') and attach them to the player."""
    if files is None:
        return
    uploaded = files.getlist("documents") if hasattr(files, "getlist") else []
    if files.get("papers"):
        uploaded = list(uploaded) + [files.get("papers")]
    for f in uploaded:
        if f is None or f.filename == "":
            continue
        path = save_upload(f, kind="document")
        if path:
            db.session.add(
                Tla3bnyPlayerFile(
                    player_id=player.id, file_path=path, original_name=f.filename
                )
            )
            if not player.papers_path:
                player.papers_path = path


@tla3bny_bp.get("/players")
def list_players():
    """Public read. Defaults to approved players; filter by academy_id,
    age_category_id, and an optional status override."""
    q = Tla3bnyPlayer.query
    academy_id = request.args.get("academy_id", type=int)
    category_id = request.args.get("age_category_id", type=int)
    status = request.args.get("status")
    if academy_id:
        q = q.filter_by(academy_id=academy_id)
    if category_id:
        q = q.filter_by(age_category_id=category_id)
    q = q.filter_by(status=status) if status else q.filter_by(status="approved")
    # (col IS NULL) ASC puts un-numbered players last — MySQL has no NULLS LAST.
    players = q.order_by(
        Tla3bnyPlayer.jersey_number.is_(None), Tla3bnyPlayer.jersey_number.asc()
    ).all()
    return jsonify([p.to_dict() for p in players])


@tla3bny_bp.get("/players/mine")
@auth.approved_academy_required
def my_players():
    academy_id = auth.current_user().id
    players = (
        Tla3bnyPlayer.query.filter_by(academy_id=academy_id)
        .order_by(Tla3bnyPlayer.jersey_number.is_(None), Tla3bnyPlayer.jersey_number.asc())
        .all()
    )
    return jsonify([p.to_dict() for p in players])


@tla3bny_bp.get("/players/manage")
@auth.role_required("super_admin")
def manage_players():
    """All players (with files) for verification. Optional status filter."""
    status = request.args.get("status")
    q = Tla3bnyPlayer.query
    if status:
        q = q.filter_by(status=status)
    players = q.order_by(Tla3bnyPlayer.created_at.desc()).all()
    return jsonify([p.to_dict() for p in players])


@tla3bny_bp.get("/players/<int:player_id>")
def get_player(player_id: int):
    player = Tla3bnyPlayer.query.get_or_404(player_id)
    return jsonify(player.to_dict())


@tla3bny_bp.get("/players/<int:player_id>/stats")
def player_stats(player_id: int):
    """Public: aggregated career stats for a player (finished matches only)."""
    player = Tla3bnyPlayer.query.get_or_404(player_id)
    events = (
        Tla3bnyMatchEvent.query.join(
            Tla3bnyMatch, Tla3bnyMatchEvent.match_id == Tla3bnyMatch.id
        )
        .filter(
            Tla3bnyMatchEvent.player_id == player_id,
            Tla3bnyMatch.status == "finished",
        )
        .all()
    )
    match_ids = {e.match_id for e in events}
    goals = sum(1 for e in events if e.event_type == "goal")
    assists = sum(1 for e in events if e.event_type == "assist")
    yellow = sum(1 for e in events if e.event_type == "yellow")
    red = sum(1 for e in events if e.event_type == "red")
    return jsonify(
        {
            "player": player.to_dict(),
            "goals": goals,
            "assists": assists,
            "yellow_cards": yellow,
            "red_cards": red,
            "matches_with_events": len(match_ids),
        }
    )


@tla3bny_bp.post("/players")
@auth.approved_academy_required
def create_player():
    academy_id = auth.current_user().id
    data, files = _read_payload()

    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name is required"}), 400

    photo_path = None
    try:
        if files is not None and files.get("photo"):
            photo_path = save_upload(files.get("photo"), kind="image")
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    player = Tla3bnyPlayer(
        academy_id=academy_id,
        age_category_id=data.get("age_category_id") or None,
        name=name,
        position=data.get("position"),
        sub_position=data.get("sub_position"),
        dob=_parse_dob(data.get("dob")),
        jersey_number=data.get("jersey_number") or None,
        photo_path=photo_path,
        status="pending",
    )
    db.session.add(player)
    db.session.flush()
    try:
        _save_documents(player, files)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    db.session.commit()
    return jsonify(player.to_dict()), 201


@tla3bny_bp.put("/players/<int:player_id>")
@auth.approved_academy_required
def update_player(player_id: int):
    academy_id = auth.current_user().id
    player = Tla3bnyPlayer.query.get_or_404(player_id)
    if player.academy_id != academy_id:
        return jsonify({"error": "Not your player"}), 403

    data, files = _read_payload()

    if data.get("name"):
        player.name = data.get("name").strip()
    if "age_category_id" in data:
        player.age_category_id = data.get("age_category_id") or None
    if "position" in data:
        player.position = data.get("position")
    if "sub_position" in data:
        player.sub_position = data.get("sub_position")
    if "dob" in data:
        player.dob = _parse_dob(data.get("dob"))
    if "jersey_number" in data:
        player.jersey_number = data.get("jersey_number") or None

    try:
        if files is not None and files.get("photo"):
            player.photo_path = save_upload(files.get("photo"), kind="image")
        _save_documents(player, files)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    # Any edit re-submits the player for verification.
    player.status = "pending"
    player.rejection_reason = None

    db.session.commit()
    return jsonify(player.to_dict())


@tla3bny_bp.delete("/players/<int:player_id>/files/<int:file_id>")
@auth.approved_academy_required
def delete_player_file(player_id: int, file_id: int):
    academy_id = auth.current_user().id
    player = Tla3bnyPlayer.query.get_or_404(player_id)
    if player.academy_id != academy_id:
        return jsonify({"error": "Not your player"}), 403
    pf = Tla3bnyPlayerFile.query.filter_by(
        id=file_id, player_id=player_id
    ).first_or_404()
    db.session.delete(pf)
    db.session.commit()
    return jsonify({"message": "deleted"})


@tla3bny_bp.delete("/players/<int:player_id>")
@auth.approved_academy_required
def delete_player(player_id: int):
    academy_id = auth.current_user().id
    player = Tla3bnyPlayer.query.get_or_404(player_id)
    if player.academy_id != academy_id:
        return jsonify({"error": "Not your player"}), 403
    db.session.delete(player)
    db.session.commit()
    return jsonify({"message": "deleted"})


@tla3bny_bp.post("/players/<int:player_id>/approve")
@auth.role_required("super_admin")
def approve_player(player_id: int):
    player = Tla3bnyPlayer.query.get_or_404(player_id)
    player.status = "approved"
    player.rejection_reason = None
    db.session.commit()
    return jsonify(player.to_dict())


@tla3bny_bp.post("/players/<int:player_id>/reject")
@auth.role_required("super_admin")
def reject_player(player_id: int):
    player = Tla3bnyPlayer.query.get_or_404(player_id)
    data = request.get_json(silent=True) or {}
    player.status = "rejected"
    player.rejection_reason = (data.get("reason") or "").strip() or None
    db.session.commit()
    return jsonify(player.to_dict())


# ── matches ─────────────────────────────────────────────────────────────────
@tla3bny_bp.get("/matches")
def list_matches():
    """Public feed. Filters: age_category_id, status, academy_id."""
    q = Tla3bnyMatch.query
    category_id = request.args.get("age_category_id", type=int)
    status = request.args.get("status")
    academy_id = request.args.get("academy_id", type=int)

    if category_id:
        q = q.filter_by(age_category_id=category_id)
    if status:
        q = q.filter_by(status=status)
    if academy_id:
        q = q.filter(
            (Tla3bnyMatch.home_academy_id == academy_id)
            | (Tla3bnyMatch.away_academy_id == academy_id)
        )

    # date IS NULL sorts undated (TBD) fixtures last — MySQL has no NULLS LAST.
    matches = q.order_by(
        Tla3bnyMatch.date.is_(None), Tla3bnyMatch.date.desc(), Tla3bnyMatch.time.desc()
    ).all()
    return jsonify([m.to_dict() for m in matches])


@tla3bny_bp.get("/matches/<int:match_id>")
def get_match(match_id: int):
    match = Tla3bnyMatch.query.get_or_404(match_id)
    return jsonify(match.to_dict(include_events=True))


@tla3bny_bp.post("/matches")
@auth.role_required("super_admin")
def create_match():
    data = request.get_json(silent=True) or {}

    home_id = data.get("home_academy_id")
    away_id = data.get("away_academy_id")
    category_id = data.get("age_category_id")

    if not home_id or not away_id or not category_id:
        return (
            jsonify(
                {
                    "error": "home_academy_id, away_academy_id and "
                    "age_category_id are required"
                }
            ),
            400,
        )
    if home_id == away_id:
        return jsonify({"error": "Home and away academies must differ"}), 400

    for aid in (home_id, away_id):
        acad = Tla3bnyUser.query.filter_by(id=aid, role="academy").first()
        if not acad:
            return jsonify({"error": f"Academy {aid} not found"}), 404

    match = Tla3bnyMatch(
        home_academy_id=home_id,
        away_academy_id=away_id,
        age_category_id=category_id,
        date=_parse_date(data.get("date")),
        time=data.get("time"),
        venue=data.get("venue"),
        duration_minutes=data.get("duration_minutes") or 60,
        num_periods=data.get("num_periods") or 2,
        max_substitutions=data.get("max_substitutions")
        if data.get("max_substitutions") is not None
        else 5,
        status="scheduled",
    )
    db.session.add(match)
    db.session.commit()
    return jsonify(match.to_dict()), 201


@tla3bny_bp.put("/matches/<int:match_id>")
@auth.role_required("super_admin")
def update_match(match_id: int):
    match = Tla3bnyMatch.query.get_or_404(match_id)
    data = request.get_json(silent=True) or {}

    for field in ("time", "venue", "status"):
        if field in data:
            setattr(match, field, data.get(field))
    if "date" in data:
        match.date = _parse_date(data.get("date"))
    if "age_category_id" in data and data.get("age_category_id"):
        match.age_category_id = data.get("age_category_id")
    for field in ("duration_minutes", "num_periods", "max_substitutions"):
        if field in data and data.get(field) is not None:
            setattr(match, field, data.get(field))

    db.session.commit()
    return jsonify(match.to_dict())


@tla3bny_bp.delete("/matches/<int:match_id>")
@auth.role_required("super_admin")
def delete_match(match_id: int):
    match = Tla3bnyMatch.query.get_or_404(match_id)
    db.session.delete(match)
    db.session.commit()
    return jsonify({"message": "deleted"})


@tla3bny_bp.post("/matches/<int:match_id>/result")
@auth.role_required("super_admin")
def enter_result(match_id: int):
    """Enter final score + events, replacing any existing events.

    events[] carry an optional temp_id; an assist links to its goal via
    related_temp_id, resolved to the real goal id after the goals are inserted.
    """
    match = Tla3bnyMatch.query.get_or_404(match_id)
    data = request.get_json(silent=True) or {}

    match.home_score = data.get("home_score")
    match.away_score = data.get("away_score")

    Tla3bnyMatchEvent.query.filter_by(match_id=match.id).delete()
    db.session.flush()

    events_in = data.get("events") or []
    temp_map = {}
    pending_assists = []

    for ev in events_in:
        etype = ev.get("event_type")
        if not etype:
            continue
        if etype == "assist" and ev.get("related_temp_id"):
            pending_assists.append(ev)
            continue
        obj = Tla3bnyMatchEvent(
            match_id=match.id,
            player_id=ev.get("player_id"),
            team_academy_id=ev.get("team_academy_id"),
            event_type=etype,
            minute=ev.get("minute"),
        )
        db.session.add(obj)
        db.session.flush()
        if ev.get("temp_id"):
            temp_map[ev["temp_id"]] = obj.id

    for ev in pending_assists:
        related = temp_map.get(ev.get("related_temp_id"))
        db.session.add(
            Tla3bnyMatchEvent(
                match_id=match.id,
                player_id=ev.get("player_id"),
                team_academy_id=ev.get("team_academy_id"),
                event_type="assist",
                minute=ev.get("minute"),
                related_event_id=related,
            )
        )

    match.status = "finished"
    db.session.commit()
    return jsonify(match.to_dict(include_events=True))


# ── lineups ─────────────────────────────────────────────────────────────────
@tla3bny_bp.get("/lineups/match/<int:match_id>")
def get_match_lineups(match_id: int):
    """Public: both teams' lineups for a match."""
    lineups = Tla3bnyLineup.query.filter_by(match_id=match_id).all()
    return jsonify([l.to_dict() for l in lineups])


def _can_edit_lineup(match: Tla3bnyMatch, academy_id: int) -> bool:
    """Super admin edits any; an approved academy edits only its own side."""
    user = auth.current_user()
    if not user:
        return False
    if user.role == "super_admin":
        return True
    if user.role == "academy" and user.status == "approved":
        return user.id == academy_id and academy_id in (
            match.home_academy_id,
            match.away_academy_id,
        )
    return False


@tla3bny_bp.put("/lineups/match/<int:match_id>/academy/<int:academy_id>")
def save_lineup(match_id: int, academy_id: int):
    """Create or replace a team's lineup for a match.

    Payload: {"formation": "4-3-3",
              "slots": [{"position_slot":"GK","player_id":3,
                         "is_substitute":false}, ...]}
    """
    match = Tla3bnyMatch.query.get_or_404(match_id)
    if academy_id not in (match.home_academy_id, match.away_academy_id):
        return jsonify({"error": "Academy is not part of this match"}), 400
    if not _can_edit_lineup(match, academy_id):
        return jsonify({"error": "Insufficient permissions"}), 403

    data = request.get_json(silent=True) or {}
    formation = data.get("formation")
    slots = data.get("slots") or []

    lineup = Tla3bnyLineup.query.filter_by(
        match_id=match_id, academy_id=academy_id
    ).first()
    if not lineup:
        lineup = Tla3bnyLineup(match_id=match_id, academy_id=academy_id)
        db.session.add(lineup)
    lineup.formation = formation

    if lineup.id:
        Tla3bnyLineupSlot.query.filter(
            Tla3bnyLineupSlot.lineup_id == lineup.id
        ).delete()
    db.session.flush()

    for s in slots:
        db.session.add(
            Tla3bnyLineupSlot(
                lineup_id=lineup.id,
                position_slot=s.get("position_slot"),
                player_id=s.get("player_id") or None,
                is_substitute=bool(s.get("is_substitute", False)),
            )
        )

    db.session.commit()
    return jsonify(lineup.to_dict())


# ── standings ───────────────────────────────────────────────────────────────
def _blank_row(academy: Tla3bnyUser) -> dict:
    return {
        "academy_id": academy.id,
        "academy_name": academy.name,
        "logo_path": academy.logo_path,
        "P": 0, "W": 0, "D": 0, "L": 0,
        "GF": 0, "GA": 0, "GD": 0, "Pts": 0,
    }


@tla3bny_bp.get("/standings")
def standings():
    """Public standings for one age category (from finished matches).

    Query: age_category_id (required).
    """
    category_id = request.args.get("age_category_id", type=int)
    if not category_id:
        return jsonify({"error": "age_category_id is required"}), 400

    matches = Tla3bnyMatch.query.filter_by(
        age_category_id=category_id, status="finished"
    ).all()

    rows: dict[int, dict] = {}

    def ensure(academy):
        if academy and academy.id not in rows:
            rows[academy.id] = _blank_row(academy)

    for m in matches:
        if m.home_score is None or m.away_score is None:
            continue
        ensure(m.home_academy)
        ensure(m.away_academy)
        if not m.home_academy or not m.away_academy:
            continue

        h = rows[m.home_academy_id]
        a = rows[m.away_academy_id]

        h["P"] += 1
        a["P"] += 1
        h["GF"] += m.home_score
        h["GA"] += m.away_score
        a["GF"] += m.away_score
        a["GA"] += m.home_score

        if m.home_score > m.away_score:
            h["W"] += 1; h["Pts"] += 3
            a["L"] += 1
        elif m.home_score < m.away_score:
            a["W"] += 1; a["Pts"] += 3
            h["L"] += 1
        else:
            h["D"] += 1; h["Pts"] += 1
            a["D"] += 1; a["Pts"] += 1

    table = list(rows.values())
    for r in table:
        r["GD"] = r["GF"] - r["GA"]

    # Recent form (last 5 finished results per team, chronological old -> new).
    ordered = sorted(
        matches, key=lambda m: (m.date.isoformat() if m.date else "", m.time or "")
    )
    form_map = defaultdict(list)
    for m in ordered:
        if m.home_score is None or m.away_score is None:
            continue
        if not m.home_academy or not m.away_academy:
            continue
        if m.home_score > m.away_score:
            form_map[m.home_academy_id].append("W")
            form_map[m.away_academy_id].append("L")
        elif m.home_score < m.away_score:
            form_map[m.home_academy_id].append("L")
            form_map[m.away_academy_id].append("W")
        else:
            form_map[m.home_academy_id].append("D")
            form_map[m.away_academy_id].append("D")
    for r in table:
        r["form"] = form_map[r["academy_id"]][-5:]

    table.sort(
        key=lambda r: (-r["Pts"], -r["GD"], -r["GF"], (r["academy_name"] or "").lower())
    )
    for i, r in enumerate(table, start=1):
        r["rank"] = i

    return jsonify(table)


# ── analysis / leaderboards ─────────────────────────────────────────────────
@tla3bny_bp.get("/analysis")
def analysis():
    """Public leaderboards for one age category, from finished matches.

    Query: age_category_id (required). Returns top_scorers, top_assisters,
    clean_sheets, yellow_cards, red_cards.
    """
    category_id = request.args.get("age_category_id", type=int)
    if not category_id:
        return jsonify({"error": "age_category_id is required"}), 400

    matches = Tla3bnyMatch.query.filter_by(
        age_category_id=category_id, status="finished"
    ).all()
    match_ids = [m.id for m in matches]

    goals = defaultdict(int)
    assists = defaultdict(int)
    yellows = defaultdict(int)
    reds = defaultdict(int)

    if match_ids:
        events = Tla3bnyMatchEvent.query.filter(
            Tla3bnyMatchEvent.match_id.in_(match_ids)
        ).all()
        for e in events:
            if e.player_id is None:
                continue
            if e.event_type == "goal":
                goals[e.player_id] += 1
            elif e.event_type == "assist":
                assists[e.player_id] += 1
            elif e.event_type == "yellow":
                yellows[e.player_id] += 1
            elif e.event_type == "red":
                reds[e.player_id] += 1

    def build_player_board(counter):
        board = []
        for pid, count in counter.items():
            p = Tla3bnyPlayer.query.get(pid)
            if not p:
                continue
            board.append(
                {
                    "player_id": pid,
                    "player_name": p.name,
                    "academy_id": p.academy_id,
                    "academy_name": p.academy.name if p.academy else None,
                    "photo_path": p.photo_path,
                    "count": count,
                }
            )
        board.sort(key=lambda x: (-x["count"], (x["player_name"] or "").lower()))
        return board

    clean = defaultdict(int)
    for m in matches:
        if m.home_score is None or m.away_score is None:
            continue
        if m.away_score == 0:
            clean[m.home_academy_id] += 1
        if m.home_score == 0:
            clean[m.away_academy_id] += 1

    clean_board = []
    for aid, count in clean.items():
        acad = Tla3bnyUser.query.get(aid)
        if not acad:
            continue
        clean_board.append(
            {
                "academy_id": aid,
                "academy_name": acad.name,
                "logo_path": acad.logo_path,
                "count": count,
            }
        )
    clean_board.sort(key=lambda x: (-x["count"], (x["academy_name"] or "").lower()))

    return jsonify(
        {
            "top_scorers": build_player_board(goals),
            "top_assisters": build_player_board(assists),
            "clean_sheets": clean_board,
            "yellow_cards": build_player_board(yellows),
            "red_cards": build_player_board(reds),
        }
    )
