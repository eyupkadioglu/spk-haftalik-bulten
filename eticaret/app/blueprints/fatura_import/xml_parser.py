"""
E-Fatura UBL-TR XML parser (GIB standart formatı, UBL-TR 1.2.1).

GIB e-Fatura XML'inde tedarikçi kimlik numarası iki farklı yerde olabilir:
  1. cac:PartyIdentification/cbc:ID[@schemeID='VKN'] — birincil yol
  2. cac:PartyTaxScheme/cbc:CompanyID               — ikincil yol (bazı yazılımlar)
"""
import xml.etree.ElementTree as ET


# GIB UBL-TR namespace haritası
_NS = {
    'ubl':  'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2',
    'cac':  'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
    'cbc':  'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
    'ext':  'urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2',
    'ds':   'http://www.w3.org/2000/09/xmldsig#',
    'xsi':  'http://www.w3.org/2001/XMLSchema-instance',
}

# UBL birim kodları → Türkçe
_BIRIM_MAP = {
    'C62': 'Adet', 'NIU': 'Adet', 'EA':  'Adet',
    'KGM': 'Kg',   'GRM': 'Gram', 'TNE': 'Ton',
    'MTR': 'Metre','MTK': 'm²',   'MTQ': 'm³',
    'LTR': 'Litre','MLT': 'mL',
    'HUR': 'Saat', 'DAY': 'Gün',  'MON': 'Ay',  'ANN': 'Yıl',
    'SET': 'Set',  'BOX': 'Kutu', 'PCE': 'Parça','PKG': 'Paket',
    'BO':  'Şişe', 'PR':  'Çift', 'ROL': 'Rulo',
}


def _txt(el, path, ns=_NS):
    """XPath path altındaki ilk eşleşmenin text değerini döner."""
    if el is None:
        return ''
    found = el.find(path, ns)
    if found is not None and found.text:
        return found.text.strip()
    return ''


def _txts(el, path, ns=_NS):
    """Çoklu elementlerin text değerlerini liste olarak döner."""
    if el is None:
        return []
    return [e.text.strip() for e in el.findall(path, ns) if e.text and e.text.strip()]


def _float(val):
    try:
        return float(str(val).replace(',', '.').strip())
    except (ValueError, TypeError):
        return 0.0


def _fmt_tarih(iso_str):
    """YYYY-MM-DD → DD.MM.YYYY"""
    if not iso_str:
        return ''
    s = iso_str.strip()
    if '-' in s:
        parts = s.split('-')
        if len(parts) == 3 and len(parts[0]) == 4:
            return f'{parts[2]}.{parts[1]}.{parts[0]}'
    return s


def _get_vkn_tckn(party, ns=_NS):
    """
    Tedarikçi partisinden VKN ve TCKN bilgisini çeker.
    Birincil kaynak: cac:PartyIdentification/cbc:ID[@schemeID='VKN']
    İkincil kaynak:  cac:PartyTaxScheme/cbc:CompanyID (uzunlukla ayrım)
    """
    vkn  = ''
    tckn = ''

    # 1. PartyIdentification (GIB standart birincil yol)
    for pid in party.findall('cac:PartyIdentification', ns):
        id_el = pid.find('cbc:ID', ns)
        if id_el is None or not id_el.text:
            continue
        val     = id_el.text.strip()
        scheme  = (id_el.get('schemeID') or '').upper()
        if scheme == 'VKN' or (not scheme and len(val) == 10):
            vkn = val
        elif scheme == 'TCKN' or (not scheme and len(val) == 11):
            tckn = val

    # 2. PartyTaxScheme/CompanyID (ikincil yol, bazı entegratörler)
    if not vkn and not tckn:
        for pts in party.findall('cac:PartyTaxScheme', ns):
            compid = _txt(pts, 'cbc:CompanyID', ns)
            if not compid:
                continue
            if len(compid) == 10 and not vkn:
                vkn = compid
            elif len(compid) == 11 and not tckn:
                tckn = compid

    return vkn, tckn


def _get_party_name(party, ns=_NS):
    """Tedarikçi/alıcı unvanını en güvenilir yerden alır."""
    return (
        _txt(party, 'cac:PartyName/cbc:Name', ns)
        or _txt(party, 'cac:PartyLegalEntity/cbc:RegistrationName', ns)
        or _txt(party, 'cac:Person/cbc:FirstName', ns)
    )


def _get_adres(party, ns=_NS):
    """PostalAddress bloğundan okunabilir adres metni üretir."""
    addr = party.find('cac:PostalAddress', ns)
    if addr is None:
        return ''
    parts = [
        _txt(addr, 'cbc:StreetName', ns),
        _txt(addr, 'cbc:BuildingNumber', ns),
        _txt(addr, 'cbc:CitySubdivisionName', ns),
        _txt(addr, 'cbc:CityName', ns),
        _txt(addr, 'cbc:PostalZone', ns),
        _txt(addr, 'cac:Country/cbc:Name', ns),
    ]
    return ' '.join(p for p in parts if p).strip()


def parse_xml(filepath):
    """
    GIB e-Fatura UBL-TR XML dosyasını okur, dict olarak döndürür.
    Dönen dict fatura_import/routes.py'deki kaydet() ile uyumludur.
    """
    tree = ET.parse(filepath)
    root = tree.getroot()

    # Fatura temel bilgileri
    fatura_no        = _txt(root, 'cbc:ID').replace(' ', '')   # bazı dosyalarda boşluklu
    fatura_tarihi    = _fmt_tarih(_txt(root, 'cbc:IssueDate'))
    fatura_tipi_kodu = _txt(root, 'cbc:InvoiceTypeCode')       # SATISINVOICE vs.
    para_birimi      = _txt(root, 'cbc:DocumentCurrencyCode') or 'TRY'

    # Notlar (birden fazla cbc:Note olabilir)
    notlar = ' | '.join(_txts(root, 'cbc:Note'))

    # --- Tedarikçi (AccountingSupplierParty) ---
    supplier_party   = root.find('.//cac:AccountingSupplierParty/cac:Party')
    tedarikci_adi    = ''
    tedarikci_vkn    = ''
    tedarikci_tckn   = ''
    tedarikci_vd     = ''
    tedarikci_adres  = ''

    if supplier_party is not None:
        tedarikci_adi   = _get_party_name(supplier_party)
        tedarikci_vkn, tedarikci_tckn = _get_vkn_tckn(supplier_party)
        # Vergi dairesi: TaxScheme/Name
        tedarikci_vd    = (
            _txt(supplier_party, 'cac:PartyTaxScheme/cac:TaxScheme/cbc:Name')
            or _txt(supplier_party, 'cac:PartyTaxScheme/cac:TaxScheme/cbc:TaxTypeCode')
        )
        tedarikci_adres = _get_adres(supplier_party)

    # --- Kalemler ---
    kalemler = []
    for line in root.findall('.//cac:InvoiceLine'):
        miktar_el  = line.find('cbc:InvoicedQuantity')
        miktar     = _float(miktar_el.text) if miktar_el is not None and miktar_el.text else 1.0
        birim_kod  = (miktar_el.get('unitCode') or 'C62') if miktar_el is not None else 'C62'
        birim      = _BIRIM_MAP.get(birim_kod.upper(), birim_kod)

        # Ürün adı/açıklaması (öncelik sırasına göre)
        aciklama = (
            _txt(line, 'cac:Item/cbc:Name')
            or _txt(line, 'cac:Item/cbc:Description')
            or _txt(line, 'cac:Item/cac:SellersItemIdentification/cbc:ID')
            or _txt(line, 'cac:Item/cac:BuyersItemIdentification/cbc:ID')
            or ''
        )

        # Birim fiyat (KDV hariç)
        birim_fiyat = _float(_txt(line, 'cac:Price/cbc:PriceAmount'))

        # Satır net tutarı (KDV hariç, iskonto sonrası)
        line_ext = _float(_txt(line, 'cbc:LineExtensionAmount'))

        # KDV oranı — InvoiceLine içindeki TaxTotal'dan al
        kdv_orani = 0.0
        kdv_pct   = line.find('.//cac:TaxTotal/cac:TaxSubtotal/cac:TaxCategory/cbc:Percent')
        if kdv_pct is not None and kdv_pct.text:
            kdv_orani = _float(kdv_pct.text)
        else:
            # Fallback: TaxTotal/TaxSubtotal/TaxCategory/cbc:ID = "0015" → KDV
            kdv_orani = 20.0

        # İskonto oranı — AllowanceCharge[ChargeIndicator=false]
        iskonto_orani = 0.0
        for ac in line.findall('cac:AllowanceCharge'):
            charge_ind = _txt(ac, 'cbc:ChargeIndicator')
            if charge_ind.lower() == 'false':
                # MultiplierFactorNumeric varsa oranı buradan al
                mult = ac.find('cbc:MultiplierFactorNumeric')
                if mult is not None and mult.text:
                    iskonto_orani = _float(mult.text) * 100
                else:
                    # Oran yoksa Amount/BaseAmount'tan hesapla
                    amount   = _float(_txt(ac, 'cbc:Amount'))
                    base_amt = _float(_txt(ac, 'cbc:BaseAmount'))
                    if base_amt > 0:
                        iskonto_orani = round(amount / base_amt * 100, 2)

        # birim_fiyat 0 ise line_ext ve miktardan hesapla
        if birim_fiyat == 0 and miktar > 0 and line_ext > 0:
            iskonto_carpan = 1 - iskonto_orani / 100
            if iskonto_carpan > 0:
                birim_fiyat = round(line_ext / miktar / iskonto_carpan, 4)

        if aciklama or miktar > 0:
            kalemler.append({
                'aciklama':      aciklama,
                'miktar':        miktar,
                'birim':         birim,
                'birim_fiyat':   birim_fiyat,
                'kdv_orani':     kdv_orani,
                'iskonto_orani': iskonto_orani,
                'line_ext':      line_ext,
            })

    # --- Toplamlar (LegalMonetaryTotal) ---
    monetary      = root.find('.//cac:LegalMonetaryTotal')
    ara_toplam    = _float(_txt(monetary, 'cbc:TaxExclusiveAmount'))  if monetary is not None else 0.0
    genel_toplam  = _float(_txt(monetary, 'cbc:PayableAmount'))       if monetary is not None else 0.0

    # Fallback: TaxInclusiveAmount (ödenecek tutar)
    if genel_toplam == 0 and monetary is not None:
        genel_toplam = _float(_txt(monetary, 'cbc:TaxInclusiveAmount'))

    # KDV: TaxTotal/TaxAmount (fatura düzeyinde)
    kdv_el     = root.find('.//cac:TaxTotal/cbc:TaxAmount')
    kdv_toplam = _float(kdv_el.text) if kdv_el is not None and kdv_el.text else round(genel_toplam - ara_toplam, 2)

    # ara_toplam 0 ise kalemlerden hesapla
    if ara_toplam == 0 and kalemler:
        ara_toplam = round(sum(k['line_ext'] for k in kalemler), 2)

    return {
        'kaynak':           'XML',
        'fatura_no':        fatura_no,
        'fatura_tarihi':    fatura_tarihi,
        'fatura_tipi_kodu': fatura_tipi_kodu,
        'para_birimi':      para_birimi,
        'tedarikci_adi':    tedarikci_adi,
        'tedarikci_vkn':    tedarikci_vkn,
        'tedarikci_tckn':   tedarikci_tckn,
        'tedarikci_vd':     tedarikci_vd,
        'tedarikci_adres':  tedarikci_adres,
        'kalemler':         kalemler,
        'ara_toplam':       round(ara_toplam, 2),
        'kdv_toplam':       round(kdv_toplam, 2),
        'genel_toplam':     round(genel_toplam, 2),
        'notlar':           notlar,
    }
