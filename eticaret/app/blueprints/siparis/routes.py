import json
from datetime import datetime, date
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.siparis import Siparis, SiparisKalem
from app.models.stok import Stok
from app.models.cari import Cari
from app.utils import next_sequence

bp = Blueprint('siparis', __name__)

DURUM_LABELS = {
    'acik': ('Açık', 'primary'),
    'onaylandi': ('Onaylandı', 'success'),
    'kismi_teslim': ('Kısmi Teslim', 'warning'),
    'tamamlandi': ('Tamamlandı', 'info'),
    'iptal': ('İptal', 'danger'),
}


@bp.route('/')
@login_required
def index():
    tip = request.args.get('tip', 'satis')
    durum = request.args.get('durum', '')
    q = request.args.get('q', '').strip()
    query = Siparis.query.filter_by(siparis_tipi=tip)
    if durum:
        query = query.filter_by(durum=durum)
    if q:
        query = query.join(Cari).filter(
            db.or_(Siparis.siparis_no.ilike(f'%{q}%'),
                   Cari.unvan.ilike(f'%{q}%'))
        )
    siparisler = query.order_by(Siparis.siparis_tarihi.desc()).all()
    return render_template('siparis/index.html', siparisler=siparisler,
                           tip=tip, durum=durum, q=q, DURUM_LABELS=DURUM_LABELS)


@bp.route('/<int:id>')
@login_required
def detail(id):
    siparis = Siparis.query.get_or_404(id)
    return render_template('siparis/detail.html', siparis=siparis, DURUM_LABELS=DURUM_LABELS)


@bp.route('/yeni', methods=['GET', 'POST'])
@login_required
def yeni():
    tip = request.args.get('tip', 'satis')
    if request.method == 'POST':
        tip = request.form.get('siparis_tipi', 'satis')
        prefix = 'SS' if tip == 'satis' else 'AS'
        siparis = Siparis(
            siparis_no=next_sequence(prefix, Siparis, 'siparis_no'),
            siparis_tipi=tip,
            cari_id=int(request.form['cari_id']),
            siparis_tarihi=datetime.strptime(request.form['siparis_tarihi'], '%d.%m.%Y').date(),
            teslim_tarihi=datetime.strptime(request.form['teslim_tarihi'], '%d.%m.%Y').date() if request.form.get('teslim_tarihi') else None,
            notlar=request.form.get('notlar'),
            created_by=current_user.id,
        )
        db.session.add(siparis)
        db.session.flush()

        kalemler_json = request.form.get('kalemler_json', '[]')
        kalemler = json.loads(kalemler_json)
        genel_toplam = 0
        for i, k in enumerate(kalemler):
            miktar = float(k.get('miktar', 0))
            birim_fiyat = float(k.get('birim_fiyat', 0))
            kdv_orani = float(k.get('kdv_orani', 20))
            ara = miktar * birim_fiyat
            kdv = ara * kdv_orani / 100
            toplam = ara + kdv
            genel_toplam += toplam
            kalem = SiparisKalem(
                siparis_id=siparis.id,
                stok_id=k.get('stok_id') or None,
                aciklama=k.get('aciklama', ''),
                miktar=miktar,
                birim=k.get('birim', 'Adet'),
                birim_fiyat=birim_fiyat,
                kdv_orani=kdv_orani,
                toplam_tutar=round(toplam, 2),
                sira=i,
            )
            db.session.add(kalem)

        siparis.genel_toplam = round(genel_toplam, 2)
        db.session.commit()
        flash(f'Sipariş {siparis.siparis_no} oluşturuldu.', 'success')
        return redirect(url_for('siparis.detail', id=siparis.id))

    cariler = Cari.query.filter_by(is_active=True).order_by(Cari.unvan).all()
    return render_template('siparis/form.html', siparis=None, tip=tip, cariler=cariler)


@bp.route('/<int:id>/onayla', methods=['POST'])
@login_required
def onayla(id):
    siparis = Siparis.query.get_or_404(id)
    siparis.durum = 'onaylandi'
    db.session.commit()
    flash('Sipariş onaylandı.', 'success')
    return redirect(url_for('siparis.detail', id=id))


@bp.route('/<int:id>/iptal', methods=['POST'])
@login_required
def iptal(id):
    siparis = Siparis.query.get_or_404(id)
    siparis.durum = 'iptal'
    db.session.commit()
    flash('Sipariş iptal edildi.', 'warning')
    return redirect(url_for('siparis.detail', id=id))


@bp.route('/<int:id>/faturalandir', methods=['POST'])
@login_required
def faturalandir(id):
    from datetime import timedelta
    from app.models.fatura import Fatura, FaturaKalem

    siparis = Siparis.query.get_or_404(id)
    if siparis.durum == 'iptal':
        flash('İptal edilmiş sipariş faturalandırılamaz.', 'danger')
        return redirect(url_for('siparis.detail', id=id))

    # Zaten faturası var mı?
    mevcut = Fatura.query.filter_by(siparis_id=siparis.id).filter(
        Fatura.durum != 'iptal').first()
    if mevcut:
        flash(f'Bu sipariş zaten faturalandırılmış: {mevcut.fatura_no}', 'warning')
        return redirect(url_for('fatura.detail', id=mevcut.id))

    prefix = 'SF' if siparis.siparis_tipi == 'satis' else 'AF'
    vade = siparis.cari.odeme_vadesi or 30

    fatura = Fatura(
        fatura_no=next_sequence(prefix, Fatura, 'fatura_no'),
        fatura_tipi=siparis.siparis_tipi,
        cari_id=siparis.cari_id,
        siparis_id=siparis.id,
        fatura_tarihi=date.today(),
        vade_tarihi=date.today() + timedelta(days=vade),
        created_by=current_user.id,
    )
    db.session.add(fatura)
    db.session.flush()

    ara = kdv = toplam = 0.0
    for i, k in enumerate(siparis.kalemler):
        net = float(k.miktar) * float(k.birim_fiyat)
        kdv_t = net * float(k.kdv_orani) / 100
        tot = net + kdv_t
        ara += net
        kdv += kdv_t
        toplam += tot
        db.session.add(FaturaKalem(
            fatura_id=fatura.id,
            stok_id=k.stok_id,
            aciklama=k.aciklama,
            miktar=k.miktar,
            birim=k.birim,
            birim_fiyat=k.birim_fiyat,
            iskonto_orani=0,
            kdv_orani=k.kdv_orani,
            kdv_tutari=round(kdv_t, 2),
            toplam_tutar=round(tot, 2),
            sira=i,
        ))

    fatura.ara_toplam = round(ara, 2)
    fatura.kdv_toplam = round(kdv, 2)
    fatura.genel_toplam = round(toplam, 2)
    fatura.kalan_tutar = round(toplam, 2)

    siparis.durum = 'tamamlandi'
    db.session.commit()
    flash(f'Fatura "{fatura.fatura_no}" oluşturuldu. Onaylamayı unutmayın.', 'success')
    return redirect(url_for('fatura.detail', id=fatura.id))
