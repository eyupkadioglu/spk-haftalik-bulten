from datetime import datetime
from app.extensions import db


class DovizKur(db.Model):
    __tablename__ = 'doviz_kurlar'

    id = db.Column(db.Integer, primary_key=True)
    tarih = db.Column(db.Date, nullable=False)
    kod = db.Column(db.String(3), nullable=False)      # USD, EUR
    alis = db.Column(db.Numeric(12, 4), default=0)
    satis = db.Column(db.Numeric(12, 4), default=0)
    guncelleme = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('tarih', 'kod', name='uq_doviz_tarih_kod'),)

    def __repr__(self):
        return f'<DovizKur {self.tarih} {self.kod} satis={self.satis}>'
