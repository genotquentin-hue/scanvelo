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
from store import load_recent, load_top5


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
    top5 = load_top5()
    today = datetime.now(timezone.utc).strftime("%d/%m/%Y")
    subject = f"🚲 Récap vélos {today} — {len(listings)} annonce(s)"

    print(f"{len(listings)} annonce(s) dans les dernières 24h")

    if dry_run:
        print(f"\n=== Top 5 meilleures annonces en ligne ({len(top5)}) ===")
        for i, l in enumerate(top5, 1):
            print(f"  {i}. [{l.get('score', '?')}/100] {l['title']} — {l.get('price_raw', '?')}")
            print(f"     💡 {l.get('conseil', '(pas de conseil)')}")
            print(f"     {l.get('url', '')}")
        print(f"\n=== Nouvelles annonces 24h ({len(listings)}) ===")
        for l in listings:
            print(f"  • {l['title']} — {l['price_raw']} — {l.get('location')}")
        return

    if send_email_recap(listings, top5=top5, subject=subject):
        print("✓ récap envoyé par email")
    else:
        print("✗ échec de l'envoi du récap")
        sys.exit(1)


if __name__ == "__main__":
    main(dry_run="--dry-run" in sys.argv)
