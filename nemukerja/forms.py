from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, IntegerField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Optional, NumberRange

class RegisterForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[Optional(), Length(max=20)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])

    role = SelectField('Role', choices=[('applicant', 'Job Seeker'), ('company', 'Company')], validators=[DataRequired()])
    company_name = StringField('Company Name', validators=[Optional(), Length(max=100)])
    description = TextAreaField('Company Description', validators=[Optional(), Length(max=500)])
    website = StringField('Website', validators=[Optional(), Length(max=200)])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class CompanyProfileForm(FlaskForm):
    company_name = StringField('Company Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(max=500)])
    contact_email = StringField('Contact Email', validators=[DataRequired(), Email()]) 
    phone = StringField('Phone Number', validators=[Optional(), Length(max=20)]) 
    website = StringField('Website', validators=[Optional(), Length(max=200)])
    submit = SubmitField('Save Profile')

class AddJobForm(FlaskForm):
    title = StringField('Job Title', validators=[DataRequired(), Length(max=100)])
    location = StringField('Location', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Job Description', validators=[DataRequired()])
    qualifications = TextAreaField('Qualifications', validators=[DataRequired()]) 
    # MENAMBAHKAN FIELD SLOTS
    slots = IntegerField('Available Slots', validators=[
        DataRequired(), 
        NumberRange(min=1, message='Slots must be at least 1')
    ], default=1)

    submit = SubmitField('Add Job')

class ApplyForm(FlaskForm):
    cover_letter = TextAreaField('Cover Letter / Notes', validators=[DataRequired()])
    submit = SubmitField('Submit Application')

class ReactiveForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Send Reactivation Link')