#!/usr/bin/env python3
"""
Site Analiz Aracı v2
--------------------
Verilen URL'leri şu kriterler açısından analiz eder:
  1. Türkçe dil desteği
  2. Türkiye telefon hattı kullanımı
  3. Online üyelik / kayıt formu varlığı

Yenilikler v2:
  - requests + urllib3 ile sağlam HTTP katmanı
  - gzip / deflate / brotli sıkıştırma sorunlarına karşı ham bayt fallback
  - SSL doğrulama başarısız olursa verify=False ile tekrar dener
  - ConnectionReset / ProtocolError için retry + HTTP fallback
  - Gerçekçi tarayıcı başlıkları (Cloudflare bypass şansı artar)
  - Sonuçlar rapor.html olarak kaydedilir
"""

import sys, re, time, datetime, warnings

# requests kontrolü
try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# stdlib fallback
import urllib.request, urllib.error
from html.parser import HTMLParser

warnings.filterwarnings("ignore")   # SSL uyarılarını sustur

# ─── HTTP Katmanı ─────────────────────────────────────────────────────────────

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate",   # brotli kasıtlı çıkartıldı
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

def _make_session():
    s = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "HEAD"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    s.headers.update(HEADERS)
    return s


def _decode_raw(raw: bytes, declared_enc: str | None) -> str:
    """Sıkıştırılmamış ham baytı güvenle metne çevirir."""
    # Gzip başlığı var mı?
    if raw[:2] == b'\x1f\x8b':
        import gzip
        try:
            raw = gzip.decompress(raw)
        except Exception:
            pass
    # Zlib/deflate?
    elif raw[:2] in (b'\x78\x9c', b'\x78\x01', b'\x78\xda'):
        import zlib
        try:
            raw = zlib.decompress(raw)
        except Exception:
            try:
                raw = zlib.decompress(raw, -zlib.MAX_WBITS)
            except Exception:
                pass
    for enc in [declared_enc or "utf-8", "utf-8", "iso-8859-9", "windows-1254", "latin-1"]:
        try:
            return raw.decode(enc, errors="replace")
        except Exception:
            continue
    return raw.decode("utf-8", errors="replace")


def fetch_requests(url: str, timeout: int = 20):
    """requests kütüphanesi ile indir (tercih edilen yol)."""
    s = _make_session()

    def _get(u, verify=True):
        return s.get(u, timeout=timeout, verify=verify,
                     allow_redirects=True, stream=False)

    # 1) HTTPS, SSL doğrulama açık
    try:
        r = _get(url)
        r.encoding = r.apparent_encoding or "utf-8"
        # encoding sorunlu olabilir → ham bayttan kendimiz çözelim
        html = _decode_raw(r.content, r.encoding)
        return html, None
    except requests.exceptions.SSLError:
        pass
    except requests.exceptions.ConnectionError as e:
        if "10054" not in str(e) and "ConnectionReset" not in str(e):
            # Kalıcı bağlantı hatası — HTTP'yi dene
            pass
    except Exception:
        pass

    # 2) SSL doğrulamayı kapat
    try:
        r = _get(url, verify=False)
        html = _decode_raw(r.content, r.apparent_encoding)
        return html, None
    except Exception:
        pass

    # 3) HTTPS başarısız → HTTP fallback
    http_url = url.replace("https://", "http://", 1)
    try:
        r = _get(http_url, verify=False)
        html = _decode_raw(r.content, r.apparent_encoding)
        return html, None
    except Exception as e:
        return None, f"Bağlantı hatası: {e}"


def fetch_urllib(url: str, timeout: int = 20):
    """requests yoksa stdlib ile dene."""
    import ssl
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    for try_url in [url, url.replace("https://", "http://", 1)]:
        try:
            req = urllib.request.Request(try_url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                raw = resp.read()
                enc = resp.headers.get_content_charset()
                return _decode_raw(raw, enc), None
        except Exception:
            continue
    return None, "Bağlantı kurulamadı (urllib fallback da başarısız)"


def fetch(url: str, timeout: int = 20):
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    if HAS_REQUESTS:
        return fetch_requests(url, timeout)
    return fetch_urllib(url, timeout)


# ─── HTML → Metin ─────────────────────────────────────────────────────────────

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

TR_LANG_RE = [
    re.compile(r'lang=["\']tr', re.I),
    re.compile(r'locale=["\']tr', re.I),
    re.compile(r'hreflang=["\']tr', re.I),
    re.compile(r'"language"\s*:\s*"tr"', re.I),
]


def check_turkish(html: str, text: str) -> dict:
    lang_tag = any(p.search(html) for p in TR_LANG_RE)
    hl = html.lower()
    matched = [w for w in TR_WORDS if w in hl]
    n = len(matched)

    if lang_tag and n >= 2:
        s, d = "Evet", f"lang/locale etiketi + {n} Türkçe ifade."
    elif lang_tag:
        s, d = "Muhtemelen Evet", "lang/locale etiketi var ancak Türkçe içerik sınırlı."
    elif n >= 5:
        s, d = "Evet", f"Dil etiketi yok ama {n} Türkçe ifade tespit edildi."
    elif n >= 2:
        s, d = "Kısmi", f"{n} Türkçe ifade bulundu; tam destek belirsiz."
    else:
        s, d = "Hayır", "Türkçe dil göstergesi bulunamadı."

    return {"sonuc": s, "detay": d, "eslesen": matched[:8]}


# ─── 2. Türkiye Telefon Hattı ────────────────────────────────────────────────

TR_PHONE_RE = [
    re.compile(r'\+90[\s\-\.]?\(?\d{3}\)?[\s\-\.]?\d{3}[\s\-\.]?\d{2}[\s\-\.]?\d{2}'),
    re.compile(r'\b0(8[015]\d|[2-9]\d\d)[\s\-\.]?\d{3}[\s\-\.]?\d{2}[\s\-\.]?\d{2}\b'),
    re.compile(r'\b444[\s\-\.]?\d{4}\b'),
]


def check_tr_phone(html: str, text: str) -> dict:
    found = []
    for pat in TR_PHONE_RE:
        found.extend(pat.findall(html))
    found = list(dict.fromkeys(m.strip() for m in found))[:6]
    if found:
        return {"sonuc": "Evet",
                "detay": f"{len(found)} Türkiye telefon numarası tespit edildi.",
                "numaralar": found}
    return {"sonuc": "Hayır",
            "detay": "Türkiye telefon numarası bulunamadı.",
            "numaralar": []}


# ─── 3. Online Üyelik ────────────────────────────────────────────────────────

MEMBERSHIP_RE = [
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
    hl = html.lower()
    matched_re = [p.pattern for p in MEMBERSHIP_RE if p.search(html)]
    matched_w  = [w for w in MEMBERSHIP_WORDS if w in hl]

    if len(matched_re) >= 2 or len(matched_w) >= 2:
        s, d = "Evet", f"{len(matched_w)} üyelik ifadesi / {len(matched_re)} yapısal gösterge."
    elif matched_re or matched_w:
        s, d = "Muhtemelen Evet", "Sınırlı üyelik göstergesi bulundu."
    else:
        s, d = "Hayır", "Online üyelik / kayıt formu göstergesi bulunamadı."

    return {"sonuc": s, "detay": d, "eslesen": matched_w[:6]}


# ─── HTML Rapor ───────────────────────────────────────────────────────────────

BADGE = {
    "Evet":           ("#16a34a", "#dcfce7"),
    "Hayır":          ("#dc2626", "#fee2e2"),
    "Muhtemelen Evet":("#d97706", "#fef3c7"),
    "Kısmi":          ("#7c3aed", "#ede9fe"),
    "Hata":           ("#6b7280", "#f3f4f6"),
}

def badge(t):
    fg, bg = BADGE.get(t, ("#374151", "#f3f4f6"))
    return f'<span class="badge" style="background:{bg};color:{fg};">{t}</span>'

def chips(items, color):
    return "".join(
        f'<span class="chip" style="border-color:{color};color:{color};">{i}</span>'
        for i in items
    )

def card(url, res):
    if "hata" in res:
        return f"""<div class="card error-card"><div class="card-header">
          <span class="site-icon">⚠</span>
          <div><div class="site-url">{url}</div>
          <div class="error-msg">{res['hata']}</div></div>
          {badge("Hata")}</div></div>"""

    tr, ph, mb = res["turkce"], res["telefon"], res["uyelik"]
    return f"""
<div class="card">
  <div class="card-header"><span class="site-icon">🌐</span>
    <div class="site-url">{url}</div></div>
  <div class="criteria-grid">
    <div class="criterion">
      <div class="criterion-title"><span>🇹🇷</span> Türkçe Dil Desteği {badge(tr['sonuc'])}</div>
      <p class="criterion-detail">{tr['detay']}</p>
      <div class="chip-row">{chips(tr.get('eslesen',[]), '#0e7490')}</div>
    </div>
    <div class="criterion">
      <div class="criterion-title"><span>📞</span> Türkiye Telefon Hattı {badge(ph['sonuc'])}</div>
      <p class="criterion-detail">{ph['detay']}</p>
      <div class="chip-row">{chips(ph.get('numaralar',[]), '#b45309')}</div>
    </div>
    <div class="criterion">
      <div class="criterion-title"><span>👤</span> Online Üyelik / Kayıt {badge(mb['sonuc'])}</div>
      <p class="criterion-detail">{mb['detay']}</p>
      <div class="chip-row">{chips(mb.get('eslesen',[]), '#7c3aed')}</div>
    </div>
  </div>
</div>"""

CSS = """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
:root { --bg:#f8fafc;--surface:#fff;--border:#e2e8f0;--text:#0f172a;--muted:#64748b;--accent:#0f172a;--radius:12px; }
body { font-family:'IBM Plex Sans',sans-serif;background:var(--bg);color:var(--text);min-height:100vh; }
header { background:var(--accent);color:#fff;padding:48px 40px 36px; }
header h1 { font-size:2rem;font-weight:600;letter-spacing:-.02em;margin-bottom:6px; }
header .subtitle { font-size:.9rem;opacity:.55;font-family:'IBM Plex Mono',monospace; }
.summary-bar { background:#1e293b;color:#fff;display:flex;gap:32px;padding:18px 40px;font-size:.82rem;font-family:'IBM Plex Mono',monospace; }
.summary-bar span { opacity:.7; } .summary-bar strong { opacity:1; }
main { max-width:960px;margin:40px auto;padding:0 24px 80px; }
.card { background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);margin-bottom:24px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.05);transition:box-shadow .2s; }
.card:hover { box-shadow:0 4px 16px rgba(0,0,0,.08); }
.error-card { border-color:#fca5a5;background:#fff5f5; }
.card-header { display:flex;align-items:center;gap:14px;padding:20px 24px;border-bottom:1px solid var(--border);background:#fafafa;flex-wrap:wrap; }
.error-card .card-header { background:#fff1f1; }
.site-icon { font-size:1.4rem;flex-shrink:0; }
.site-url { font-family:'IBM Plex Mono',monospace;font-size:.92rem;font-weight:500;color:#0369a1;flex:1;word-break:break-all; }
.error-msg { font-size:.82rem;color:#dc2626;margin-top:2px; }
.criteria-grid { display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); }
.criterion { padding:20px 24px;border-right:1px solid var(--border); }
.criterion:last-child { border-right:none; }
.criterion-title { display:flex;align-items:center;gap:8px;font-weight:600;font-size:.85rem;margin-bottom:8px;flex-wrap:wrap; }
.criterion-detail { font-size:.8rem;color:var(--muted);line-height:1.5;margin-bottom:10px; }
.badge { display:inline-block;padding:3px 10px;border-radius:999px;font-size:.72rem;font-weight:600;white-space:nowrap;flex-shrink:0;margin-left:auto; }
.chip-row { display:flex;flex-wrap:wrap;gap:6px;margin-top:4px; }
.chip { display:inline-block;padding:2px 9px;border-radius:6px;border:1px solid;font-size:.72rem;font-family:'IBM Plex Mono',monospace;background:transparent; }
footer { text-align:center;padding:32px;font-size:.75rem;color:var(--muted);border-top:1px solid var(--border); }
@media(max-width:640px){ header{padding:32px 20px 24px;} main{padding:0 16px 60px;} .summary-bar{padding:14px 20px;gap:20px;flex-wrap:wrap;} .criteria-grid{grid-template-columns:1fr;} .criterion{border-right:none;border-bottom:1px solid var(--border);} .criterion:last-child{border-bottom:none;} }
"""

def build_html(results, ts):
    errors  = sum(1 for r in results.values() if "hata" in r)
    success = len(results) - errors
    all_cards = "\n".join(card(u, r) for u, r in results.items())
    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Site Analiz Raporu</title>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
<header>
  <h1>🔍 Site Analiz Raporu</h1>
  <div class="subtitle">Oluşturulma: {ts}</div>
</header>
<div class="summary-bar">
  <span>Toplam site: <strong>{len(results)}</strong></span>
  <span>Başarılı: <strong>{success}</strong></span>
  <span>Hatalı: <strong>{errors}</strong></span>
</div>
<main>{all_cards}</main>
<footer>Bu rapor otomatik oluşturulmuştur. Sonuçlar tahminidir; sayfanın tüm alt linkleri taranmamıştır.</footer>
</body></html>"""


# ─── Analiz ───────────────────────────────────────────────────────────────────

def analyze(url):
    print(f"  ↳ İndiriliyor: {url}")
    html, err = fetch(url)
    if err:
        print(f"  ✗ {err}")
        return {"hata": err}
    print(f"  ✓ {len(html):,} karakter indirildi")
    text = html_to_text(html)
    return {
        "turkce":  check_turkish(html, text),
        "telefon": check_tr_phone(html, text),
        "uyelik":  check_membership(html, text),
    }


def run(urls, output_path="rapor.html"):
    if not HAS_REQUESTS:
        print("⚠ 'requests' kütüphanesi bulunamadı → stdlib fallback kullanılıyor")
        print("  Öneri: pip install requests")
    results = {}
    for url in urls:
        print(f"\n[•] {url}")
        results[url] = analyze(url)
        time.sleep(1)

    html_out = build_html(results, datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S"))
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_out)
    print(f"\n✅ Rapor kaydedildi → {output_path}")


# ─── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Kullanım : python site_analiz.py <url1> [url2 ...]")
        print("Örnek    : python site_analiz.py xmtrfx.online trendyol.com")
        sys.exit(1)
    run(sys.argv[1:])
