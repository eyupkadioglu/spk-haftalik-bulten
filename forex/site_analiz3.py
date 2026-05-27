#!/usr/bin/env python3
"""
Site Analiz Aracı v3
--------------------
Düzeltmeler:
  - URL temizleme: sondaki virgül/boşluk/tırnak otomatik kaldırılır
  - gzip hatası: requests stream=True + manuel decompress ile çözüldü
  - SSL fallback zinciri korundu
"""

import sys, re, time, datetime, warnings, gzip, zlib

try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

import urllib.request, urllib.error
from html.parser import HTMLParser

warnings.filterwarnings("ignore")

# ─── URL Temizleyici ──────────────────────────────────────────────────────────

def clean_url(url: str) -> str:
    """Sondaki virgül, boşluk, tırnak gibi karakterleri temizler."""
    url = url.strip().strip(",").strip("'\"").strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url

# ─── Ham bayt → metin ─────────────────────────────────────────────────────────

def decode_raw(raw: bytes, enc: str | None = None) -> str:
    """Sıkıştırılmış veya düz baytı güvenle metne çevirir."""
    # gzip
    if raw[:2] == b'\x1f\x8b':
        try:
            raw = gzip.decompress(raw)
        except Exception:
            pass
    # zlib / deflate
    elif len(raw) >= 2 and raw[0] == 0x78 and raw[1] in (0x01, 0x9c, 0xda, 0x5e):
        try:
            raw = zlib.decompress(raw)
        except Exception:
            try:
                raw = zlib.decompress(raw, -zlib.MAX_WBITS)
            except Exception:
                pass

    for e in [enc or "utf-8", "utf-8", "iso-8859-9", "windows-1254", "latin-1"]:
        if not e:
            continue
        try:
            return raw.decode(e, errors="replace")
        except Exception:
            continue
    return raw.decode("utf-8", errors="replace")

# ─── HTTP Katmanı ─────────────────────────────────────────────────────────────

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    # Encoding istemiyoruz — ham bayt almak daha güvenli
    "Accept-Encoding": "identity",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

def make_session():
    s = requests.Session()
    retry = Retry(
        total=3, backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,
    )
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.mount("http://",  HTTPAdapter(max_retries=retry))
    s.headers.update(HEADERS)
    return s

def fetch_with_requests(url: str, timeout=20):
    s = make_session()

    def _try(u, verify=True):
        # stream=True → şifre çözmesini requests'e bırakmıyoruz
        r = s.get(u, timeout=timeout, verify=verify,
                  allow_redirects=True, stream=True)
        raw = r.raw.read(decode_content=False)   # ← sıkıştırılmış ham bayt
        enc = r.encoding or r.apparent_encoding or "utf-8"
        return decode_raw(raw, enc)

    # 1) HTTPS normal
    try:
        return _try(url), None
    except requests.exceptions.SSLError:
        pass
    except Exception:
        pass

    # 2) SSL doğrulamasız
    try:
        return _try(url, verify=False), None
    except Exception:
        pass

    # 3) HTTP fallback
    http_url = re.sub(r'^https://', 'http://', url)
    try:
        return _try(http_url, verify=False), None
    except Exception as e:
        return None, f"Bağlantı hatası: {e}"

def fetch_with_urllib(url: str, timeout=20):
    import ssl
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    for try_url in [url, re.sub(r'^https://', 'http://', url)]:
        try:
            req = urllib.request.Request(try_url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                raw = resp.read()
                enc = resp.headers.get_content_charset()
                return decode_raw(raw, enc), None
        except Exception:
            continue
    return None, "Bağlantı kurulamadı"

def fetch(url: str, timeout=20):
    url = clean_url(url)
    if HAS_REQUESTS:
        return fetch_with_requests(url, timeout)
    return fetch_with_urllib(url, timeout)

# ─── HTML → Metin ─────────────────────────────────────────────────────────────

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self._skip = False
        self._skip_tags = {"script","style","noscript","svg","head"}

    def handle_starttag(self, tag, attrs):
        if tag in self._skip_tags: self._skip = True

    def handle_endtag(self, tag):
        if tag in self._skip_tags: self._skip = False

    def handle_data(self, data):
        if not self._skip: self.parts.append(data)

    def get_text(self): return " ".join(self.parts)

def html_to_text(html):
    p = TextExtractor()
    try: p.feed(html)
    except Exception: pass
    return p.get_text()

# ─── Kriterler ────────────────────────────────────────────────────────────────

TR_WORDS = [
    "anasayfa","hakkımızda","iletişim","ürünler","hizmetler","giriş",
    "kayıt","üye ol","sepet","ara","arama","tıklayın","indirim",
    "kampanya","bize ulaşın","müşteri","sipariş","teslimat","kargo",
    "iade","şifre","kullanıcı","tamam","iptal","güncelle","kaydet",
    "daha fazla","göster",
]
TR_LANG_RE = [
    re.compile(r'lang=["\']tr', re.I),
    re.compile(r'locale=["\']tr', re.I),
    re.compile(r'hreflang=["\']tr', re.I),
    re.compile(r'"language"\s*:\s*"tr"', re.I),
]

def check_turkish(html, text):
    lang_tag = any(p.search(html) for p in TR_LANG_RE)
    hl = html.lower()
    matched = [w for w in TR_WORDS if w in hl]
    n = len(matched)
    if lang_tag and n >= 2:   s,d = "Evet",          f"lang/locale etiketi + {n} Türkçe ifade."
    elif lang_tag:             s,d = "Muhtemelen Evet","lang/locale etiketi var, içerik sınırlı."
    elif n >= 5:               s,d = "Evet",          f"Etiketsiz ama {n} Türkçe ifade bulundu."
    elif n >= 2:               s,d = "Kısmi",         f"{n} Türkçe ifade; tam destek belirsiz."
    else:                      s,d = "Hayır",         "Türkçe dil göstergesi bulunamadı."
    return {"sonuc":s,"detay":d,"eslesen":matched[:8]}

TR_PHONE_RE = [
    re.compile(r'\+90[\s\-\.]?\(?\d{3}\)?[\s\-\.]?\d{3}[\s\-\.]?\d{2}[\s\-\.]?\d{2}'),
    re.compile(r'\b0(8[015]\d|[2-9]\d\d)[\s\-\.]?\d{3}[\s\-\.]?\d{2}[\s\-\.]?\d{2}\b'),
    re.compile(r'\b444[\s\-\.]?\d{4}\b'),
]

def check_tr_phone(html, text):
    found = []
    for pat in TR_PHONE_RE:
        found.extend(pat.findall(html))
    found = list(dict.fromkeys(m.strip() for m in found))[:6]
    if found:
        return {"sonuc":"Evet",  "detay":f"{len(found)} Türkiye numarası tespit edildi.","numaralar":found}
    return     {"sonuc":"Hayır", "detay":"Türkiye telefon numarası bulunamadı.",          "numaralar":[]}

MEMB_RE = [
    re.compile(r'\b(sign[\s\-]?up|register|create[\s\-]?account|join[\s\-]?now|membership)\b', re.I),
    re.compile(r'\b(üye[\s\-]?ol|kayıt[\s\-]?ol|hesap[\s\-]?oluştur|üyelik|kaydol)\b', re.I),
    re.compile(r'<input[^>]+type=["\']?(email|password)["\']?', re.I),
    re.compile(r'href=["\'][^"\']*/(register|signup|uye-ol|kayit|join)["\']', re.I),
]
MEMB_WORDS = [
    "üye ol","kayıt ol","sign up","register","create account",
    "join","membership","hesap oluştur","üyelik","kaydol",
]

def check_membership(html, text):
    hl = html.lower()
    mr = [p.pattern for p in MEMB_RE if p.search(html)]
    mw = [w for w in MEMB_WORDS if w in hl]
    if len(mr) >= 2 or len(mw) >= 2: s,d = "Evet",           f"{len(mw)} ifade / {len(mr)} yapısal gösterge."
    elif mr or mw:                     s,d = "Muhtemelen Evet","Sınırlı üyelik göstergesi bulundu."
    else:                              s,d = "Hayır",          "Online üyelik göstergesi bulunamadı."
    return {"sonuc":s,"detay":d,"eslesen":mw[:6]}

# ─── HTML Rapor ───────────────────────────────────────────────────────────────

BADGE_COLORS = {
    "Evet":("#16a34a","#dcfce7"), "Hayır":("#dc2626","#fee2e2"),
    "Muhtemelen Evet":("#d97706","#fef3c7"), "Kısmi":("#7c3aed","#ede9fe"),
    "Hata":("#6b7280","#f3f4f6"),
}

def badge(t):
    fg,bg = BADGE_COLORS.get(t,("#374151","#f3f4f6"))
    return f'<span class="badge" style="background:{bg};color:{fg};">{t}</span>'

def chips(items, color):
    return "".join(f'<span class="chip" style="border-color:{color};color:{color};">{i}</span>' for i in items)

def card(url, res):
    if "hata" in res:
        return f"""<div class="card error-card"><div class="card-header">
<span class="site-icon">⚠</span>
<div><div class="site-url">{url}</div><div class="error-msg">{res['hata']}</div></div>
{badge("Hata")}</div></div>"""
    tr,ph,mb = res["turkce"],res["telefon"],res["uyelik"]
    return f"""
<div class="card">
  <div class="card-header"><span class="site-icon">🌐</span><div class="site-url">{url}</div></div>
  <div class="criteria-grid">
    <div class="criterion">
      <div class="criterion-title"><span>🇹🇷</span> Türkçe Dil Desteği {badge(tr['sonuc'])}</div>
      <p class="criterion-detail">{tr['detay']}</p>
      <div class="chip-row">{chips(tr.get('eslesen',[]),'#0e7490')}</div>
    </div>
    <div class="criterion">
      <div class="criterion-title"><span>📞</span> Türkiye Telefon Hattı {badge(ph['sonuc'])}</div>
      <p class="criterion-detail">{ph['detay']}</p>
      <div class="chip-row">{chips(ph.get('numaralar',[]),'#b45309')}</div>
    </div>
    <div class="criterion">
      <div class="criterion-title"><span>👤</span> Online Üyelik / Kayıt {badge(mb['sonuc'])}</div>
      <p class="criterion-detail">{mb['detay']}</p>
      <div class="chip-row">{chips(mb.get('eslesen',[]),'#7c3aed')}</div>
    </div>
  </div>
</div>"""

CSS = """
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{--bg:#f8fafc;--surface:#fff;--border:#e2e8f0;--text:#0f172a;--muted:#64748b;--accent:#0f172a;--radius:12px}
body{font-family:'IBM Plex Sans',sans-serif;background:var(--bg);color:var(--text);min-height:100vh}
header{background:var(--accent);color:#fff;padding:48px 40px 36px}
header h1{font-size:2rem;font-weight:600;letter-spacing:-.02em;margin-bottom:6px}
header .subtitle{font-size:.9rem;opacity:.55;font-family:'IBM Plex Mono',monospace}
.summary-bar{background:#1e293b;color:#fff;display:flex;gap:32px;padding:18px 40px;font-size:.82rem;font-family:'IBM Plex Mono',monospace}
.summary-bar span{opacity:.7}.summary-bar strong{opacity:1}
main{max-width:960px;margin:40px auto;padding:0 24px 80px}
.card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);margin-bottom:24px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.05);transition:box-shadow .2s}
.card:hover{box-shadow:0 4px 16px rgba(0,0,0,.08)}
.error-card{border-color:#fca5a5;background:#fff5f5}
.card-header{display:flex;align-items:center;gap:14px;padding:20px 24px;border-bottom:1px solid var(--border);background:#fafafa;flex-wrap:wrap}
.error-card .card-header{background:#fff1f1}
.site-icon{font-size:1.4rem;flex-shrink:0}
.site-url{font-family:'IBM Plex Mono',monospace;font-size:.92rem;font-weight:500;color:#0369a1;flex:1;word-break:break-all}
.error-msg{font-size:.82rem;color:#dc2626;margin-top:2px}
.criteria-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr))}
.criterion{padding:20px 24px;border-right:1px solid var(--border)}
.criterion:last-child{border-right:none}
.criterion-title{display:flex;align-items:center;gap:8px;font-weight:600;font-size:.85rem;margin-bottom:8px;flex-wrap:wrap}
.criterion-detail{font-size:.8rem;color:var(--muted);line-height:1.5;margin-bottom:10px}
.badge{display:inline-block;padding:3px 10px;border-radius:999px;font-size:.72rem;font-weight:600;white-space:nowrap;flex-shrink:0;margin-left:auto}
.chip-row{display:flex;flex-wrap:wrap;gap:6px;margin-top:4px}
.chip{display:inline-block;padding:2px 9px;border-radius:6px;border:1px solid;font-size:.72rem;font-family:'IBM Plex Mono',monospace;background:transparent}
footer{text-align:center;padding:32px;font-size:.75rem;color:var(--muted);border-top:1px solid var(--border)}
@media(max-width:640px){header{padding:32px 20px 24px}main{padding:0 16px 60px}.summary-bar{padding:14px 20px;gap:20px;flex-wrap:wrap}.criteria-grid{grid-template-columns:1fr}.criterion{border-right:none;border-bottom:1px solid var(--border)}.criterion:last-child{border-bottom:none}}
"""

def build_html(results, ts):
    errors  = sum(1 for r in results.values() if "hata" in r)
    success = len(results) - errors
    all_cards = "\n".join(card(u,r) for u,r in results.items())
    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
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
<footer>Bu rapor otomatik oluşturulmuştur. Sonuçlar tahminidir.</footer>
</body></html>"""

# ─── Analiz ───────────────────────────────────────────────────────────────────

def analyze(url):
    display_url = clean_url(url)   # temizlenmiş hali göster
    print(f"  ↳ İndiriliyor: {display_url}")
    html, err = fetch(url)
    if err:
        print(f"  ✗ {err}")
        return display_url, {"hata": err}
    print(f"  ✓ {len(html):,} karakter alındı")
    text = html_to_text(html)
    return display_url, {
        "turkce":  check_turkish(html, text),
        "telefon": check_tr_phone(html, text),
        "uyelik":  check_membership(html, text),
    }

def run(urls, output_path="rapor.html"):
    if not HAS_REQUESTS:
        print("⚠  'requests' bulunamadı → pip install requests")
    results = {}
    for raw_url in urls:
        print(f"\n[•] {raw_url.strip()}")
        clean, res = analyze(raw_url)
        results[clean] = res
        time.sleep(1)

    html_out = build_html(results, datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S"))
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_out)
    print(f"\n✅ Rapor kaydedildi → {output_path}")

# ─── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Kullanım : python site_analiz.py <url1> [url2 ...]")
        print("Örnek    : python site_analiz.py turkey-xm.com xmtrfx.online xmarabia.net")
        sys.exit(1)
    run(sys.argv[1:])
