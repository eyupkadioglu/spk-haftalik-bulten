from datetime import datetime, date
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func
from app.extensions import db
from app.models.muhasebe import HesapPlani, MuhasebeKayit, MuhasebeKalem

bp = Blueprint('muhasebe', __name__)


@bp.route('/')
@login_required
def index():
    q = request.args.get('q', '').strip()
    query = MuhasebeKayit.query
    if q:
        query = query.filter(
            db.or_(MuhasebeKayit.aciklama.ilike(f'%{q}%'),
                   MuhasebeKayit.belge_no.ilike(f'%{q}%'))
        )
    kayitlar = query.order_by(MuhasebeKayit.tarih.desc(), MuhasebeKayit.id.desc()).limit(100).all()
    return render_template('muhasebe/index.html', kayitlar=kayitlar, q=q)


@bp.route('/<int:id>')
@login_required
def detail(id):
    kayit = MuhasebeKayit.query.get_or_404(id)
    return render_template('muhasebe/detail.html', kayit=kayit)


@bp.route('/yeni', methods=['GET', 'POST'])
@login_required
def yeni():
    if request.method == 'POST':
        kayit = MuhasebeKayit(
            tarih=datetime.strptime(request.form['tarih'], '%d.%m.%Y').date(),
            aciklama=request.form['aciklama'],
            belge_no=request.form.get('belge_no'),
            belge_tipi='diger',
            user_id=current_user.id
        )
        db.session.add(kayit)
        db.session.flush()

        hesap_kodlari = request.form.getlist('hesap_kodu[]')
        borclar = request.form.getlist('borc[]')
        alacaklar = request.form.getlist('alacak[]')
        aciklamalar = request.form.getlist('kalem_aciklama[]')

        for hk, b, a, ac in zip(hesap_kodlari, borclar, alacaklar, aciklamalar):
            if hk:
                kalem = MuhasebeKalem(
                    kayit_id=kayit.id,
                    hesap_kodu=hk,
                    borc=float(b or 0),
                    alacak=float(a or 0),
                    aciklama=ac
                )
                db.session.add(kalem)

        db.session.commit()
        flash(f'Yevmiye kaydı oluşturuldu.', 'success')
        return redirect(url_for('muhasebe.detail', id=kayit.id))

    hesaplar = HesapPlani.query.filter_by(is_active=True).order_by(HesapPlani.kod).all()
    return render_template('muhasebe/form.html', hesaplar=hesaplar)


@bp.route('/hesap-plani')
@login_required
def hesap_plani():
    hesaplar = HesapPlani.query.filter_by(ust_kod=None, is_active=True).order_by(HesapPlani.kod).all()
    tum_hesaplar = HesapPlani.query.filter_by(is_active=True).order_by(HesapPlani.kod).all()
    return render_template('muhasebe/hesap_plani.html', hesaplar=hesaplar, tum_hesaplar=tum_hesaplar)


@bp.route('/hesap-plani/yeni', methods=['POST'])
@login_required
def hesap_yeni():
    kod = request.form.get('kod', '').strip()
    ad = request.form.get('ad', '').strip()
    tip = request.form.get('tip', 'aktif')
    ust_kod = request.form.get('ust_kod') or None
    if kod and ad:
        h = HesapPlani(kod=kod, ad=ad, tip=tip, ust_kod=ust_kod)
        db.session.add(h)
        db.session.commit()
        flash(f'Hesap {kod} eklendi.', 'success')
    return redirect(url_for('muhasebe.hesap_plani'))


@bp.route('/mizan')
@login_required
def mizan():
    rows = db.session.query(
        MuhasebeKalem.hesap_kodu,
        HesapPlani.ad,
        HesapPlani.tip,
        func.sum(MuhasebeKalem.borc).label('toplam_borc'),
        func.sum(MuhasebeKalem.alacak).label('toplam_alacak'),
    ).join(HesapPlani, MuhasebeKalem.hesap_kodu == HesapPlani.kod) \
     .group_by(MuhasebeKalem.hesap_kodu, HesapPlani.ad, HesapPlani.tip) \
     .order_by(MuhasebeKalem.hesap_kodu).all()

    return render_template('muhasebe/mizan.html', rows=rows)


@bp.route('/api/hesaplar')
@login_required
def api_hesaplar():
    q = request.args.get('q', '').strip()
    query = HesapPlani.query.filter_by(is_active=True)
    if q:
        query = query.filter(
            db.or_(HesapPlani.kod.ilike(f'%{q}%'), HesapPlani.ad.ilike(f'%{q}%'))
        )
    results = [{'kod': h.kod, 'ad': h.ad, 'tip': h.tip} for h in query.limit(20).all()]
    return jsonify(results)
