from app.extensions import db


class FirmaAyar(db.Model):
    __tablename__ = 'firma_ayar'
    id = db.Column(db.Integer, primary_key=True)
    firma_adi = db.Column(db.String(200), default='')
    adres = db.Column(db.Text, default='')
    telefon = db.Column(db.String(50), default='')
    email = db.Column(db.String(120), default='')
    website = db.Column(db.String(120), default='')
    vergi_no = db.Column(db.String(20), default='')
    vergi_dairesi = db.Column(db.String(100), default='')
    logo = db.Column(db.String(255))
    varsayilan_para_birimi = db.Column(db.String(5), default='TRY')
    teklif_notu = db.Column(db.Text, default='')
    fatura_notu = db.Column(db.Text, default='')

    @classmethod
    def get(cls):
        ayar = cls.query.first()
        if not ayar:
            ayar = cls()
            db.session.add(ayar)
            db.session.commit()
        return ayar
