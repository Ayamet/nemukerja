import os
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, session
from nemukerja.extensions import db, login_manager, bcrypt
from flask_migrate import Migrate
from flask_babel import Babel
from flask_login import login_user, login_required, logout_user, current_user
from sqlalchemy import or_

from nemukerja.models import User, Company, JobListing, Application, Applicant
from nemukerja.forms import (
    RegisterForm, LoginForm, CompanyProfileForm, AddJobForm, ApplyForm,
    ReactiveForm, ContactForm, FeedbackForm
)

# --- [PERUBAHAN UTAMA PENYEBAB ERROR] ---

# 1. Definisikan fungsi pemilih bahasa terlebih dahulu di luar 'create_app'
def get_locale():
    # Mengambil bahasa dari session jika ada, jika tidak, cocokkan dengan preferensi browser
    if 'language' in session and session['language'] in Config.LANGUAGES:
        return session['language']
    return request.accept_languages.best_match(Config.LANGUAGES)

# 2. Inisialisasi Babel dengan memberikan fungsi pemilih bahasa secara langsung
babel = Babel(locale_selector=get_locale)


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-me')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'mysql+pymysql://root:@localhost/nemukerja_db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LANGUAGES = ['en', 'id']
    BABEL_DEFAULT_LOCALE = 'en'

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inisialisasi ekstensi
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    babel.init_app(app) # Cara inisialisasi ini tetap sama
    login_manager.login_view = 'login'
    migrate = Migrate(app, db)
    
    # 3. Hapus dekorator @babel.localeselector dari sini karena sudah ditangani di atas
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # --- Routes ---

    @app.route('/')
    def index():
        jobs = JobListing.query.order_by(JobListing.posted_at.desc()).all()
        return render_template('base.html', jobs=jobs)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        form = LoginForm()
        if form.validate_on_submit():
            identifier = form.username_or_email.data
            user = User.query.filter(or_(User.username == identifier, User.email == identifier)).first()
            
            if user and bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                flash('Login berhasil.', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Username/Email atau password salah.', 'danger')
        return render_template('login.html', form=form)

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        form = RegisterForm()
        if form.validate_on_submit():
            pw_hash = bcrypt.generate_password_hash(form.password.data).decode()
            u = User(
                username=form.username.data,
                email=form.email.data.lower(),
                password=pw_hash,
                role='company' if form.role.data == 'company' else 'applicant'
            )
            db.session.add(u)
            db.session.commit()

            if u.role == 'applicant':
                applicant_profile = Applicant(id_user=u.id, full_name=form.name.data)
                db.session.add(applicant_profile)
            
            if u.role == 'company':
                co = Company(
                    id_user=u.id,
                    company_name=form.company_name.data,
                    description=form.description.data,
                    phone=form.phone.data,
                    contact_email=u.email
                )
                db.session.add(co)
            
            db.session.commit()
            flash('Akun berhasil dibuat! Silakan login.', 'success')
            return redirect(url_for('login'))
        return render_template('register.html', form=form)

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('Anda telah logout.', 'info')
        return redirect(url_for('index'))

    @app.route('/dashboard')
    def dashboard():
        jobs = JobListing.query.order_by(JobListing.posted_at.desc()).all()
        if current_user.is_authenticated:
            if current_user.role == 'company':
                co = Company.query.filter_by(id_user=current_user.id).first()
                if not co:
                    flash('Mohon lengkapi profil perusahaan Anda terlebih dahulu.', 'warning')
                    return redirect(url_for('company_profile'))
                jobs = co.jobs if co else []
                return render_template('dashboard_company.html', jobs=jobs, company=co)
            else:
                return render_template('dashboard_user.html', jobs=jobs)
        else:
            return render_template('dashboard_user.html', jobs=jobs, guest=True)

    @app.route('/job/<int:job_id>')
    def job_detail(job_id):
        job = JobListing.query.get_or_404(job_id)
        data = {
            'id': job.id, 'title': job.title, 'location': job.location,
            'description': job.description, 'qualifications': job.qualifications,
            'company': job.company.company_name if job.company else None,
            'applied_count': len(job.applications)
        }
        return jsonify(data)

    @app.route('/apply/<int:job_id>', methods=['GET', 'POST'])
    @login_required
    def apply(job_id):
        if current_user.role != 'applicant':
            flash('Hanya pencari kerja yang dapat melamar.', 'danger')
            return redirect(url_for('dashboard'))
        job = JobListing.query.get_or_404(job_id)
        form = ApplyForm()
        applicant = current_user.applicant_profile
        if not applicant:
            flash('Profil pelamar tidak ditemukan.', 'danger')
            return redirect(url_for('dashboard'))
        existing_application = Application.query.filter_by(id_applicant=applicant.id, id_job=job.id).first()
        if existing_application:
            flash('Anda sudah melamar pekerjaan ini.', 'warning')
            return redirect(url_for('dashboard'))
        if form.validate_on_submit():
            application = Application(
                id_applicant=applicant.id,
                id_job=job.id,
                notes=form.notes.data
            )
            db.session.add(application)
            db.session.commit()
            flash('Lamaran berhasil dikirim.', 'success')
            return redirect(url_for('dashboard'))
        return render_template('apply.html', form=form, job=job)

    @app.route('/company-profile', methods=['GET', 'POST'])
    @login_required
    def company_profile():
        if current_user.role != 'company':
            flash('Hanya akun perusahaan yang dapat mengakses halaman ini.', 'danger')
            return redirect(url_for('index'))
        form = CompanyProfileForm()
        co = Company.query.filter_by(id_user=current_user.id).first()
        if form.validate_on_submit():
            if not co:
                co = Company(id_user=current_user.id)
                db.session.add(co)
            co.company_name = form.company_name.data
            co.description = form.description.data
            db.session.commit()
            flash('Profil perusahaan disimpan.', 'success')
            return redirect(url_for('dashboard'))
        if co:
            form.company_name.data = co.company_name
            form.description.data = co.description
        return render_template('company_profile.html', form=form, company=co)
    
    @app.route('/company/add-job', methods=['GET', 'POST'])
    @login_required
    def add_job():
        if current_user.role != 'company':
            flash('Hanya perusahaan yang dapat menambah lowongan.', 'danger')
            return redirect(url_for('dashboard'))
        co = Company.query.filter_by(id_user=current_user.id).first()
        if not co:
            flash('Mohon lengkapi profil perusahaan Anda terlebih dahulu.', 'warning')
            return redirect(url_for('company_profile'))
        form = AddJobForm()
        if form.validate_on_submit():
            job = JobListing(
                title=form.title.data, location=form.location.data,
                description=form.description.data,
                qualifications=form.qualifications.data,
                id_company=co.id
            )
            db.session.add(job)
            db.session.commit()
            flash('Lowongan berhasil ditambahkan.', 'success')
            return redirect(url_for('dashboard'))
        return render_template('add_job.html', form=form)

    @app.route('/about')
    def about():
        return render_template('about.html')
    
    @app.route('/address')
    def address():
        return render_template('address.html')

    @app.route('/faq')
    def faq():
        return render_template('faq.html')
        
    @app.route('/reactivate', methods=['GET', 'POST'])
    def reactivate():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        form = ReactiveForm()
        if form.validate_on_submit():
            flash('Tautan reaktivasi telah dikirim ke email Anda.', 'success')
            return redirect(url_for('login'))
        return render_template('reactive.html', form=form)

    @app.route('/contact', methods=['GET', 'POST'])
    def contact():
        form = ContactForm()
        if form.validate_on_submit():
            flash('Your message has been sent successfully!', 'success')
            return redirect(url_for('contact')) 
        return render_template('contact.html', form=form)

    @app.route('/feedback', methods=['GET', 'POST'])
    def feedback():
        form = FeedbackForm()
        if form.validate_on_submit():
            flash('Thank you for your feedback!', 'success')
            return redirect(url_for('feedback'))
        return render_template('feedback.html', form=form)

    @app.route('/set_language/<lang>')
    def set_language(lang):
        if lang in Config.LANGUAGES:
            session['language'] = lang
        return redirect(request.referrer or url_for('index'))
        
    return app