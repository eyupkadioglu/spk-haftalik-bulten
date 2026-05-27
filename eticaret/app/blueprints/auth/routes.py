from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db
from app.models.user import User

bp = Blueprint('auth', __name__)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()

        if user and user.is_active and user.check_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard.index'))

        flash('Kullanıcı adı veya şifre hatalı.', 'danger')

    return render_template('auth/login.html')


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Başarıyla çıkış yapıldı.', 'info')
    return redirect(url_for('auth.login'))


@bp.route('/profil', methods=['GET', 'POST'])
@login_required
def profil():
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        if full_name:
            current_user.full_name = full_name
        if email:
            current_user.email = email
        if new_password:
            if new_password != confirm_password:
                flash('Şifreler eşleşmiyor.', 'danger')
                return redirect(url_for('auth.profil'))
            current_user.set_password(new_password)

        db.session.commit()
        flash('Profil güncellendi.', 'success')
        return redirect(url_for('auth.profil'))

    return render_template('auth/profil.html')
