import os
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from extensions import db, login_manager, bcrypt
from flask_migrate import Migrate
from flask_login import login_user, login_required, logout_user, current_user
from models import User, Company, Job, Application
from forms import RegisterForm, LoginForm, CompanyProfileForm, AddJobForm, ApplyForm, ReactiveForm

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-me')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///db.sqlite3')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    migrate = Migrate(app, db)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Create DB and seed demo data (runs once at startup)
    with app.app_context():
        db.create_all()
        if User.query.count() == 0:
            pw = bcrypt.generate_password_hash('password').decode()
            demo_company_user = User(email='company@example.com', password_hash=pw, role='company', name='Demo HR')
            demo_user = User(email='user@example.com', password_hash=pw, role='user', name='Demo User')
            db.session.add_all([demo_company_user, demo_user])
            db.session.commit()
            co = Company(user_id=demo_company_user.id, company_name='PT. Contoh', description='Perusahaan demo')
            db.session.add(co)
            db.session.commit()
            j1 = Job(title='Operator Produksi (Device)', location='Batam', description='Deskripsi pekerjaan', slots=3, company_id=co.id)
            j2 = Job(title='Admin Kantor', location='Jakarta', description='Deskripsi admin', slots=2, company_id=co.id)
            db.session.add_all([j1, j2])
            db.session.commit()

    # Routes
    @app.route('/')
    def index():
        jobs = Job.query.order_by(Job.created_at.desc()).all()
        return render_template('base.html', jobs=jobs)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data.lower()).first()
            if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
                login_user(user, remember=form.remember.data)
                flash('Login successful.', 'success')
                return redirect(url_for('dashboard'))
            flash('Invalid email or password.', 'danger')
        return render_template('login.html', form=form)

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        form = RegisterForm()
        if form.validate_on_submit():
            existing = User.query.filter_by(email=form.email.data.lower()).first()
            if existing:
                flash('Email already registered.', 'danger')
                return redirect(url_for('register'))
            pw_hash = bcrypt.generate_password_hash(form.password.data).decode()
            u = User(
                email=form.email.data.lower(),
                password_hash=pw_hash,
                role=form.role.data,
                name=form.name.data
            )
            db.session.add(u)
            db.session.commit()
            if form.role.data == 'company':
                co = Company(
                    user_id=u.id,
                    company_name=form.company_name.data,
                    description=form.description.data,
                    website=form.website.data
                )
                db.session.add(co)
                db.session.commit()
            flash('Account created successfully! Please login.', 'success')
            if u.role == 'company':
                login_user(u)
                return redirect(url_for('company_profile'))
            return redirect(url_for('login'))
        return render_template('register.html', form=form)

    @app.route('/reactivate', methods=['GET', 'POST'])
    def reactivate():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        form = ReactiveForm()
        if form.validate_on_submit():
            flash('Reactivation link sent to your email.', 'success')  # Placeholder
            return redirect(url_for('login'))
        return render_template('reactive.html', form=form)

    @app.route('/company-profile', methods=['GET', 'POST'])
    @login_required
    def company_profile():
        if current_user.role != 'company':
            flash('Only company accounts can access this.', 'danger')
            return redirect(url_for('index'))
        form = CompanyProfileForm()
        co = Company.query.filter_by(user_id=current_user.id).first()
        if form.validate_on_submit():
            if not co:
                co = Company(user_id=current_user.id)
                db.session.add(co)
            co.company_name = form.company_name.data
            co.description = form.description.data
            co.website = form.website.data
            db.session.commit()
            flash('Company profile saved.', 'success')
            return redirect(url_for('dashboard'))
        if co:
            form.company_name.data = co.company_name
            form.description.data = co.description
            form.website.data = co.website
        return render_template('company_profile.html', form=form, company=co)

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('Logged out.', 'info')
        return redirect(url_for('index'))

    @app.route('/dashboard')
    def dashboard():
        jobs = Job.query.order_by(Job.created_at.desc()).all()
        if current_user.is_authenticated:
            if current_user.role == 'company':
                co = Company.query.filter_by(user_id=current_user.id).first()
                if not co:
                    flash('Please complete your company profile first.', 'warning')
                    return redirect(url_for('company_profile'))
                jobs = co.jobs if co else []
                return render_template('dashboard_company.html', jobs=jobs, company=co)
            else:
                return render_template('dashboard_user.html', jobs=jobs)
        else:
            # Guest user: show job listing
            return render_template('dashboard_user.html', jobs=jobs, guest=True)

    @app.route('/job/<int:job_id>')
    def job_detail(job_id):
        job = Job.query.get_or_404(job_id)
        data = {
            'id': job.id,
            'title': job.title,
            'location': job.location,
            'description': job.description,
            'slots': job.slots,
            'is_open': job.is_open,
            'company': job.company.company_name if job.company else None,
            'applied_count': len(job.applications)
        }
        return jsonify(data)

    @app.route('/apply/<int:job_id>', methods=['GET', 'POST'])
    @login_required
    def apply(job_id):
        if current_user.role != 'user':
            flash('Only job seekers can apply for jobs.', 'danger')
            return redirect(url_for('dashboard'))
        job = Job.query.get_or_404(job_id)
        form = ApplyForm()
        existing_application = Application.query.filter_by(
            user_id=current_user.id,
            job_id=job.id
        ).first()
        if existing_application:
            flash('You have already applied for this job.', 'warning')
            return redirect(url_for('dashboard'))
        if not job.is_open:
            flash('This job is closed.', 'warning')
            return redirect(url_for('dashboard'))
        if form.validate_on_submit():
            if len(job.applications) >= job.slots:
                job.is_open = False
                db.session.commit()
                flash('Slots full, job closed automatically.', 'warning')
                return redirect(url_for('dashboard'))
            application = Application(
                user_id=current_user.id,
                job_id=job.id,
                cover_letter=form.cover_letter.data
            )
            db.session.add(application)
            db.session.commit()
            flash('Application submitted. Wait for company response.', 'success')
            return redirect(url_for('dashboard'))
        return render_template('apply.html', form=form, job=job)

    @app.route('/company/add-job', methods=['GET', 'POST'])
    @login_required
    def add_job():
        if current_user.role != 'company':
            flash('Only companies can add jobs.', 'danger')
            return redirect(url_for('dashboard'))
        co = Company.query.filter_by(user_id=current_user.id).first()
        if not co:
            flash('Please complete your company profile first.', 'warning')
            return redirect(url_for('company_profile'))
        form = AddJobForm()
        if form.validate_on_submit():
            job = Job(
                title=form.title.data,
                location=form.location.data,
                description=form.description.data,
                slots=form.slots.data,
                company_id=co.id
            )
            db.session.add(job)
            db.session.commit()
            flash('Job added.', 'success')
            return redirect(url_for('dashboard'))
        return render_template('add_job.html', form=form)

    @app.route('/about')
    def about():
        return render_template('about.html')

    @app.route('/contact')
    def contact():
        return render_template('contact.html')

    @app.route('/address')
    def address():
        return render_template('address.html')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)