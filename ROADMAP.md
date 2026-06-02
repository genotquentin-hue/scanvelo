# Roadmap / état du projet

Suivi des étapes pour reprendre le projet dans une autre session.
Le code et l'architecture sont décrits dans `CLAUDE.md` et `README.md`.

## ✅ Fait

- [x] Code complet : scraper 2ememain (parsing `__NEXT_DATA__`), filtres
      (distance GPS 20km Bruxelles + prix €500–1200), notifications Telegram +
      email, persistance JSON (`data/seen_ids.json`, `data/recent.json`)
- [x] 16 modèles de vélos configurés dans `config.py` (`SEARCH_KEYWORDS`)
- [x] Testé en réel : `python3 main.py --dry-run` fonctionne (187 annonces
      récupérées → 3 pertinentes lors du test)
- [x] Workflow GitHub Actions (`.github/workflows/scraper.yml`)
- [x] Dépôt git initialisé et poussé sur https://github.com/genotquentin-hue/scanvelo (privé)

## ✅ Configuration des accès (fait)

### 1. Bot Telegram (pour les alertes instantanées)
- [x] Créer le bot via `@BotFather` sur Telegram → `/newbot` → token récupéré
- [x] Envoyer un message au bot depuis Telegram
- [x] Récupérer le **chat_id** via l'API Telegram

### 2. Email Gmail (pour le récap quotidien)
- [x] Activer la validation en 2 étapes sur Google
- [x] Générer un **App Password** : https://myaccount.google.com/apppasswords

### 3. Configuration locale
- [x] Remplir le `.env` local avec token, chat_id, app password
- [x] `python3 main.py --dry-run` ✓ (245 annonces → 3 pertinentes)
- [x] `python3 main.py` ✓ (scrape + persiste, 0 nouvelle annonce car déjà vues)
- [x] Modifier `config.py` pour charger le `.env` sans dépendre de `python-dotenv`

## ✅ GitHub Actions (fait)

### 4. Secrets GitHub Actions
- [x] `TELEGRAM_TOKEN`
- [x] `TELEGRAM_CHAT_ID`
- [x] `GMAIL_USER` = `genot.quentin@gmail.com`
- [x] `GMAIL_APP_PASSWORD`
- [x] `GMAIL_TO` = `genot.quentin@gmail.com`

### 5. Test du workflow
- [x] Workflow testé manuellement (**Actions → Run workflow**)
- [x] Exécution réussie sur GitHub Actions
- [x] Fichiers `seen_ids.json` et `recent.json` mis à jour et poussés automatiquement

**🚀 Bot opérationnel !**
- Scraping : **toutes les 30 min** (6h–21h UTC) → alertes Telegram si nouvelles annonces
- Récap email : **chaque jour à 6h UTC** (8h Bruxelles)

## 🛠 Confort (optionnel)
- [ ] Éviter de retaper le token à chaque `git push` : configurer SSH **ou** un credential helper git
- [ ] Installer `python-dotenv` en local (actuellement absent ; import rendu optionnel dans `config.py`)

## 💡 Évolutions possibles (plus tard)
- [ ] Ajouter marktplaats.nl (même plateforme Adevinta → cloner `scraper/deuxiememain.py`)
- [ ] Affiner la fourchette de prix dans `config.py` une fois le marché mieux connu
- [ ] Ajuster les heures du cron dans le workflow (actuellement en UTC)

## ⚠️ Notes
- Le token GitHub utilisé pour le 1er push doit avoir les scopes **`repo` + `workflow`**.
- Un token a été collé en clair dans un chat puis régénéré → l'ancien est invalide. Token régénéré via @BotFather et mis à jour dans `.env` + secret GitHub Actions (2026-06-02).
