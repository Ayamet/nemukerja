from nemukerja.extensions import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from datetime import datetime

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column('id_user', db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column('password', db.String(255), nullable=False)
    role = db.Column(db.Enum('applicant', 'company'), nullable=False)
    created_at = db.Column(db.TIMESTAMP, server_default=func.now())
    updated_at = db.Column(db.TIMESTAMP, server_default=func.now(), onupdate=func.now())

    applicant_profile = db.relationship('Applicant', backref='user', uselist=False, cascade="all, delete-orphan")
    company_profile = db.relationship('Company', backref='user', uselist=False, cascade="all, delete-orphan")

class Applicant(db.Model):
    __tablename__ = 'applicants'
    id = db.Column('id_applicant', db.Integer, primary_key=True)
    id_user = db.Column(db.Integer, db.ForeignKey('users.id_user'), nullable=False)
    full_name = db.Column(db.String(255))
    cv_path = db.Column(db.String(255))
    skills = db.Column(db.Text)
    created_at = db.Column(db.TIMESTAMP, server_default=func.now())
    updated_at = db.Column(db.TIMESTAMP, server_default=func.now(), onupdate=func.now())

    applications = db.relationship('Application', backref='applicant', cascade="all, delete-orphan")
    
    @property
    def name(self):
        return self.full_name

    @property
    def email(self):
        return self.user.email


class Company(db.Model):
    __tablename__ = 'companies'
    id = db.Column('id_company', db.Integer, primary_key=True)
    id_user = db.Column(db.Integer, db.ForeignKey('users.id_user'), nullable=False)
    company_name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    contact_email = db.Column(db.String(255))
    phone = db.Column(db.String(50))
    created_at = db.Column(db.TIMESTAMP, server_default=func.now())
    updated_at = db.Column(db.TIMESTAMP, server_default=func.now(), onupdate=func.now())

    jobs = db.relationship('JobListing', backref='company', cascade="all, delete-orphan")

class JobListing(db.Model):
    __tablename__ = 'job_listings'
    id = db.Column('id_job', db.Integer, primary_key=True)
    id_company = db.Column(db.Integer, db.ForeignKey('companies.id_company'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    qualifications = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(255))
    
    # MENAMBAHKAN KOLOM SLOTS
    slots = db.Column(db.Integer, default=1, nullable=False)

    posted_at = db.Column(db.TIMESTAMP, server_default=func.now())
    updated_at = db.Column(db.TIMESTAMP, server_default=func.now(), onupdate=func.now())

    applications = db.relationship('Application', backref='job', cascade="all, delete-orphan")

class Application(db.Model):
    __tablename__ = 'applications'
    id = db.Column('id_application', db.Integer, primary_key=True)
    id_applicant = db.Column(db.Integer, db.ForeignKey('applicants.id_applicant'), nullable=False)
    id_job = db.Column(db.Integer, db.ForeignKey('job_listings.id_job'), nullable=False)
    status = db.Column(db.Enum('Pending','Diterima','Ditolak'), nullable=False, default='Pending')
    notes = db.Column(db.Text)
    applied_at = db.Column(db.TIMESTAMP, server_default=func.now())
    updated_at = db.Column(db.TIMESTAMP, server_default=func.now(), onupdate=func.now())