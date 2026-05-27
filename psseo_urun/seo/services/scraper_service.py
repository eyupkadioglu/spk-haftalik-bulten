"""
Ürün sayfasından veri çekme servisi.
Kullanıcı bir URL veya marka+model girince ürün bilgilerini otomatik doldurur.
"""
import re
import urllib.request
import urllib.error
from html.parser import HTMLParser


class _MetinCikartici(HTMLParser):
    """HTML'den düz metin çıkarır."""
    def __init__(self):
        super().__init__()
        self.parcalar   = []
        self._atla      = False

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style', 'nav', 'footer', 'header'):
            self._atla = True

    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'nav', 'footer', 'header'):
            self._atla = False

    def handle_data(self, data):
        if not self._atla:
            temiz = data.strip()
            if temiz:
                self.parcalar.append(temiz)

    def metin(self):
        return '\n'.join(self.parcalar)


def _html_indir(url, timeout=10):
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'Mozilla/5.0 (compatible; psseo-bot/1.0)'}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        kodlama = resp.headers.get_content_charset() or 'utf-8'
        return resp.read().decode(kodlama, errors='replace')


def _baslik_bul(html):
    m = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.IGNORECASE | re.DOTALL)
    if m:
        return re.sub(r'<[^>]+>', '', m.group(1)).strip()
    m = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
    if m:
        return re.sub(r'<[^>]+>', '', m.group(1)).strip()
    return ''


def _meta_aciklama_bul(html):
    m = re.search(
        r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)',
        html, re.IGNORECASE
    )
    if m:
        return m.group(1).strip()
    m = re.search(
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']description["\']',
        html, re.IGNORECASE
    )
    if m:
        return m.group(1).strip()
    return ''


def scrape_url(url):
    """
    URL'den ürün bilgilerini çeker.
    Döner: {'ad': ..., 'ham_aciklama': ..., 'teknik_ozellik': ...}
    Hata durumunda ValueError fırlatır.
    """
    try:
        html = _html_indir(url)
    except Exception as e:
        raise ValueError(f'URL indirilemedi: {e}')

    ad           = _baslik_bul(html)
    ham_aciklama = _meta_aciklama_bul(html)

    # Sayfanın düz metninden teknik özellik bölümünü bulmaya çalış
    parser = _MetinCikartici()
    parser.feed(html)
    tam_metin = parser.metin()

    # "Teknik Özellikler" / "Specifications" bölümünü bul
    teknik = ''
    bolum_m = re.search(
        r'(?:Teknik[_ ]Özellik|Specifications?|Özellikler)[^\n]*\n([\s\S]{50,800}?)(?:\n\n|\Z)',
        tam_metin, re.IGNORECASE
    )
    if bolum_m:
        teknik = bolum_m.group(1).strip()

    return {
        'ad':            ad,
        'ham_aciklama':  ham_aciklama,
        'teknik_ozellik': teknik,
    }
