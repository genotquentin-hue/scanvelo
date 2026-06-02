"""Persistance simple : la liste des annonces déjà vues, dans un fichier JSON.

Pourquoi un JSON et pas une base SQLite ? Parce que le scraper tourne sur
GitHub Actions, qui repart d'un environnement vierge à chaque exécution. Un
fichier JSON commité dans le dépôt persiste entre les runs et reste lisible.
"""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from config import RECENT_PATH, RECENT_RETENTION_HOURS, SEEN_IDS_PATH


def load_seen_ids(path: Path = SEEN_IDS_PATH) -> set[str]:
    """Retourne l'ensemble des IDs d'annonces déjà vues.

    On utilise un set (et pas une liste) car le test « est-ce déjà vu ? »
    est instantané sur un set, peu importe le nombre d'éléments.
    """
    if not path.exists():
        return set()
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return set(data.get("ids", []))


def save_seen_ids(ids: set[str], path: Path = SEEN_IDS_PATH) -> None:
    """Écrit l'ensemble des IDs vus, trié pour un diff git propre."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "ids": sorted(ids),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_recent(path: Path = RECENT_PATH) -> list[dict]:
    """Charge les annonces récentes (pour le récap quotidien)."""
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def add_recent(new_listings: list[dict], path: Path = RECENT_PATH) -> None:
    """Ajoute des annonces au fichier récent et purge celles de +48h.

    Chaque annonce reçoit un champ `seen_at` (horodatage UTC) au moment où on
    la voit pour la première fois. recap.py s'en sert pour ne garder que les
    dernières 24h.
    """
    now = datetime.now(timezone.utc)
    stamped = []
    for l in new_listings:
        entry = dict(l)
        entry["seen_at"] = now.isoformat()
        stamped.append(entry)

    existing = load_recent(path)
    combined = existing + stamped

    # Purge : on retire les annonces trop vieilles pour garder le fichier petit.
    cutoff = now - timedelta(hours=RECENT_RETENTION_HOURS)
    kept = []
    for l in combined:
        try:
            seen = datetime.fromisoformat(l["seen_at"])
        except (KeyError, ValueError):
            continue  # entrée malformée → on la jette
        if seen >= cutoff:
            kept.append(l)

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(kept, f, ensure_ascii=False, indent=2)
