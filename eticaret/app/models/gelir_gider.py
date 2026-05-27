from datetime import datetime
from app.extensions import db


class GelirGiderKategori(db.Model):
    __tablename__ = 'gelir_gider_kategori'

    id = db.Column(db.Integer, primary_key=True)
    ad = db.Column(db.String(128), nullable=False)
    tip = db.Column(db.String(16), nullable=False)  # gelir | gider
    ust_id = db.Column(db.Integer, db.ForeignKey('gelir_gider_kategori.id'), nullable=True)
    alt_kategoriler = db.relationship('GelirGiderKategori',
                                      backref=db.backref('ust', remote_side='GelirGiderKategori.id'))
    kayitlar = db.relationship('GelirGider', backref='kategori', lazy='dynamic')

    def __repr__(self):
        return f'<GelirGiderKategori {self.ad}>'


class GelirGider(db.Model):
    __tablename__ = 'gelir_gider'

    id = db.Column(db.Integer, primary_key=True)
    tip = db.Column(db.String(16), nullable=False)  # gelir | gider
    kategori_id = db.Column(db.Integer, db.ForeignKey('gelir_gider_kategori.id'), nullable=True)
    tutar = db.Column(db.Numeric(18, 2), nullable=False)
    kdv_tutari = db.Column(db.Numeric(18, 2), default=0)
    aciklama = db.Column(db.String(512))
    tarih = db.Column(db.Date, nullable=False)
    kasa_id = db.Column(db.Integer, db.ForeignKey('kasa_hesap.id'), nullable=True)
    belge_no = db.Column(db.String(64))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    kasa = db.relationship('KasaHesap', backref='gelir_giderler',
                           foreign_keys=[kasa_id])

    def __repr__(self):
        return f'<GelirGider {self.tip} {self.tutar}>'
