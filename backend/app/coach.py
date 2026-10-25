import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from flask import jsonify, request

from app.config import CALL_STAGES


def register_coach_routes(app):
    @app.post("/api/coach")
    def get_ai_coaching():
        data = request.get_json(silent=True) or {}
        stage_id = data.get("stage_id")

        if not isinstance(stage_id, int) or isinstance(stage_id, bool):
            return jsonify({"error": "stage_id must be an integer"}), 400

        stage = next(
            (item for item in CALL_STAGES if item["id"] == stage_id),
            None,
        )
        if stage is None:
            return jsonify({"error": "Invalid call stage"}), 400

        prospect_words = data.get("prospect_words", "")
        notes = data.get("notes", "")

        if not isinstance(prospect_words, str) or not isinstance(notes, str):
            return jsonify({"error": "Notes and prospect words must be text"}), 400

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return jsonify({
                "error": "AI coaching is not configured. Add GEMINI_API_KEY to the backend environment."
            }), 503

        model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

        prompt = f"""
Help a sales representative during a live cold call.

Current stage: {stage["name"]}
Stage purpose: {stage["purpose"]}
Suggested talk track: {stage["prompt"]}
Stage guidance: {stage["guidance"]}

Prospect's exact words:
{prospect_words[:2500] or "(Not captured yet)"}

Additional notes:
{notes[:2000] or "(No additional notes)"}

Return concise, practical coaching with these three headings:
1. What to listen for
2. A useful next question or response
3. One thing to avoid

Be respectful and honest. Do not invent facts about the prospect or their company.
Do not pressure the prospect. If they ask not to be contacted, recommend ending politely
and recording the do-not-contact outcome. Keep the whole response under 150 words.
"""

        endpoint = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent?{urlencode({'key': api_key})}"
        )

        payload = {
            "systemInstruction": {
                "parts": [{
                    "text": (
                        "You are a thoughtful cold-call coaching assistant. "
                        "Provide concise, ethical, stage-specific guidance."
                    )
                }]
            },
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "thinkingConfig": {"thinkingLevel": "low"},
                "maxOutputTokens": 300
            }
        }

        req = Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode("utf-8"))

            candidates = result.get("candidates", [])
            parts = (
                candidates[0].get("content", {}).get("parts", [])
                if candidates else []
            )
            coaching = "\n".join(
                part.get("text", "")
                for part in parts
                if part.get("text")
            ).strip()

            if not coaching:
                return jsonify({
                    "error": "The AI returned no coaching text. Try again."
                }), 502

            return jsonify({
                "stage_id": stage_id,
                "stage_name": stage["name"],
                "coaching": coaching,
            }), 200

        except HTTPError as exc:
            if exc.code == 429:
                return jsonify({
                    "error": "Gemini rate limit reached. Check your free-tier quota and try again later."
                }), 429

            if exc.code in (400, 401, 403):
                return jsonify({
                    "error": "Gemini rejected the request. Check your API key, model access, and API settings."
                }), 502

            app.logger.warning("Gemini API returned HTTP %s", exc.code)
            return jsonify({"error": "The AI service request failed."}), 502

        except URLError as exc:
            # Log only the exception category: never log the request URL because it
            # includes the API key in its query string.
            reason = exc.reason
            reason_type = type(reason).__name__
            app.logger.warning(
                "Gemini connection failed (reason_type=%s)", reason_type
            )

            if isinstance(reason, TimeoutError):
                message = "The Gemini request timed out. Check your connection and try again."
            elif isinstance(reason, OSError) and getattr(reason, "errno", None) in (-2, 11001, 11002):
                message = "Could not resolve the Gemini API hostname. Check DNS or network settings."
            else:
                message = (
                    f"Could not reach the Gemini API ({reason_type}). "
                    "Check outbound HTTPS access, DNS, proxy, or TLS settings."
                )

            return jsonify({"error": message}), 502

        except TimeoutError:
            app.logger.warning("Gemini request timed out before a response was received")
            return jsonify({
                "error": "The Gemini request timed out. Check your connection and try again."
            }), 502

        except (ValueError, KeyError, IndexError, TypeError):
            app.logger.exception("Could not parse the Gemini response")
            return jsonify({"error": "The AI response could not be processed."}), 502
