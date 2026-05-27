from datetime import datetime
from app.extensions import db


class Teklif(db.Model):
    __tablename__ = 'teklifler'
    id = db.Column(db.Integer, primary_key=True)
    teklif_no = db.Column(db.String(30), unique=True, nullable=False)
    cari_id = db.Column(db.Integer, db.ForeignKey('cari.id'), nullable=False)
    teklif_tarihi = db.Column(db.Date, default=datetime.today)
    gecerlilik_tarihi = db.Column(db.Date)
    durum = db.Column(db.String(20), default='taslak')  # taslak/gonderildi/siparise_donustu/iptal
    siparis_id = db.Column(db.Integer, db.ForeignKey('siparis.id'), nullable=True)
    para_birimi = db.Column(db.String(5), default='TRY')
    ara_toplam = db.Column(db.Numeric(15, 2), default=0)
    kdv_toplam = db.Column(db.Numeric(15, 2), default=0)
    genel_toplam = db.Column(db.Numeric(15, 2), default=0)
    notlar = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    cari = db.relationship('Cari', backref='teklifler')
    user = db.relationship('User', backref='teklifler')
    siparis = db.relationship('Siparis', backref='teklif', foreign_keys=[siparis_id])
    kalemler = db.relationship('TeklifKalem', backref='teklif',
                               cascade='all,delete-orphan', lazy='dynamic',
                               order_by='TeklifKalem.sira')


class TeklifKalem(db.Model):
    __tablename__ = 'teklif_kalemler'
    id = db.Column(db.Integer, primary_key=True)
    teklif_id = db.Column(db.Integer, db.ForeignKey('teklifler.id'), nullable=False)
    stok_id = db.Column(db.Integer, db.ForeignKey('stok.id'))
    aciklama = db.Column(db.String(300))
    miktar = db.Column(db.Numeric(15, 3), default=1)
    birim = db.Column(db.String(20), default='Adet')
    birim_fiyat = db.Column(db.Numeric(15, 2), default=0)
    iskonto_orani = db.Column(db.Numeric(5, 2), default=0)
    kdv_orani = db.Column(db.Numeric(5, 2), default=20)
    kdv_tutari = db.Column(db.Numeric(15, 2), default=0)
    toplam_tutar = db.Column(db.Numeric(15, 2), default=0)
    sira = db.Column(db.Integer, default=0)

    stok = db.relationship('Stok')
