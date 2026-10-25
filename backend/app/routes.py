from datetime import datetime, timezone

from flask import jsonify, request

from app import db
from app.config import CALL_STAGES, CALL_OUTCOMES
from app.models import Call


def register_routes(app):
    @app.get("/api/health")
    def health():
        return jsonify({
            "status": "healthy",
            "service": "deepthought-fde-backend"
        }), 200

    @app.get("/api/stages")
    def get_stages():
        return jsonify({"stages": CALL_STAGES}), 200

    @app.get("/api/stages/<int:stage_id>")
    def get_stage(stage_id):
        stage = next((s for s in CALL_STAGES if s["id"] == stage_id), None)

        if stage is None:
            return jsonify({"error": "Stage not found"}), 404

        return jsonify({"stage": stage}), 200

    @app.get("/api/outcomes")
    def get_outcomes():
        return jsonify({"outcomes": CALL_OUTCOMES}), 200

    @app.post("/api/calls")
    def create_call():
        data = request.get_json(silent=True) or {}

        prospect_name = data.get("prospect_name", "Unknown")
        company_name = data.get("company_name", "")

        if not isinstance(prospect_name, str) or not prospect_name.strip():
            return jsonify({"error": "prospect_name must not be empty"}), 400

        if not isinstance(company_name, str):
            return jsonify({"error": "company_name must be a string"}), 400

        call = Call(
            prospect_name=prospect_name.strip(),
            company_name=company_name.strip(),
        )
        db.session.add(call)
        db.session.commit()

        return jsonify({"call": call.to_dict()}), 201

    @app.get("/api/calls")
    def get_calls():
        calls = Call.query.order_by(Call.started_at.desc(), Call.id.desc()).all()
        return jsonify({"calls": [call.to_dict() for call in calls]}), 200

    @app.get("/api/calls/<int:call_id>")
    def get_call(call_id):
        call = db.session.get(Call, call_id)

        if call is None:
            return jsonify({"error": "Call not found"}), 404

        return jsonify({"call": call.to_dict()}), 200

    @app.patch("/api/calls/<int:call_id>")
    def update_call(call_id):
        call = db.session.get(Call, call_id)

        if call is None:
            return jsonify({"error": "Call not found"}), 404

        if call.status != "in_progress":
            return jsonify({"error": "This call has already ended"}), 409

        data = request.get_json(silent=True) or {}

        if "current_stage" in data:
            stage_id = data["current_stage"]

            if not isinstance(stage_id, int) or isinstance(stage_id, bool):
                return jsonify({"error": "current_stage must be an integer"}), 400

            if not 1 <= stage_id <= len(CALL_STAGES):
                return jsonify({"error": "Invalid call stage"}), 400

            call.current_stage = stage_id

        for field in ("prospect_words", "notes", "next_step"):
            if field in data:
                if not isinstance(data[field], str):
                    return jsonify({"error": f"{field} must be a string"}), 400
                setattr(call, field, data[field])

        if "outcome" in data:
            if data["outcome"] not in CALL_OUTCOMES:
                return jsonify({"error": "Invalid call outcome"}), 400
            call.outcome = data["outcome"]

        db.session.commit()
        return jsonify({"call": call.to_dict()}), 200

    @app.post("/api/calls/<int:call_id>/end")
    def end_call(call_id):
        call = db.session.get(Call, call_id)

        if call is None:
            return jsonify({"error": "Call not found"}), 404

        if call.status != "in_progress":
            return jsonify({"error": "This call has already ended"}), 409

        data = request.get_json(silent=True) or {}

        if "outcome" in data:
            if data["outcome"] not in CALL_OUTCOMES:
                return jsonify({"error": "Invalid call outcome"}), 400
            call.outcome = data["outcome"]

        if "next_step" in data:
            if not isinstance(data["next_step"], str):
                return jsonify({"error": "next_step must be a string"}), 400
            call.next_step = data["next_step"]

        if "prospect_words" in data:
            if not isinstance(data["prospect_words"], str):
                return jsonify({"error": "prospect_words must be a string"}), 400
            call.prospect_words = data["prospect_words"]

        if "notes" in data:
            if not isinstance(data["notes"], str):
                return jsonify({"error": "notes must be a string"}), 400
            call.notes = data["notes"]

        call.status = "completed"
        call.ended_at = datetime.now(timezone.utc)
        db.session.commit()

        return jsonify({"call": call.to_dict()}), 200
