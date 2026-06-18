"""Re-analyse les annonces de recent.json avec les critères actuels et reconstruit top5.

Usage : python3 bootstrap_top5.py [--dry-run]
"""
import sys

from analyzer import analyze_listing
from store import load_recent, load_top5, save_top5

dry_run = "--dry-run" in sys.argv

listings = load_recent()
print(f"{len(listings)} annonce(s) dans recent.json")

candidates = []
for l in listings:
    print(f"\n→ {l['title']} — {l.get('price_raw')}")
    verdict = analyze_listing(l)
    garder = True if verdict is None else verdict["garder"]
    l["_analyse"] = verdict

    if verdict:
        tag = "✓ GARDER" if garder else "✗ écarté"
        print(f"  [{tag} {verdict['score']}/100] {verdict['raison']}")
        print(f"  💡 {verdict['conseil']}")
    else:
        print("  [pas d'analyse — fail-safe, gardé]")

    if garder:
        candidates.append({
            "id": l["id"],
            "title": l.get("title", ""),
            "price_raw": l.get("price_raw", ""),
            "location": l.get("location", ""),
            "url": l.get("url", ""),
            "posted_at": l.get("posted_at", ""),
            "score": verdict["score"] if verdict else 0,
            "raison": verdict["raison"] if verdict else "",
            "conseil": verdict["conseil"] if verdict else "",
        })

candidates.sort(key=lambda x: x["score"], reverse=True)
top5 = candidates[:5]

print(f"\n{'[DRY-RUN] ' if dry_run else ''}Top 5 résultant : {len(top5)} entrée(s)")
for i, l in enumerate(top5, 1):
    print(f"  {i}. [{l['score']}/100] {l['title']}")

if not dry_run:
    save_top5(top5)
    print("top5.json mis à jour.")
