from datetime import datetime
from app.extensions import db


class KasaHesap(db.Model):
    __tablename__ = 'kasa_hesap'

    id = db.Column(db.Integer, primary_key=True)
    ad = db.Column(db.String(128), nullable=False)
    hesap_tipi = db.Column(db.String(32), default='kasa')  # kasa | banka
    banka_adi = db.Column(db.String(128), nullable=True)
    hesap_no = db.Column(db.String(64), nullable=True)
    iban = db.Column(db.String(32), nullable=True)
    para_birimi = db.Column(db.String(8), default='TRY')
    bakiye = db.Column(db.Numeric(18, 2), default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    hareketler = db.relationship('KasaHareket', backref='kasa_hesap', lazy='dynamic',
                                 foreign_keys='KasaHareket.kasa_id')

    def __repr__(self):
        return f'<KasaHesap {self.ad}>'


class KasaHareket(db.Model):
    __tablename__ = 'kasa_hareket'

    id = db.Column(db.Integer, primary_key=True)
    kasa_id = db.Column(db.Integer, db.ForeignKey('kasa_hesap.id'), nullable=False)
    hedef_kasa_id = db.Column(db.Integer, db.ForeignKey('kasa_hesap.id'), nullable=True)
    hareket_tipi = db.Column(db.String(32), nullable=False)
    # tahsilat | odeme | giris | cikis | virman
    tutar = db.Column(db.Numeric(18, 2), nullable=False)
    aciklama = db.Column(db.String(512))
    tarih = db.Column(db.DateTime, default=datetime.utcnow)
    cari_id = db.Column(db.Integer, db.ForeignKey('cari.id'), nullable=True)
    fatura_id = db.Column(db.Integer, db.ForeignKey('fatura.id'), nullable=True)
    belge_no = db.Column(db.String(64))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    hedef_kasa = db.relationship('KasaHesap', foreign_keys=[hedef_kasa_id],
                                 backref='gelen_virmanlar')

    def __repr__(self):
        return f'<KasaHareket {self.hareket_tipi} {self.tutar}>'
