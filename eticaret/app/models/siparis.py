from datetime import datetime
from app.extensions import db


class Siparis(db.Model):
    __tablename__ = 'siparis'

    id = db.Column(db.Integer, primary_key=True)
    siparis_no = db.Column(db.String(64), unique=True, nullable=False, index=True)
    siparis_tipi = db.Column(db.String(16), nullable=False)  # satis | alis
    cari_id = db.Column(db.Integer, db.ForeignKey('cari.id'), nullable=False)
    siparis_tarihi = db.Column(db.Date, nullable=False)
    teslim_tarihi = db.Column(db.Date, nullable=True)
    durum = db.Column(db.String(32), default='acik')
    # acik | onaylandi | kismi_teslim | tamamlandi | iptal
    genel_toplam = db.Column(db.Numeric(18, 2), default=0)
    notlar = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    kalemler = db.relationship('SiparisKalem', backref='siparis', lazy='joined',
                               cascade='all, delete-orphan',
                               order_by='SiparisKalem.sira')
    faturalar = db.relationship('Fatura', backref='siparis', lazy='dynamic',
                                foreign_keys='Fatura.siparis_id')

    def __repr__(self):
        return f'<Siparis {self.siparis_no}>'


class SiparisKalem(db.Model):
    __tablename__ = 'siparis_kalem'

    id = db.Column(db.Integer, primary_key=True)
    siparis_id = db.Column(db.Integer, db.ForeignKey('siparis.id'), nullable=False)
    stok_id = db.Column(db.Integer, db.ForeignKey('stok.id'), nullable=True)
    aciklama = db.Column(db.String(512), nullable=False)
    miktar = db.Column(db.Numeric(18, 3), nullable=False)
    birim = db.Column(db.String(32), default='Adet')
    birim_fiyat = db.Column(db.Numeric(18, 4), nullable=False)
    kdv_orani = db.Column(db.Numeric(5, 2), default=20)
    toplam_tutar = db.Column(db.Numeric(18, 2), nullable=False)
    teslim_miktar = db.Column(db.Numeric(18, 3), default=0)
    sira = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<SiparisKalem {self.aciklama}>'
