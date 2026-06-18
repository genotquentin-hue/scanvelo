"""Envoi des notifications : Telegram (alertes instantanées) + email (récap).

On utilise l'API HTTP de Telegram directement via `requests` plutôt qu'une
librairie dédiée : un seul appel suffit, pas besoin d'une dépendance de plus.
"""
import smtplib
from email.message import EmailMessage
from html import escape

import requests

from config import (
    GMAIL_APP_PASSWORD,
    GMAIL_TO,
    GMAIL_USER,
    TELEGRAM_CHAT_ID,
    TELEGRAM_TOKEN,
)
from filters import distance_to_brussels, has_size_m

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


# --- Telegram : alertes instantanées ---

def send_telegram(listing: dict) -> bool:
    """Envoie une alerte Telegram pour une annonce. Retourne True si OK."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("  [warn] Telegram non configuré (token/chat_id manquants)")
        return False

    text = _format_telegram(listing)
    try:
        resp = requests.post(
            TELEGRAM_API.format(token=TELEGRAM_TOKEN),
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": False,
            },
            timeout=15,
        )
        resp.raise_for_status()
        return True
    except requests.RequestException as e:
        print(f"  [warn] échec envoi Telegram : {e}")
        return False


def _format_telegram(listing: dict) -> str:
    """Construit le message HTML d'une alerte. escape() neutralise les
    caractères spéciaux (<, >, &) pour ne pas casser le HTML Telegram."""
    title = escape(listing.get("title", "Sans titre"))
    price = escape(listing.get("price_raw", "?"))
    city = escape(listing.get("location") or "lieu inconnu")
    url = listing.get("url", "")

    dist = distance_to_brussels(listing)
    dist_str = f" (~{dist:.0f} km)" if dist is not None else ""
    size_str = "\n📏 Taille M mentionnée" if has_size_m(listing) else ""

    analyse = listing.get("_analyse")
    analyse_str = ""
    if analyse:
        analyse_str = (
            f"\n🤖 {analyse['score']}/100 — {escape(analyse['raison'])}"
            f"\n💡 {escape(analyse['conseil'])}"
        )

    return (
        f"🚲 <b>Nouveau vélo</b>\n\n"
        f"🏷 {title}\n"
        f"💰 {price}\n"
        f"📍 {city}{dist_str}"
        f"{size_str}"
        f"{analyse_str}\n\n"
        f'🔗 <a href="{escape(url)}">Voir l\'annonce</a>'
    )


# --- Email : récap quotidien ---

def send_email_recap(listings: list[dict], subject: str | None = None, top5: list[dict] | None = None) -> bool:
    """Envoie un récap par email via Gmail SMTP. Retourne True si OK."""
    if not GMAIL_USER or not GMAIL_APP_PASSWORD or not GMAIL_TO:
        print("  [warn] Gmail non configuré (user/app_password/to manquants)")
        return False

    if subject is None:
        subject = f"🚲 Récap vélos — {len(listings)} nouvelle(s) annonce(s)"

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = GMAIL_USER
    msg["To"] = GMAIL_TO
    msg.set_content(_format_email_text(listings, top5 or []))
    msg.add_alternative(_format_email_html(listings, top5 or []), subtype="html")

    try:
        # Port 465 = SMTP over SSL (connexion chiffrée d'emblée).
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        return True
    except (smtplib.SMTPException, OSError) as e:
        print(f"  [warn] échec envoi email : {e}")
        return False


def _format_email_text(listings: list[dict], top5: list[dict]) -> str:
    lines = []
    if top5:
        lines.append(f"=== TOP 5 MEILLEURES ANNONCES EN LIGNE ===\n")
        for i, l in enumerate(top5, 1):
            lines.append(f"{i}. [{l.get('score', '?')}/100] {l.get('title', '?')} — {l.get('price_raw', '?')}")
            if l.get("conseil"):
                lines.append(f"   💡 {l['conseil']}")
            lines.append(f"   {l.get('url', '')}\n")
    if not listings:
        lines.append("Aucune nouvelle annonce dans les dernières 24h.")
    else:
        lines.append(f"\n=== NOUVELLES ANNONCES 24H ({len(listings)}) ===\n")
        for i, l in enumerate(listings, 1):
            city = l.get("location") or "?"
            lines.append(f"{i}. {l.get('title', '?')} — {l.get('price_raw', '?')} — {city}")
            lines.append(f"   {l.get('url', '')}\n")
    return "\n".join(lines)


def _format_email_html(listings: list[dict], top5: list[dict]) -> str:
    parts = []

    if top5:
        top5_rows = []
        for i, l in enumerate(top5, 1):
            title = escape(l.get("title", "?"))
            price = escape(l.get("price_raw", "?"))
            url = escape(l.get("url", ""))
            score = l.get("score", "?")
            conseil = escape(l.get("conseil", ""))
            top5_rows.append(
                f'<li style="margin-bottom:16px">'
                f'<span style="font-size:1.1em"><b>{i}.</b> '
                f'<a href="{url}">{title}</a></span><br>'
                f'<span style="color:#555">💰 {price} · 🤖 {score}/100</span><br>'
                f'<span style="color:#333;font-style:italic">💡 {conseil}</span>'
                f"</li>"
            )
        parts.append(
            f'<h2 style="color:#1a6b2e">🏆 Top 5 meilleures annonces en ligne</h2>'
            f'<ul style="list-style:none;padding:0">{"".join(top5_rows)}</ul>'
            f'<hr style="margin:24px 0">'
        )

    if not listings:
        parts.append("<p>Aucune nouvelle annonce dans les dernières 24h. 🚲</p>")
    else:
        rows = []
        for l in listings:
            title = escape(l.get("title", "?"))
            price = escape(l.get("price_raw", "?"))
            city = escape(l.get("location") or "?")
            url = escape(l.get("url", ""))
            size = " · 📏 taille M" if has_size_m(l) else ""
            rows.append(
                f'<li style="margin-bottom:12px">'
                f'<a href="{url}"><b>{title}</b></a><br>'
                f"💰 {price} · 📍 {city}{size}"
                f"</li>"
            )
        parts.append(
            f"<h2>🚲 {len(listings)} nouvelle(s) annonce(s) (24h)</h2>"
            f'<ul style="list-style:none;padding:0">{"".join(rows)}</ul>'
        )

    return "".join(parts)
