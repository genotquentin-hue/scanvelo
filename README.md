# 🚲 Bike Monitor — Annonces vélos gravel Bruxelles

Surveille les petites annonces de vélos gravel/commute d'occasion près de Bruxelles
(±20km) et envoie :
- une **alerte Telegram** dès qu'une nouvelle annonce correspond,
- un **récap par email** chaque matin.

## Sites surveillés
- [2ememain.be](https://www.2ememain.be) (catégorie vélos)

## Modèles recherchés
Van Rysel GRVL, Kona Rove, Trek Checkpoint, Specialized Diverge, Canyon Grail,
Canyon Grizl, Giant Revolt, Cannondale Topstone, Scott Speedster Gravel,
Cube Nuroad, Fuji Jari, Focus Atlas, Bergamont Grandurance, Orbea Terra,
Ridley Kanzo, Breezer Doppler. (modifiable dans `config.py`)

## Installation locale

```bash
python -m venv .venv
source .venv/bin/activate        # Windows : .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # puis remplis tes secrets
```

## Utilisation

```bash
python main.py --dry-run    # teste sans envoyer de notif ni écrire seen_ids.json
python main.py              # scrape + notifie + met à jour seen_ids.json
python recap.py             # envoie le récap email des dernières 24h
```

## Déploiement

Le scraper tourne automatiquement via **GitHub Actions** (voir
`.github/workflows/scraper.yml`). Les secrets Telegram/Gmail sont à configurer
dans *Settings → Secrets and variables → Actions* du dépôt GitHub.

La liste des annonces déjà vues est stockée dans `data/seen_ids.json`, commité
par le workflow pour persister entre les exécutions.

## Structure

```
config.py       # mots-clés, villes, fourchette de prix
store.py        # lecture/écriture de seen_ids.json
scraper/        # scrapers par site (base.py + deuxiememain.py)
filters.py      # filtres localisation / prix / taille
notifier.py     # envoi Telegram + email
main.py         # exécution du scraping + alertes
recap.py        # récap quotidien par email
```
# scanvelo
