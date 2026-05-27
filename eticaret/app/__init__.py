from flask import Flask
from config import config
from app.extensions import db, login_manager, migrate, csrf
from app.utils import register_template_filters


def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Bu sayfaya erişmek için giriş yapmalısınız.'
    login_manager.login_message_category = 'warning'

    register_template_filters(app)

    from datetime import datetime

    @app.context_processor
    def inject_globals():
        from app.models.ayar import FirmaAyar
        from flask_login import current_user
        ayar = None
        try:
            if current_user and current_user.is_authenticated:
                ayar = FirmaAyar.get()
        except Exception:
            pass
        return {'now': datetime.now, 'firma_ayar': ayar}

    # Import models so Flask-Migrate can detect them
    with app.app_context():
        from app.models import (User, Cari, StokKategori, Stok, StokHareket,
                                Siparis, SiparisKalem, Fatura, FaturaKalem,
                                KasaHesap, KasaHareket, GelirGiderKategori,
                                GelirGider, HesapPlani, MuhasebeKayit, MuhasebeKalem,
                                Teklif, TeklifKalem, DovizKur)
        from app.models.ayar import FirmaAyar

    from app.blueprints.auth.routes import bp as auth_bp
    from app.blueprints.dashboard.routes import bp as dashboard_bp
    from app.blueprints.cari.routes import bp as cari_bp
    from app.blueprints.stok.routes import bp as stok_bp
    from app.blueprints.siparis.routes import bp as siparis_bp
    from app.blueprints.fatura.routes import bp as fatura_bp
    from app.blueprints.kasa.routes import bp as kasa_bp
    from app.blueprints.gelir_gider.routes import bp as gelir_gider_bp
    from app.blueprints.muhasebe.routes import bp as muhasebe_bp
    from app.blueprints.teklif.routes import bp as teklif_bp
    from app.blueprints.import_export.routes import bp as import_export_bp
    from app.blueprints.ayarlar.routes import bp as ayarlar_bp
    from app.blueprints.fatura_import.routes import bp as fatura_import_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/')
    app.register_blueprint(cari_bp, url_prefix='/cari')
    app.register_blueprint(stok_bp, url_prefix='/stok')
    app.register_blueprint(siparis_bp, url_prefix='/siparis')
    app.register_blueprint(fatura_bp, url_prefix='/fatura')
    app.register_blueprint(kasa_bp, url_prefix='/kasa')
    app.register_blueprint(gelir_gider_bp, url_prefix='/gelir-gider')
    app.register_blueprint(muhasebe_bp, url_prefix='/muhasebe')
    app.register_blueprint(teklif_bp, url_prefix='/teklif')
    app.register_blueprint(import_export_bp, url_prefix='/import-export')
    app.register_blueprint(ayarlar_bp, url_prefix='/ayarlar')
    app.register_blueprint(fatura_import_bp, url_prefix='/fatura/import')

    return app
