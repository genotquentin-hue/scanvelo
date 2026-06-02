"""Récap quotidien par email. Lancé une fois par jour par GitHub Actions.

Lit recent.json, garde les annonces vues dans les dernières 24h, et envoie
un email récapitulatif via Gmail.

Usage :
  python recap.py            # envoie le récap
  python recap.py --dry-run  # affiche le récap sans l'envoyer
"""
import sys
from datetime import datetime, timedelta, timezone

from notifier import send_email_recap
from store import load_recent


def listings_last_24h() -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    recent = load_recent()
    result = []
    for l in recent:
        try:
            seen = datetime.fromisoformat(l["seen_at"])
        except (KeyError, ValueError):
            continue
        if seen >= cutoff:
            result.append(l)
    # Du plus récent au plus ancien
    result.sort(key=lambda l: l["seen_at"], reverse=True)
    return result


def main(dry_run: bool = False) -> None:
    listings = listings_last_24h()
    today = datetime.now(timezone.utc).strftime("%d/%m/%Y")
    subject = f"🚲 Récap vélos {today} — {len(listings)} annonce(s)"

    print(f"{len(listings)} annonce(s) dans les dernières 24h")

    if dry_run:
        for l in listings:
            print(f"  • {l['title']} — {l['price_raw']} — {l.get('location')}")
        return

    if send_email_recap(listings, subject=subject):
        print("✓ récap envoyé par email")
    else:
        print("✗ échec de l'envoi du récap")


if __name__ == "__main__":
    main(dry_run="--dry-run" in sys.argv)
