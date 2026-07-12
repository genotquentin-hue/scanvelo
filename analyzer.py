"""Analyse IA d'une annonce via DeepSeek.

Juge si un vélo correspond au besoin : vélotaf quotidien + balades WE,
état correct, budget < 1000 €. Utilisé par main.py entre la dédup et la notif.
"""
import json

import requests

from config import ANALYSE_CRITERES, ANALYSE_MODEL, DEEPSEEK_API_KEY

DEEPSEEK_API = "https://api.deepseek.com/chat/completions"


def analyze_listing(listing: dict) -> dict | None:
    """Retourne {"garder": bool, "score": int, "raison": str, "conseil": str} ou None (fail-safe)."""
    if not DEEPSEEK_API_KEY:
        return None

    prix = listing.get("price_raw") or "prix non précisé"
    user_msg = (
        f"Titre : {listing.get('title', '')}\n"
        f"Prix : {prix}\n"
        f"Description : {listing.get('description', '').strip() or '(aucune description)'}"
    )

    try:
        resp = requests.post(
            DEEPSEEK_API,
            headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}"},
            json={
                "model": ANALYSE_MODEL,
                "messages": [
                    {"role": "system", "content": ANALYSE_CRITERES},
                    {"role": "user", "content": user_msg},
                ],
                "response_format": {"type": "json_object"},
                "max_tokens": 512,
            },
            timeout=30,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        v = json.loads(content)

        garder = v["garder"]
        score = v["score"]
        raison = v["raison"]
        conseil = v["conseil"]
        if not isinstance(garder, bool) or not isinstance(score, int):
            raise ValueError(f"schéma inattendu : {v}")

        return {"garder": garder, "score": score, "raison": raison, "conseil": conseil}
    except Exception as e:
        print(f"  [warn] analyse IA échouée → fail-safe (notif quand même) : {e}")
        return None
