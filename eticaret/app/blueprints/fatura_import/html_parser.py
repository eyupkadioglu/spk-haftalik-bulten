"""
GIB e-Fatura HTML parser.
Bauhaus ve benzeri firmaların HTML formatındaki e-faturalarını okur.
QR kod JSON verisi + lineTable kombinasyonu ile parse eder.
"""
import json
import re

try:
    from bs4 import BeautifulSoup
    _BS4_OK = True
except ImportError:
    _BS4_OK = False


def _tr_float(text):
    if not text:
        return 0.0
    text = str(text).strip().replace('\xa0', '').replace('TL', '').replace('₺', '').strip()
    if ',' in text and '.' in text:
        text = text.replace('.', '').replace(',', '.')
    elif ',' in text:
        text = text.replace(',', '.')
    try:
        return float(text)
    except ValueError:
        return 0.0


def _fmt_tarih(date_str):
    """YYYY-MM-DD veya DD-MM-YYYY → DD.MM.YYYY"""
    if not date_str:
        return ''
    parts = re.split(r'[-/]', date_str.strip())
    if len(parts) == 3:
        if len(parts[0]) == 4:          # YYYY-MM-DD
            return f'{parts[2]}.{parts[1]}.{parts[0]}'
        else:                           # DD-MM-YYYY
            return f'{parts[0]}.{parts[1]}.{parts[2]}'
    return date_str


def _clean(el):
    """BeautifulSoup elementinden temiz metin döndürür."""
    return el.get_text(separator=' ', strip=True).replace('\xa0', ' ').strip()


def _find_supplier_name(soup, qr_data):
    """Tedarikçi ünvanını birden fazla yerden deneyerek bulur."""
    # 1. QR JSON'da unvan/adi anahtarı var mı?
    for key in ('unvan', 'saticiadi', 'ad', 'name'):
        val = qr_data.get(key, '').strip()
        if val:
            return val

    # 2. "Sayın" veya "Satıcı" etiketine yakın başlık
    for tag in soup.find_all(['h1', 'h2', 'h3', 'strong', 'b']):
        txt = _clean(tag)
        if txt and 20 < len(txt) < 200 and not any(
            x in txt.lower() for x in ('fatura', 'invoice', 'e-arşiv', 'e-fatura', 'sayın', 'alıcı')
        ):
            return txt

    # 3. İlk h1 (genel fallback)
    first_h1 = soup.find('h1')
    if first_h1:
        return _clean(first_h1)

    return ''


def _find_supplier_address(soup, tedarikci_vkn):
    """Tedarikçi adresini HTML'de arar."""
    vkn_clean = tedarikci_vkn.replace(' ', '')

    for td in soup.find_all('td'):
        txt = _clean(td)
        # VKN bilinen ise doğrulayarak ara; bilinmiyorsa sadece Tel/V.D. etiketi yeterli
        vkn_eslesti = (not vkn_clean) or (vkn_clean and vkn_clean in txt.replace(' ', ''))
        if vkn_eslesti and ('Tel' in txt or 'Fax' in txt or 'V.D.' in txt or 'Vergi' in txt):
            lines = [s.get_text(strip=True) for s in td.find_all(['span', 'p', 'div']) if s.get_text(strip=True)]
            if lines:
                return ', '.join(lines[:3])
            # span yoksa td metninin ilk iki satırını al
            raw_lines = [l.strip() for l in txt.splitlines() if l.strip()]
            return ', '.join(raw_lines[:2])

    return ''


def _parse_line_table(soup):
    """#lineTable veya benzeri tablodan kalem satırlarını çıkarır."""
    kalemler = []

    # GIB standart: id="lineTable"
    line_table = soup.find('table', id='lineTable')

    # Bulunamazsa kalem içerdiği anlaşılan ilk tabloyu dene
    if not line_table:
        for tbl in soup.find_all('table'):
            headers = [_clean(th).lower() for th in tbl.find_all('th')]
            header_txt = ' '.join(headers)
            if any(k in header_txt for k in ('miktar', 'adet', 'tutar', 'fiyat', 'hizmet', 'mal')):
                line_table = tbl
                break

    if not line_table:
        return kalemler

    rows = line_table.find_all('tr')
    # Başlık satırından sütun indekslerini çıkar
    header_row = rows[0] if rows else None
    col_map = {}  # {'aciklama': 1, 'miktar': 2, ...}
    if header_row:
        for i, th in enumerate(header_row.find_all(['th', 'td'])):
            h = _clean(th).lower()
            if any(k in h for k in ('mal', 'hizmet', 'ürün', 'açıklama', 'tanım')):
                col_map.setdefault('aciklama', i)
            elif any(k in h for k in ('miktar', 'adet', 'qty', 'quantity')):
                col_map.setdefault('miktar', i)
            elif any(k in h for k in ('birim fiyat', 'birim fiy', 'unit price', 'fiyat')):
                col_map.setdefault('fiyat', i)
            elif h in ('birim', 'unit', 'br'):
                col_map.setdefault('birim', i)
            elif 'kdv' in h or 'vergi' in h or 'tax' in h:
                col_map.setdefault('kdv', i)

    # Varsayılan GIB sütun düzeni: 0=sıra, 1=açıklama, 2=miktar, 3=birim, 4=birim fiyat, 5=kdv%, 6=tutar
    aciklama_col = col_map.get('aciklama', 1)
    miktar_col   = col_map.get('miktar',   2)
    birim_col    = col_map.get('birim',    3)
    fiyat_col    = col_map.get('fiyat',    4)
    kdv_col      = col_map.get('kdv',      5)

    for row in rows[1:]:
        cells = row.find_all('td')
        if len(cells) < max(aciklama_col, miktar_col, fiyat_col, kdv_col) + 1:
            continue

        aciklama    = _clean(cells[aciklama_col]) if len(cells) > aciklama_col else ''
        miktar_str  = _clean(cells[miktar_col])   if len(cells) > miktar_col   else '1'
        birim       = _clean(cells[birim_col])     if len(cells) > birim_col    else 'Adet'
        fiyat_str   = _clean(cells[fiyat_col])     if len(cells) > fiyat_col    else '0'
        kdv_str     = _clean(cells[kdv_col]).replace('%', '').strip() if len(cells) > kdv_col else '20'

        miktar      = _tr_float(miktar_str)
        birim_fiyat = _tr_float(fiyat_str)
        try:
            kdv_orani = float(kdv_str.replace(',', '.'))
        except ValueError:
            kdv_orani = 20.0

        if aciklama and miktar > 0:
            kalemler.append({
                'aciklama':      aciklama,
                'miktar':        miktar,
                'birim':         birim or 'Adet',
                'birim_fiyat':   birim_fiyat,
                'kdv_orani':     kdv_orani,
                'iskonto_orani': 0.0,
            })

    return kalemler


def parse_html(filepath):
    """
    GIB HTML e-Fatura dosyasını parse eder.
    Dönen dict fatura_import/routes.py kaydet() ile uyumludur.
    """
    if not _BS4_OK:
        raise ImportError(
            "beautifulsoup4 yüklü değil. 'pip install beautifulsoup4' komutunu çalıştırın."
        )

    with open(filepath, 'rb') as f:
        raw = f.read()

    soup = BeautifulSoup(raw, 'html.parser')

    # --- QR kod JSON verisi (#qrvalue div) ---
    qr_data = {}
    qr_div = soup.find('div', id='qrvalue')
    if qr_div:
        try:
            qr_data = json.loads(qr_div.get_text(strip=True))
        except (json.JSONDecodeError, ValueError):
            pass

    fatura_no     = qr_data.get('no', '').strip()
    fatura_tarihi = _fmt_tarih(qr_data.get('tarih', ''))

    # VKN: 10 hane → VKN, 11 hane → TCKN
    vkntckn       = qr_data.get('vkntckn', '').strip()
    tedarikci_vkn  = vkntckn if len(vkntckn) == 10 else ''
    tedarikci_tckn = vkntckn if len(vkntckn) == 11 else ''

    # Toplamlar
    ara_toplam   = _tr_float(qr_data.get('malhizmettoplam', 0))
    genel_toplam = _tr_float(qr_data.get('odenecek', 0))

    kdv_toplam = 0.0
    for key, val in qr_data.items():
        if 'hesaplanankdv' in key.lower():
            kdv_toplam += _tr_float(val)
    if kdv_toplam == 0 and genel_toplam > 0 and ara_toplam > 0:
        kdv_toplam = round(genel_toplam - ara_toplam, 2)

    # --- Fatura no QR'da yoksa HTML'den ara ---
    if not fatura_no:
        for el in soup.find_all(string=re.compile(r'[A-Z]{3}\d{4}\d{9}|[A-Z]{2,3}\d{7,16}')):
            m = re.search(r'([A-Z]{2,3}\d{7,16})', el)
            if m:
                fatura_no = m.group(1)
                break

    # --- Tedarikçi bilgileri ---
    tedarikci_adi   = _find_supplier_name(soup, qr_data)
    tedarikci_adres = _find_supplier_address(soup, tedarikci_vkn)

    # --- Kalemler ---
    kalemler = _parse_line_table(soup)

    # Kalem bulunamazsa ara toplamdan tek satır oluştur
    if not kalemler and ara_toplam > 0:
        kdv_oran = round(kdv_toplam / ara_toplam * 100) if ara_toplam else 20
        kalemler = [{
            'aciklama':      'HTML\'den otomatik okunan kalem (düzenleme gerekebilir)',
            'miktar':        1,
            'birim':         'Adet',
            'birim_fiyat':   ara_toplam,
            'kdv_orani':     kdv_oran,
            'iskonto_orani': 0.0,
        }]

    return {
        'kaynak':          'HTML',
        'fatura_no':       fatura_no,
        'fatura_tarihi':   fatura_tarihi,
        'tedarikci_adi':   tedarikci_adi,
        'tedarikci_vkn':   tedarikci_vkn,
        'tedarikci_tckn':  tedarikci_tckn,
        'tedarikci_adres': tedarikci_adres,
        'kalemler':        kalemler,
        'ara_toplam':      round(ara_toplam, 2),
        'kdv_toplam':      round(kdv_toplam, 2),
        'genel_toplam':    round(genel_toplam, 2),
        'notlar':          '',
    }
