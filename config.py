"""Configuration centrale : tout ce qui se règle est ici.

On centralise les constantes dans un seul fichier pour ne pas avoir à
fouiller le code quand on veut ajuster un mot-clé ou une fourchette de prix.
"""
import os
from pathlib import Path

# Charge les variables du fichier .env dans os.environ.
# En local : lit le fichier .env. Sur GitHub Actions : le .env n'existe pas,
# mais les secrets sont déjà dans os.environ → load_dotenv ne casse rien.
# L'import est optionnel : si python-dotenv n'est pas installé, on continue
# avec les variables d'environnement déjà présentes.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# --- Chemins ---
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
SEEN_IDS_PATH = DATA_DIR / "seen_ids.json"
# Annonces récentes (avec toutes leurs données), pour le récap quotidien.
# Commité dans le dépôt pour survivre entre les runs GitHub Actions.
RECENT_PATH = DATA_DIR / "recent.json"
# Combien de temps on garde une annonce dans recent.json (en heures).
RECENT_RETENTION_HOURS = 48

# --- Mots-clés de recherche ---
# Chaque entrée devient une recherche distincte sur le site.
SEARCH_KEYWORDS = [
    "van rysel grvl",
    "kona rove",
    "trek checkpoint",
    "specialized diverge",
    "canyon grail",
    "canyon grizl",
    "giant revolt",
    "cannondale topstone",
    "scott speedster gravel",
    "cube nuroad",
    "fuji jari",
    "focus atlas",
    "bergamont grandurance",
    "orbea terra",
    "ridley kanzo",
    "breezer doppler",
]

# --- Fourchette de prix (en centimes d'euro) ---
# On stocke en centimes pour éviter les erreurs d'arrondi des floats.
MIN_PRICE_CENTS = 50_000   # 500 €
MAX_PRICE_CENTS = 120_000  # 1200 €

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
