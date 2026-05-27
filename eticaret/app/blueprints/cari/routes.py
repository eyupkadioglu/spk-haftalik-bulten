from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.cari import Cari
from app.models.fatura import Fatura
from app.utils import next_sequence

bp = Blueprint('cari', __name__)


@bp.route('/')
@login_required
def index():
    tip = request.args.get('tip', '')
    q = request.args.get('q', '').strip()
    query = Cari.query.filter_by(is_active=True)
    if tip in ('musteri', 'tedarikci', 'her_ikisi'):
        query = query.filter(Cari.cari_tipi == tip)
    if q:
        query = query.filter(
            db.or_(Cari.unvan.ilike(f'%{q}%'), Cari.cari_kodu.ilike(f'%{q}%'),
                   Cari.vergi_no.ilike(f'%{q}%'))
        )
    cariler = query.order_by(Cari.unvan).all()
    return render_template('cari/index.html', cariler=cariler, tip=tip, q=q)


@bp.route('/<int:id>')
@login_required
def detail(id):
    cari = Cari.query.get_or_404(id)
    faturalar = cari.faturalar.order_by(Fatura.fatura_tarihi.desc()).limit(20).all()
    return render_template('cari/detail.html', cari=cari, faturalar=faturalar)


@bp.route('/yeni', methods=['GET', 'POST'])
@login_required
def yeni():
    if request.method == 'POST':
        cari = Cari(
            cari_kodu=next_sequence('CRI', Cari, 'cari_kodu'),
            unvan=request.form['unvan'],
            cari_tipi=request.form['cari_tipi'],
            vergi_no=request.form.get('vergi_no'),
            tckn=request.form.get('tckn'),
            vergi_dairesi=request.form.get('vergi_dairesi'),
            telefon=request.form.get('telefon'),
            email=request.form.get('email'),
            adres=request.form.get('adres'),
            sehir=request.form.get('sehir'),
            ulke=request.form.get('ulke', 'Türkiye'),
            odeme_vadesi=int(request.form.get('odeme_vadesi') or 30),
            notlar=request.form.get('notlar'),
        )
        db.session.add(cari)
        db.session.commit()
        flash(f'Cari "{cari.unvan}" oluşturuldu.', 'success')
        return redirect(url_for('cari.detail', id=cari.id))
    return render_template('cari/form.html', cari=None)


@bp.route('/<int:id>/duzenle', methods=['GET', 'POST'])
@login_required
def duzenle(id):
    cari = Cari.query.get_or_404(id)
    if request.method == 'POST':
        cari.unvan = request.form['unvan']
        cari.cari_tipi = request.form['cari_tipi']
        cari.vergi_no = request.form.get('vergi_no')
        cari.tckn = request.form.get('tckn')
        cari.vergi_dairesi = request.form.get('vergi_dairesi')
        cari.telefon = request.form.get('telefon')
        cari.email = request.form.get('email')
        cari.adres = request.form.get('adres')
        cari.sehir = request.form.get('sehir')
        cari.ulke = request.form.get('ulke', 'Türkiye')
        cari.odeme_vadesi = int(request.form.get('odeme_vadesi') or 30)
        cari.notlar = request.form.get('notlar')
        db.session.commit()
        flash('Cari güncellendi.', 'success')
        return redirect(url_for('cari.detail', id=cari.id))
    return render_template('cari/form.html', cari=cari)


@bp.route('/<int:id>/sil', methods=['POST'])
@login_required
def sil(id):
    cari = Cari.query.get_or_404(id)
    cari.is_active = False
    db.session.commit()
    flash(f'Cari "{cari.unvan}" silindi.', 'warning')
    return redirect(url_for('cari.index'))


@bp.route('/api/search')
@login_required
def api_search():
    q = request.args.get('q', '').strip()
    tip = request.args.get('tip', '')
    query = Cari.query.filter_by(is_active=True)
    if tip:
        query = query.filter(
            db.or_(Cari.cari_tipi == tip, Cari.cari_tipi == 'her_ikisi')
        )
    if q:
        query = query.filter(
            db.or_(Cari.unvan.ilike(f'%{q}%'), Cari.cari_kodu.ilike(f'%{q}%'))
        )
    results = [{'id': c.id, 'text': f'{c.cari_kodu} — {c.unvan}'} for c in query.limit(20).all()]
    return jsonify(results)
