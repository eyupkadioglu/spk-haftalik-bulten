from datetime import datetime
from app.extensions import db


class StokKategori(db.Model):
    __tablename__ = 'stok_kategori'

    id = db.Column(db.Integer, primary_key=True)
    ad = db.Column(db.String(128), nullable=False)
    ust_id = db.Column(db.Integer, db.ForeignKey('stok_kategori.id'), nullable=True)
    alt_kategoriler = db.relationship('StokKategori',
                                      backref=db.backref('ust', remote_side='StokKategori.id'),
                                      lazy='dynamic')
    stoklar = db.relationship('Stok', backref='kategori', lazy='dynamic')

    def __repr__(self):
        return f'<StokKategori {self.ad}>'


class Stok(db.Model):
    __tablename__ = 'stok'

    id = db.Column(db.Integer, primary_key=True)
    stok_kodu = db.Column(db.String(64), unique=True, nullable=False, index=True)
    barkod = db.Column(db.String(64), unique=True, nullable=True)
    ad = db.Column(db.String(256), nullable=False)
    kategori_id = db.Column(db.Integer, db.ForeignKey('stok_kategori.id'), nullable=True)
    birim = db.Column(db.String(32), default='Adet')
    alis_fiyati = db.Column(db.Numeric(18, 4), default=0)
    satis_fiyati = db.Column(db.Numeric(18, 4), default=0)
    kdv_orani = db.Column(db.Numeric(5, 2), default=20)
    stok_miktari = db.Column(db.Numeric(18, 3), default=0)
    min_stok = db.Column(db.Numeric(18, 3), default=0)
    max_stok = db.Column(db.Numeric(18, 3), default=0)
    aciklama = db.Column(db.Text)
    resim = db.Column(db.String(255))
    urun_tipi = db.Column(db.String(10), default='stok')  # stok / hizmet
    marka = db.Column(db.String(100))
    tedarikci_id = db.Column(db.Integer, db.ForeignKey('cari.id'), nullable=True)
    tedarikci_kodu = db.Column(db.String(100))
    alis_kdv_orani = db.Column(db.Numeric(5, 2), default=20)
    alis_para_birimi = db.Column(db.String(5), default='TRY')
    satis_para_birimi = db.Column(db.String(5), default='TRY')
    ortalama_maliyet = db.Column(db.Numeric(18, 4), default=0)  # ağırlıklı ortalama maliyet
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tedarikci = db.relationship('Cari', backref='stoklar', foreign_keys=[tedarikci_id])
    hareketler = db.relationship('StokHareket', backref='stok', lazy='dynamic')
    fatura_kalemleri = db.relationship('FaturaKalem', backref='stok', lazy='dynamic')
    siparis_kalemleri = db.relationship('SiparisKalem', backref='stok', lazy='dynamic')

    def guncelle_ortalama_maliyet(self, qty_in, price_in):
        """Alış/giriş işleminden önce çağır — ortalama maliyeti günceller."""
        old_qty = float(self.stok_miktari or 0)
        old_avg = float(self.ortalama_maliyet or 0)
        total_qty = old_qty + qty_in
        if total_qty > 0:
            self.ortalama_maliyet = round(
                ((old_qty * old_avg) + (qty_in * price_in)) / total_qty, 4
            )
        elif price_in:
            self.ortalama_maliyet = price_in

    @property
    def dusuk_stok(self):
        return float(self.stok_miktari or 0) <= float(self.min_stok or 0)

    def __repr__(self):
        return f'<Stok {self.stok_kodu} {self.ad}>'


class StokHareket(db.Model):
    __tablename__ = 'stok_hareket'

    id = db.Column(db.Integer, primary_key=True)
    stok_id = db.Column(db.Integer, db.ForeignKey('stok.id'), nullable=False)
    hareket_tipi = db.Column(db.String(32), nullable=False)
    # giris | cikis | iade_giris | iade_cikis | sayim | devir
    miktar = db.Column(db.Numeric(18, 3), nullable=False)
    birim_fiyat = db.Column(db.Numeric(18, 4), default=0)
    toplam_tutar = db.Column(db.Numeric(18, 2), default=0)
    fatura_id = db.Column(db.Integer, db.ForeignKey('fatura.id'), nullable=True)
    aciklama = db.Column(db.String(512))
    tarih = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<StokHareket {self.hareket_tipi} {self.miktar}>'
