"""Safely check Gemini API connectivity using backend/.env.

Run from the backend directory: python check_gemini.py
This sends one tiny test prompt. The API key is read from .env, used as a
request header, and is never printed or put into the URL.
"""
import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from dotenv import load_dotenv


def main():
    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip()

    if not api_key:
        print("CONFIG ERROR: GEMINI_API_KEY is missing from backend/.env.")
        return 2

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent"
    )
    payload = {
        "contents": [{"parts": [{"text": "Reply with exactly: OK"}]}],
        "generationConfig": {
            "thinkingConfig": {"thinkingLevel": "minimal"},
            "maxOutputTokens": 16,
        },
    }
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        },
        method="POST",
    )

    print(f"Testing Gemini connectivity with model: {model}")
    print("The API key will not be displayed.")

    try:
        with urlopen(request, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
        candidates = result.get("candidates", [])
        parts = candidates[0].get("content", {}).get("parts", []) if candidates else []
        text = " ".join(part.get("text", "") for part in parts if part.get("text")).strip()
        if not text:
            print("API REACHED, BUT NO TEXT WAS RETURNED.")
            print("Check the model response details in Google AI Studio.")
            return 1
        print("SUCCESS: Gemini API returned a response.")
        print(f"Response: {text[:200]}")
        return 0

    except HTTPError as exc:
        try:
            body = json.loads(exc.read().decode("utf-8"))
            message = body.get("error", {}).get("message", "No provider error message.")
        except (ValueError, AttributeError):
            message = "Could not parse provider error response."
        print(f"HTTP ERROR: {exc.code}")
        print(f"Provider message: {str(message)[:500]}")
        print("If the message refers to the API key, check that the key is active and allowed for the Gemini API.")
        return 1

    except URLError as exc:
        print(f"NETWORK ERROR: {type(exc.reason).__name__}")
        print("Could not complete the HTTPS request. Check the network, DNS, proxy, or TLS settings.")
        return 1

    except TimeoutError:
        print("TIMEOUT: No Gemini response arrived within 60 seconds.")
        print("If this persists, use the TCP test below and check Google AI Studio's status page.")
        return 1

    except (ValueError, KeyError, IndexError, TypeError):
        print("RESPONSE ERROR: Gemini replied, but the response could not be parsed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
