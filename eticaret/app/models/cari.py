from datetime import datetime
from app.extensions import db


class Cari(db.Model):
    __tablename__ = 'cari'

    id = db.Column(db.Integer, primary_key=True)
    cari_kodu = db.Column(db.String(32), unique=True, nullable=False, index=True)
    unvan = db.Column(db.String(256), nullable=False)
    cari_tipi = db.Column(db.String(16), nullable=False)  # musteri | tedarikci | her_ikisi
    vergi_no = db.Column(db.String(32))
    tckn = db.Column(db.String(11))
    vergi_dairesi = db.Column(db.String(128))
    telefon = db.Column(db.String(32))
    email = db.Column(db.String(128))
    adres = db.Column(db.Text)
    sehir = db.Column(db.String(64))
    ulke = db.Column(db.String(64), default='Türkiye')
    acik_hesap_limiti = db.Column(db.Numeric(18, 2), default=0)
    odeme_vadesi = db.Column(db.Integer, default=30)
    notlar = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    faturalar = db.relationship('Fatura', backref='cari', lazy='dynamic',
                                foreign_keys='Fatura.cari_id')
    siparisler = db.relationship('Siparis', backref='cari', lazy='dynamic',
                                 foreign_keys='Siparis.cari_id')
    kasa_hareketler = db.relationship('KasaHareket', backref='cari', lazy='dynamic',
                                      foreign_keys='KasaHareket.cari_id')

    @property
    def bakiye(self):
        alacak = sum(
            float(f.kalan_tutar or 0)
            for f in self.faturalar
            if f.fatura_tipi == 'satis' and f.durum != 'iptal'
        )
        borc = sum(
            float(f.kalan_tutar or 0)
            for f in self.faturalar
            if f.fatura_tipi == 'alis' and f.durum != 'iptal'
        )
        return alacak - borc

    def __repr__(self):
        return f'<Cari {self.cari_kodu} {self.unvan}>'
