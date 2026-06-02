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

from filters import passes_filters
from notifier import send_telegram
from scraper.deuxiememain import DeuxiememainScraper
from store import add_recent, load_seen_ids, save_seen_ids

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

    if dry_run:
        print("\n[DRY-RUN] Annonces qui seraient notifiées :")
        for l in new_listings:
            print(f"  • {l['title']} — {l['price_raw']} — {l.get('location')}")
            print(f"    {l['url']}")
        return

    # 5. Notifications Telegram
    for l in new_listings:
        if send_telegram(l):
            print(f"  ✓ notifié : {l['title']}")
        # On ajoute l'ID aux "vus" même si la notif échoue, pour éviter de
        # spammer la même annonce en boucle au run suivant. (Compromis simple.)
        seen_ids.add(l["id"])

    # 6. Persistance
    if new_listings:
        add_recent(new_listings)
    save_seen_ids(seen_ids)
    print("\nTerminé.")


if __name__ == "__main__":
    main(dry_run="--dry-run" in sys.argv)
