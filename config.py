"""Configuration centrale : tout ce qui se règle est ici.

On centralise les constantes dans un seul fichier pour ne pas avoir à
fouiller le code quand on veut ajuster un mot-clé ou une fourchette de prix.
"""
import os
from pathlib import Path

# Charge les variables du fichier .env dans os.environ.
# Lecture manuelle du .env pour éviter la dépendance à python-dotenv.
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())

# --- Chemins ---
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
SEEN_IDS_PATH = DATA_DIR / "seen_ids.json"
# Annonces récentes (avec toutes leurs données), pour le récap quotidien.
# Commité dans le dépôt pour survivre entre les runs GitHub Actions.
RECENT_PATH = DATA_DIR / "recent.json"
# Top 5 meilleures annonces actuellement en ligne (score IA + vérif URL).
TOP5_PATH = DATA_DIR / "top5.json"
# Combien de temps on garde une annonce dans recent.json (en heures).
RECENT_RETENTION_HOURS = 48

# --- Mots-clés de recherche ---
# Chaque entrée devient une recherche distincte sur le site.
SEARCH_KEYWORDS = [
    # --- Gravel ---
    "van rysel grvl",
    "kona rove",
    "trek checkpoint",
    "specialized diverge",
    "canyon grail",
    "canyon grizl",
    "giant revolt",
    "cannondale topstone",
    "scott speedster gravel",
    "cube cross race",
    "fuji jari",
    "focus atlas",
    "bergamont grandurance",
    "orbea terra",
    "ridley kanzo",
    "merida silex",
    "gt grade",
    "genesis croix de fer",
    "vitus energie",
    "rose backroad",
    "felt vr",
    "ghost asket gravel",
    "principia gravel h10",
    # --- Commute / hybride ---
    "cube nuroad",
    "breezer doppler",
    "orbea vector",
    "bergamont sweep",
    "marin four corners",
    "trek fx",
    "giant toughroad",
    "giant escape",
    "specialized crosstrail",
    "decathlon triban",
    "koga roadster",
    "tout terrain silkroad",
]

# --- Fourchette de prix (en centimes d'euro) ---
# On stocke en centimes pour éviter les erreurs d'arrondi des floats.
MIN_PRICE_CENTS = 50_000   # 500 €
MAX_PRICE_CENTS = 100_000  # 1000 €

# --- Villes dans ~20km de Bruxelles ---
# Le filtre de distance du site est appliqué en JavaScript (invisible en HTTP),
# donc on compare le nom de ville de l'annonce à cette liste blanche.
# Tout en minuscules pour comparer sans se soucier de la casse.
BRUSSELS_CITIES = {
    "bruxelles", "brussel", "brussels", "1000",
    "etterbeek", "ixelles", "elsene", "schaerbeek", "schaarbeek",
    "molenbeek", "sint-jans-molenbeek", "forest", "vorst",
    "anderlecht", "uccle", "ukkel", "watermael", "watermael-boitsfort",
    "jette", "laeken", "laken", "evere", "ganshoren", "koekelberg",
    "berchem-sainte-agathe", "saint-gilles", "sint-gillis",
    "saint-josse", "auderghem", "oudergem",
    "woluwe-saint-pierre", "woluwe-saint-lambert", "sint-pieters-woluwe",
    "sint-lambrechts-woluwe",
    "kraainem", "wezembeek-oppem", "tervuren", "overijse", "hoeilaart",
    "waterloo", "braine-l'alleud", "eigenbrakel", "nivelles",
    "vilvoorde", "vilvorde", "machelen", "zaventem", "sterrebeek",
    "diegem", "nossegem", "kortenberg", "grimbergen", "wemmel",
    "dilbeek", "asse", "halle", "beersel", "rhode-saint-genese",
    "sint-genesius-rode", "drogenbos", "linkebeek", "la hulpe", "terhulpen",
}

# Distance max indicative (pour mémoire ; non utilisée par le filtre texte).
MAX_DISTANCE_KM = 20

# --- Secrets (chargés depuis .env ou les secrets GitHub Actions) ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

GMAIL_USER = os.environ.get("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
GMAIL_TO = os.environ.get("GMAIL_TO", "")

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# --- Analyse IA ---
ANALYSE_MODEL = "claude-haiku-4-5"

ANALYSE_CRITERES = """Tu analyses des annonces de vélos d'occasion pour un acheteur bruxellois.

Profil de l'acheteur :
- Homme, 173 cm → taille cadre M (54-56 cm selon le type de vélo)
- Usage principal : vélotaf ~11 km/jour sur pistes cyclables et pavés bruxellois
- Usage secondaire : balades gravel le week-end (chemins mixtes)
- Stockage : cave/garage sécurisé (pas de contrainte de poids)
- Style préféré : gravel avec guidon drop (polyvalent route + chemin)
  → hybride à guidon plat acceptable mais score réduit
- Budget max : 1000 €
- Ouvert à toutes les marques si la qualité est au rendez-vous

Critères pour ÉCARTER (garder=false) :
- Vélo électrique / VAE / e-bike (moteur, batterie mentionnés)
- Vélo explicitement pour femme (WSD, step-through, "dame", coloris féminins assumés, taille XS/S féminin)
- Pièces détachées ou cadre nu
- Signaux rédhibitoires : rouille importante, accident, fourche tordue, cadre fissuré, pièces manquantes essentielles
- Taille incompatible explicitement mentionnée (S, XS, L, XL, 58 cm+, 50 cm-)
- VTT descente, vélo de route de compétition pure, vélo enfant
- État mauvais ("à réparer", "pour pièces", "ne fonctionne pas")

Si la taille n'est pas mentionnée → ne pas pénaliser.
Si le genre est ambigu → garder (bénéfice du doute).

Score (0-100) — bonus appliquer dans l'ordre :
+10 : freins à disque hydraulique (essentiel sous la pluie bruxelloise)
+5  : pneus larges 35 mm+ (confort sur pavés)
+5  : porte-bagages ou compatibilité porte-bagages (bonus vélotaf)
+5  : modèle très revendable (Trek, Specialized, Canyon, Giant, Cannondale sur modèles courants)
-10 : freins à patins uniquement (rim brake) — pénalité pluie
-5  : hybride à guidon plat (fonctionnel mais moins polyvalent que souhaité)

raison : une phrase expliquant pourquoi tu gardes ou écartes.

conseil : 2-3 phrases de conseiller d'achat honnête :
- Prix neuf estimé du modèle et calcul explicite de la décote (prix demandé / prix neuf)
- Grille de jugement à appliquer strictement :
    < 40% du neuf  → excellente affaire
    40-60% du neuf → bonne affaire
    60-75% du neuf → prix correct, acceptable
    75-90% du neuf → trop cher pour de l'occasion, négocier fortement ou passer
    > 90% du neuf  → déconseillé, autant acheter neuf
- Point d'attention concret (composant à vérifier, négociation possible)
- Verdict final : "excellente affaire", "bonne affaire", "prix correct", "trop cher — négocier", "éviter — prix neuf"

Réponds uniquement avec le JSON demandé, en français."""
