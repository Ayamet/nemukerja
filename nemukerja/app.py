import os
import uuid
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, send_from_directory, current_app
from nemukerja.extensions import db, login_manager, bcrypt
from flask_migrate import Migrate
from flask_login import login_user, login_required, logout_user, current_user
from datetime import timedelta
from nemukerja.models import User, Company, JobListing, Application, Applicant, Notification
from nemukerja.forms import RegisterForm, LoginForm, CompanyProfileForm, AddJobForm, ApplyForm, ReactiveForm
from werkzeug.utils import secure_filename
import json

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-me')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'mysql+pymysql://root:@localhost/nemukerja_db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REMEMBER_COOKIE_DURATION = timedelta(days=30)
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024 

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

    # Admin authorization decorator - INSIDE create_app
    def admin_required(f):
        @login_required
        def decorated_function(*args, **kwargs):
            if current_user.role != 'admin':
                flash('Admin access required.', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        decorated_function.__name__ = f.__name__
        return decorated_function

    # Admin Routes - INSIDE create_app
    @app.route('/admin/dashboard')
    @login_required
    @admin_required
    def admin_dashboard():
        # Get statistics for admin dashboard
        total_users = User.query.count()
        total_companies = Company.query.count()
        total_jobs = JobListing.query.count()
        total_applications = Application.query.count()
        
        # Get user counts by role
        user_count = User.query.filter_by(role='applicant').count()
        company_user_count = User.query.filter_by(role='company').count()
        
        # Get job statistics
        jobs = JobListing.query.all()
        open_jobs = len([job for job in jobs if getattr(job, 'is_open', True)])
        closed_jobs = len([job for job in jobs if not getattr(job, 'is_open', True)])
        
        # Recent activity
        recent_activity = []
        
        return render_template('admin_dashboard.html',
                             total_users=total_users,
                             total_companies=total_companies,
                             total_jobs=total_jobs,
                             total_applications=total_applications,
                             user_count=user_count,
                             company_user_count=company_user_count,
                             open_jobs=open_jobs,
                             closed_jobs=closed_jobs,
                             recent_activity=recent_activity)

    @app.route('/admin/users')
    @login_required
    @admin_required
    def admin_users():
        users = User.query.all()
        return render_template('admin_users.html', users=users)

    @app.route('/admin/companies')
    @login_required
    @admin_required
    def admin_companies():
        companies = Company.query.all()
        return render_template('admin_companies.html', companies=companies)

    @app.route('/admin/jobs')
    @login_required
    @admin_required
    def admin_jobs():
        jobs = JobListing.query.all()
        return render_template('admin_jobs.html', jobs=jobs)

    # Your existing routes continue here...
    @app.route('/')
    def index():
        jobs = JobListing.query.order_by(JobListing.posted_at.desc()).all()
        return render_template('index.html', jobs=jobs, guest=True)

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

    @app.route('/my-applications')
    @login_required
    def my_applications():
        if current_user.role != 'applicant':
            flash('Only applicants can access this page.', 'danger')
            return redirect(url_for('dashboard'))
        
        applicant = current_user.applicant_profile
        if not applicant:
            flash('Applicant profile not found.', 'danger')
            return redirect(url_for('dashboard'))
        
        applications = Application.query.filter_by(id_applicant=applicant.id).order_by(Application.applied_at.desc()).all()
        
        return render_template('my_applications.html', applications=applications)

    # Notification routes
    @app.route('/notifications')
    @login_required
    def get_notifications():
        notifications = Notification.query.filter_by(id_user=current_user.id).order_by(Notification.created_at.desc()).limit(10).all()
        return jsonify([n.to_dict() for n in notifications])

    @app.route('/notifications/read/<int:notification_id>', methods=['POST'])
    @login_required
    def mark_notification_read(notification_id):
        notification = Notification.query.get_or_404(notification_id)
        if notification.id_user != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        notification.is_read = True
        db.session.commit()
        return jsonify({'success': True})

    @app.route('/notifications/read-all', methods=['POST'])
    @login_required
    def mark_all_notifications_read():
        Notification.query.filter_by(id_user=current_user.id, is_read=False).update({'is_read': True})
        db.session.commit()
        return jsonify({'success': True})

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
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif current_user.role == 'company':
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
            'applied_count': len(job.applications),
            'slots': job.slots
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

        # Check if already applied
        existing_application = Application.query.filter_by(
            id_applicant=applicant.id, 
            id_job=job.id
        ).first()
        if existing_application:
            flash('You have already applied for this job.', 'warning')
            return redirect(url_for('dashboard'))

        form = ApplyForm()
        if form.validate_on_submit():
            # Handle CV upload
            cv_file = form.cv_file.data
            if cv_file:
                try:
                    # Generate unique filename
                    original_filename = secure_filename(cv_file.filename)
                    file_ext = os.path.splitext(original_filename)[1]
                    unique_filename = f"{uuid.uuid4().hex}{file_ext}"
                    
                    # Ensure upload directory exists
                    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'cv')
                    os.makedirs(upload_dir, exist_ok=True)
                    
                    # Save file
                    file_path = os.path.join(upload_dir, unique_filename)
                    cv_file.save(file_path)
                    
                    # Update applicant with CV path (using existing cv_path field)
                    applicant.cv_path = unique_filename
                    db.session.commit()
                    
                except Exception as e:
                    flash('Error uploading CV file.', 'danger')
                    return redirect(url_for('apply', job_id=job_id))

            # Create application
            application = Application(
                id_applicant=applicant.id,
                id_job=job.id,
                notes=form.cover_letter.data
            )
            db.session.add(application)
            db.session.commit()
            
            # Create notification for company when application is received
            notification = Notification(
                id_user=job.company.id_user,
                title="New Application Received",
                message=f"{current_user.applicant_profile.full_name} applied for {job.title}",
                type='application_received',
                related_id=application.id
            )
            db.session.add(notification)
            db.session.commit()
            
            flash('Application submitted successfully! Wait for company response.', 'success')
            return redirect(url_for('dashboard'))
        
        return render_template('apply.html', form=form, job=job)

    # ADD new route for viewing CV
    @app.route('/cv/<filename>')
    @login_required
    def view_cv(filename):
        # Security check - only company can view CV
        if current_user.role != 'company':
            flash('Unauthorized access.', 'danger')
            return redirect(url_for('dashboard'))
        
        return send_from_directory(
            os.path.join(current_app.root_path, 'static', 'uploads', 'cv'),
            filename
        )
    
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
                slots=form.slots.data,
                id_company=company.id
            )
            db.session.add(new_job)
            db.session.commit()
            
            # Create notifications for all applicants when new job is posted
            applicants = Applicant.query.all()
            for applicant in applicants:
                notification = Notification(
                    id_user=applicant.id_user,
                    title="New Job Posted",
                    message=f"A new job '{new_job.title}' has been posted by {company.company_name}",
                    type='job_posted',
                    related_id=new_job.id
                )
                db.session.add(notification)
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
        
        # Create notification for applicant when application is accepted
        notification = Notification(
            id_user=application.applicant.id_user,
            title="Application Status Updated",
            message=f"Your application for {application.job.title} has been accepted",
            type='application_status',
            related_id=application.id
        )
        db.session.add(notification)
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
        
        # Create notification for applicant when application is rejected
        notification = Notification(
            id_user=application.applicant.id_user,
            title="Application Status Updated",
            message=f"Your application for {application.job.title} has been rejected",
            type='application_status',
            related_id=application.id
        )
        db.session.add(notification)
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