"""Analyse IA d'une annonce via Claude Haiku.

Juge si un vélo correspond au besoin : vélotaf quotidien + balades WE,
état correct, budget < 1000 €. Utilisé par main.py entre la dédup et la notif.
"""
try:
    import anthropic
    from pydantic import BaseModel

    class Verdict(BaseModel):
        garder: bool
        score: int     # 0-100, adéquation globale
        raison: str    # pourquoi garder ou écarter (une phrase)
        conseil: str   # conseil d'achat : prix vs neuf, points d'attention, verdict final

    _ANTHROPIC_AVAILABLE = True
except ImportError:
    _ANTHROPIC_AVAILABLE = False

from config import ANALYSE_CRITERES, ANALYSE_MODEL, ANTHROPIC_API_KEY


def analyze_listing(listing: dict) -> dict | None:
    """Retourne {"garder": bool, "score": int, "raison": str} ou None (fail-safe)."""
    if not _ANTHROPIC_AVAILABLE:
        print("  [info] module anthropic absent → analyse désactivée (fail-safe)")
        return None
    if not ANTHROPIC_API_KEY:
        return None

    prix = listing.get("price_raw") or "prix non précisé"
    user_msg = (
        f"Titre : {listing.get('title', '')}\n"
        f"Prix : {prix}\n"
        f"Description : {listing.get('description', '').strip() or '(aucune description)'}"
    )

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        response = client.messages.parse(
            model=ANALYSE_MODEL,
            max_tokens=512,
            system=ANALYSE_CRITERES,
            messages=[{"role": "user", "content": user_msg}],
            output_format=Verdict,
        )
        v = response.parsed_output
        return {"garder": v.garder, "score": v.score, "raison": v.raison, "conseil": v.conseil}
    except Exception as e:
        print(f"  [warn] analyse IA échouée → fail-safe (notif quand même) : {e}")
        return None
