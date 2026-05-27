#!/usr/bin/env python3
"""
Site Analiz Aracı
-----------------
Verilen URL'leri şu kriterler açısından analiz eder:
  1. Türkçe dil desteği
  2. Türkiye telefon hattı kullanımı (+90 veya 0850 vb.)
  3. Online üyelik / kayıt formu varlığı
Sonuçları güzel bir HTML raporu olarak kaydeder.
"""

import sys
import re
import time
import datetime
import urllib.request
import urllib.error
from html.parser import HTMLParser

# ─── Yardımcı: Ham HTML'i indir ──────────────────────────────────────────────

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
}


def fetch(url: str, timeout: int = 15):
    """URL'yi indirir. Döndürür: (html_metin, hata_mesajı)"""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            encoding = resp.headers.get_content_charset() or "utf-8"
            try:
                return raw.decode(encoding, errors="replace"), None
            except Exception:
                return raw.decode("utf-8", errors="replace"), None
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}: {e.reason}"
    except urllib.error.URLError as e:
        return None, f"Bağlantı hatası: {e.reason}"
    except Exception as e:
        return None, str(e)


# ─── Basit HTML metin çıkarıcı ───────────────────────────────────────────────

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self._skip = False
        self._skip_tags = {"script", "style", "noscript", "svg", "head"}

    def handle_starttag(self, tag, attrs):
        if tag in self._skip_tags:
            self._skip = True

    def handle_endtag(self, tag):
        if tag in self._skip_tags:
            self._skip = False

    def handle_data(self, data):
        if not self._skip:
            self.parts.append(data)

    def get_text(self):
        return " ".join(self.parts)


def html_to_text(html: str) -> str:
    p = TextExtractor()
    try:
        p.feed(html)
    except Exception:
        pass
    return p.get_text()


# ─── 1. Türkçe Dil Desteği ───────────────────────────────────────────────────

TR_WORDS = [
    "anasayfa", "hakkımızda", "iletişim", "ürünler", "hizmetler",
    "giriş", "kayıt", "üye ol", "sepet", "ara", "arama", "devam",
    "tıklayın", "indirim", "kampanya", "bize ulaşın", "müşteri",
    "sipariş", "teslimat", "kargo", "iade", "şifre", "kullanıcı",
    "tamam", "iptal", "güncelle", "kaydet", "daha fazla", "göster",
]

TR_LANG_PATTERNS = [
    re.compile(r'lang=["\']tr', re.I),
    re.compile(r'locale=["\']tr', re.I),
    re.compile(r'hreflang=["\']tr', re.I),
    re.compile(r'"language"\s*:\s*"tr"', re.I),
    re.compile(r"content-language[\"']?\s*[=:]\s*[\"']?tr", re.I),
]


def check_turkish(html: str, text: str) -> dict:
    lang_tag = any(p.search(html) for p in TR_LANG_PATTERNS)
    html_lower = html.lower()
    matched_words = [w for w in TR_WORDS if w in html_lower]
    word_count = len(matched_words)

    if lang_tag and word_count >= 2:
        result = "Evet"
        detail = f"lang/locale etiketi tespit edildi; {word_count} Türkçe ifade bulundu."
    elif lang_tag:
        result = "Muhtemelen Evet"
        detail = "lang/locale etiketi mevcut ancak Türkçe içerik sınırlı."
    elif word_count >= 5:
        result = "Evet"
        detail = f"Dil etiketi yok ama {word_count} Türkçe ifade tespit edildi."
    elif word_count >= 2:
        result = "Kısmi"
        detail = f"{word_count} Türkçe ifade bulundu; tam destek belirsiz."
    else:
        result = "Hayır"
        detail = "Türkçe dil göstergesi bulunamadı."

    return {"sonuc": result, "detay": detail, "eslesen": matched_words[:8]}


# ─── 2. Türkiye Telefon Hattı ────────────────────────────────────────────────

TR_PHONE_PATTERNS = [
    re.compile(r'\+90[\s\-\.]?\(?\d{3}\)?[\s\-\.]?\d{3}[\s\-\.]?\d{2}[\s\-\.]?\d{2}'),
    re.compile(r'\b0(8[015]\d|[2-9]\d\d)[\s\-\.]?\d{3}[\s\-\.]?\d{2}[\s\-\.]?\d{2}\b'),
    re.compile(r'\b444[\s\-\.]?\d{4}\b'),
]


def check_tr_phone(html: str, text: str) -> dict:
    found = []
    for pat in TR_PHONE_PATTERNS:
        matches = pat.findall(html)
        found.extend(matches)

    found = list(dict.fromkeys(m.strip() for m in found))[:6]

    if found:
        return {
            "sonuc": "Evet",
            "detay": f"{len(found)} adet Türkiye telefon numarası tespit edildi.",
            "numaralar": found,
        }
    return {
        "sonuc": "Hayır",
        "detay": "Türkiye telefon numarası bulunamadı.",
        "numaralar": [],
    }


# ─── 3. Online Üyelik / Kayıt ────────────────────────────────────────────────

MEMBERSHIP_PATTERNS = [
    re.compile(r'\b(sign[\s\-]?up|register|create[\s\-]?account|join[\s\-]?now|membership)\b', re.I),
    re.compile(r'\b(üye[\s\-]?ol|kayıt[\s\-]?ol|hesap[\s\-]?oluştur|üyelik|kaydol)\b', re.I),
    re.compile(r'<input[^>]+type=["\']?(email|password)["\']?', re.I),
    re.compile(r'href=["\'][^"\']*/(register|signup|uye-ol|kayit|join)["\']', re.I),
]

MEMBERSHIP_WORDS = [
    "üye ol", "kayıt ol", "sign up", "register", "create account",
    "join", "membership", "hesap oluştur", "üyelik", "kaydol",
]


def check_membership(html: str, text: str) -> dict:
    html_lower = html.lower()
    matched = [p.pattern for p in MEMBERSHIP_PATTERNS if p.search(html)]
    word_matches = [w for w in MEMBERSHIP_WORDS if w in html_lower]

    if len(matched) >= 2 or len(word_matches) >= 2:
        result = "Evet"
        detail = f"{len(word_matches)} üyelik ifadesi / {len(matched)} yapısal gösterge tespit edildi."
    elif matched or word_matches:
        result = "Muhtemelen Evet"
        detail = "Sınırlı üyelik göstergesi bulundu; sayfanın tamamı taranmadı."
    else:
        result = "Hayır"
        detail = "Online üyelik / kayıt formu göstergesi bulunamadı."

    return {"sonuc": result, "detay": detail, "eslesen": word_matches[:6]}


# ─── HTML Rapor Oluşturucu ────────────────────────────────────────────────────

BADGE_COLORS = {
    "Evet": ("#16a34a", "#dcfce7"),
    "Hayır": ("#dc2626", "#fee2e2"),
    "Muhtemelen Evet": ("#d97706", "#fef3c7"),
    "Kısmi": ("#7c3aed", "#ede9fe"),
    "Hata": ("#6b7280", "#f3f4f6"),
}


def badge(text: str) -> str:
    fg, bg = BADGE_COLORS.get(text, ("#374151", "#f3f4f6"))
    return (
        f'<span class="badge" style="background:{bg};color:{fg};">'
        f'{text}</span>'
    )


def chips(items, color="#1e40af") -> str:
    if not items:
        return ""
    return "".join(
        f'<span class="chip" style="border-color:{color};color:{color};">{i}</span>'
        for i in items
    )


def render_site_card(url: str, result: dict) -> str:
    if "hata" in result:
        return f"""
        <div class="card error-card">
          <div class="card-header">
            <span class="site-icon">⚠</span>
            <div>
              <div class="site-url">{url}</div>
              <div class="error-msg">{result['hata']}</div>
            </div>
            {badge("Hata")}
          </div>
        </div>"""

    tr = result["turkce"]
    ph = result["telefon"]
    mb = result["uyelik"]

    tr_chips = chips(tr.get("eslesen", []), "#0e7490")
    mb_chips = chips(mb.get("eslesen", []), "#7c3aed")
    ph_chips = chips(ph.get("numaralar", []), "#b45309")

    return f"""
    <div class="card">
      <div class="card-header">
        <span class="site-icon">🌐</span>
        <div class="site-url">{url}</div>
      </div>

      <div class="criteria-grid">

        <div class="criterion">
          <div class="criterion-title">
            <span class="icon">🇹🇷</span> Türkçe Dil Desteği
            {badge(tr['sonuc'])}
          </div>
          <p class="criterion-detail">{tr['detay']}</p>
          <div class="chip-row">{tr_chips}</div>
        </div>

        <div class="criterion">
          <div class="criterion-title">
            <span class="icon">📞</span> Türkiye Telefon Hattı
            {badge(ph['sonuc'])}
          </div>
          <p class="criterion-detail">{ph['detay']}</p>
          <div class="chip-row">{ph_chips}</div>
        </div>

        <div class="criterion">
          <div class="criterion-title">
            <span class="icon">👤</span> Online Üyelik / Kayıt
            {badge(mb['sonuc'])}
          </div>
          <p class="criterion-detail">{mb['detay']}</p>
          <div class="chip-row">{mb_chips}</div>
        </div>

      </div>
    </div>"""


HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Site Analiz Raporu</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  :root {{
    --bg: #f8fafc; --surface: #ffffff; --border: #e2e8f0;
    --text: #0f172a; --muted: #64748b; --accent: #0f172a; --radius: 12px;
  }}
  body {{ font-family: 'IBM Plex Sans', sans-serif; background: var(--bg); color: var(--text); min-height: 100vh; }}
  header {{ background: var(--accent); color: #fff; padding: 48px 40px 36px; }}
  header h1 {{ font-size: 2rem; font-weight: 600; letter-spacing: -0.02em; margin-bottom: 6px; }}
  header .subtitle {{ font-size: 0.9rem; opacity: 0.55; font-family: 'IBM Plex Mono', monospace; }}
  .summary-bar {{ background: #1e293b; color: #fff; display: flex; gap: 32px; padding: 18px 40px; font-size: 0.82rem; font-family: 'IBM Plex Mono', monospace; }}
  .summary-bar span {{ opacity: 0.7; }} .summary-bar strong {{ opacity: 1; }}
  main {{ max-width: 960px; margin: 40px auto; padding: 0 24px 80px; }}
  .card {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); margin-bottom: 24px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,.05); transition: box-shadow .2s; }}
  .card:hover {{ box-shadow: 0 4px 16px rgba(0,0,0,.08); }}
  .error-card {{ border-color: #fca5a5; background: #fff5f5; }}
  .card-header {{ display: flex; align-items: center; gap: 14px; padding: 20px 24px; border-bottom: 1px solid var(--border); background: #fafafa; flex-wrap: wrap; }}
  .error-card .card-header {{ background: #fff1f1; }}
  .site-icon {{ font-size: 1.4rem; flex-shrink: 0; }}
  .site-url {{ font-family: 'IBM Plex Mono', monospace; font-size: 0.92rem; font-weight: 500; color: #0369a1; flex: 1; word-break: break-all; }}
  .error-msg {{ font-size: 0.82rem; color: #dc2626; margin-top: 2px; }}
  .criteria-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); }}
  .criterion {{ padding: 20px 24px; border-right: 1px solid var(--border); }}
  .criterion:last-child {{ border-right: none; }}
  .criterion-title {{ display: flex; align-items: center; gap: 8px; font-weight: 600; font-size: 0.85rem; margin-bottom: 8px; flex-wrap: wrap; }}
  .criterion-detail {{ font-size: 0.8rem; color: var(--muted); line-height: 1.5; margin-bottom: 10px; }}
  .badge {{ display: inline-block; padding: 3px 10px; border-radius: 999px; font-size: 0.72rem; font-weight: 600; white-space: nowrap; flex-shrink: 0; margin-left: auto; }}
  .chip-row {{ display: flex; flex-wrap: wrap; gap: 6px; margin-top: 4px; }}
  .chip {{ display: inline-block; padding: 2px 9px; border-radius: 6px; border: 1px solid; font-size: 0.72rem; font-family: 'IBM Plex Mono', monospace; background: transparent; }}
  footer {{ text-align: center; padding: 32px; font-size: 0.75rem; color: var(--muted); border-top: 1px solid var(--border); }}
  @media (max-width: 640px) {{
    header {{ padding: 32px 20px 24px; }} main {{ padding: 0 16px 60px; }}
    .summary-bar {{ padding: 14px 20px; gap: 20px; flex-wrap: wrap; }}
    .criteria-grid {{ grid-template-columns: 1fr; }}
    .criterion {{ border-right: none; border-bottom: 1px solid var(--border); }}
    .criterion:last-child {{ border-bottom: none; }}
  }}
</style>
</head>
<body>
<header>
  <h1>🔍 Site Analiz Raporu</h1>
  <div class="subtitle">Oluşturulma: {timestamp}</div>
</header>
<div class="summary-bar">
  <span>Toplam site: <strong>{total}</strong></span>
  <span>Başarılı: <strong>{success}</strong></span>
  <span>Hatalı: <strong>{errors}</strong></span>
</div>
<main>
{cards}
</main>
<footer>
  Bu rapor otomatik olarak oluşturulmuştur. Sonuçlar tahmini niteliktedir; sayfanın tüm alt linkleri taranmamıştır.
</footer>
</body>
</html>
"""


# ─── Ana Analiz Fonksiyonu ───────────────────────────────────────────────────

def analyze(url: str) -> dict:
    print(f"  Indiriliyor: {url}")
    html, err = fetch(url)
    if err:
        return {"hata": err}
    text = html_to_text(html)
    return {
        "turkce": check_turkish(html, text),
        "telefon": check_tr_phone(html, text),
        "uyelik": check_membership(html, text),
    }


def run(urls, output_path="rapor.html"):
    results = {}
    for url in urls:
        print(f"\n[+] {url}")
        results[url] = analyze(url)
        time.sleep(0.5)

    cards = "\n".join(render_site_card(u, r) for u, r in results.items())
    errors = sum(1 for r in results.values() if "hata" in r)

    html_out = HTML_TEMPLATE.format(
        timestamp=datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
        total=len(urls),
        success=len(urls) - errors,
        errors=errors,
        cards=cards,
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_out)

    print(f"\nRapor kaydedildi -> {output_path}")
    return output_path


# ─── CLI ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Kullanim: python site_analiz.py <url1> [url2 url3 ...]")
        print("Ornek   : python site_analiz.py hepsiburada.com trendyol.com")
        sys.exit(1)

    url_list = sys.argv[1:]
    run(url_list, output_path="rapor.html")
