import os
import uuid
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, send_from_directory, current_app
from nemukerja.extensions import db, login_manager, bcrypt
from flask_migrate import Migrate
from flask_login import login_user, login_required, logout_user, current_user
from datetime import timedelta
from nemukerja.models import User, Company, JobListing, Application, Applicant, Notification
from nemukerja.forms import RegisterForm, LoginForm, CompanyProfileForm, AddJobForm, ApplyForm, ReactiveForm, ApplicantProfileForm
from werkzeug.utils import secure_filename
import json
from sqlalchemy import or_, desc

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
        
        # RECENT ACTIVITY LOGIC
        # Fetch recent activities (limit 10 from each category to combine)
        # Perlu join dengan Company/Applicant untuk mendapatkan nama di deskripsi
        recent_users = User.query.order_by(desc(User.created_at)).limit(10).all()
        recent_jobs = JobListing.query.join(Company).order_by(desc(JobListing.posted_at)).limit(10).all()
        recent_applications = Application.query.join(Applicant).join(JobListing).order_by(desc(Application.applied_at)).limit(10).all()
        
        recent_activity = []
        
        # 1. Process Users (Registration)
        for user in recent_users:
            role_type = 'user' if user.role == 'applicant' else ('company' if user.role == 'company' else 'user')
            recent_activity.append({
                'type': role_type,
                'description': f"{user.name} ({user.role.capitalize()}) registered.",
                'date': user.created_at
            })

        # 2. Process Jobs (New Postings)
        for job in recent_jobs:
            recent_activity.append({
                'type': 'job',
                'description': f"New Job: '{job.title}' posted by {job.company.company_name}.",
                'date': job.posted_at
            })

        # 3. Process Applications (New Applications)
        for app in recent_applications:
            recent_activity.append({
                'type': 'application',
                'description': f"New Application for '{app.job.title}' by {app.applicant.full_name} (Status: {app.status}).",
                'date': app.applied_at
            })
            
        # Sort all activities by date (descending) and take top 20
        recent_activity.sort(key=lambda x: x['date'], reverse=True)
        recent_activity = recent_activity[:20]

        # Format the date string for the template
        for activity in recent_activity:
            activity['date'] = activity['date'].strftime('%Y-%m-%d %H:%M')
        # END RECENT ACTIVITY LOGIC
        
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
        from sqlalchemy.orm import joinedload
        users = User.query.options(joinedload(User.applicant_profile), joinedload(User.company_profile)).all()
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

    @app.route('/')
    def index():
        # Parameter untuk Pencarian dan Filter
        search_query = request.args.get('search', '', type=str)
        location_filter = request.args.get('location', '', type=str)
        salary_min_filter = request.args.get('salary_min', type=int)
        company_filter = request.args.get('company', '', type=str)
        
        # Pagination Parameters
        page = request.args.get('page', 1, type=int)
        per_page = 9 # Jumlah item per halaman

        # Query Awal (filter is_open=True sudah ada)
        query = JobListing.query.filter_by(is_open=True).order_by(JobListing.posted_at.desc())

        # 1. Implementasi Filter & Search
        filters = []

        # Search Judul atau Kualifikasi
        if search_query:
            filters.append(or_(
                JobListing.title.ilike(f'%{search_query}%'),
                JobListing.qualifications.ilike(f'%{search_query}%')
            ))

        # Filter Lokasi
        if location_filter:
            filters.append(JobListing.location.ilike(f'%{location_filter}%'))

        # Filter Gaji Minimum
        if salary_min_filter is not None and salary_min_filter > 0:
            # Cari lowongan yang gaji_min-nya lebih besar atau sama dengan filter
            filters.append(JobListing.salary_min >= salary_min_filter) 
            # ATAU cari lowongan yang rentang gajinya mencakup nilai filter
            filters.append(JobListing.salary_max >= salary_min_filter)


        # Filter Perusahaan
        if company_filter:
            # Membutuhkan join atau subquery, kita akan menggunakan join sederhana dengan filter nama
            # Ini memerlukan modifikasi di query awal atau join, untuk sementara kita buat query terpisah
            company_ids = db.session.query(Company.id).filter(Company.company_name.ilike(f'%{company_filter}%')).subquery()
            filters.append(JobListing.id_company.in_(company_ids))


        if filters:
            query = query.filter(*filters)
        
        # 2. Implementasi Pagination
        jobs_pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        jobs = jobs_pagination.items
        
        # Perlu list semua perusahaan untuk dropdown filter
        companies = Company.query.all()

        return render_template('index.html', 
                               jobs=jobs, 
                               pagination=jobs_pagination, # BARU
                               companies=companies,       # BARU
                               search_query=search_query, # BARU
                               guest=True)

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
        
        return render_template('my_applications.html', applications=applications, title_suffix="All Applications")

    @app.route('/my-pending')
    @login_required
    def my_pending_applications():
        if current_user.role != 'applicant':
            flash('Only applicants can access this page.', 'danger')
            return redirect(url_for('dashboard'))
        
        applicant = current_user.applicant_profile
        if not applicant:
            flash('Applicant profile not found.', 'danger')
            return redirect(url_for('dashboard'))
        
        # Filter hanya yang Pending
        applications = Application.query.filter_by(
            id_applicant=applicant.id,
            status='Pending'
        ).order_by(Application.applied_at.desc()).all()
        
        return render_template('my_applications.html', applications=applications, title_suffix="Pending Applications")

    @app.route('/my-accepted')
    @login_required
    def my_accepted_applications():
        if current_user.role != 'applicant':
            flash('Only applicants can access this page.', 'danger')
            return redirect(url_for('dashboard'))
        
        applicant = current_user.applicant_profile
        if not applicant:
            flash('Applicant profile not found.', 'danger')
            return redirect(url_for('dashboard'))
        
        # Filter hanya yang Diterima
        applications = Application.query.filter_by(
            id_applicant=applicant.id,
            status='Diterima'
        ).order_by(Application.applied_at.desc()).all()
        
        return render_template('my_applications.html', applications=applications, title_suffix="Accepted Applications")


    # Notification routes
    @app.route('/notifications')
    @login_required
    def get_notifications():
        notifications = Notification.query.filter_by(id_user=current_user.id).order_by(Notification.created_at.desc()).limit(10).all()
        return jsonify([n.to_dict() for n in notifications])
    
    # NEW API: Mendapatkan Job ID dari Application ID (untuk navigasi notifikasi)
    @app.route('/api/get_job_id/<int:application_id>')
    @login_required
    def get_job_id_from_application(application_id):
        application = Application.query.get(application_id)
        if not application:
            return jsonify({'job_id': None}), 404
        
        # Jika pengguna adalah Pelamar, pastikan aplikasi ini miliknya
        if current_user.role == 'applicant' and application.id_applicant != current_user.applicant_profile.id:
             return jsonify({'job_id': None}), 403
        
        # Jika pengguna adalah Perusahaan, pastikan aplikasi ini untuk lowongan mereka
        if current_user.role == 'company' and application.job.company.user.id != current_user.id:
            return jsonify({'job_id': None}), 403

        return jsonify({'job_id': application.id_job})

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

    # === RUTE PROFIL APPLICANT (PELAMAR) ===

    # RUTE BARU: Untuk MELIHAT profil pelamar
    @app.route('/profile/applicant/view')
    @login_required
    def view_applicant_profile():
        if current_user.role != 'applicant':
            flash('Hanya akun pelamar yang dapat mengakses halaman ini.', 'danger')
            return redirect(url_for('dashboard'))

        applicant = current_user.applicant_profile
        if not applicant:
            flash('Profil pelamar tidak ditemukan.', 'danger')
            return redirect(url_for('dashboard'))
        
        # Render template untuk MELIHAT profil
        return render_template('view_applicant_profile.html', applicant=applicant)

    # RUTE DIPERBARUI: Untuk MENGEDIT profil pelamar
    # (Menggantikan @app.route('/profile/applicant', ...))
    @app.route('/profile/applicant/edit', methods=['GET', 'POST'])
    @login_required
    def edit_applicant_profile():
        if current_user.role != 'applicant':
            flash('Hanya akun pelamar yang dapat mengakses halaman ini.', 'danger')
            return redirect(url_for('dashboard'))

        applicant = current_user.applicant_profile
        if not applicant:
            flash('Profil pelamar tidak ditemukan.', 'danger')
            return redirect(url_for('dashboard'))

        # Gunakan ApplicantProfileForm dari forms.py
        form = ApplicantProfileForm(obj=applicant)
        
        if form.validate_on_submit():
            # 1. Update data dasar (nama dan skills)
            applicant.full_name = form.full_name.data
            applicant.skills = form.skills.data

            # 2. Handle upload CV jika ada file baru
            cv_file = form.cv_file.data
            if cv_file:
                try:
                    # Hapus file CV lama jika ada
                    if applicant.cv_path:
                        old_path = os.path.join(current_app.root_path, 'static', 'uploads', 'cv', applicant.cv_path)
                        if os.path.exists(old_path):
                            os.remove(old_path)
                            
                    # Simpan file baru dengan nama unik
                    original_filename = secure_filename(cv_file.filename)
                    file_ext = os.path.splitext(original_filename)[1]
                    unique_filename = f"{uuid.uuid4().hex}{file_ext}"
                    
                    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'cv')
                    os.makedirs(upload_dir, exist_ok=True)
                    
                    file_path = os.path.join(upload_dir, unique_filename)
                    cv_file.save(file_path)
                    
                    applicant.cv_path = unique_filename
                    
                except Exception as e:
                    flash(f'Error mengunggah file CV: {e}', 'danger')
                    db.session.rollback()
                    return redirect(url_for('edit_applicant_profile'))

            db.session.commit()
            flash('Profil berhasil disimpan!', 'success')
            # Redirect ke halaman MELIHAT profil setelah selesai edit
            return redirect(url_for('view_applicant_profile'))

        # Render template untuk MENGEDIT profil
        return render_template('edit_applicant_profile.html', form=form, applicant=applicant)


    # === RUTE PROFIL COMPANY (PERUSAHAAN) ===

    # RUTE BARU: Untuk MELIHAT profil perusahaan
    @app.route('/profile/company/view')
    @login_required
    def view_company_profile():
        if current_user.role != 'company':
            flash('Hanya akun perusahaan yang dapat mengakses halaman ini.', 'danger')
            return redirect(url_for('index'))

        company = current_user.company_profile
        if not company:
            flash('Profil perusahaan tidak ditemukan. Harap lengkapi.', 'warning')
            return redirect(url_for('edit_company_profile'))

        # Ambil data statistik untuk ditampilkan di halaman lihat profil
        jobs = JobListing.query.filter_by(id_company=company.id).order_by(JobListing.posted_at.desc()).all()
        total_jobs = len(jobs)
        open_jobs = len([job for job in jobs if getattr(job, 'is_open', True)])
        total_applications = sum(len(job.applications) for job in jobs)
        
        # Ambil 5 lamaran terbaru (sesuai template view_company_profile.html)
        recent_applications = db.session.query(Application).join(JobListing).filter(JobListing.id_company == company.id).order_by(Application.applied_at.desc()).limit(5).all()

        # Render template MELIHAT profil
        return render_template('view_company_profile.html', 
                               company=company,
                               jobs=jobs, # Kirim daftar pekerjaan
                               recent_applications=recent_applications, # Kirim lamaran terbaru
                               total_jobs=total_jobs,
                               open_jobs=open_jobs,
                               total_applications=total_applications)

    # RUTE DIPERBARUI: Untuk MENGEDIT profil perusahaan
    # (Menggantikan @app.route('/company-profile', ...))
    @app.route('/profile/company/edit', methods=['GET', 'POST'])
    @login_required
    def edit_company_profile():
        if current_user.role != 'company':
            flash('Hanya akun perusahaan yang dapat mengakses halaman ini.', 'danger')
            return redirect(url_for('index'))

        company = current_user.company_profile
        if not company:
            # Jika profil belum ada (kasus jarang terjadi), buat baru
            company = Company(id_user=current_user.id, company_name="New Company")
            db.session.add(company)
            db.session.commit()
            flash('Harap lengkapi profil perusahaan Anda.', 'info')

        # Gunakan CompanyProfileForm dari forms.py
        form = CompanyProfileForm(obj=company)
        
        if form.validate_on_submit():
            # Mengisi objek company dengan data dari form
            form.populate_obj(company)
            db.session.commit()
            flash('Profil perusahaan berhasil disimpan!', 'success')
            # Redirect ke halaman MELIHAT profil setelah selesai edit
            return redirect(url_for('view_company_profile'))

        # Render template MENGEDIT profil
        return render_template('edit_company_profile.html', form=form)

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
            if not company or not company.company_name or company.company_name == "New Company":
                flash('Please complete your company profile first.', 'warning')
                # PERBARUI INI: Arahkan ke rute edit yang baru
                return redirect(url_for('edit_company_profile'))

            jobs = JobListing.query.filter_by(id_company=company.id).order_by(JobListing.posted_at.desc()).all()
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
            # (Logika dashboard applicant/user)
            jobs = JobListing.query.filter_by(is_open=True).order_by(JobListing.posted_at.desc()).all()
            
            applicant_profile = current_user.applicant_profile
            total_app = applicant_profile.applications if applicant_profile else []
            pending_app_count = len([app for app in total_app if app.status == 'Pending'])
            accepted_app_count = len([app for app in total_app if app.status == 'Diterima'])

            return render_template('dashboard_user.html', 
                                   jobs=jobs, 
                                   guest=False,
                                   total_app_count=len(total_app),
                                   pending_app_count=pending_app_count,
                                   accepted_app_count=accepted_app_count)

    @app.route('/job/<int:job_id>')
    def job_detail(job_id):
        job = JobListing.query.get_or_404(job_id)
        
        # Hitung pelamar aktif (Pending atau Diterima)
        used_slots = Application.query.filter_by(id_job=job.id).filter(
            Application.status.in_(['Pending', 'Diterima'])
        ).count()
        
        data = {
            'id': job.id,
            'title': job.title,
            'location': job.location,
            'salary_min': job.salary_min, # BARU
            'salary_max': job.salary_max, # BARU
            'description': job.description,
            'qualifications': job.qualifications,
            'company': job.company.company_name if job.company else "N/A",
            'applied_count': used_slots,
            'slots': job.slots,
            'is_open': job.is_open
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
        
        # --- NEW SLOT CHECK LOGIC ---
        # Hitung slot yang terpakai (Pending atau Diterima)
        used_slots = Application.query.filter_by(id_job=job.id).filter(
            Application.status.in_(['Pending', 'Diterima'])
        ).count()
        
        if used_slots >= job.slots:
            flash('Slot lamaran untuk pekerjaan ini sudah penuh.', 'danger')
            return redirect(url_for('dashboard'))

        if not job.is_open:
            flash(f'Pekerjaan "{job.title}" saat ini tidak terbuka untuk lamaran.', 'danger')
            return redirect(url_for('dashboard'))
        # --- END NEW SLOT CHECK LOGIC ---

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
    
    @app.route('/company/job/<int:job_id>/close', methods=['POST'])
    @login_required
    def close_job(job_id):
        job = JobListing.query.get_or_404(job_id)
        if current_user.role != 'company' or job.company.user.id != current_user.id:
            flash('You are not authorized to manage this job.', 'danger')
            return redirect(url_for('dashboard'))

        job.is_open = False
        db.session.commit()
        flash(f'Job "{job.title}" has been closed. You may now delete it.', 'warning')
        return redirect(url_for('dashboard'))

    @app.route('/company/job/<int:job_id>/open', methods=['POST'])
    @login_required
    def open_job(job_id):
        job = JobListing.query.get_or_404(job_id)
        if current_user.role != 'company' or job.company.user.id != current_user.id:
            flash('You are not authorized to manage this job.', 'danger')
            return redirect(url_for('dashboard'))
        
        job.is_open = True
        db.session.commit()
        flash(f'Job "{job.title}" has been reopened. It is now visible to applicants.', 'success')
        return redirect(url_for('dashboard'))

    @app.route('/company/job/<int:job_id>/delete', methods=['POST'])
    @login_required
    def delete_job(job_id):
        job = JobListing.query.get_or_404(job_id)
        if current_user.role != 'company' or job.company.user.id != current_user.id:
            flash('You are not authorized to manage this job.', 'danger')
            return redirect(url_for('dashboard'))

        if job.is_open:
            flash('Job must be closed before deletion.', 'danger')
            return redirect(url_for('dashboard'))

        job_title = job.title
        
        # Collect IDs of users who applied
        applicant_users = [app.applicant.user for app in job.applications]

        db.session.delete(job)
        db.session.commit()
        
        # Create notifications for relevant applicants
        for user in applicant_users:
            notification = Notification(
                id_user=user.id,
                title="Job Posting Removed",
                message=f"The job '{job_title}' you applied for has been removed by the company.",
                type='job_posted',
                related_id=None 
            )
            db.session.add(notification)
        db.session.commit()

        flash(f'Job "{job_title}" has been successfully deleted.', 'success')
        return redirect(url_for('dashboard'))

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
                salary_min=form.salary_min.data, # BARU
                salary_max=form.salary_max.data, # BARU
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
    
    @app.route('/notifications/clear-all', methods=['POST'])
    @login_required
    def clear_all_notifications():
        # Menghapus semua notifikasi milik pengguna
        # FIX: Menambahkan synchronize_session=False untuk batch delete agar commit berhasil di DB
        Notification.query.filter_by(id_user=current_user.id).delete(synchronize_session=False)
        db.session.commit()
        return jsonify({'success': True})

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)