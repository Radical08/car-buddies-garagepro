from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, DecimalField, IntegerField, DateField, BooleanField, FileField
from wtforms.validators import DataRequired, Email, Length, Optional, NumberRange, ValidationError
from datetime import date
from app.models import CarOwner, Car

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

class CarOwnerForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(max=100)])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(max=20)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=120)])
    address = TextAreaField('Address', validators=[Optional(), Length(max=500)])

class CarForm(FlaskForm):
    license_plate = StringField('License Plate', validators=[DataRequired(), Length(max=20)])
    make = StringField('Make', validators=[DataRequired(), Length(max=50)])
    model = StringField('Model', validators=[DataRequired(), Length(max=50)])
    year = IntegerField('Year', validators=[Optional(), NumberRange(min=1900, max=2030)])
    color = StringField('Color', validators=[Optional(), Length(max=30)])
    vin = StringField('VIN', validators=[Optional(), Length(max=50)])
    owner_id = SelectField('Owner', coerce=int, validators=[DataRequired()])
    
    def validate_license_plate(self, field):
        if Car.query.filter_by(license_plate=field.data.upper()).first():
            raise ValidationError('This license plate is already registered.')

class ServiceJobForm(FlaskForm):
    date_in = DateField('Date In', validators=[DataRequired()], default=date.today)
    mileage_in = IntegerField('Mileage In', validators=[DataRequired(), NumberRange(min=0)])
    car_id = SelectField('Car', coerce=int, validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Optional()])

class ServiceItemForm(FlaskForm):
    description = StringField('Service Description', validators=[DataRequired(), Length(max=200)])
    cost = DecimalField('Cost (R)', validators=[DataRequired(), NumberRange(min=0)], places=2)
    is_fixed = BooleanField('Fixed/Completed')

class QuickServiceItemForm(FlaskForm):
    description = SelectField('Service Type', choices=[
        ('oil_change', '🛢️ Oil Change'),
        ('brake_service', '🛑 Brake Service'),
        ('suspension', '🔄 Suspension Repair'),
        ('engine_diagnosis', '🔧 Engine Diagnosis'),
        ('tire_rotation', '🌀 Tire Rotation'),
        ('battery_replacement', '🔋 Battery Replacement'),
        ('aircon_service', '❄️ Air Conditioning Service'),
        ('custom', '🔧 Custom Service')
    ], validators=[DataRequired()])
    custom_description = StringField('Custom Description', validators=[Optional(), Length(max=200)])
    cost = DecimalField('Cost (R)', validators=[DataRequired(), NumberRange(min=0)], places=2)
    is_fixed = BooleanField('Fixed/Completed')

class PaymentForm(FlaskForm):
    amount = DecimalField('Amount (R)', validators=[DataRequired(), NumberRange(min=0.01)], places=2)
    date = DateField('Payment Date', validators=[DataRequired()], default=date.today)
    description = StringField('Description', validators=[Optional(), Length(max=200)])
    owner_id = SelectField('Customer', coerce=int, validators=[DataRequired()])

class SearchForm(FlaskForm):
    search_query = StringField('Search', validators=[DataRequired()])
    search_type = SelectField('Search Type', choices=[
        ('license_plate', '🚗 License Plate'),
        ('owner_name', '👤 Owner Name'),
        ('car_make', '🏎️ Car Make/Model'),
        ('phone', '📞 Phone Number')
    ], validators=[DataRequired()])

class UserProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(max=64)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    current_password = PasswordField('Current Password', validators=[Optional()])
    new_password = PasswordField('New Password', validators=[Optional(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', validators=[Optional()])

class BackupForm(FlaskForm):
    backup_type = SelectField('Backup Type', choices=[
        ('full', 'Full Backup (Database + Files)'),
        ('database', 'Database Only'),
        ('settings', 'Settings Only')
    ], validators=[DataRequired()])
    include_attachments = BooleanField('Include File Attachments', default=True)

class EmailForm(FlaskForm):
    recipient_email = StringField('Recipient Email', validators=[DataRequired(), Email()])
    subject = StringField('Subject', validators=[DataRequired(), Length(max=200)])
    message = TextAreaField('Message', validators=[Optional()])
    include_attachment = BooleanField('Include Attachment', default=True)