from datetime import datetime
from app.extensions import db


class Fatura(db.Model):
    __tablename__ = 'fatura'

    id = db.Column(db.Integer, primary_key=True)
    fatura_no = db.Column(db.String(64), unique=True, nullable=False, index=True)
    fatura_tipi = db.Column(db.String(16), nullable=False)  # satis | alis
    cari_id = db.Column(db.Integer, db.ForeignKey('cari.id'), nullable=False)
    siparis_id = db.Column(db.Integer, db.ForeignKey('siparis.id'), nullable=True)
    fatura_tarihi = db.Column(db.Date, nullable=False)
    vade_tarihi = db.Column(db.Date, nullable=True)
    durum = db.Column(db.String(32), default='taslak')
    # taslak | onaylandi | kismi_odendi | odendi | iptal
    odeme_sekli = db.Column(db.String(32), nullable=True)
    # nakit | havale | cek | senet | kredi_karti
    ara_toplam = db.Column(db.Numeric(18, 2), default=0)
    kdv_toplam = db.Column(db.Numeric(18, 2), default=0)
    genel_toplam = db.Column(db.Numeric(18, 2), default=0)
    odenen_tutar = db.Column(db.Numeric(18, 2), default=0)
    kalan_tutar = db.Column(db.Numeric(18, 2), default=0)
    iskonto_orani = db.Column(db.Numeric(5, 2), default=0)
    notlar = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    kalemler = db.relationship('FaturaKalem', backref='fatura', lazy='joined',
                               cascade='all, delete-orphan',
                               order_by='FaturaKalem.sira')
    tahsilatlar = db.relationship('KasaHareket', backref='fatura', lazy='dynamic',
                                  foreign_keys='KasaHareket.fatura_id')
    stok_hareketler = db.relationship('StokHareket', backref='fatura', lazy='dynamic',
                                      foreign_keys='StokHareket.fatura_id')

    def __repr__(self):
        return f'<Fatura {self.fatura_no}>'


class FaturaKalem(db.Model):
    __tablename__ = 'fatura_kalem'

    id = db.Column(db.Integer, primary_key=True)
    fatura_id = db.Column(db.Integer, db.ForeignKey('fatura.id'), nullable=False)
    stok_id = db.Column(db.Integer, db.ForeignKey('stok.id'), nullable=True)
    aciklama = db.Column(db.String(512), nullable=False)
    miktar = db.Column(db.Numeric(18, 3), nullable=False)
    birim = db.Column(db.String(32), default='Adet')
    birim_fiyat = db.Column(db.Numeric(18, 4), nullable=False)
    iskonto_orani = db.Column(db.Numeric(5, 2), default=0)
    kdv_orani = db.Column(db.Numeric(5, 2), default=20)
    kdv_tutari = db.Column(db.Numeric(18, 2), default=0)
    toplam_tutar = db.Column(db.Numeric(18, 2), nullable=False)
    maliyet_fiyat = db.Column(db.Numeric(18, 4), nullable=True)  # satış anındaki ortalama maliyet snapshot
    sira = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<FaturaKalem {self.aciklama}>'
