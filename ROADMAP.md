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

## 🔲 À faire — configuration des accès

### 1. Bot Telegram (pour les alertes instantanées)
- [ ] Créer le bot via `@BotFather` sur Telegram → `/newbot` → récupérer le **token** (`TELEGRAM_TOKEN`)
- [ ] Envoyer un message au bot depuis ton compte Telegram (obligatoire)
- [ ] Récupérer le **chat_id** (`TELEGRAM_CHAT_ID`) avec cette commande (remplacer le token) :
      ```
      curl -s "https://api.telegram.org/bot<TON_TOKEN>/getUpdates" | python3 -c "import sys,json; print(json.load(sys.stdin)['result'][-1]['message']['chat']['id'])"
      ```

### 2. Email Gmail (pour le récap quotidien)
- [ ] Activer la validation en 2 étapes sur le compte Google
- [ ] Générer un **App Password** : https://myaccount.google.com/apppasswords → valeur `GMAIL_APP_PASSWORD`

### 3. Secrets GitHub Actions
Dans le dépôt : **Settings → Secrets and variables → Actions → New repository secret**
- [ ] `TELEGRAM_TOKEN`
- [ ] `TELEGRAM_CHAT_ID`
- [ ] `GMAIL_USER` = `genot.quentin@gmail.com`
- [ ] `GMAIL_APP_PASSWORD`
- [ ] `GMAIL_TO` = `genot.quentin@gmail.com`

### 4. Test de bout en bout
- [ ] Remplir un fichier `.env` local (copier `.env.example`) avec les mêmes valeurs
- [ ] `python3 main.py --dry-run` puis `python3 main.py` → vérifier une alerte Telegram reçue
- [ ] `python3 recap.py` → vérifier l'email reçu
- [ ] Sur GitHub : onglet **Actions** → lancer le workflow manuellement (**Run workflow**) pour valider en conditions réelles

## 🛠 Confort (optionnel)
- [ ] Éviter de retaper le token à chaque `git push` : configurer SSH **ou** un credential helper git
- [ ] Installer `python-dotenv` en local (actuellement absent ; import rendu optionnel dans `config.py`)

## 💡 Évolutions possibles (plus tard)
- [ ] Ajouter marktplaats.nl (même plateforme Adevinta → cloner `scraper/deuxiememain.py`)
- [ ] Affiner la fourchette de prix dans `config.py` une fois le marché mieux connu
- [ ] Ajuster les heures du cron dans le workflow (actuellement en UTC)

## ⚠️ Notes
- Le token GitHub utilisé pour le 1er push doit avoir les scopes **`repo` + `workflow`**.
- Un token a été collé en clair dans un chat puis régénéré → l'ancien est invalide.
