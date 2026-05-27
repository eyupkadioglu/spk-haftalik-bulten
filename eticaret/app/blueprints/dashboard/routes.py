from datetime import date, timedelta
from flask import Blueprint, render_template, jsonify
from flask_login import login_required
from sqlalchemy import func, extract
from app.extensions import db
from app.models.fatura import Fatura
from app.models.stok import Stok
from app.models.kasa import KasaHesap
from app.models.cari import Cari
from app.utils_kur import son_kurlar, kur_guncelle_db

bp = Blueprint('dashboard', __name__)


@bp.route('/')
@login_required
def index():
    today = date.today()
    month_start = today.replace(day=1)

    satis_toplam = db.session.query(func.sum(Fatura.genel_toplam)).filter(
        Fatura.fatura_tipi == 'satis',
        Fatura.fatura_tarihi >= month_start,
        Fatura.durum != 'iptal'
    ).scalar() or 0

    alis_toplam = db.session.query(func.sum(Fatura.genel_toplam)).filter(
        Fatura.fatura_tipi == 'alis',
        Fatura.fatura_tarihi >= month_start,
        Fatura.durum != 'iptal'
    ).scalar() or 0

    musteri_sayisi = Cari.query.filter_by(cari_tipi='musteri', is_active=True).count()
    dusuk_stok_sayisi = Stok.query.filter(
        Stok.is_active == True,
        Stok.stok_miktari <= Stok.min_stok
    ).count()

    kasa_bakiye = db.session.query(func.sum(KasaHesap.bakiye)).filter_by(is_active=True).scalar() or 0
    son_faturalar = Fatura.query.order_by(Fatura.created_at.desc()).limit(8).all()
    kurlar = son_kurlar()

    return render_template('dashboard/index.html',
                           satis_toplam=satis_toplam,
                           alis_toplam=alis_toplam,
                           musteri_sayisi=musteri_sayisi,
                           dusuk_stok_sayisi=dusuk_stok_sayisi,
                           kasa_bakiye=kasa_bakiye,
                           son_faturalar=son_faturalar,
                           kurlar=kurlar)


@bp.route('/api/dashboard-stats')
@login_required
def dashboard_stats():
    today = date.today()
    labels, satis_data, alis_data = [], [], []

    for i in range(5, -1, -1):
        d = today.replace(day=1) - timedelta(days=i * 28)
        ay = d.replace(day=1)
        ay_sonu = (ay.replace(month=ay.month % 12 + 1, day=1) - timedelta(days=1)) if ay.month < 12 else ay.replace(month=12, day=31)
        labels.append(ay.strftime('%b %Y'))

        s = db.session.query(func.sum(Fatura.genel_toplam)).filter(
            Fatura.fatura_tipi == 'satis',
            Fatura.fatura_tarihi >= ay,
            Fatura.fatura_tarihi <= ay_sonu,
            Fatura.durum != 'iptal'
        ).scalar() or 0
        satis_data.append(float(s))

        a = db.session.query(func.sum(Fatura.genel_toplam)).filter(
            Fatura.fatura_tipi == 'alis',
            Fatura.fatura_tarihi >= ay,
            Fatura.fatura_tarihi <= ay_sonu,
            Fatura.durum != 'iptal'
        ).scalar() or 0
        alis_data.append(float(a))

    return jsonify({'labels': labels, 'satis': satis_data, 'alis': alis_data})


@bp.route('/api/kur-guncelle', methods=['POST'])
@login_required
def kur_guncelle():
    """TCMB'den önceki iş günü satış kurunu çekip DB'ye kaydeder."""
    sonuc = kur_guncelle_db()
    if sonuc is None:
        return jsonify({'ok': False, 'mesaj': 'TCMB\'ye ulaşılamadı, daha sonra tekrar deneyin.'}), 503
    veri = {k: {'satis': v['satis'], 'alis': v['alis'], 'tarih': v['tarih'].strftime('%d.%m.%Y')}
            for k, v in sonuc.items()}
    return jsonify({'ok': True, 'kurlar': veri})


@bp.route('/api/son-kurlar')
@login_required
def api_son_kurlar():
    kurlar = son_kurlar()
    veri = {k: {'satis': v['satis'], 'alis': v['alis'], 'tarih': v['tarih'].strftime('%d.%m.%Y')}
            for k, v in kurlar.items()}
    return jsonify(veri)
