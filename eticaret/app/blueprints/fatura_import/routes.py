import os
from datetime import datetime

from flask import Blueprint, render_template, request, jsonify, url_for, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models.fatura import Fatura, FaturaKalem
from app.models.stok import Stok
from app.models.cari import Cari
from app.utils import next_sequence

bp = Blueprint('fatura_import', __name__)

_ALLOWED = {'pdf', 'xml', 'html', 'htm'}


def _ext(filename):
    return filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''


@bp.route('/')
@login_required
def index():
    return render_template('fatura_import/index.html')


@bp.route('/stok-ara')
@login_required
def stok_ara():
    """Stok adı / kodu / barkod ile arama — JSON liste döner."""
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify([])
    stoklar = Stok.query.filter(
        Stok.is_active == True,
        db.or_(
            Stok.ad.ilike(f'%{q}%'),
            Stok.stok_kodu.ilike(f'%{q}%'),
            Stok.barkod.ilike(f'%{q}%'),
            Stok.tedarikci_kodu.ilike(f'%{q}%'),
        )
    ).order_by(Stok.ad).limit(20).all()
    return jsonify([{
        'id':           s.id,
        'stok_kodu':    s.stok_kodu,
        'ad':           s.ad,
        'birim':        s.birim,
        'stok_miktari': float(s.stok_miktari or 0),
        'alis_fiyati':  float(s.alis_fiyati or 0),
        'kdv_orani':    float(s.alis_kdv_orani or s.kdv_orani or 20),
    } for s in stoklar])


@bp.route('/debug', methods=['POST'])
@login_required
def debug():
    """Dosyayı parse edip ham sonucu JSON olarak döner (geliştirme için)."""
    if 'dosya' not in request.files:
        return jsonify({'hata': 'Dosya seçilmedi'}), 400
    dosya = request.files['dosya']
    ext = _ext(dosya.filename)
    if ext not in _ALLOWED:
        return jsonify({'hata': 'Desteklenmeyen format'}), 400
    import tempfile, os as _os
    with tempfile.NamedTemporaryFile(delete=False, suffix='.' + ext) as tmp:
        dosya.save(tmp.name)
        try:
            if ext == 'pdf':
                from .pdf_parser import parse_pdf
                sonuc = parse_pdf(tmp.name)
            elif ext == 'xml':
                from .xml_parser import parse_xml
                sonuc = parse_xml(tmp.name)
            else:
                from .html_parser import parse_html
                sonuc = parse_html(tmp.name)
        finally:
            _os.unlink(tmp.name)
    return jsonify(sonuc)


@bp.route('/isle', methods=['POST'])
@login_required
def isle():
    """Yüklenen PDF, XML veya HTML dosyasını parse edip JSON döner."""
    if 'dosya' not in request.files:
        return jsonify({'hata': 'Dosya seçilmedi'}), 400

    dosya = request.files['dosya']
    if not dosya.filename:
        return jsonify({'hata': 'Dosya seçilmedi'}), 400

    ext = _ext(dosya.filename)
    if ext not in _ALLOWED:
        return jsonify({'hata': 'Sadece PDF, XML veya HTML dosyası desteklenmektedir'}), 400

    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'fatura_import')
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, secure_filename(dosya.filename))
    dosya.save(filepath)

    try:
        if ext == 'pdf':
            from .pdf_parser import parse_pdf
            sonuc = parse_pdf(filepath)
        elif ext == 'xml':
            from .xml_parser import parse_xml
            sonuc = parse_xml(filepath)
        else:
            from .html_parser import parse_html
            sonuc = parse_html(filepath)
        return jsonify(sonuc)
    except Exception as e:
        return jsonify({'hata': str(e)}), 500


@bp.route('/kaydet', methods=['POST'])
@login_required
def kaydet():
    """Önizlemeden onaylanan faturayı veritabanına kaydeder."""
    data = request.get_json(force=True)
    if not data:
        return jsonify({'hata': 'Veri bulunamadı'}), 400

    try:
        # --- Cariyi bul veya oluştur ---
        cari = None
        vkn   = (data.get('tedarikci_vkn') or '').strip()
        unvan = (data.get('tedarikci_adi') or '').strip()

        if vkn:
            cari = Cari.query.filter_by(vergi_no=vkn).first()
        if not cari and unvan:
            cari = Cari.query.filter(Cari.unvan.ilike(f'%{unvan}%')).first()

        if not cari:
            cari_kodu = next_sequence('TED', Cari, 'cari_kodu')
            cari = Cari(
                cari_kodu=cari_kodu,
                unvan=unvan or 'Bilinmeyen Tedarikçi',
                cari_tipi='tedarikci',
                vergi_no=vkn or None,
                adres=data.get('tedarikci_adres') or None,
            )
            db.session.add(cari)
            db.session.flush()

        # --- Tarih ---
        tarih_str = (data.get('fatura_tarihi') or '').strip()
        try:
            if '.' in tarih_str:
                fatura_tarihi = datetime.strptime(tarih_str, '%d.%m.%Y').date()
            elif '-' in tarih_str:
                fatura_tarihi = datetime.strptime(tarih_str, '%Y-%m-%d').date()
            else:
                fatura_tarihi = datetime.now().date()
        except ValueError:
            fatura_tarihi = datetime.now().date()

        # --- Fatura no ---
        fatura_no = (data.get('fatura_no') or '').strip()
        if not fatura_no or Fatura.query.filter_by(fatura_no=fatura_no).first():
            fatura_no = next_sequence('AF', Fatura, 'fatura_no')

        fatura = Fatura(
            fatura_no=fatura_no,
            fatura_tipi='alis',
            cari_id=cari.id,
            fatura_tarihi=fatura_tarihi,
            durum='taslak',
            notlar=data.get('notlar') or '',
            created_by=current_user.id,
        )

        ara_toplam = 0.0
        kdv_toplam = 0.0

        for i, k in enumerate(data.get('kalemler') or []):
            miktar      = float(k.get('miktar') or 1)
            birim_fiyat = float(k.get('birim_fiyat') or 0)
            kdv_orani   = float(k.get('kdv_orani') or 20)
            iskonto     = float(k.get('iskonto_orani') or 0)

            net    = round(miktar * birim_fiyat * (1 - iskonto / 100), 4)
            kdv    = round(net * kdv_orani / 100, 2)
            toplam = round(net + kdv, 2)

            # Stok eşleştirme
            stok_id_raw = k.get('stok_id')
            stok_id = int(stok_id_raw) if stok_id_raw else None

            if stok_id:
                stok = Stok.query.get(stok_id)
                if stok:
                    # Son alış fiyatı ve KDV oranını güncelle
                    stok.alis_fiyati    = birim_fiyat
                    stok.alis_kdv_orani = kdv_orani

            fatura.kalemler.append(FaturaKalem(
                stok_id=stok_id,
                aciklama=k.get('aciklama') or '',
                miktar=miktar,
                birim=k.get('birim') or 'Adet',
                birim_fiyat=birim_fiyat,
                iskonto_orani=iskonto,
                kdv_orani=kdv_orani,
                kdv_tutari=kdv,
                toplam_tutar=toplam,
                sira=i,
            ))
            ara_toplam += net
            kdv_toplam += kdv

        fatura.ara_toplam   = round(ara_toplam, 2)
        fatura.kdv_toplam   = round(kdv_toplam, 2)
        fatura.genel_toplam = round(ara_toplam + kdv_toplam, 2)
        fatura.kalan_tutar  = fatura.genel_toplam

        db.session.add(fatura)
        db.session.commit()

        eslesme_sayisi = sum(1 for k in (data.get('kalemler') or []) if k.get('stok_id'))

        return jsonify({
            'basarili':       True,
            'fatura_id':      fatura.id,
            'fatura_no':      fatura.fatura_no,
            'eslesme_sayisi': eslesme_sayisi,
            'redirect':       url_for('fatura.detail', id=fatura.id),
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'hata': str(e)}), 500
