import os
import uuid
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required
from app.extensions import db
from app.models.ayar import FirmaAyar

bp = Blueprint('ayarlar', __name__)


def _kaydet_logo(dosya):
    if not dosya or dosya.filename == '':
        return None
    ext = os.path.splitext(dosya.filename)[1].lower()
    izinli = current_app.config.get('UPLOAD_EXTENSIONS', {'.jpg', '.jpeg', '.png', '.gif', '.webp'})
    if ext not in izinli:
        return None
    klasor = os.path.join(current_app.root_path, 'static', 'uploads', 'firma')
    os.makedirs(klasor, exist_ok=True)
    dosya_adi = f"logo{ext}"
    dosya.save(os.path.join(klasor, dosya_adi))
    return f"uploads/firma/{dosya_adi}"


@bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    ayar = FirmaAyar.get()
    if request.method == 'POST':
        ayar.firma_adi = request.form.get('firma_adi', '')
        ayar.adres = request.form.get('adres', '')
        ayar.telefon = request.form.get('telefon', '')
        ayar.email = request.form.get('email', '')
        ayar.website = request.form.get('website', '')
        ayar.vergi_no = request.form.get('vergi_no', '')
        ayar.vergi_dairesi = request.form.get('vergi_dairesi', '')
        ayar.varsayilan_para_birimi = request.form.get('varsayilan_para_birimi', 'TRY')
        ayar.teklif_notu = request.form.get('teklif_notu', '')
        ayar.fatura_notu = request.form.get('fatura_notu', '')

        if request.form.get('logo_sil') == '1':
            _logo_sil(ayar)
            ayar.logo = None

        yeni_logo = _kaydet_logo(request.files.get('logo'))
        if yeni_logo:
            ayar.logo = yeni_logo

        db.session.commit()
        flash('Ayarlar kaydedildi.', 'success')
        return redirect(url_for('ayarlar.index'))

    return render_template('ayarlar/index.html', ayar=ayar)


def _logo_sil(ayar):
    if ayar.logo:
        tam_yol = os.path.join(current_app.root_path, 'static', ayar.logo)
        if os.path.exists(tam_yol):
            os.remove(tam_yol)
