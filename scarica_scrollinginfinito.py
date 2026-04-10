#!/usr/bin/env python3
"""
Scarica tutti i post pubblici di Scrolling Infinito (Substack) come PDF + Markdown.
Range: 4 ottobre 2021 → 7 aprile 2026

Prerequisiti (esegui una volta sola):
    pip3 install requests playwright beautifulsoup4 markdownify
    python3 -m playwright install chromium

Uso:
    python3 scarica_scrollinginfinito.py

Output:
    scrollinginfinito_pdf/   → un PDF per ogni post (testo + link + immagini)
    scrollinginfinito_md/    → un file .md per ogni post (base di conoscenza)
    scrollinginfinito_md/00_INDICE.md → indice completo di tutti i post
"""

import requests
import time
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List

# ── Configurazione ────────────────────────────────────────────────────────────
PUBLICATION_URL = "https://scrollinginfinito.substack.com"
DIR_PDF = Path("scrollinginfinito_pdf")
DIR_MD  = Path("scrollinginfinito_md")

DATA_INIZIO = datetime(2021, 10, 4, tzinfo=timezone.utc)
DATA_FINE   = datetime(2026, 4, 7, 23, 59, 59, tzinfo=timezone.utc)

DELAY_TRA_DOWNLOAD = 2   # secondi tra un post e l'altro
# ──────────────────────────────────────────────────────────────────────────────

# CSS iniettato nella pagina prima di stampare — nasconde TUTTO ciò che non è
# contenuto editoriale. Usa !important per sovrascrivere qualsiasi stile inline.
CSS_NASCONDI_BANNER = """
<style id="__clean_print__">
  /* ── Modale iscrizione (confermata dall'utente) ── */
  [aria-label="Finestra modale di iscrizione"],
  [aria-label="Subscribe"],
  [role="dialog"],

  /* ── Backdrop / overlay ── */
  [class*="modal-backdrop"],
  [class*="ModalBackdrop"],
  [class*="backdrop"],
  [class*="Backdrop"],
  [class*="overlay"]:not(article):not(section),

  /* ── Cookie / GDPR ── */
  [class*="cookie"], [id*="cookie"],
  [class*="gdpr"],   [id*="gdpr"],
  [class*="consent"],

  /* ── Widget iscrizione Substack ── */
  .subscription-widget-wrap,
  .subscribe-widget,
  [data-component="SubscribeWidget"],
  [class*="subscribe-prompt"],
  [class*="SubscribePrompt"],
  [class*="SubscribeTo"],
  [class*="subscribe-cta"],

  /* ── Paywall ── */
  .paywall, [class*="paywall"], .paywall-fade,

  /* ── "Scopri di più" / upsell ── */
  [class*="post-upsell"], [class*="upsell"],
  [class*="reader2-clamp"], [class*="clamp-padding"],
  .post-footer-cta,

  /* ── Footer iscrizione ── */
  [class*="footer-subscribe"], .subscribe-footer,
  [class*="SubscribeFooter"],

  /* ── Header / nav sticky ── */
  header[class*="sticky"], nav[class*="sticky"],
  [class*="sticky-header"], [class*="StickyHeader"],

  /* ── Toast / notifiche ── */
  [class*="toast"], [class*="notification-bar"]

  { display: none !important; visibility: hidden !important; }

  /* Sblocca scroll del body bloccato dalla modale */
  body, html {
    overflow: auto !important;
    position: static !important;
  }
</style>
"""


def get_all_posts() -> List[dict]:
    """Recupera tutti i post dalla pubblicazione tramite l'API Substack."""
    posts  = []
    offset = 0
    limit  = 50
    print("📡  Recupero elenco post dall'API Substack...")
    while True:
        url = f"{PUBLICATION_URL}/api/v1/posts?limit={limit}&offset={offset}"
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            batch = resp.json()
        except requests.RequestException as e:
            print(f"  ⚠️  Errore di rete: {e}")
            break
        if not batch:
            break
        posts.extend(batch)
        print(f"  Recuperati {len(posts)} post finora…")
        if len(batch) < limit:
            break
        offset += limit
        time.sleep(0.5)
    return posts


def filtra_per_data(posts: List[dict]) -> List[dict]:
    filtrati = []
    for p in posts:
        raw = p.get("post_date") or p.get("published_at") or ""
        if not raw:
            continue
        try:
            pub = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            continue
        if DATA_INIZIO <= pub <= DATA_FINE:
            filtrati.append(p)
    filtrati.sort(key=lambda p: p.get("post_date") or p.get("published_at") or "")
    return filtrati


def sanitize(name: str) -> str:
    for c in r'\/:*?"<>|':
        name = name.replace(c, "_")
    return name[:120].strip()


def prefisso_data(post: dict) -> str:
    raw = post.get("post_date") or post.get("published_at") or ""
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).strftime("%Y-%m-%d")
    except ValueError:
        return "0000-00-00"


# ── Rimozione banner ──────────────────────────────────────────────────────────

def inietta_css_pulizia(page) -> None:
    """Inietta un <style> con display:none !important su tutti i banner."""
    page.evaluate(f"""
        () => {{
            // Rimuovi eventuale iniezione precedente
            const old = document.getElementById('__clean_print__');
            if (old) old.remove();

            // Inietta il nuovo foglio di stile
            document.head.insertAdjacentHTML('beforeend', `{CSS_NASCONDI_BANNER}`);
        }}
    """)


def rimuovi_banner_dom(page) -> None:
    """Secondo passaggio: rimozione diretta dal DOM + tasto Escape."""
    # Tasto Escape — chiude molte modali native
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)

    page.evaluate("""
        () => {
            const sels = [
                '[aria-label="Finestra modale di iscrizione"]',
                '[aria-label="Subscribe"]',
                '[role="dialog"]',
                '[class*="modal-backdrop"]', '[class*="backdrop"]',
                '[class*="overlay"]',
                '[class*="cookie"]', '[id*="cookie"]',
                '[class*="gdpr"]',   '[id*="gdpr"]',
                '[class*="consent"]',
                '.subscription-widget-wrap', '.subscribe-widget',
                '[data-component="SubscribeWidget"]',
                '[class*="subscribe-prompt"]', '[class*="SubscribePrompt"]',
                '[class*="SubscribeTo"]', '[class*="subscribe-cta"]',
                '.paywall', '[class*="paywall"]', '.paywall-fade',
                '[class*="post-upsell"]', '[class*="upsell"]',
                '[class*="reader2-clamp"]', '.post-footer-cta',
                '[class*="footer-subscribe"]', '.subscribe-footer',
                '[class*="toast"]', '[class*="notification-bar"]',
            ];
            sels.forEach(s => {
                document.querySelectorAll(s).forEach(el => el.remove());
            });

            // Rimuovi tutti gli elementi fixed/sticky non editoriali
            document.querySelectorAll('*').forEach(el => {
                const cs = window.getComputedStyle(el);
                if (cs.position === 'fixed' || cs.position === 'sticky') {
                    const tag = el.tagName.toLowerCase();
                    if (!['article','main','section','p','h1','h2',
                          'h3','h4','figure','img','a','div'].includes(tag) ||
                        el.getAttribute('aria-label') === 'Finestra modale di iscrizione') {
                        el.remove();
                    }
                }
            });

            document.body.style.overflow   = 'auto';
            document.body.style.position   = 'static';
            document.documentElement.style.overflow = 'auto';
        }
    """)


# ── Export PDF ────────────────────────────────────────────────────────────────

def salva_pdf(page, post: dict) -> bool:
    url    = post.get("canonical_url") or post.get("url", "")
    titolo = post.get("title", "senza_titolo")
    nome   = f"{prefisso_data(post)}_{sanitize(titolo)}.pdf"
    path   = DIR_PDF / nome

    if path.exists():
        print(f"  ⏭️  PDF già presente, salto")
        return True
    if not url:
        print(f"  ⚠️  URL mancante")
        return False

    try:
        page.goto(url, wait_until="networkidle", timeout=60_000)
        page.wait_for_timeout(3000)          # attendi JS post-caricamento

        inietta_css_pulizia(page)            # 1° passaggio: CSS !important
        page.wait_for_timeout(600)
        rimuovi_banner_dom(page)             # 2° passaggio: rimozione DOM
        page.wait_for_timeout(400)

        page.pdf(
            path=str(path),
            format="A4",
            print_background=True,
            margin={"top": "15mm", "bottom": "15mm",
                    "left": "15mm", "right": "15mm"},
        )
        print(f"  ✅  PDF: {nome}")
        return True
    except Exception as e:
        print(f"  ❌  PDF fallito: {e}")
        return False


# ── Export Markdown ───────────────────────────────────────────────────────────

def salva_markdown(page, post: dict) -> bool:
    """
    Estrae il contenuto editoriale del post e lo salva come file .md.
    Preserva: titolo, data, testo completo, link, intestazioni, liste.
    Utile come base di conoscenza per studiare i contenuti.
    """
    try:
        from markdownify import markdownify as md
        from bs4 import BeautifulSoup
    except ImportError:
        return False   # dipendenze opzionali

    url    = post.get("canonical_url") or post.get("url", "")
    titolo = post.get("title", "senza_titolo")
    nome   = f"{prefisso_data(post)}_{sanitize(titolo)}.md"
    path   = DIR_MD / nome

    if path.exists():
        print(f"  ⏭️  MD già presente, salto")
        return True

    try:
        # Estrai HTML del contenuto principale (già sulla pagina caricata)
        html_content = page.evaluate("""
            () => {
                // Substack usa .available-content o article come contenitore
                const selettori = [
                    '.available-content',
                    'article .body',
                    'article',
                    'main',
                ];
                for (const s of selettori) {
                    const el = document.querySelector(s);
                    if (el) return el.innerHTML;
                }
                return document.body.innerHTML;
            }
        """)

        soup = BeautifulSoup(html_content, "html.parser")

        # Rimuovi elementi non editoriali anche dal markdown
        for tag in soup.select(
            "[class*='subscribe'], [class*='paywall'], "
            "[class*='upsell'], [class*='cookie'], [role='dialog']"
        ):
            tag.decompose()

        testo_md = md(str(soup), heading_style="ATX", bullets="-")

        # Intestazione YAML-like con metadati
        raw_date = post.get("post_date") or post.get("published_at") or ""
        try:
            data_it = datetime.fromisoformat(
                raw_date.replace("Z", "+00:00")
            ).strftime("%-d %B %Y")
        except Exception:
            data_it = raw_date[:10]

        intestazione = (
            f"# {titolo}\n\n"
            f"**Data:** {data_it}  \n"
            f"**Fonte:** {url}  \n\n"
            f"---\n\n"
        )

        path.write_text(intestazione + testo_md, encoding="utf-8")
        print(f"  ✅  MD:  {nome}")
        return True

    except Exception as e:
        print(f"  ❌  MD fallito: {e}")
        return False


def crea_indice(posts: List[dict]) -> None:
    """Genera un file indice Markdown con tutti i post linkati."""
    path = DIR_MD / "00_INDICE.md"
    righe = [
        "# Scrolling Infinito — Indice completo\n",
        f"*Post dal {DATA_INIZIO.date()} al {DATA_FINE.date()}*\n\n",
        "| Data | Titolo | Link originale |\n",
        "|------|--------|----------------|\n",
    ]
    for p in posts:
        titolo = p.get("title", "—")
        url    = p.get("canonical_url") or p.get("url", "")
        data   = prefisso_data(p)
        nome_md = f"{data}_{sanitize(titolo)}.md"
        righe.append(f"| {data} | [{titolo}]({nome_md}) | [apri]({url}) |\n")

    path.write_text("".join(righe), encoding="utf-8")
    print(f"\n📋  Indice salvato: {path.name}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("❌  Playwright non trovato.")
        print("   Esegui: pip3 install playwright && python3 -m playwright install chromium")
        sys.exit(1)

    # Verifica dipendenze opzionali per il markdown
    markdown_ok = True
    try:
        import markdownify  # noqa
        import bs4           # noqa
    except ImportError:
        markdown_ok = False
        print("⚠️  markdownify / beautifulsoup4 non trovati — solo PDF, niente .md")
        print("   Per abilitare: pip3 install beautifulsoup4 markdownify\n")

    DIR_PDF.mkdir(exist_ok=True)
    if markdown_ok:
        DIR_MD.mkdir(exist_ok=True)

    print(f"📁  PDF  → {DIR_PDF.resolve()}")
    if markdown_ok:
        print(f"📁  MD   → {DIR_MD.resolve()}")
    print()

    # 1. Recupera post
    tutti = get_all_posts()
    if not tutti:
        print("❌  Nessun post trovato.")
        sys.exit(1)
    print(f"\n📋  Post totali: {len(tutti)}")

    # 2. Filtra
    da_scaricare = filtra_per_data(tutti)
    print(f"📅  Nel range {DATA_INIZIO.date()} → {DATA_FINE.date()}: "
          f"{len(da_scaricare)} post\n")
    if not da_scaricare:
        sys.exit(0)

    # 3. Crea indice
    if markdown_ok:
        crea_indice(da_scaricare)

    # 4. Download
    print("🖨️  Avvio download...\n")
    ok_pdf = ok_md = errori = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()

        for i, post in enumerate(da_scaricare, 1):
            titolo = post.get("title", "—")
            print(f"[{i}/{len(da_scaricare)}] {titolo}")

            # PDF
            if salva_pdf(page, post):
                ok_pdf += 1
            else:
                errori += 1

            # Markdown (la pagina è già caricata e pulita)
            if markdown_ok:
                if salva_markdown(page, post):
                    ok_md += 1

            if i < len(da_scaricare):
                time.sleep(DELAY_TRA_DOWNLOAD)

        context.close()
        browser.close()

    print(f"\n{'─'*52}")
    print(f"✅  PDF salvati      : {ok_pdf}")
    if markdown_ok:
        print(f"✅  Markdown salvati : {ok_md}")
    print(f"❌  Errori           : {errori}")
    print(f"📁  PDF  → {DIR_PDF.resolve()}")
    if markdown_ok:
        print(f"📁  MD   → {DIR_MD.resolve()}")
    print(f"{'─'*52}")


if __name__ == "__main__":
    main()
