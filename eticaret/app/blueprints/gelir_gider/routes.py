from datetime import datetime, date
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func, extract
from app.extensions import db
from app.models.gelir_gider import GelirGider, GelirGiderKategori
from app.models.kasa import KasaHesap

bp = Blueprint('gelir_gider', __name__)


@bp.route('/')
@login_required
def index():
    tip = request.args.get('tip', '')
    kategori_id = request.args.get('kategori_id', type=int)
    yil = request.args.get('yil', date.today().year, type=int)
    ay = request.args.get('ay', type=int)

    query = GelirGider.query
    if tip in ('gelir', 'gider'):
        query = query.filter_by(tip=tip)
    if kategori_id:
        query = query.filter_by(kategori_id=kategori_id)
    if yil:
        query = query.filter(extract('year', GelirGider.tarih) == yil)
    if ay:
        query = query.filter(extract('month', GelirGider.tarih) == ay)

    kayitlar = query.order_by(GelirGider.tarih.desc()).all()
    kategoriler = GelirGiderKategori.query.order_by(GelirGiderKategori.ad).all()
    return render_template('gelir_gider/index.html', kayitlar=kayitlar,
                           kategoriler=kategoriler, tip=tip, yil=yil, ay=ay,
                           kategori_id=kategori_id)


@bp.route('/yeni', methods=['GET', 'POST'])
@login_required
def yeni():
    if request.method == 'POST':
        gg = GelirGider(
            tip=request.form['tip'],
            kategori_id=request.form.get('kategori_id', type=int),
            tutar=float(request.form['tutar']),
            kdv_tutari=float(request.form.get('kdv_tutari') or 0),
            aciklama=request.form.get('aciklama'),
            tarih=datetime.strptime(request.form['tarih'], '%d.%m.%Y').date(),
            kasa_id=request.form.get('kasa_id', type=int),
            belge_no=request.form.get('belge_no'),
            user_id=current_user.id
        )
        db.session.add(gg)

        if gg.kasa_id:
            kasa = KasaHesap.query.get(gg.kasa_id)
            if kasa:
                if gg.tip == 'gelir':
                    kasa.bakiye = float(kasa.bakiye or 0) + float(gg.tutar)
                else:
                    kasa.bakiye = float(kasa.bakiye or 0) - float(gg.tutar)

        db.session.commit()
        flash('Kayıt oluşturuldu.', 'success')
        return redirect(url_for('gelir_gider.index'))

    kategoriler = GelirGiderKategori.query.order_by(GelirGiderKategori.ad).all()
    kasalar = KasaHesap.query.filter_by(is_active=True).all()
    return render_template('gelir_gider/form.html',
                           kategoriler=kategoriler, kasalar=kasalar)


@bp.route('/<int:id>/sil', methods=['POST'])
@login_required
def sil(id):
    gg = GelirGider.query.get_or_404(id)
    if gg.kasa_id:
        kasa = KasaHesap.query.get(gg.kasa_id)
        if kasa:
            if gg.tip == 'gelir':
                kasa.bakiye = float(kasa.bakiye or 0) - float(gg.tutar)
            else:
                kasa.bakiye = float(kasa.bakiye or 0) + float(gg.tutar)
    db.session.delete(gg)
    db.session.commit()
    flash('Kayıt silindi.', 'warning')
    return redirect(url_for('gelir_gider.index'))


@bp.route('/kategoriler')
@login_required
def kategoriler():
    kategoriler = GelirGiderKategori.query.order_by(GelirGiderKategori.ad).all()
    return render_template('gelir_gider/kategoriler.html', kategoriler=kategoriler)


@bp.route('/kategoriler/yeni', methods=['POST'])
@login_required
def kategori_yeni():
    ad = request.form.get('ad', '').strip()
    tip = request.form.get('tip', 'gider')
    if ad:
        k = GelirGiderKategori(ad=ad, tip=tip)
        db.session.add(k)
        db.session.commit()
        flash(f'Kategori "{ad}" eklendi.', 'success')
    return redirect(url_for('gelir_gider.index'))


@bp.route('/api/ozet')
@login_required
def api_ozet():
    yil = request.args.get('yil', date.today().year, type=int)
    labels = ['Oca', 'Şub', 'Mar', 'Nis', 'May', 'Haz',
              'Tem', 'Ağu', 'Eyl', 'Eki', 'Kas', 'Ara']
    gelir_data, gider_data = [], []
    for ay in range(1, 13):
        g = db.session.query(func.sum(GelirGider.tutar)).filter(
            GelirGider.tip == 'gelir',
            extract('year', GelirGider.tarih) == yil,
            extract('month', GelirGider.tarih) == ay
        ).scalar() or 0
        e = db.session.query(func.sum(GelirGider.tutar)).filter(
            GelirGider.tip == 'gider',
            extract('year', GelirGider.tarih) == yil,
            extract('month', GelirGider.tarih) == ay
        ).scalar() or 0
        gelir_data.append(float(g))
        gider_data.append(float(e))
    return jsonify({'labels': labels, 'gelir': gelir_data, 'gider': gider_data})
