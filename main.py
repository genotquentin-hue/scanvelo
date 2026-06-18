"""Point d'entrée du scraping. Lancé toutes les 30 min par GitHub Actions.

Déroulé :
  1. charge les IDs déjà vus
  2. scrape chaque site
  3. garde les annonces qui passent les filtres (lieu + prix)
  4. ne garde que les NOUVELLES (pas déjà vues)
  5. envoie une alerte Telegram par nouvelle annonce
  6. met à jour seen_ids.json et recent.json

Usage :
  python main.py            # exécution normale
  python main.py --dry-run  # affiche tout, sans notifier ni rien écrire
"""
import sys

from analyzer import analyze_listing
from filters import passes_filters
from notifier import send_telegram
from scraper.deuxiememain import DeuxiememainScraper
from store import add_recent, load_seen_ids, load_top5, save_seen_ids, update_top5

# Liste des scrapers actifs. Pour ajouter marktplaats plus tard : une ligne ici.
SCRAPERS = [DeuxiememainScraper]


def main(dry_run: bool = False) -> None:
    seen_ids = load_seen_ids()
    print(f"IDs déjà connus : {len(seen_ids)}")

    # 1+2. Scrape tous les sites
    all_listings: list[dict] = []
    for scraper_cls in SCRAPERS:
        scraper = scraper_cls()
        print(f"\n=== {scraper.source} ===")
        all_listings.extend(scraper.run())

    # 3. Filtres (lieu + prix)
    relevant = [l for l in all_listings if passes_filters(l)]
    print(f"\n{len(all_listings)} annonces récupérées, {len(relevant)} pertinentes")

    # 4. Nouveautés uniquement
    new_listings = [l for l in relevant if l["id"] not in seen_ids]
    print(f"{len(new_listings)} nouvelle(s) annonce(s)")

    # 5. Analyse IA
    kept_listings: list[dict] = []

    for l in new_listings:
        verdict = analyze_listing(l)
        garder = True if verdict is None else verdict["garder"]
        l["_analyse"] = verdict
        # L'ID est marqué "vu" même si écarté : évite de re-payer l'analyse au run suivant.
        seen_ids.add(l["id"])

        if garder:
            kept_listings.append(l)

        if dry_run:
            tag = "✓ GARDER" if garder else "✗ écarté"
            score = f" {verdict['score']}/100" if verdict else " (pas d'analyse)"
            raison = f" — {verdict['raison']}" if verdict else ""
            conseil = f"\n    💡 {verdict['conseil']}" if verdict else ""
            print(f"  [{tag}{score}]{raison}")
            print(f"  • {l['title']} — {l.get('price_raw')} — {l.get('location')}")
            print(f"    {l['url']}{conseil}")

    # 6. Bootstrap top5 si nécessaire : analyse les annonces déjà vues mais absentes du top5
    # (sans les notifier sur Telegram — elles sont déjà connues)
    current_top5_ids = {l["id"] for l in load_top5()}
    kept_ids = {l["id"] for l in kept_listings}
    needed = 5 - len(current_top5_ids) - len(kept_ids)
    if needed > 0:
        already_seen = [l for l in relevant if l["id"] not in kept_ids and l["id"] not in current_top5_ids]
        if already_seen:
            print(f"\n[bootstrap top5] {len(already_seen)} annonce(s) à analyser pour remplir le top5…")
        for l in already_seen:
            verdict = analyze_listing(l)
            garder = True if verdict is None else verdict["garder"]
            l["_analyse"] = verdict
            if garder:
                kept_listings.append(l)
                kept_ids.add(l["id"])
                needed -= 1
            if dry_run:
                tag = "✓ top5" if garder else "✗ écarté"
                score = f" {verdict['score']}/100" if verdict else ""
                print(f"  [bootstrap {tag}{score}] {l['title']}")
            if needed <= 0:
                break

    # 7. Mise à jour du top5 (vérifie les URL encore en ligne + ajoute les nouvelles)
    update_top5(kept_listings, dry_run=dry_run)

    if dry_run:
        return

    # 7. Notifications Telegram
    for l in kept_listings:
        if send_telegram(l):
            print(f"  ✓ notifié : {l['title']}")

    # 8. Persistance
    if kept_listings:
        add_recent(kept_listings)
    save_seen_ids(seen_ids)
    print("\nTerminé.")


if __name__ == "__main__":
    main(dry_run="--dry-run" in sys.argv)
