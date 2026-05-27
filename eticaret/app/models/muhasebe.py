from datetime import datetime
from app.extensions import db


class HesapPlani(db.Model):
    __tablename__ = 'hesap_plani'

    id = db.Column(db.Integer, primary_key=True)
    kod = db.Column(db.String(32), unique=True, nullable=False, index=True)
    ad = db.Column(db.String(256), nullable=False)
    tip = db.Column(db.String(16), nullable=False)
    # aktif | pasif | gelir | gider | oz_kaynak
    ust_kod = db.Column(db.String(32), db.ForeignKey('hesap_plani.kod'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    alt_hesaplar = db.relationship('HesapPlani',
                                   backref=db.backref('ust_hesap', remote_side='HesapPlani.kod'))
    kalemler = db.relationship('MuhasebeKalem', backref='hesap', lazy='dynamic',
                               foreign_keys='MuhasebeKalem.hesap_kodu')

    def __repr__(self):
        return f'<HesapPlani {self.kod} {self.ad}>'


class MuhasebeKayit(db.Model):
    __tablename__ = 'muhasebe_kayit'

    id = db.Column(db.Integer, primary_key=True)
    tarih = db.Column(db.Date, nullable=False)
    aciklama = db.Column(db.String(512), nullable=False)
    belge_no = db.Column(db.String(64))
    belge_tipi = db.Column(db.String(32))
    # fatura | tahsilat | odeme | gelir_gider | diger
    fatura_id = db.Column(db.Integer, db.ForeignKey('fatura.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    kalemler = db.relationship('MuhasebeKalem', backref='kayit', lazy='joined',
                               cascade='all, delete-orphan')

    def __repr__(self):
        return f'<MuhasebeKayit {self.belge_no}>'


class MuhasebeKalem(db.Model):
    __tablename__ = 'muhasebe_kalem'

    id = db.Column(db.Integer, primary_key=True)
    kayit_id = db.Column(db.Integer, db.ForeignKey('muhasebe_kayit.id'), nullable=False)
    hesap_kodu = db.Column(db.String(32), db.ForeignKey('hesap_plani.kod'), nullable=False)
    borc = db.Column(db.Numeric(18, 2), default=0)
    alacak = db.Column(db.Numeric(18, 2), default=0)
    aciklama = db.Column(db.String(256))

    def __repr__(self):
        return f'<MuhasebeKalem {self.hesap_kodu}>'
