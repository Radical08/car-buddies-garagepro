from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
from app import db, login_manager

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class CarOwner(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120))
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    cars = db.relationship('Car', backref='owner', lazy=True, cascade='all, delete-orphan')
    transactions = db.relationship('Transaction', backref='owner', lazy=True)
    
    @property
    def balance(self):
        total_invoices = sum(transaction.amount for transaction in self.transactions 
                           if transaction.transaction_type == 'invoice')
        total_payments = sum(transaction.amount for transaction in self.transactions 
                           if transaction.transaction_type == 'payment')
        return total_invoices - total_payments
    
    def __repr__(self):
        return f'<CarOwner {self.name}>'

class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    license_plate = db.Column(db.String(20), unique=True, nullable=False)
    make = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer)
    color = db.Column(db.String(30))
    vin = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign key
    owner_id = db.Column(db.Integer, db.ForeignKey('car_owner.id'), nullable=False)
    
    # Relationships
    service_jobs = db.relationship('ServiceJob', backref='car', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Car {self.license_plate} - {self.make} {self.model}>'

class ServiceJob(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_in = db.Column(db.Date, nullable=False, default=date.today)
    date_out = db.Column(db.Date)
    mileage_in = db.Column(db.Integer, nullable=False)
    mileage_out = db.Column(db.Integer)
    status = db.Column(db.String(20), default='in_progress')  # in_progress, completed, quoted
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign key
    car_id = db.Column(db.Integer, db.ForeignKey('car.id'), nullable=False)
    
    # Relationships
    service_items = db.relationship('ServiceItem', backref='service_job', lazy=True, cascade='all, delete-orphan')
    
    @property
    def total_cost(self):
        return sum(item.cost for item in self.service_items if item.is_fixed)
    
    @property
    def quoted_cost(self):
        return sum(item.cost for item in self.service_items)
    
    def __repr__(self):
        return f'<ServiceJob {self.id} - {self.car.license_plate}>'

class ServiceItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    cost = db.Column(db.Float, nullable=False, default=0.0)
    is_fixed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign key
    service_job_id = db.Column(db.Integer, db.ForeignKey('service_job.id'), nullable=False)
    
    def __repr__(self):
        return f'<ServiceItem {self.description} - R{self.cost}>'

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # invoice, payment
    description = db.Column(db.String(200))
    date = db.Column(db.Date, nullable=False, default=date.today)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign keys
    owner_id = db.Column(db.Integer, db.ForeignKey('car_owner.id'), nullable=False)
    service_job_id = db.Column(db.Integer, db.ForeignKey('service_job.id'))
    
    def __repr__(self):
        return f'<Transaction {self.transaction_type} - R{self.amount}>'

class ServiceCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    base_price = db.Column(db.Float, default=0.0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ServiceCategory {self.name}>'

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))