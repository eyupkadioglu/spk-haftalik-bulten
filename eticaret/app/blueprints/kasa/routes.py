from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.kasa import KasaHesap, KasaHareket
from app.models.fatura import Fatura
from app.models.cari import Cari

bp = Blueprint('kasa', __name__)


@bp.route('/')
@login_required
def index():
    kasalar = KasaHesap.query.filter_by(is_active=True).order_by(KasaHesap.ad).all()
    return render_template('kasa/index.html', kasalar=kasalar)


@bp.route('/<int:id>')
@login_required
def detail(id):
    kasa = KasaHesap.query.get_or_404(id)
    hareketler = kasa.hareketler.order_by(KasaHareket.tarih.desc()).limit(50).all()
    return render_template('kasa/detail.html', kasa=kasa, hareketler=hareketler)


@bp.route('/yeni-hesap', methods=['GET', 'POST'])
@login_required
def yeni_hesap():
    if request.method == 'POST':
        k = KasaHesap(
            ad=request.form['ad'],
            hesap_tipi=request.form.get('hesap_tipi', 'kasa'),
            banka_adi=request.form.get('banka_adi'),
            hesap_no=request.form.get('hesap_no'),
            iban=request.form.get('iban'),
            para_birimi=request.form.get('para_birimi', 'TRY'),
        )
        db.session.add(k)
        db.session.commit()
        flash(f'"{k.ad}" hesabı oluşturuldu.', 'success')
        return redirect(url_for('kasa.index'))
    return render_template('kasa/yeni_hesap.html')


@bp.route('/<int:id>/tahsilat', methods=['GET', 'POST'])
@login_required
def tahsilat(id):
    kasa = KasaHesap.query.get_or_404(id)
    if request.method == 'POST':
        tutar = float(request.form['tutar'])
        cari_id = request.form.get('cari_id', type=int)
        fatura_id = request.form.get('fatura_id', type=int)

        h = KasaHareket(
            kasa_id=kasa.id,
            hareket_tipi='tahsilat',
            tutar=tutar,
            aciklama=request.form.get('aciklama', ''),
            tarih=datetime.strptime(request.form['tarih'], '%d.%m.%Y'),
            cari_id=cari_id,
            fatura_id=fatura_id,
            belge_no=request.form.get('belge_no'),
            user_id=current_user.id
        )
        kasa.bakiye = float(kasa.bakiye or 0) + tutar
        db.session.add(h)

        if fatura_id:
            fatura = Fatura.query.get(fatura_id)
            if fatura:
                fatura.odenen_tutar = float(fatura.odenen_tutar or 0) + tutar
                fatura.kalan_tutar = float(fatura.genel_toplam or 0) - float(fatura.odenen_tutar)
                if float(fatura.kalan_tutar) <= 0:
                    fatura.durum = 'odendi'
                    fatura.kalan_tutar = 0
                elif float(fatura.odenen_tutar) > 0:
                    fatura.durum = 'kismi_odendi'

        db.session.commit()
        flash(f'{tutar:,.2f} ₺ tahsilat yapıldı.', 'success')
        return redirect(url_for('kasa.detail', id=id))

    cariler = Cari.query.filter_by(is_active=True).order_by(Cari.unvan).all()
    faturalar = Fatura.query.filter(
        Fatura.fatura_tipi == 'satis',
        Fatura.durum.in_(['onaylandi', 'kismi_odendi'])
    ).order_by(Fatura.fatura_tarihi.desc()).all()
    return render_template('kasa/hareket_form.html', kasa=kasa, tip='tahsilat',
                           cariler=cariler, faturalar=faturalar)


@bp.route('/<int:id>/odeme', methods=['GET', 'POST'])
@login_required
def odeme(id):
    kasa = KasaHesap.query.get_or_404(id)
    if request.method == 'POST':
        tutar = float(request.form['tutar'])
        cari_id = request.form.get('cari_id', type=int)
        fatura_id = request.form.get('fatura_id', type=int)

        h = KasaHareket(
            kasa_id=kasa.id,
            hareket_tipi='odeme',
            tutar=tutar,
            aciklama=request.form.get('aciklama', ''),
            tarih=datetime.strptime(request.form['tarih'], '%d.%m.%Y'),
            cari_id=cari_id,
            fatura_id=fatura_id,
            belge_no=request.form.get('belge_no'),
            user_id=current_user.id
        )
        kasa.bakiye = float(kasa.bakiye or 0) - tutar
        db.session.add(h)

        if fatura_id:
            fatura = Fatura.query.get(fatura_id)
            if fatura:
                fatura.odenen_tutar = float(fatura.odenen_tutar or 0) + tutar
                fatura.kalan_tutar = float(fatura.genel_toplam or 0) - float(fatura.odenen_tutar)
                if float(fatura.kalan_tutar) <= 0:
                    fatura.durum = 'odendi'
                    fatura.kalan_tutar = 0
                elif float(fatura.odenen_tutar) > 0:
                    fatura.durum = 'kismi_odendi'

        db.session.commit()
        flash(f'{tutar:,.2f} ₺ ödeme yapıldı.', 'success')
        return redirect(url_for('kasa.detail', id=id))

    cariler = Cari.query.filter_by(is_active=True).order_by(Cari.unvan).all()
    faturalar = Fatura.query.filter(
        Fatura.fatura_tipi == 'alis',
        Fatura.durum.in_(['onaylandi', 'kismi_odendi'])
    ).order_by(Fatura.fatura_tarihi.desc()).all()
    return render_template('kasa/hareket_form.html', kasa=kasa, tip='odeme',
                           cariler=cariler, faturalar=faturalar)


@bp.route('/virman', methods=['GET', 'POST'])
@login_required
def virman():
    if request.method == 'POST':
        kaynak_id = int(request.form['kaynak_id'])
        hedef_id = int(request.form['hedef_id'])
        tutar = float(request.form['tutar'])

        kaynak = KasaHesap.query.get_or_404(kaynak_id)
        hedef = KasaHesap.query.get_or_404(hedef_id)

        cikis = KasaHareket(
            kasa_id=kaynak_id, hedef_kasa_id=hedef_id,
            hareket_tipi='virman', tutar=tutar,
            aciklama=f'Virman → {hedef.ad}',
            tarih=datetime.strptime(request.form['tarih'], '%d.%m.%Y'),
            user_id=current_user.id
        )
        giris = KasaHareket(
            kasa_id=hedef_id,
            hareket_tipi='virman', tutar=tutar,
            aciklama=f'Virman ← {kaynak.ad}',
            tarih=datetime.strptime(request.form['tarih'], '%d.%m.%Y'),
            user_id=current_user.id
        )
        kaynak.bakiye = float(kaynak.bakiye or 0) - tutar
        hedef.bakiye = float(hedef.bakiye or 0) + tutar

        db.session.add_all([cikis, giris])
        db.session.commit()
        flash(f'{tutar:,.2f} ₺ virman yapıldı.', 'success')
        return redirect(url_for('kasa.index'))

    kasalar = KasaHesap.query.filter_by(is_active=True).all()
    return render_template('kasa/virman.html', kasalar=kasalar)
