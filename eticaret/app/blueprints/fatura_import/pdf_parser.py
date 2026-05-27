"""
E-Arşiv Fatura PDF parser.
GIB standart e-arşiv faturalarını ve genel fatura PDF'lerini okur.
"""
import re

try:
    import pdfplumber
    _PDF_OK = True
except ImportError:
    _PDF_OK = False


def _tr_float(text):
    """Türkçe sayı formatını (1.234,56) float'a çevirir."""
    if not text:
        return 0.0
    text = text.strip().replace(' ', '')
    # 1.234,56 → 1234.56
    if ',' in text and '.' in text:
        text = text.replace('.', '').replace(',', '.')
    elif ',' in text:
        text = text.replace(',', '.')
    try:
        return float(text)
    except ValueError:
        return 0.0


def _bul(pattern, text, group=1, flags=re.IGNORECASE):
    m = re.search(pattern, text, flags)
    return m.group(group).strip() if m else ''


def _bul_fatura_no(text):
    patterns = [
        r'(?:Fatura\s+No|FATURA\s+NO|Invoice\s+No)[:\s]+([A-Z0-9]{3,}\d{4}\d{8})',
        r'(?:Fatura\s+No|FATURA\s+NO)[:\s]+([\w\-]+)',
        # GIB e-arşiv: seri+sıra numarası örn: EAR2024000000001 veya ABC 2024 000000001
        r'\b([A-Z]{3}\s*\d{4}\s*\d{9})\b',
        r'\b([A-Z]{2,3}\d{7,16})\b',
    ]
    for p in patterns:
        val = _bul(p, text)
        if val:
            return val.replace(' ', '')
    return ''


def _bul_tarih(text):
    # DD.MM.YYYY veya DD/MM/YYYY
    pattern = r'\b(\d{2}[./]\d{2}[./]\d{4})\b'
    m = re.search(pattern, text)
    if m:
        return m.group(1).replace('/', '.')
    return ''


def _bul_vkn(text):
    # VKN: 10 hane, TCKN: 11 hane
    patterns = [
        r'(?:V\.?K\.?N\.?|Vergi\s+No)[:\s]*(\d{10})',
        r'(?:T\.?C\.?K\.?N\.?|TC\s+No)[:\s]*(\d{11})',
    ]
    for p in patterns:
        val = _bul(p, text)
        if val:
            return val
    # VKN ara aramak
    m = re.search(r'\b(\d{10})\b', text)
    return m.group(1) if m else ''


def _bul_tckn(text):
    m = re.search(r'(?:T\.?C\.?K\.?N\.?|TC\s+No)[:\s]*(\d{11})', text, re.IGNORECASE)
    return m.group(1).strip() if m else ''


def _bul_unvan(text):
    patterns = [
        r'(?:Satıcı\s*(?:Ünvan[ıi]|Unvan[ıi]|Adı)|SATICI\s*ÜNVANI?)[:\s]+([^\n]{3,150})',
        r'(?:Firma\s+Adı|Şirket\s+(?:Adı|Ünvanı)|Unvan[ıi])[:\s]+([^\n]{3,150})',
        r'(?:Gönderen|Düzenleyen)[:\s]+([^\n]{3,150})',
        # GIB e-arşiv: satıcı tablosunda ilk büyük satır
        r'^([A-ZÇĞİÖŞÜa-zçğışöşü][\w\s\.&,\-]{10,120}(?:A\.Ş\.|LTD\.|LİMİTED|ANONİM|TİC\.|SAN\.).*)',
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE | re.MULTILINE)
        if m:
            val = m.group(1).strip()
            if val:
                return val[:200].split('\n')[0].strip()
    return ''


def _bul_tutar(text, pattern):
    m = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
    if m:
        return _tr_float(m.group(1))
    return 0.0


def _bul_adres(text):
    m = re.search(r'(?:Adres|ADDRESS)[:\s]+(.+?)(?:\n\n|\r\n\r\n|V\.?K\.?N|Tel)', text, re.IGNORECASE | re.DOTALL)
    if m:
        return ' '.join(m.group(1).split())[:300]
    return ''


def _parse_kalemler(text):
    """
    PDF'den kalem tablosunu çıkarmaya çalışır.
    GIB e-arşiv faturalarında tablo düzeni farklı olabilir.
    Basit satır-tabanlı regex kullanılır.
    """
    kalemler = []

    # Tablo bölümünü bul (Mal/Hizmet bölümü)
    tablo_match = re.search(
        r'(?:Mal\s+Hizmet\s+Ad[ıi]|Ürün\s+Ad[ıi]|Hizmet\s+Tan[ıi]m[ıi]).*?(?=Mal\s+Hizmet\s+Toplam[ıi]|Toplam\s+KDV|GENEL\s+TOPLAM)',
        text, re.IGNORECASE | re.DOTALL
    )
    tablo_text = tablo_match.group(0) if tablo_match else text

    # Her satırda: açıklama + miktar + birim + birim fiyat + KDV% + tutar
    # Örnek: "Yazılım Hizmeti 1 Adet 1.000,00 %18 1.180,00"
    satir_pattern = re.compile(
        r'^(.+?)\s+'               # açıklama
        r'(\d+(?:[.,]\d+)?)\s+'   # miktar
        r'(Adet|Kg|Lt|m²|m³|Metre|Saat|Gün|Set|Kutu|Paket|Parça)\s+'  # birim
        r'([\d.,]+)\s+'           # birim fiyat
        r'%?(\d+)\s+'             # KDV oranı
        r'([\d.,]+)',              # toplam
        re.IGNORECASE | re.MULTILINE
    )

    for m in satir_pattern.finditer(tablo_text):
        aciklama = m.group(1).strip()
        miktar = _tr_float(m.group(2))
        birim = m.group(3)
        birim_fiyat = _tr_float(m.group(4))
        kdv_orani = float(m.group(5))

        if aciklama and miktar > 0 and birim_fiyat > 0:
            kalemler.append({
                'aciklama': aciklama,
                'miktar': miktar,
                'birim': birim,
                'birim_fiyat': birim_fiyat,
                'kdv_orani': kdv_orani,
                'iskonto_orani': 0.0,
            })

    return kalemler


def _parse_kalemler_tablo(pdf):
    """pdfplumber tablo çıkarımı ile kalemleri bul."""
    kalemler = []
    for page in pdf.pages:
        tables = page.extract_tables()
        for table in tables:
            if not table or len(table) < 2:
                continue
            # Başlık satırını bul
            header = [str(c or '').lower().strip() for c in table[0]]
            header_str = ' '.join(header)
            if not any(k in header_str for k in ('miktar', 'adet', 'tutar', 'fiyat', 'hizmet', 'mal')):
                continue

            # Sütun indekslerini belirle
            def col_idx(*keywords):
                for kw in keywords:
                    for i, h in enumerate(header):
                        if kw in h:
                            return i
                return None

            aciklama_col = col_idx('mal', 'hizmet', 'ürün', 'açıklama', 'tanım', 'ad')
            miktar_col   = col_idx('miktar', 'adet', 'qty')
            birim_col    = col_idx('birim')
            fiyat_col    = col_idx('birim fiy', 'fiyat', 'price')
            kdv_col      = col_idx('kdv', 'vergi', 'tax')

            if aciklama_col is None or miktar_col is None or fiyat_col is None:
                continue

            for row in table[1:]:
                try:
                    aciklama    = str(row[aciklama_col] or '').strip()
                    miktar      = _tr_float(str(row[miktar_col] or '0'))
                    birim       = str(row[birim_col] or 'Adet').strip() if birim_col is not None else 'Adet'
                    birim_fiyat = _tr_float(str(row[fiyat_col] or '0'))
                    kdv_orani   = _tr_float(str(row[kdv_col] or '20').replace('%', '')) if kdv_col is not None else 20.0
                except (IndexError, TypeError):
                    continue
                if aciklama and miktar > 0 and birim_fiyat > 0:
                    kalemler.append({
                        'aciklama': aciklama,
                        'miktar': miktar,
                        'birim': birim or 'Adet',
                        'birim_fiyat': birim_fiyat,
                        'kdv_orani': kdv_orani or 20.0,
                        'iskonto_orani': 0.0,
                    })
    return kalemler


def parse_pdf(filepath):
    """
    E-Arşiv fatura PDF'ini okur, dict olarak döndürür.
    pdfplumber ile metin çıkarımı yapılır.
    """
    if not _PDF_OK:
        raise ImportError("pdfplumber yüklü değil. 'pip install pdfplumber' komutunu çalıştırın.")

    full_text = ''
    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            extracted = page.extract_text(x_tolerance=3, y_tolerance=3)
            if extracted:
                full_text += extracted + '\n'
        # Tablo tabanlı kalem çıkarımını önce dene
        kalemler_tablo = _parse_kalemler_tablo(pdf)

    fatura_no = _bul_fatura_no(full_text)
    fatura_tarihi = _bul_tarih(full_text)
    vkn = _bul_vkn(full_text)
    tckn = _bul_tckn(full_text)
    unvan = _bul_unvan(full_text)
    adres = _bul_adres(full_text)

    ara_toplam = _bul_tutar(full_text,
        r'(?:Mal\s*Hizmet\s*Toplam[ıi]|Matrah|Toplam\s*(?!KDV))[:\s]*([\d.,]+)')
    kdv_toplam = _bul_tutar(full_text,
        r'(?:Toplam\s*KDV|KDV\s*Tutarı)[:\s]*([\d.,]+)')
    genel_toplam = _bul_tutar(full_text,
        r'(?:Genel\s*Toplam|GENEL\s*TOPLAM|Ödenecek\s*Tutar|Vergiler\s*Dahil\s*Toplam)[:\s]*([\d.,]+)')

    if genel_toplam == 0 and ara_toplam > 0:
        genel_toplam = round(ara_toplam + kdv_toplam, 2)

    # Tablo çıkarımı başarısızsa regex ile dene
    kalemler = kalemler_tablo if kalemler_tablo else _parse_kalemler(full_text)

    # Kalem bulunamadıysa toplam tutardan tek satır oluştur
    if not kalemler and genel_toplam > 0:
        kdv_orani = 20
        if ara_toplam > 0 and kdv_toplam > 0:
            kdv_orani = round(kdv_toplam / ara_toplam * 100)
        kalemler = [{
            'aciklama': 'PDF\'den otomatik okunan kalem (düzenleme gerekebilir)',
            'miktar': 1,
            'birim': 'Adet',
            'birim_fiyat': round(ara_toplam, 2) if ara_toplam > 0 else round(genel_toplam / (1 + kdv_orani / 100), 2),
            'kdv_orani': kdv_orani,
            'iskonto_orani': 0.0,
        }]

    return {
        'kaynak': 'PDF',
        'fatura_no': fatura_no,
        'fatura_tarihi': fatura_tarihi,
        'tedarikci_adi': unvan,
        'tedarikci_vkn': vkn,
        'tedarikci_tckn': tckn,
        'tedarikci_adres': adres,
        'kalemler': kalemler,
        'ara_toplam': round(ara_toplam, 2),
        'kdv_toplam': round(kdv_toplam, 2),
        'genel_toplam': round(genel_toplam, 2),
        'notlar': '',
        'ham_metin': full_text[:3000],
    }
