"""Lab co-pilot support endpoints: image uploads (returning an ``upload_id``) and the read-only run audit log."""
from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

from ..agents import compatibility
from ..agents.service import get_run, list_runs, read_display, store_upload
from ..db import get_db, get_setting
from ..security import IMAGE_EXTENSIONS, validate_upload
from .common import ApiError, int_arg, llm
from .ratelimit import rate_limited

bp = Blueprint("agent", __name__, url_prefix="/api/agent")


@bp.post("/uploads")
@rate_limited("upload")
def upload_image():
    """Validate an instrument photo, store it under a server-generated name and read its display.

    The response carries an ``upload_id``; tools only ever accept that id, never a path. Any error
    code read from the image must be confirmed by the user before the co-pilot acts on it.
    """
    cfg = current_app.config
    max_bytes = min(cfg["MAX_CONTENT_LENGTH"], cfg["AGENT_UPLOAD_MAX_MB"] * 1024 * 1024)
    image = validate_upload(request.files.get("image"), IMAGE_EXTENSIONS, max_bytes=max_bytes,
                            max_image_pixels=cfg["MAX_IMAGE_PIXELS"])
    reading = read_display(llm(), image)
    upload_id = store_upload(get_db(), image, cfg["UPLOAD_DIR"], reading)
    codes = reading["extracted_codes"]
    return jsonify({
        "upload_id": upload_id,
        "extracted_codes": codes,
        "extracted_code": codes[0] if codes else None,
        "equipment_type": reading["equipment_type"],
        "observed_text": reading["observed_text"],
        "image_quality": reading["image_quality"],
        "mode": reading["mode"],
        "needs_confirmation": True,
        "message": ("Is this the code on your display?" if codes else
                    "No error code could be read from the image. Type the code shown on the display."),
    }), 201


@bp.get("/runs")
def runs():
    """Recent co-pilot runs for this organisation (read-only audit view)."""
    return jsonify(list_runs(get_db(), int_arg("limit", 50, 1, 200)))


@bp.get("/runs/<request_id>")
def run_detail(request_id: str):
    run = get_run(get_db(), request_id[:64])
    if run is None:
        raise ApiError("Run not found.", 404)
    return jsonify(run)


@bp.get("/info")
def info():
    """Static facts the UI shows next to co-pilot answers."""
    cfg = current_app.config
    db = get_db()
    return jsonify({
        "demo_data": get_setting(db, "demo_records") == "true" or get_setting(db, "demo_documents") == "true",
        "compatibility_label": compatibility.MATRIX_LABEL,
        "compatibility_expert_reviewed": compatibility.MATRIX_REVIEWED,
        "decision_support_note": "Decision support only. Confirm safety-critical steps with your lab supervisor.",
        "max_llm_calls": cfg["AGENT_MAX_LLM_CALLS"],
        "tool_timeout_s": cfg["AGENT_TOOL_TIMEOUT_S"],
        "max_question_chars": cfg["AGENT_MAX_QUESTION_CHARS"],
        "upload_max_mb": cfg["AGENT_UPLOAD_MAX_MB"],
    })
