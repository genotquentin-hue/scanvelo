# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Projet

Moniteur d'annonces de vélos gravel/commute d'occasion près de Bruxelles (rayon 20km). Scrape 2ememain.be, envoie une alerte Telegram par nouvelle annonce et un récap email quotidien. Tourne sur GitHub Actions.

## Commandes

```bash
python3 main.py --dry-run    # scrape + affiche ce qui serait notifié, sans rien envoyer ni écrire
python3 main.py              # exécution réelle : notifie + met à jour seen_ids.json / recent.json
python3 recap.py --dry-run   # affiche le récap 24h sans l'envoyer
python3 recap.py             # envoie le récap email
python3 -m py_compile *.py scraper/*.py   # vérif syntaxe (pas de suite de tests formelle)
```

`--dry-run` est le moyen sûr de tester une modif du scraper/filtres sans solliciter Telegram ni polluer les fichiers d'état.

Pas de framework de test : valider avec `--dry-run` et des assertions inline ponctuelles (`python3 -c "..."`).

**Environnement local (Manjaro)** : `pip` n'est pas installé au niveau système et `python-dotenv` peut manquer — c'est pour ça que son import est rendu optionnel dans `config.py`. `requests` est dispo. Sur GitHub Actions, `pip install -r requirements.txt` fonctionne normalement.

## Architecture

**Flux principal** (`main.py`) : charge les IDs vus → `BaseScraper.run()` par site → filtre (lieu + prix) → ne garde que les IDs nouveaux → `send_telegram()` par annonce → persiste. Ajouter un site = ajouter une classe à la liste `SCRAPERS`.

**Le scraper parse du JSON, pas du HTML.** 2ememain est en Next.js : `scraper/deuxiememain.py` extrait le bloc `<script id="__NEXT_DATA__">` et lit `props.pageProps.searchRequestAndResponse.listings`. Ne pas réintroduire BeautifulSoup/sélecteurs CSS — c'est volontairement absent car le JSON est stable, le HTML non. Chaque annonce brute passe par `_normalize()` qui produit le dict standard (id, title, price_cents, price_type, latitude/longitude, url, etc.). Les sous-catégories `velos-pieces`/`velos-accessoires` sont exclues (ce sont des pièces, pas des vélos).

**`scraper/base.py`** porte l'anti-bot, partagé par tous les scrapers : headers de vrai navigateur, `warm_up()` (visite la home pour les cookies avant de chercher), `_polite_sleep()` (délais **aléatoires** 4–12s), et `run()` qui mélange l'ordre des recherches. Toute évolution anti-bot va ici, pas dans les scrapers concrets.

**Filtrage** (`filters.py`) : la localisation utilise la distance GPS réelle (haversine vers le centre de Bruxelles) quand lat/long sont présents, avec repli sur la liste blanche `BRUSSELS_CITIES` sinon. Le prix garde les annonces sans prix (« faire une offre »). **La taille M est indicative, pas bloquante** (`has_size_m` sert à afficher un badge dans la notif, pas à filtrer) — beaucoup d'annonces ne précisent pas la taille.

**Persistance** (`store.py`) — deux fichiers JSON **commités** dans le dépôt (pas une base de données), car GitHub Actions repart d'un checkout vierge à chaque run :
- `data/seen_ids.json` : ensemble des IDs déjà vus → déduplication.
- `data/recent.json` : annonces des dernières 48h avec horodatage `seen_at` → source du récap quotidien. Auto-purgé au-delà de `RECENT_RETENTION_HOURS`.

Le workflow committe ces deux fichiers après chaque run ; c'est ce qui fait persister l'état entre exécutions.

**Notifications** (`notifier.py`) : Telegram via l'API HTTP brute (`requests`, pas de lib dédiée) ; email via `smtplib` SSL + App Password Gmail.

**Automatisation** (`.github/workflows/scraper.yml`) : un seul workflow, deux comportements selon le cron qui déclenche. `github.event.schedule == '0 6 * * *'` → récap email ; tout le reste (y compris `workflow_dispatch` manuel) → scraping. Heures cron en **UTC**.

## Configuration

Tout ce qui se règle est dans `config.py` : `SEARCH_KEYWORDS` (un mot-clé = une recherche), `BRUSSELS_CITIES`, `MIN/MAX_PRICE_CENTS` (prix stockés en **centimes** partout pour éviter les floats), secrets via variables d'environnement. Les secrets se mettent dans `.env` en local (voir `.env.example`) et dans les *GitHub Actions secrets* en prod : `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`, `GMAIL_USER`, `GMAIL_APP_PASSWORD`, `GMAIL_TO`, `DEEPSEEK_API_KEY`.

**Analyse IA** (`analyzer.py`) : score chaque annonce via l'API DeepSeek (`requests` brut, pas de SDK — même philosophie que `notifier.py` pour Telegram). Sans `DEEPSEEK_API_KEY`, l'analyse est désactivée en fail-safe : les annonces sont notifiées sans score plutôt que bloquées.

**Déclenchement du scraping** : cron-job.org (externe, appelle `workflow_dispatch` toutes les heures) est le déclencheur principal ; le cron natif GitHub Actions n'est qu'un filet de sécurité peu fréquent et décalé de la minute `:00` — un vrai backup horaire ferait tourner deux runs quasi simultanés et provoquerait des conflits de push sur `data/*.json` (donc des doublons de notif Telegram, cf. `.github/workflows/scraper.yml`). Ne pas repasser ce cron à une cadence horaire sans repenser la dédup.
