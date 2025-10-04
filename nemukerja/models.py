# [PERUBAHAN] Impor diubah menjadi absolut dari paket 'nemukerja'
from nemukerja.extensions import db
from flask_login import UserMixin
from datetime import datetime

# Tabel 'users' di SQL cocok dengan model User ini
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column('id_user', db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('applicant', 'company'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relasi ke Applicant dan Company
    applicant_profile = db.relationship('Applicant', backref='user', uselist=False)
    company_profile = db.relationship('Company', backref='user', uselist=False)

# Tabel 'companies' di SQL cocok dengan model Company ini
class Company(db.Model):
    __tablename__ = 'companies'
    id = db.Column('id_company', db.Integer, primary_key=True)
    id_user = db.Column('id_user', db.Integer, db.ForeignKey('users.id_user'), nullable=False)
    company_name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    contact_email = db.Column(db.String(255))
    phone = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relasi ke JobListing
    jobs = db.relationship('JobListing', backref='company', lazy=True)

# Tabel 'job_listings' di SQL cocok dengan model JobListing ini
class JobListing(db.Model):
    __tablename__ = 'job_listings'
    id = db.Column('id_job', db.Integer, primary_key=True)
    id_company = db.Column('id_company', db.Integer, db.ForeignKey('companies.id_company'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    qualifications = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(255))
    posted_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relasi ke Application
    applications = db.relationship('Application', backref='job', lazy=True)

# Tabel 'applicants' (BARU) di SQL cocok dengan model Applicant ini
class Applicant(db.Model):
    __tablename__ = 'applicants'
    id = db.Column('id_applicant', db.Integer, primary_key=True)
    id_user = db.Column('id_user', db.Integer, db.ForeignKey('users.id_user'), nullable=False)
    full_name = db.Column(db.String(255))
    cv_path = db.Column(db.String(255))
    skills = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relasi ke Application
    applications = db.relationship('Application', backref='applicant', lazy=True)

# Tabel 'applications' di SQL cocok dengan model Application ini
class Application(db.Model):
    __tablename__ = 'applications'
    id = db.Column('id_application', db.Integer, primary_key=True)
    id_applicant = db.Column('id_applicant', db.Integer, db.ForeignKey('applicants.id_applicant'), nullable=False)
    id_job = db.Column('id_job', db.Integer, db.ForeignKey('job_listings.id_job'), nullable=False)
    status = db.Column(db.Enum('Pending', 'Diterima', 'Ditolak'), nullable=False, default='Pending')
    notes = db.Column(db.Text)
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)