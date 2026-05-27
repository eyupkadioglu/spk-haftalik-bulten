import json
from datetime import datetime, date
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.fatura import Fatura, FaturaKalem
from app.models.stok import Stok, StokHareket
from app.models.cari import Cari
from app.models.muhasebe import MuhasebeKayit, MuhasebeKalem, HesapPlani
from app.utils import next_sequence

bp = Blueprint('fatura', __name__)

DURUM_LABELS = {
    'taslak': ('Taslak', 'secondary'),
    'onaylandi': ('Onaylandı', 'success'),
    'kismi_odendi': ('Kısmi Ödendi', 'warning'),
    'odendi': ('Ödendi', 'info'),
    'iptal': ('İptal', 'danger'),
}


@bp.route('/')
@login_required
def index():
    tip = request.args.get('tip', 'satis')
    durum = request.args.get('durum', '')
    q = request.args.get('q', '').strip()
    query = Fatura.query.filter_by(fatura_tipi=tip)
    if durum:
        query = query.filter_by(durum=durum)
    if q:
        query = query.join(Cari).filter(
            db.or_(Fatura.fatura_no.ilike(f'%{q}%'), Cari.unvan.ilike(f'%{q}%'))
        )
    faturalar = query.order_by(Fatura.fatura_tarihi.desc()).all()
    return render_template('fatura/index.html', faturalar=faturalar,
                           tip=tip, durum=durum, q=q, DURUM_LABELS=DURUM_LABELS)


@bp.route('/<int:id>')
@login_required
def detail(id):
    fatura = Fatura.query.get_or_404(id)
    return render_template('fatura/detail.html', fatura=fatura, DURUM_LABELS=DURUM_LABELS)


@bp.route('/<int:id>/yazdir')
@login_required
def yazdir(id):
    fatura = Fatura.query.get_or_404(id)
    return render_template('fatura/yazdir.html', fatura=fatura)


@bp.route('/yeni', methods=['GET', 'POST'])
@login_required
def yeni():
    tip = request.args.get('tip', 'satis')
    if request.method == 'POST':
        tip = request.form.get('fatura_tipi', 'satis')
        prefix = 'SF' if tip == 'satis' else 'AF'

        ara_toplam = float(request.form.get('ara_toplam', 0))
        kdv_toplam = float(request.form.get('kdv_toplam', 0))
        genel_toplam = float(request.form.get('genel_toplam', 0))

        fatura = Fatura(
            fatura_no=next_sequence(prefix, Fatura, 'fatura_no'),
            fatura_tipi=tip,
            cari_id=int(request.form['cari_id']),
            fatura_tarihi=datetime.strptime(request.form['fatura_tarihi'], '%d.%m.%Y').date(),
            vade_tarihi=datetime.strptime(request.form['vade_tarihi'], '%d.%m.%Y').date() if request.form.get('vade_tarihi') else None,
            odeme_sekli=request.form.get('odeme_sekli'),
            ara_toplam=ara_toplam,
            kdv_toplam=kdv_toplam,
            genel_toplam=genel_toplam,
            kalan_tutar=genel_toplam,
            notlar=request.form.get('notlar'),
            created_by=current_user.id,
        )
        db.session.add(fatura)
        db.session.flush()

        kalemler_json = request.form.get('kalemler_json', '[]')
        for i, k in enumerate(json.loads(kalemler_json)):
            miktar = float(k.get('miktar', 0))
            birim_fiyat = float(k.get('birim_fiyat', 0))
            kdv_orani = float(k.get('kdv_orani', 20))
            iskonto = float(k.get('iskonto_orani', 0))
            ara = miktar * birim_fiyat * (1 - iskonto / 100)
            kdv_t = ara * kdv_orani / 100
            toplam = ara + kdv_t
            kalem = FaturaKalem(
                fatura_id=fatura.id,
                stok_id=k.get('stok_id') or None,
                aciklama=k.get('aciklama', ''),
                miktar=miktar,
                birim=k.get('birim', 'Adet'),
                birim_fiyat=birim_fiyat,
                iskonto_orani=iskonto,
                kdv_orani=kdv_orani,
                kdv_tutari=round(kdv_t, 2),
                toplam_tutar=round(toplam, 2),
                sira=i,
            )
            db.session.add(kalem)

        db.session.commit()
        flash(f'Fatura {fatura.fatura_no} oluşturuldu.', 'success')
        return redirect(url_for('fatura.detail', id=fatura.id))

    cariler = Cari.query.filter_by(is_active=True).order_by(Cari.unvan).all()
    return render_template('fatura/form.html', fatura=None, tip=tip, cariler=cariler)


@bp.route('/<int:id>/onayla', methods=['POST'])
@login_required
def onayla(id):
    fatura = Fatura.query.get_or_404(id)
    if fatura.durum != 'taslak':
        flash('Sadece taslak faturalar onaylanabilir.', 'danger')
        return redirect(url_for('fatura.detail', id=id))

    # Stok hareketleri oluştur
    for kalem in fatura.kalemler:
        if kalem.stok_id:
            stok = Stok.query.get(kalem.stok_id)
            if stok:
                miktar = float(kalem.miktar)
                birim_fiyat = float(kalem.birim_fiyat)
                if fatura.fatura_tipi == 'alis':
                    # Alış: ortalama maliyeti güncelle (stok artmadan önce)
                    stok.guncelle_ortalama_maliyet(miktar, birim_fiyat)
                    stok.stok_miktari = float(stok.stok_miktari or 0) + miktar
                    tip = 'giris'
                else:
                    # Satış: mevcut ortalama maliyeti kalem üzerine snapshot al
                    kalem.maliyet_fiyat = float(stok.ortalama_maliyet or 0)
                    stok.stok_miktari = float(stok.stok_miktari or 0) - miktar
                    tip = 'cikis'
                h = StokHareket(
                    stok_id=stok.id,
                    hareket_tipi=tip,
                    miktar=miktar,
                    birim_fiyat=birim_fiyat,
                    toplam_tutar=float(kalem.toplam_tutar),
                    fatura_id=fatura.id,
                    aciklama=f'Fatura: {fatura.fatura_no}',
                    user_id=current_user.id
                )
                db.session.add(h)

    fatura.durum = 'onaylandi'
    db.session.commit()
    flash(f'Fatura {fatura.fatura_no} onaylandı.', 'success')
    return redirect(url_for('fatura.detail', id=id))


@bp.route('/<int:id>/iptal', methods=['POST'])
@login_required
def iptal(id):
    fatura = Fatura.query.get_or_404(id)
    fatura.durum = 'iptal'
    db.session.commit()
    flash('Fatura iptal edildi.', 'warning')
    return redirect(url_for('fatura.detail', id=id))
