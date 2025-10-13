import os
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from extensions import db, login_manager, bcrypt
from flask_migrate import Migrate
from flask_login import login_user, login_required, logout_user, current_user
from datetime import timedelta
from models import User, Company, JobListing, Application, Applicant
from forms import RegisterForm, LoginForm, CompanyProfileForm, AddJobForm, ApplyForm, ReactiveForm
from datetime import timedelta

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-me')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'mysql+pymysql://root:@localhost/nemukerja_db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REMEMBER_COOKIE_DURATION = timedelta(days=30)
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    migrate = Migrate(app, db)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

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
            user = User.query.filter_by(email=form.email.data.lower()).first()
            if user and bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                return redirect(url_for('dashboard'))
            flash('Invalid email or password.', 'danger')
        return render_template('login.html', form=form)

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        form = RegisterForm()
        if form.validate_on_submit():
            if User.query.filter_by(email=form.email.data.lower()).first():
                flash('Email already registered.', 'danger')
                return redirect(url_for('register'))

            pw_hash = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            new_user = User(
                email=form.email.data.lower(),
                password=pw_hash,
                role=form.role.data
            )
            db.session.add(new_user)
            db.session.commit()

            if form.role.data == 'applicant':

                profile = Applicant(id_user=new_user.id, full_name=form.name.data)
                db.session.add(profile)
            elif form.role.data == 'company':

                profile = Company(
                    id_user=new_user.id,
                    company_name=form.company_name.data,
                    description=form.description.data,
                    contact_email=new_user.email,
                    phone=form.phone.data
                )
                db.session.add(profile)

            db.session.commit()
            flash('Account created successfully! Please login.', 'success')
            return redirect(url_for('login'))
        return render_template('register.html', form=form)

    @app.route('/reactivate', methods=['GET', 'POST'])
    def reactivate():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        form = ReactiveForm()
        if form.validate_on_submit():
            flash('If your email exists in our system, a reactivation link has been sent.', 'info')
            return redirect(url_for('login'))
        return render_template('reactive.html', form=form)

    @app.route('/company-profile', methods=['GET', 'POST'])
    @login_required
    def company_profile():
        if current_user.role != 'company':
            flash('Only company accounts can access this page.', 'danger')
            return redirect(url_for('index'))

        company = current_user.company_profile
        if not company:

            company = Company(id_user=current_user.id, company_name="New Company")
            db.session.add(company)
            db.session.commit()

        form = CompanyProfileForm(obj=company)
        if form.validate_on_submit():
            form.populate_obj(company)
            db.session.commit()
            flash('Company profile saved.', 'success')
            return redirect(url_for('dashboard'))

        return render_template('company_profile.html', form=form, company=company)

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('index'))

    @app.route('/dashboard')
    @login_required
    def dashboard():
        if current_user.role == 'company':
            company = current_user.company_profile
            if not company or not company.company_name:
                flash('Please complete your company profile first.', 'warning')
                return redirect(url_for('company_profile'))

            jobs = company.jobs if company else []
            total_jobs = len(jobs)
            total_applications = sum(len(job.applications) for job in jobs)
            recent_applications = db.session.query(Application).join(JobListing).filter(JobListing.id_company == company.id).order_by(Application.applied_at.desc()).limit(5).all()

            return render_template('dashboard_company.html',
                                     jobs=jobs,
                                     company=company,
                                     total_jobs=total_jobs,
                                     total_applications=total_applications,
                                     recent_applications=recent_applications)
        else: 
            jobs = JobListing.query.order_by(JobListing.posted_at.desc()).all()
            return render_template('dashboard_user.html', jobs=jobs, guest=False)

    @app.route('/job/<int:job_id>')
    def job_detail(job_id):
        job = JobListing.query.get_or_404(job_id)
        data = {

            'id': job.id,
            'title': job.title,
            'location': job.location,
            'description': job.description,
            'qualifications': job.qualifications,
            'company': job.company.company_name if job.company else "N/A",
            'applied_count': len(job.applications)
        }
        return jsonify(data)

    @app.route('/apply/<int:job_id>', methods=['GET', 'POST'])
    @login_required
    def apply(job_id):
        if current_user.role != 'applicant':
            flash('Only applicants can apply for jobs.', 'danger')
            return redirect(url_for('dashboard'))

        job = JobListing.query.get_or_404(job_id)
        applicant = current_user.applicant_profile
        if not applicant:
            flash('Applicant profile not found.', 'danger')
            return redirect(url_for('dashboard'))

        if Application.query.filter_by(id_applicant=applicant.id, id_job=job.id).first():
            flash('You have already applied for this job.', 'warning')
            return redirect(url_for('dashboard'))

        form = ApplyForm()
        if form.validate_on_submit():
            application = Application(

                id_applicant=applicant.id,
                id_job=job.id,
                notes=form.cover_letter.data
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

        company = current_user.company_profile
        if not company:
            flash('Please complete your company profile first.', 'warning')
            return redirect(url_for('company_profile'))

        form = AddJobForm()
        if form.validate_on_submit():
            new_job = JobListing(
                title=form.title.data,
                location=form.location.data,
                description=form.description.data,
                qualifications=form.qualifications.data,

                id_company=company.id
            )
            db.session.add(new_job)
            db.session.commit()
            flash('Job added successfully.', 'success')
            return redirect(url_for('dashboard'))
        return render_template('add_job.html', form=form)

    @app.route('/company/job/<int:job_id>/edit', methods=['GET', 'POST'])
    @login_required
    def edit_job(job_id):
        if current_user.role != 'company':
            return redirect(url_for('dashboard'))
        job = JobListing.query.get_or_404(job_id)

        if job.company.user.id != current_user.id:
            flash('You are not authorized to edit this job.', 'danger')
            return redirect(url_for('dashboard'))

        form = AddJobForm(obj=job)
        if form.validate_on_submit():
            form.populate_obj(job)
            db.session.commit()
            flash('Job updated.', 'success')
            return redirect(url_for('dashboard'))

        return render_template('edit_job.html', form=form, job=job)

    @app.route('/company/applications')
    @login_required
    def company_applications():
        if current_user.role != 'company':
            return redirect(url_for('dashboard'))
        company = current_user.company_profile
        if not company:
            return redirect(url_for('dashboard'))

        applications = db.session.query(Application).join(JobListing).filter(JobListing.id_company == company.id).order_by(Application.applied_at.desc()).all()
        return render_template('company_applications.html', applications=applications)

    @app.route('/company/application/<int:application_id>/accept', methods=['POST'])
    @login_required
    def accept_application(application_id):
        if current_user.role != 'company':
            return redirect(url_for('dashboard'))
        application = Application.query.get_or_404(application_id)

        if application.job.company.user.id != current_user.id:
            flash('You are not authorized to manage this application.', 'danger')
            return redirect(url_for('company_applications'))
        application.status = 'Diterima'
        db.session.commit()
        flash('Application accepted.', 'success')
        return redirect(url_for('view_application', application_id=application_id))

    @app.route('/company/application/<int:application_id>/reject', methods=['POST'])
    @login_required
    def reject_application(application_id):
        if current_user.role != 'company':
            return redirect(url_for('dashboard'))
        application = Application.query.get_or_404(application_id)

        if application.job.company.user.id != current_user.id:
            flash('You are not authorized to manage this application.', 'danger')
            return redirect(url_for('company_applications'))
        application.status = 'Ditolak'
        db.session.commit()
        flash('Application rejected.', 'info')
        return redirect(url_for('view_application', application_id=application_id))

    @app.route('/company/application/<int:application_id>')
    @login_required
    def view_application(application_id):
        if current_user.role != 'company':
            return redirect(url_for('dashboard'))
        application = Application.query.get_or_404(application_id)

        if application.job.company.user.id != current_user.id:
            flash('You are not authorized to view this application.', 'danger')
            return redirect(url_for('company_applications'))
        return render_template('view_application.html', application=application)

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