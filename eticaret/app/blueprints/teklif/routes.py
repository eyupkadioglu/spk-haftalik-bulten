import json
import urllib.parse
from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.teklif import Teklif, TeklifKalem
from app.models.cari import Cari
from app.models.stok import Stok
from app.models.siparis import Siparis, SiparisKalem
from app.utils import next_sequence

bp = Blueprint('teklif', __name__)

DURUM_LABELS = {
    'taslak': ('secondary', 'Taslak'),
    'gonderildi': ('info', 'Gönderildi'),
    'siparise_donustu': ('success', 'Siparişe Dönüştürüldü'),
    'iptal': ('dark', 'İptal'),
}


@bp.route('/')
@login_required
def index():
    q = request.args.get('q', '').strip()
    durum = request.args.get('durum', '')
    query = Teklif.query
    if q:
        query = query.filter(Teklif.teklif_no.ilike(f'%{q}%'))
    if durum:
        query = query.filter_by(durum=durum)
    teklifler = query.order_by(Teklif.teklif_tarihi.desc()).all()
    return render_template('teklif/index.html', teklifler=teklifler,
                           q=q, durum=durum, durum_labels=DURUM_LABELS,
                           today=date.today())


@bp.route('/<int:id>')
@login_required
def detail(id):
    teklif = Teklif.query.get_or_404(id)
    kalemler = teklif.kalemler.all()
    return render_template('teklif/detail.html', teklif=teklif,
                           kalemler=kalemler, durum_labels=DURUM_LABELS)


@bp.route('/yeni', methods=['GET', 'POST'])
@login_required
def yeni():
    if request.method == 'POST':
        return _kaydet_teklif(None)
    cariler = Cari.query.filter_by(is_active=True).order_by(Cari.unvan).all()
    bugun = date.today()
    gecerli = bugun + timedelta(days=30)
    return render_template('teklif/form.html', teklif=None, cariler=cariler,
                           bugun=bugun.strftime('%d.%m.%Y'),
                           gecerli=gecerli.strftime('%d.%m.%Y'))


@bp.route('/<int:id>/duzenle', methods=['GET', 'POST'])
@login_required
def duzenle(id):
    teklif = Teklif.query.get_or_404(id)
    if teklif.durum not in ('taslak', 'gonderildi'):
        flash('Sadece taslak veya gönderilmiş teklifler düzenlenebilir.', 'warning')
        return redirect(url_for('teklif.detail', id=id))
    if request.method == 'POST':
        return _kaydet_teklif(teklif)
    cariler = Cari.query.filter_by(is_active=True).order_by(Cari.unvan).all()
    kalemler_json = json.dumps([{
        'stok_id': k.stok_id or '',
        'aciklama': k.aciklama or '',
        'miktar': float(k.miktar),
        'birim': k.birim,
        'birim_fiyat': float(k.birim_fiyat),
        'iskonto_orani': float(k.iskonto_orani),
        'kdv_orani': float(k.kdv_orani),
        'kdv_tutari': float(k.kdv_tutari),
        'toplam_tutar': float(k.toplam_tutar),
    } for k in teklif.kalemler], ensure_ascii=False)
    return render_template('teklif/form.html', teklif=teklif, cariler=cariler,
                           kalemler_json=kalemler_json)


def _kaydet_teklif(teklif):
    cari_id = request.form.get('cari_id', type=int)
    teklif_tarihi = request.form.get('teklif_tarihi')
    gecerlilik_tarihi = request.form.get('gecerlilik_tarihi')
    notlar = request.form.get('notlar', '')
    para_birimi = request.form.get('para_birimi', 'TRY')
    kalemler_json_str = request.form.get('kalemler_json', '[]')

    cariler = Cari.query.filter_by(is_active=True).order_by(Cari.unvan).all()

    def _hata(mesaj):
        flash(mesaj, 'danger')
        return render_template('teklif/form.html', teklif=teklif, cariler=cariler,
                               kalemler_json=kalemler_json_str,
                               bugun=date.today().strftime('%d.%m.%Y'),
                               gecerli=(date.today() + __import__('datetime').timedelta(days=30)).strftime('%d.%m.%Y'))

    if not cari_id:
        return _hata('Lütfen bir cari seçin.')

    try:
        t_tarih = datetime.strptime(teklif_tarihi, '%d.%m.%Y').date() if teklif_tarihi else date.today()
        g_tarih = datetime.strptime(gecerlilik_tarihi, '%d.%m.%Y').date() if gecerlilik_tarihi else None
    except ValueError:
        t_tarih = date.today()
        g_tarih = None

    kalemler_data = json.loads(kalemler_json_str)
    if not kalemler_data:
        return _hata('En az bir kalem eklemelisiniz.')

    yeni_kayit = teklif is None
    if yeni_kayit:
        teklif = Teklif(
            teklif_no=next_sequence('TKL', Teklif, 'teklif_no'),
            cari_id=cari_id,
            teklif_tarihi=t_tarih,
            gecerlilik_tarihi=g_tarih,
            notlar=notlar,
            para_birimi=para_birimi,
            user_id=current_user.id,
        )
        db.session.add(teklif)
        db.session.flush()  # teklif.id'yi almak için
    else:
        teklif.cari_id = cari_id
        teklif.teklif_tarihi = t_tarih
        teklif.gecerlilik_tarihi = g_tarih
        teklif.notlar = notlar
        teklif.para_birimi = para_birimi

    # Mevcut kalemleri sil (sadece güncelleme modunda)
    if not yeni_kayit:
        TeklifKalem.query.filter_by(teklif_id=teklif.id).delete()
        db.session.flush()

    ara = kdv = toplam = 0.0
    for i, k in enumerate(kalemler_data):
        stok_id = k.get('stok_id') or None
        miktar = float(k.get('miktar', 1))
        birim_fiyat = float(k.get('birim_fiyat', 0))
        iskonto = float(k.get('iskonto_orani', 0))
        kdv_oran = float(k.get('kdv_orani', 20))
        net = miktar * birim_fiyat * (1 - iskonto / 100)
        kdv_t = net * kdv_oran / 100
        tot = net + kdv_t
        ara += net
        kdv += kdv_t
        toplam += tot
        kalem = TeklifKalem(
            teklif_id=teklif.id,
            stok_id=stok_id,
            aciklama=k.get('aciklama', ''),
            miktar=miktar,
            birim=k.get('birim', 'Adet'),
            birim_fiyat=birim_fiyat,
            iskonto_orani=iskonto,
            kdv_orani=kdv_oran,
            kdv_tutari=round(kdv_t, 2),
            toplam_tutar=round(tot, 2),
            sira=i,
        )
        db.session.add(kalem)

    teklif.ara_toplam = round(ara, 2)
    teklif.kdv_toplam = round(kdv, 2)
    teklif.genel_toplam = round(toplam, 2)
    db.session.commit()

    flash(f'Teklif "{teklif.teklif_no}" kaydedildi.', 'success')
    return redirect(url_for('teklif.detail', id=teklif.id))


@bp.route('/<int:id>/gonder', methods=['POST'])
@login_required
def gonder(id):
    teklif = Teklif.query.get_or_404(id)
    if teklif.durum != 'taslak':
        flash('Sadece taslak teklifler gönderilebilir.', 'warning')
    else:
        teklif.durum = 'gonderildi'
        db.session.commit()
        flash(f'Teklif "{teklif.teklif_no}" gönderildi olarak işaretlendi.', 'success')
    return redirect(url_for('teklif.detail', id=id))


@bp.route('/<int:id>/gonder-bilgi')
@login_required
def gonder_bilgi(id):
    """E-posta / WhatsApp gönderim linklerini JSON olarak döner."""
    teklif = Teklif.query.get_or_404(id)
    cari = teklif.cari
    yazdir_url = url_for('teklif.yazdir', id=id, _external=True)

    pb = teklif.para_birimi or 'TRY'
    sembol = {'TRY': '₺', 'USD': '$', 'EUR': '€'}.get(pb, pb)

    def _fmt(tutar_float, sembol_str):
        return f"{sembol_str}{tutar_float:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

    tutar = _fmt(float(teklif.genel_toplam), sembol)

    # Yabancı para birimi ise TL karşılığını hesapla
    try_karsiligi = ''
    if pb != 'TRY':
        from app.utils_kur import son_kurlar
        kurlar = son_kurlar()
        kur_bilgi = kurlar.get(pb)
        if kur_bilgi:
            kur = kur_bilgi['satis']
            try_tutar = float(teklif.genel_toplam) * kur
            tarih = kur_bilgi['tarih'].strftime('%d.%m.%Y')
            try_karsiligi = f"\nTL karşılığı (TCMB {tarih} kuru {kur:,.4f}₺): {_fmt(try_tutar, '₺')}"

    mesaj = (
        f"Sayın {cari.unvan},\n\n"
        f"{teklif.teklif_no} numaralı teklifimizi bilgilerinize sunarız.\n"
        f"Toplam tutar: {tutar}{try_karsiligi}\n"
        f"Geçerlilik: {teklif.gecerlilik_tarihi.strftime('%d.%m.%Y') if teklif.gecerlilik_tarihi else '—'}\n\n"
        f"Teklif detayı: {yazdir_url}\n\n"
        f"Saygılarımızla"
    )

    email = cari.email or ''
    konu = f"Teklif — {teklif.teklif_no}"
    mailto = f"mailto:{email}?subject={urllib.parse.quote(konu)}&body={urllib.parse.quote(mesaj)}"

    telefon = (cari.telefon or '').replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
    if telefon.startswith('0'):
        telefon = '90' + telefon[1:]
    elif not telefon.startswith('90') and telefon:
        telefon = '90' + telefon
    wa_url = f"https://wa.me/{telefon}?text={urllib.parse.quote(mesaj)}" if telefon else f"https://wa.me/?text={urllib.parse.quote(mesaj)}"

    return jsonify({
        'mailto': mailto,
        'whatsapp': wa_url,
        'email': email,
        'telefon': cari.telefon or '',
        'mesaj': mesaj,
    })


@bp.route('/<int:id>/iptal', methods=['POST'])
@login_required
def iptal(id):
    teklif = Teklif.query.get_or_404(id)
    teklif.durum = 'iptal'
    db.session.commit()
    flash(f'Teklif "{teklif.teklif_no}" iptal edildi.', 'warning')
    return redirect(url_for('teklif.detail', id=id))


@bp.route('/<int:id>/sipariste-donustur', methods=['POST'])
@login_required
def sipariste_donustur(id):
    teklif = Teklif.query.get_or_404(id)
    if teklif.durum == 'iptal':
        flash('İptal edilmiş teklifler siparişe dönüştürülemez.', 'warning')
        return redirect(url_for('teklif.detail', id=id))
    if teklif.durum == 'siparise_donustu' and teklif.siparis_id:
        flash('Bu teklif zaten siparişe dönüştürülmüştü.', 'warning')
        return redirect(url_for('siparis.detail', id=teklif.siparis_id))

    siparis = Siparis(
        siparis_no=next_sequence('SS', Siparis, 'siparis_no'),
        siparis_tipi='satis',
        cari_id=teklif.cari_id,
        siparis_tarihi=date.today(),
        genel_toplam=teklif.genel_toplam,
        notlar=f'Teklif {teklif.teklif_no} üzerinden oluşturuldu.',
        created_by=current_user.id,
    )
    db.session.add(siparis)
    db.session.flush()

    for i, k in enumerate(teklif.kalemler):
        kalem = SiparisKalem(
            siparis_id=siparis.id,
            stok_id=k.stok_id,
            aciklama=k.aciklama or (k.stok.ad if k.stok else ''),
            miktar=k.miktar,
            birim=k.birim,
            birim_fiyat=k.birim_fiyat,
            kdv_orani=k.kdv_orani,
            toplam_tutar=k.toplam_tutar,
            sira=i,
        )
        db.session.add(kalem)

    teklif.durum = 'siparise_donustu'
    teklif.siparis_id = siparis.id
    db.session.commit()
    flash(f'Sipariş "{siparis.siparis_no}" oluşturuldu.', 'success')
    return redirect(url_for('siparis.detail', id=siparis.id))


@bp.route('/<int:id>/yazdir')
@login_required
def yazdir(id):
    teklif = Teklif.query.get_or_404(id)
    kalemler = teklif.kalemler.all()
    return render_template('teklif/yazdir.html', teklif=teklif,
                           kalemler=kalemler, durum_labels=DURUM_LABELS)
