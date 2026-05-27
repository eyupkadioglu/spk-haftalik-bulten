import os
import uuid
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models.stok import Stok, StokKategori, StokHareket
from app.models.cari import Cari
from app.models.fatura import Fatura, FaturaKalem
from app.models.siparis import Siparis, SiparisKalem
from app.models.teklif import Teklif, TeklifKalem
from app.utils import next_sequence

bp = Blueprint('stok', __name__)


def _kaydet_resim(dosya):
    if not dosya or dosya.filename == '':
        return None
    ext = os.path.splitext(dosya.filename)[1].lower()
    izinli = current_app.config.get('UPLOAD_EXTENSIONS', {'.jpg', '.jpeg', '.png', '.gif', '.webp'})
    if ext not in izinli:
        return None
    klasor = os.path.join(current_app.root_path, 'static', 'uploads', 'stok')
    os.makedirs(klasor, exist_ok=True)
    dosya_adi = f"{uuid.uuid4().hex}{ext}"
    dosya.save(os.path.join(klasor, dosya_adi))
    return f"uploads/stok/{dosya_adi}"


def _kaydet_resim_url(url):
    """Downloads image from URL, saves locally, returns relative path or None."""
    if not url or not url.startswith(('http://', 'https://')):
        return None
    try:
        import urllib.request
        import urllib.parse
        # Determine extension from URL path
        parsed_path = urllib.parse.urlparse(url).path
        ext = os.path.splitext(parsed_path)[1].lower().split('?')[0]
        izinli = current_app.config.get('UPLOAD_EXTENSIONS', {'.jpg', '.jpeg', '.png', '.gif', '.webp'})
        if ext not in izinli:
            ext = '.jpg'  # fallback
        klasor = os.path.join(current_app.root_path, 'static', 'uploads', 'stok')
        os.makedirs(klasor, exist_ok=True)
        dosya_adi = f"{uuid.uuid4().hex}{ext}"
        tam_yol = os.path.join(klasor, dosya_adi)
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            content_type = resp.headers.get('Content-Type', '')
            # Detect extension from Content-Type if not in URL
            if ext not in izinli:
                ct_map = {'image/jpeg': '.jpg', 'image/png': '.png',
                          'image/gif': '.gif', 'image/webp': '.webp'}
                ext = ct_map.get(content_type.split(';')[0].strip(), '.jpg')
                dosya_adi = f"{uuid.uuid4().hex}{ext}"
                tam_yol = os.path.join(klasor, dosya_adi)
            with open(tam_yol, 'wb') as f:
                f.write(resp.read(5 * 1024 * 1024))  # max 5MB
        return f"uploads/stok/{dosya_adi}"
    except Exception:
        return None


def _sil_resim(resim_yolu):
    if not resim_yolu:
        return
    tam_yol = os.path.join(current_app.root_path, 'static', resim_yolu)
    if os.path.exists(tam_yol):
        os.remove(tam_yol)


def _stok_from_form(stok=None):
    """Form verilerinden stok nesnesini doldurur. Yeni nesne için stok=None."""
    yeni = stok is None
    if yeni:
        stok = Stok(
            stok_kodu=request.form.get('stok_kodu') or next_sequence('STK', Stok, 'stok_kodu'),
        )

    stok.ad = request.form['ad']
    stok.barkod = request.form.get('barkod') or None
    stok.urun_tipi = request.form.get('urun_tipi', 'stok')
    stok.kategori_id = request.form.get('kategori_id', type=int)
    stok.marka = request.form.get('marka') or None
    stok.tedarikci_id = request.form.get('tedarikci_id', type=int) or None
    stok.tedarikci_kodu = request.form.get('tedarikci_kodu') or None
    stok.birim = request.form.get('birim', 'Adet')
    stok.alis_fiyati = request.form.get('alis_fiyati') or 0
    stok.satis_fiyati = request.form.get('satis_fiyati') or 0
    stok.kdv_orani = request.form.get('satis_kdv_orani') or 20       # kdv_orani = satış KDV
    stok.alis_kdv_orani = request.form.get('alis_kdv_orani') or 20
    stok.alis_para_birimi = request.form.get('alis_para_birimi', 'TRY')
    stok.satis_para_birimi = request.form.get('satis_para_birimi', 'TRY')
    stok.min_stok = request.form.get('min_stok') or 0
    stok.max_stok = request.form.get('max_stok') or 0
    stok.aciklama = request.form.get('aciklama')

    # Resim — önce silme, sonra dosya, sonra URL
    if request.form.get('resim_sil') == '1':
        _sil_resim(stok.resim)
        stok.resim = None
    yeni_resim = _kaydet_resim(request.files.get('resim'))
    if not yeni_resim:
        resim_url = request.form.get('resim_url', '').strip()
        if resim_url:
            yeni_resim = _kaydet_resim_url(resim_url)
    if yeni_resim:
        _sil_resim(stok.resim)
        stok.resim = yeni_resim

    return stok, yeni


@bp.route('/')
@login_required
def index():
    q = request.args.get('q', '').strip()
    kategori_id = request.args.get('kategori_id', type=int)
    dusuk = request.args.get('dusuk', '')
    urun_tipi = request.args.get('urun_tipi', '')
    query = Stok.query.filter_by(is_active=True)
    if q:
        query = query.filter(
            db.or_(Stok.ad.ilike(f'%{q}%'), Stok.stok_kodu.ilike(f'%{q}%'),
                   Stok.barkod.ilike(f'%{q}%'), Stok.marka.ilike(f'%{q}%'))
        )
    if kategori_id:
        query = query.filter_by(kategori_id=kategori_id)
    if dusuk:
        query = query.filter(Stok.stok_miktari <= Stok.min_stok)
    if urun_tipi:
        query = query.filter_by(urun_tipi=urun_tipi)
    stoklar = query.order_by(Stok.ad).all()
    kategoriler = StokKategori.query.order_by(StokKategori.ad).all()
    return render_template('stok/index.html', stoklar=stoklar, kategoriler=kategoriler,
                           q=q, kategori_id=kategori_id, dusuk=dusuk, urun_tipi=urun_tipi)


@bp.route('/<int:id>')
@login_required
def detail(id):
    stok = Stok.query.get_or_404(id)
    hareketler = stok.hareketler.order_by(StokHareket.tarih.desc()).limit(30).all()
    _fq = (FaturaKalem.query
        .filter(FaturaKalem.stok_id == id)
        .join(Fatura, FaturaKalem.fatura_id == Fatura.id))
    alis_fatura_kalemleri = (_fq.filter(Fatura.fatura_tipi == 'alis')
        .order_by(Fatura.fatura_tarihi.desc()).limit(30).all())
    satis_fatura_kalemleri = (_fq.filter(Fatura.fatura_tipi == 'satis')
        .order_by(Fatura.fatura_tarihi.desc()).limit(30).all())
    siparis_kalemleri = (SiparisKalem.query
        .filter(SiparisKalem.stok_id == id)
        .join(Siparis, SiparisKalem.siparis_id == Siparis.id)
        .order_by(Siparis.siparis_tarihi.desc())
        .limit(30).all())
    teklif_kalemleri = (TeklifKalem.query
        .filter(TeklifKalem.stok_id == id)
        .join(Teklif, TeklifKalem.teklif_id == Teklif.id)
        .order_by(Teklif.teklif_tarihi.desc())
        .limit(30).all())
    return render_template('stok/detail.html', stok=stok, hareketler=hareketler,
                           alis_fatura_kalemleri=alis_fatura_kalemleri,
                           satis_fatura_kalemleri=satis_fatura_kalemleri,
                           siparis_kalemleri=siparis_kalemleri,
                           teklif_kalemleri=teklif_kalemleri)


@bp.route('/yeni', methods=['GET', 'POST'])
@login_required
def yeni():
    if request.method == 'POST':
        stok, _ = _stok_from_form(None)
        db.session.add(stok)
        db.session.flush()
        acilis = request.form.get('acilis_miktar', type=float)
        if acilis and acilis > 0 and stok.urun_tipi == 'stok':
            db.session.add(StokHareket(
                stok_id=stok.id,
                hareket_tipi='giris',
                miktar=acilis,
                birim_fiyat=stok.alis_fiyati,
                toplam_tutar=float(stok.alis_fiyati or 0) * acilis,
                aciklama='Açılış stoku',
                user_id=current_user.id,
            ))
            stok.stok_miktari = acilis
        db.session.commit()
        flash(f'"{stok.ad}" oluşturuldu.', 'success')
        return redirect(url_for('stok.detail', id=stok.id))
    kategoriler = StokKategori.query.order_by(StokKategori.ad).all()
    tedarikciler = Cari.query.filter(
        db.or_(Cari.cari_tipi == 'tedarikci', Cari.cari_tipi == 'her_ikisi')
    ).filter_by(is_active=True).order_by(Cari.unvan).all()
    return render_template('stok/form.html', stok=None, kategoriler=kategoriler,
                           tedarikciler=tedarikciler)


@bp.route('/<int:id>/duzenle', methods=['GET', 'POST'])
@login_required
def duzenle(id):
    stok = Stok.query.get_or_404(id)
    if request.method == 'POST':
        _stok_from_form(stok)
        db.session.commit()
        flash('Stok güncellendi.', 'success')
        return redirect(url_for('stok.detail', id=stok.id))
    kategoriler = StokKategori.query.order_by(StokKategori.ad).all()
    tedarikciler = Cari.query.filter(
        db.or_(Cari.cari_tipi == 'tedarikci', Cari.cari_tipi == 'her_ikisi')
    ).filter_by(is_active=True).order_by(Cari.unvan).all()
    return render_template('stok/form.html', stok=stok, kategoriler=kategoriler,
                           tedarikciler=tedarikciler)


@bp.route('/<int:id>/sil', methods=['POST'])
@login_required
def sil(id):
    stok = Stok.query.get_or_404(id)
    stok.is_active = False
    db.session.commit()
    flash(f'"{stok.ad}" silindi.', 'warning')
    return redirect(url_for('stok.index'))


@bp.route('/toplu-sil', methods=['POST'])
@login_required
def toplu_sil():
    ids = request.form.getlist('ids')
    if not ids:
        flash('Hiç ürün seçilmedi.', 'warning')
        return redirect(url_for('stok.index'))
    count = Stok.query.filter(Stok.id.in_(ids)).update({'is_active': False}, synchronize_session=False)
    db.session.commit()
    flash(f'{count} ürün silindi.', 'warning')
    return redirect(url_for('stok.index'))


@bp.route('/transfer', methods=['GET', 'POST'])
@login_required
def transfer():
    if request.method == 'POST':
        tip = request.form.get('tip')
        aciklama_ek = request.form.get('aciklama', '').strip()
        ref_no = f"TRF-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        try:
            if tip == 'virman':
                kaynak_id = request.form.get('kaynak_id', type=int)
                hedef_id  = request.form.get('hedef_id', type=int)
                k_miktar  = float(request.form.get('kaynak_miktar') or 0)
                h_miktar  = float(request.form.get('hedef_miktar') or 0)
                k_fiyat   = float(request.form.get('kaynak_fiyat') or 0)
                h_fiyat   = float(request.form.get('hedef_fiyat') or 0)

                if not all([kaynak_id, hedef_id]) or k_miktar <= 0 or h_miktar <= 0:
                    flash('Tüm alanları eksiksiz doldurun.', 'danger')
                    return redirect(url_for('stok.transfer'))

                k_toplam = round(k_miktar * k_fiyat, 2)
                h_toplam = round(h_miktar * h_fiyat, 2)
                if abs(k_toplam - h_toplam) > 0.02:
                    flash(f'Toplam tutarlar eşit değil: Kaynak {k_toplam:.2f} ≠ Hedef {h_toplam:.2f}', 'danger')
                    return redirect(url_for('stok.transfer'))

                kaynak = Stok.query.get_or_404(kaynak_id)
                hedef  = Stok.query.get_or_404(hedef_id)
                aciklama = f"{ref_no} | Virman: {kaynak.ad} → {hedef.ad}" + (f" | {aciklama_ek}" if aciklama_ek else "")

                db.session.add(StokHareket(stok_id=kaynak_id,
                    hareket_tipi='virman_cikis', miktar=k_miktar,
                    birim_fiyat=k_fiyat, toplam_tutar=k_toplam,
                    aciklama=aciklama, user_id=current_user.id))
                kaynak.stok_miktari = float(kaynak.stok_miktari or 0) - k_miktar

                hedef.guncelle_ortalama_maliyet(h_miktar, h_fiyat)
                db.session.add(StokHareket(stok_id=hedef_id,
                    hareket_tipi='virman_giris', miktar=h_miktar,
                    birim_fiyat=h_fiyat, toplam_tutar=h_toplam,
                    aciklama=aciklama, user_id=current_user.id))
                hedef.stok_miktari = float(hedef.stok_miktari or 0) + h_miktar

                db.session.commit()
                flash(f'Virman tamamlandı ({ref_no}): {kaynak.ad} → {hedef.ad}', 'success')

            elif tip == 'parcalama':
                # 1 kaynak → N hedef (birleştirmenin tersi)
                kaynak_id    = request.form.get('kaynak_id', type=int)
                k_miktar     = float(request.form.get('kaynak_miktar') or 0)
                k_fiyat      = float(request.form.get('kaynak_fiyat') or 0)
                hedef_ids    = request.form.getlist('hedef_ids')
                hedef_miktar = request.form.getlist('hedef_miktarlar')
                hedef_fiyat  = request.form.getlist('hedef_fiyatlar')

                if not kaynak_id or k_miktar <= 0:
                    flash('Kaynak stok ve miktar gereklidir.', 'danger')
                    return redirect(url_for('stok.transfer'))

                kaynak = Stok.query.get_or_404(kaynak_id)
                k_toplam = round(k_miktar * k_fiyat, 2)
                aciklama = f"{ref_no} | Parçalama: {kaynak.ad}" + (f" | {aciklama_ek}" if aciklama_ek else "")

                toplam_hedef = 0.0
                satirlar = [(int(hid), float(hm or 0), float(hf or 0))
                            for hid, hm, hf in zip(hedef_ids, hedef_miktar, hedef_fiyat)
                            if float(hm or 0) > 0]

                if not satirlar:
                    flash('En az bir hedef satır gereklidir.', 'danger')
                    return redirect(url_for('stok.transfer'))

                for hid, hm, hf in satirlar:
                    toplam_hedef += round(hm * hf, 2)

                if abs(k_toplam - toplam_hedef) > 0.02:
                    flash(f'Toplam tutarlar eşit değil: Kaynak {k_toplam:.2f} ≠ Hedefler {toplam_hedef:.2f}', 'danger')
                    return redirect(url_for('stok.transfer'))

                db.session.add(StokHareket(stok_id=kaynak_id,
                    hareket_tipi='parcalama_cikis', miktar=k_miktar,
                    birim_fiyat=k_fiyat, toplam_tutar=k_toplam,
                    aciklama=aciklama, user_id=current_user.id))
                kaynak.stok_miktari = float(kaynak.stok_miktari or 0) - k_miktar

                for hid, hm, hf in satirlar:
                    hedef = Stok.query.get_or_404(hid)
                    h_toplam = round(hm * hf, 2)
                    hedef.guncelle_ortalama_maliyet(hm, hf)
                    db.session.add(StokHareket(stok_id=hid,
                        hareket_tipi='parcalama_giris', miktar=hm,
                        birim_fiyat=hf, toplam_tutar=h_toplam,
                        aciklama=aciklama, user_id=current_user.id))
                    hedef.stok_miktari = float(hedef.stok_miktari or 0) + hm

                db.session.commit()
                flash(f'Parçalama tamamlandı ({ref_no}): {kaynak.ad} → {len(satirlar)} ürün', 'success')

            elif tip == 'birlestirme':
                kaynak_ids     = request.form.getlist('kaynak_ids')
                kaynak_miktar  = request.form.getlist('kaynak_miktarlar')
                kaynak_fiyat   = request.form.getlist('kaynak_fiyatlar')
                hedef_id       = request.form.get('hedef_id', type=int)
                h_miktar       = float(request.form.get('hedef_miktar') or 0)
                h_fiyat        = float(request.form.get('hedef_fiyat') or 0)

                if not hedef_id or h_miktar <= 0:
                    flash('Hedef stok ve miktar gereklidir.', 'danger')
                    return redirect(url_for('stok.transfer'))

                hedef = Stok.query.get_or_404(hedef_id)
                toplam_kaynak = 0.0
                kaynak_satirlari = list(zip(kaynak_ids, kaynak_miktar, kaynak_fiyat))

                for kid, km, kf in kaynak_satirlari:
                    km = float(km or 0)
                    kf = float(kf or 0)
                    if km <= 0:
                        continue
                    kaynak = Stok.query.get_or_404(int(kid))
                    toplam = round(km * kf, 2)
                    toplam_kaynak += toplam
                    aciklama = f"{ref_no} | Birleştirme → {hedef.ad}" + (f" | {aciklama_ek}" if aciklama_ek else "")
                    db.session.add(StokHareket(stok_id=int(kid),
                        hareket_tipi='birlestirme_cikis', miktar=km,
                        birim_fiyat=kf, toplam_tutar=toplam,
                        aciklama=aciklama, user_id=current_user.id))
                    kaynak.stok_miktari = float(kaynak.stok_miktari or 0) - km

                h_toplam = round(h_miktar * h_fiyat, 2)
                if abs(toplam_kaynak - h_toplam) > 0.02:
                    db.session.rollback()
                    flash(f'Toplam tutarlar eşit değil: Kaynak {toplam_kaynak:.2f} ≠ Hedef {h_toplam:.2f}', 'danger')
                    return redirect(url_for('stok.transfer'))

                aciklama = f"{ref_no} | Birleştirme → {hedef.ad}" + (f" | {aciklama_ek}" if aciklama_ek else "")
                hedef.guncelle_ortalama_maliyet(h_miktar, h_fiyat)
                db.session.add(StokHareket(stok_id=hedef_id,
                    hareket_tipi='birlestirme_giris', miktar=h_miktar,
                    birim_fiyat=h_fiyat, toplam_tutar=h_toplam,
                    aciklama=aciklama, user_id=current_user.id))
                hedef.stok_miktari = float(hedef.stok_miktari or 0) + h_miktar

                db.session.commit()
                flash(f'Birleştirme tamamlandı ({ref_no}) → {hedef.ad}', 'success')

        except Exception as e:
            db.session.rollback()
            flash(f'Hata oluştu: {e}', 'danger')

        return redirect(url_for('stok.transfer'))

    return render_template('stok/transfer.html')


@bp.route('/deger-raporu')
@login_required
def deger_raporu():
    q = request.args.get('q', '').strip()
    kategori_id = request.args.get('kategori_id', type=int)

    query = Stok.query.filter_by(is_active=True, urun_tipi='stok')
    if q:
        query = query.filter(
            db.or_(Stok.ad.ilike(f'%{q}%'), Stok.stok_kodu.ilike(f'%{q}%'))
        )
    if kategori_id:
        query = query.filter_by(kategori_id=kategori_id)

    stoklar = query.order_by(Stok.ad).all()

    # Para birimi bazında toplamlar
    pb_toplamlar = {}
    for s in stoklar:
        miktar = float(s.stok_miktari or 0)
        ort_mal = float(s.ortalama_maliyet or 0)
        satis_f = float(s.satis_fiyati or 0)
        pb_alis = (s.alis_para_birimi or 'TRY').upper()
        pb_satis = (s.satis_para_birimi or 'TRY').upper()

        if pb_alis not in pb_toplamlar:
            pb_toplamlar[pb_alis] = {'maliyet': 0.0, 'satis': 0.0, 'adet': 0}
        if pb_satis not in pb_toplamlar:
            pb_toplamlar[pb_satis] = {'maliyet': 0.0, 'satis': 0.0, 'adet': 0}

        pb_toplamlar[pb_alis]['maliyet'] += miktar * ort_mal
        pb_toplamlar[pb_satis]['satis'] += miktar * satis_f
        pb_toplamlar[pb_alis]['adet'] += 1

    # Kategori bazında toplamlar (TRY ürünler için)
    kat_toplamlar = {}
    for s in stoklar:
        kat_ad = s.kategori.ad if s.kategori else 'Kategorisiz'
        miktar = float(s.stok_miktari or 0)
        ort_mal = float(s.ortalama_maliyet or 0)
        satis_f = float(s.satis_fiyati or 0)
        if kat_ad not in kat_toplamlar:
            kat_toplamlar[kat_ad] = {'maliyet': 0.0, 'satis': 0.0, 'urun': 0, 'pb': s.alis_para_birimi or 'TRY'}
        kat_toplamlar[kat_ad]['maliyet'] += miktar * ort_mal
        kat_toplamlar[kat_ad]['satis'] += miktar * satis_f
        kat_toplamlar[kat_ad]['urun'] += 1

    kategoriler = StokKategori.query.order_by(StokKategori.ad).all()
    return render_template('stok/deger_raporu.html',
                           stoklar=stoklar,
                           pb_toplamlar=pb_toplamlar,
                           kat_toplamlar=kat_toplamlar,
                           kategoriler=kategoriler,
                           q=q, kategori_id=kategori_id)


@bp.route('/hareketler')
@login_required
def hareketler():
    hareketler = StokHareket.query.order_by(StokHareket.tarih.desc()).limit(100).all()
    return render_template('stok/hareketler.html', hareketler=hareketler)


@bp.route('/<int:id>/hareket-ekle', methods=['POST'])
@login_required
def hareket_ekle(id):
    stok = Stok.query.get_or_404(id)
    tip = request.form['hareket_tipi']
    miktar = float(request.form['miktar'])
    birim_fiyat = float(request.form.get('birim_fiyat') or 0)
    aciklama = request.form.get('aciklama', '')

    if tip in ('giris', 'iade_giris', 'devir') and birim_fiyat > 0:
        stok.guncelle_ortalama_maliyet(miktar, birim_fiyat)
    db.session.add(StokHareket(
        stok_id=stok.id,
        hareket_tipi=tip,
        miktar=miktar,
        birim_fiyat=birim_fiyat,
        toplam_tutar=miktar * birim_fiyat,
        aciklama=aciklama,
        user_id=current_user.id,
    ))
    if tip in ('giris', 'iade_giris', 'devir', 'sayim'):
        stok.stok_miktari = float(stok.stok_miktari or 0) + miktar
    else:
        stok.stok_miktari = float(stok.stok_miktari or 0) - miktar

    db.session.commit()
    flash('Stok hareketi eklendi.', 'success')
    return redirect(url_for('stok.detail', id=stok.id))


@bp.route('/kategoriler')
@login_required
def kategoriler():
    kategoriler = StokKategori.query.order_by(StokKategori.ad).all()
    return render_template('stok/kategoriler.html', kategoriler=kategoriler)


@bp.route('/kategoriler/yeni', methods=['POST'])
@login_required
def kategori_yeni():
    ad = request.form.get('ad', '').strip()
    if ad:
        db.session.add(StokKategori(ad=ad))
        db.session.commit()
        flash(f'Kategori "{ad}" eklendi.', 'success')
    return redirect(url_for('stok.kategoriler'))


@bp.route('/api/search')
@login_required
def api_search():
    q = request.args.get('q', '').strip()
    query = Stok.query.filter_by(is_active=True)
    if q:
        query = query.filter(
            db.or_(Stok.ad.ilike(f'%{q}%'), Stok.stok_kodu.ilike(f'%{q}%'),
                   Stok.barkod.ilike(f'%{q}%'))
        )
    results = [{
        'id': s.id,
        'ad': s.ad,
        'stok_kodu': s.stok_kodu,
        'marka': s.marka or '',
        'birim': s.birim,
        'urun_tipi': s.urun_tipi or 'stok',
        'satis_fiyati': float(s.satis_fiyati or 0),
        'alis_fiyati': float(s.alis_fiyati or 0),
        'kdv_orani': float(s.kdv_orani or 20),
        'alis_kdv_orani': float(s.alis_kdv_orani or s.kdv_orani or 20),
        'satis_para_birimi': s.satis_para_birimi or 'TRY',
        'alis_para_birimi': s.alis_para_birimi or 'TRY',
        'resim': url_for('static', filename=s.resim) if s.resim else None,
    } for s in query.limit(20).all()]
    return jsonify(results)
