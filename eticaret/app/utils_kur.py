"""TCMB döviz kuru çekme yardımcıları."""
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime


# today.xml → her zaman en son yayımlanan (= önceki iş günü) kurları döner
_TCMB_TODAY = 'https://www.tcmb.gov.tr/kurlar/today.xml'


def _fetch_xml(url, timeout=10):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return ET.parse(resp)


def tcmb_kur_cek():
    """
    TCMB today.xml'den USD ve EUR satış/alış kurlarını çeker.
    today.xml TCMB'nin en son yayımladığı iş günü verisidir (önceki iş günü).
    Döner: {'USD': {'alis': float, 'satis': float, 'tarih': date}, 'EUR': {...}}
    """
    try:
        tree = _fetch_xml(_TCMB_TODAY)
    except Exception as e:
        return {}

    root = tree.getroot()

    # XML kök attribute'undan tarihi oku: Date="05/22/2026"
    tarih_str = root.get('Date', '')
    try:
        tarih = datetime.strptime(tarih_str, '%m/%d/%Y').date()
    except ValueError:
        from datetime import date
        tarih = date.today()

    sonuc = {}
    for cur in root.findall('Currency'):
        kod = cur.get('CurrencyCode', '').upper()
        if kod not in ('USD', 'EUR'):
            continue
        try:
            unit = float(cur.findtext('Unit') or 1)
            alis_raw = cur.findtext('ForexBuying') or '0'
            satis_raw = cur.findtext('ForexSelling') or '0'
            alis = float(alis_raw) / unit
            satis = float(satis_raw) / unit
            if satis > 0:
                sonuc[kod] = {
                    'alis': round(alis, 4),
                    'satis': round(satis, 4),
                    'tarih': tarih,
                }
        except (ValueError, TypeError, ZeroDivisionError):
            continue

    return sonuc


def kur_guncelle_db():
    """
    TCMB'den kur çekip DB'ye kaydeder.
    Döner: {'USD': ..., 'EUR': ...} veya None (hata durumunda).
    """
    from app.extensions import db
    from app.models.doviz import DovizKur
    from datetime import datetime as dt

    kurlar = tcmb_kur_cek()
    if not kurlar:
        return None

    for kod, bilgi in kurlar.items():
        mevcut = DovizKur.query.filter_by(tarih=bilgi['tarih'], kod=kod).first()
        if mevcut:
            mevcut.alis = bilgi['alis']
            mevcut.satis = bilgi['satis']
            mevcut.guncelleme = dt.utcnow()
        else:
            db.session.add(DovizKur(
                tarih=bilgi['tarih'],
                kod=kod,
                alis=bilgi['alis'],
                satis=bilgi['satis'],
                guncelleme=dt.utcnow(),
            ))
    db.session.commit()
    return kurlar


def son_kurlar():
    """
    DB'deki en güncel USD ve EUR kurlarını döner.
    {'USD': {'satis': float, 'alis': float, 'tarih': date}, 'EUR': {...}}
    """
    from app.models.doviz import DovizKur

    sonuc = {}
    for kod in ('USD', 'EUR'):
        row = (DovizKur.query
               .filter_by(kod=kod)
               .order_by(DovizKur.tarih.desc())
               .first())
        if row:
            sonuc[kod] = {
                'satis': float(row.satis),
                'alis': float(row.alis),
                'tarih': row.tarih,
            }
    return sonuc
