import smtplib
import os
import shutil
from email.message import EmailMessage
from flask import current_app
from fpdf import FPDF
from datetime import datetime, date, timedelta
from app import db
from app.models import CarOwner, Car, ServiceJob, Transaction, ServiceItem, ServiceCategory
import zipfile
from sqlalchemy import func, extract

class PDF(FPDF):
    def header(self):
        # Logo
        logo_path = os.path.join(current_app.root_path, 'static', 'images', 'garage_logo.png')
        if os.path.exists(logo_path):
            self.image(logo_path, 10, 8, 33)
        
        # Garage info
        self.set_font('Arial', 'B', 16)
        self.cell(80)
        self.cell(30, 10, current_app.config['GARAGE_NAME'], 0, 0, 'C')
        self.ln(5)
        
        self.set_font('Arial', '', 10)
        self.cell(80)
        self.cell(30, 10, current_app.config['GARAGE_ADDRESS'], 0, 0, 'C')
        self.ln(4)
        
        self.cell(80)
        self.cell(30, 10, f"Tel: {current_app.config['GARAGE_PHONE']}", 0, 0, 'C')
        self.ln(4)
        
        self.cell(80)
        self.cell(30, 10, f"Email: {current_app.config['GARAGE_EMAIL']}", 0, 0, 'C')
        self.ln(10)
        
        # Line break
        self.line(10, 30, 200, 30)

def send_email(to_email, subject, body, attachment=None, attachment_name=None):
    """Send email using SMTP"""
    try:
        # Create message
        msg = EmailMessage()
        msg['From'] = current_app.config['EMAIL_USERNAME']
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add body
        msg.set_content(body, subtype='html')
        
        # Add attachment if provided
        if attachment and attachment_name:
            msg.add_attachment(attachment, maintype='application', subtype='octet-stream', filename=attachment_name)
        
        # Connect to server and send
        server = smtplib.SMTP(current_app.config['EMAIL_SERVER'], current_app.config['EMAIL_PORT'])
        server.starttls()
        server.login(current_app.config['EMAIL_USERNAME'], current_app.config['EMAIL_PASSWORD'])
        server.send_message(msg)
        server.quit()
        
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

def generate_quotation_pdf(service_job):
    """Generate quotation PDF for a service job"""
    pdf = PDF()
    pdf.add_page()
    
    # Title
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'QUOTATION', 0, 1, 'C')
    pdf.ln(5)
    
    # Customer and car info
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Customer & Vehicle Details:', 0, 1)
    pdf.set_font('Arial', '', 10)
    
    owner = service_job.car.owner
    car = service_job.car
    
    pdf.cell(0, 6, f"Customer: {owner.name}", 0, 1)
    pdf.cell(0, 6, f"Phone: {owner.phone}", 0, 1)
    if owner.email:
        pdf.cell(0, 6, f"Email: {owner.email}", 0, 1)
    pdf.cell(0, 6, f"Vehicle: {car.make} {car.model} ({car.year})", 0, 1)
    pdf.cell(0, 6, f"License Plate: {car.license_plate}", 0, 1)
    pdf.cell(0, 6, f"VIN: {car.vin or 'N/A'}", 0, 1)
    pdf.cell(0, 6, f"Date In: {service_job.date_in}", 0, 1)
    pdf.cell(0, 6, f"Mileage In: {service_job.mileage_in:,} km", 0, 1)
    pdf.ln(5)
    
    # Services table header
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Proposed Services:', 0, 1)
    
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(120, 8, 'Description', 1, 0)
    pdf.cell(30, 8, 'Status', 1, 0, 'C')
    pdf.cell(30, 8, 'Cost (R)', 1, 1, 'R')
    
    # Services items
    pdf.set_font('Arial', '', 10)
    total = 0
    for item in service_job.service_items:
        status = "Fixed" if item.is_fixed else "Pending"
        pdf.cell(120, 8, item.description, 1, 0)
        pdf.cell(30, 8, status, 1, 0, 'C')
        pdf.cell(30, 8, f"{item.cost:,.2f}", 1, 1, 'R')
        total += item.cost
    
    # Total
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(150, 8, 'TOTAL QUOTATION:', 1, 0, 'R')
    pdf.cell(30, 8, f"{total:,.2f}", 1, 1, 'R')
    
    # Notes
    pdf.ln(10)
    pdf.set_font('Arial', 'I', 9)
    pdf.multi_cell(0, 5, "Note: This is a quotation. Final invoice may vary based on actual work completed. Prices include VAT.")
    
    return pdf.output(dest='S').encode('latin1')

def generate_invoice_pdf(service_job):
    """Generate invoice PDF for a completed service job"""
    pdf = PDF()
    pdf.add_page()
    
    # Title
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'INVOICE', 0, 1, 'C')
    pdf.ln(5)
    
    # Customer and car info
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Customer & Vehicle Details:', 0, 1)
    pdf.set_font('Arial', '', 10)
    
    owner = service_job.car.owner
    car = service_job.car
    
    pdf.cell(0, 6, f"Customer: {owner.name}", 0, 1)
    pdf.cell(0, 6, f"Phone: {owner.phone}", 0, 1)
    if owner.email:
        pdf.cell(0, 6, f"Email: {owner.email}", 0, 1)
    pdf.cell(0, 6, f"Vehicle: {car.make} {car.model} ({car.year})", 0, 1)
    pdf.cell(0, 6, f"License Plate: {car.license_plate}", 0, 1)
    pdf.cell(0, 6, f"Date In: {service_job.date_in}", 0, 1)
    pdf.cell(0, 6, f"Date Out: {service_job.date_out}", 0, 1)
    pdf.cell(0, 6, f"Mileage In: {service_job.mileage_in:,} km", 0, 1)
    if service_job.mileage_out:
        pdf.cell(0, 6, f"Mileage Out: {service_job.mileage_out:,} km", 0, 1)
    pdf.ln(5)
    
    # Services table header (only fixed items)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Services Completed:', 0, 1)
    
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(140, 8, 'Description', 1, 0)
    pdf.cell(40, 8, 'Cost (R)', 1, 1, 'R')
    
    # Services items (only fixed ones)
    pdf.set_font('Arial', '', 10)
    total = 0
    for item in service_job.service_items:
        if item.is_fixed:  # Only include fixed items in invoice
            pdf.cell(140, 8, item.description, 1, 0)
            pdf.cell(40, 8, f"{item.cost:,.2f}", 1, 1, 'R')
            total += item.cost
    
    # Total
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(140, 8, 'TOTAL DUE:', 1, 0, 'R')
    pdf.cell(40, 8, f"{total:,.2f}", 1, 1, 'R')
    
    # Payment terms
    pdf.ln(10)
    pdf.set_font('Arial', 'I', 9)
    pdf.multi_cell(0, 5, "Payment Terms: Payment due upon receipt. Thank you for your business!")
    
    return pdf.output(dest='S').encode('latin1')

def generate_receipt_pdf(payment):
    """Generate receipt PDF for a payment"""
    pdf = PDF()
    pdf.add_page()
    
    # Title
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'PAYMENT RECEIPT', 0, 1, 'C')
    pdf.ln(5)
    
    # Customer info
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Payment Details:', 0, 1)
    pdf.set_font('Arial', '', 10)
    
    owner = payment.owner
    
    pdf.cell(0, 6, f"Customer: {owner.name}", 0, 1)
    pdf.cell(0, 6, f"Phone: {owner.phone}", 0, 1)
    if owner.email:
        pdf.cell(0, 6, f"Email: {owner.email}", 0, 1)
    pdf.cell(0, 6, f"Receipt Date: {payment.date}", 0, 1)
    pdf.cell(0, 6, f"Receipt Number: RCP{payment.id:06d}", 0, 1)
    pdf.ln(5)
    
    # Payment details
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Payment Information:', 0, 1)
    
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(100, 8, 'Description', 1, 0)
    pdf.cell(40, 8, 'Amount (R)', 1, 1, 'R')
    
    pdf.set_font('Arial', '', 10)
    pdf.cell(100, 8, payment.description or 'Payment received', 1, 0)
    pdf.cell(40, 8, f"{payment.amount:,.2f}", 1, 1, 'R')
    
    # New balance
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(100, 8, 'Remaining Balance:', 1, 0, 'R')
    pdf.cell(40, 8, f"{owner.balance:,.2f}", 1, 1, 'R')
    
    # Thank you message
    pdf.ln(10)
    pdf.set_font('Arial', 'I', 9)
    pdf.multi_cell(0, 5, "Thank you for your payment! We appreciate your business.")
    
    return pdf.output(dest='S').encode('latin1')

def send_quotation_email(service_job, recipient_email):
    """Send quotation via email"""
    try:
        # Generate PDF
        pdf_bytes = generate_quotation_pdf(service_job)
        
        # Create email content
        subject = f"Quotation for {service_job.car.license_plate} - THE CAR BUDDIES"
        body = f"""
        <html>
        <body>
            <h2>🚗 Quotation from THE CAR BUDDIES</h2>
            <p>Dear {service_job.car.owner.name},</p>
            <p>Please find attached the quotation for your vehicle <strong>{service_job.car.license_plate}</strong>.</p>
            <p><strong>Vehicle:</strong> {service_job.car.make} {service_job.car.model}</p>
            <p><strong>Total Quotation:</strong> R {service_job.quoted_cost:,.2f}</p>
            <br>
            <p>Thank you for choosing THE CAR BUDDIES!</p>
            <p><strong>THE CAR BUDDIES</strong><br>
            661 Baobab Road<br>
            0789292789 / 0772576803</p>
        </body>
        </html>
        """
        
        # Send email
        success = send_email(
            recipient_email,
            subject,
            body,
            attachment=pdf_bytes,
            attachment_name=f"quotation_{service_job.car.license_plate}.pdf"
        )
        
        return success
    except Exception as e:
        print(f"Error sending quotation email: {e}")
        return False

def send_invoice_email(service_job, recipient_email):
    """Send invoice via email"""
    try:
        # Generate PDF
        pdf_bytes = generate_invoice_pdf(service_job)
        
        # Create email content
        subject = f"Invoice for {service_job.car.license_plate} - THE CAR BUDDIES"
        body = f"""
        <html>
        <body>
            <h2>🧾 Invoice from THE CAR BUDDIES</h2>
            <p>Dear {service_job.car.owner.name},</p>
            <p>Please find attached the invoice for services completed on your vehicle <strong>{service_job.car.license_plate}</strong>.</p>
            <p><strong>Vehicle:</strong> {service_job.car.make} {service_job.car.model}</p>
            <p><strong>Total Due:</strong> R {service_job.total_cost:,.2f}</p>
            <br>
            <p>Thank you for your business!</p>
            <p><strong>THE CAR BUDDIES</strong><br>
            661 Baobab Road<br>
            0789292789 / 0772576803</p>
        </body>
        </html>
        """
        
        # Send email
        success = send_email(
            recipient_email,
            subject,
            body,
            attachment=pdf_bytes,
            attachment_name=f"invoice_{service_job.car.license_plate}.pdf"
        )
        
        return success
    except Exception as e:
        print(f"Error sending invoice email: {e}")
        return False

def format_currency(amount):
    """Format amount as South African Rand"""
    return f"R {amount:,.2f}"

def get_dashboard_stats():
    """Get comprehensive dashboard statistics"""
    total_cars = Car.query.count()
    total_owners = CarOwner.query.count()
    active_jobs = ServiceJob.query.filter_by(status='in_progress').count()
    completed_jobs = ServiceJob.query.filter_by(status='completed').count()
    
    # Calculate total revenue and outstanding balances
    total_revenue = db.session.query(func.sum(Transaction.amount)).filter_by(transaction_type='payment').scalar() or 0
    total_outstanding = sum(owner.balance for owner in CarOwner.query.all())
    
    # Recent activity
    recent_jobs = ServiceJob.query.order_by(ServiceJob.created_at.desc()).limit(5).all()
    recent_transactions = Transaction.query.order_by(Transaction.created_at.desc()).limit(5).all()
    
    # Monthly revenue
    current_month = date.today().replace(day=1)
    monthly_revenue = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.transaction_type == 'payment',
        Transaction.date >= current_month
    ).scalar() or 0
    
    return {
        'total_cars': total_cars,
        'total_owners': total_owners,
        'active_jobs': active_jobs,
        'completed_jobs': completed_jobs,
        'total_revenue': total_revenue,
        'total_outstanding': total_outstanding,
        'monthly_revenue': monthly_revenue,
        'recent_jobs': recent_jobs,
        'recent_transactions': recent_transactions
    }

def backup_database(backup_type='database', include_attachments=True):
    """Create a backup of the database and optionally attachments"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = os.path.join(current_app.root_path, 'backups')
    
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    if backup_type == 'database':
        # Simple database backup (for SQLite)
        db_path = os.path.join(current_app.root_path, 'instance', 'garage.db')
        backup_file = os.path.join(backup_dir, f'database_backup_{timestamp}.db')
        shutil.copy2(db_path, backup_file)
        
    elif backup_type == 'full':
        # Create a zip with database and attachments
        backup_file = os.path.join(backup_dir, f'full_backup_{timestamp}.zip')
        with zipfile.ZipFile(backup_file, 'w') as zipf:
            # Add database
            db_path = os.path.join(current_app.root_path, 'instance', 'garage.db')
            if os.path.exists(db_path):
                zipf.write(db_path, 'garage.db')
            
            # Add attachments if requested
            if include_attachments:
                attachments_dir = os.path.join(current_app.root_path, 'static', 'attachments')
                if os.path.exists(attachments_dir):
                    for root, dirs, files in os.walk(attachments_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, current_app.root_path)
                            zipf.write(file_path, arcname)
    
    return os.path.basename(backup_file)

def initialize_default_data():
    """Initialize the database with default data"""
    # Create default user if not exists
    from app.models import User
    from werkzeug.security import generate_password_hash
    
    if not User.query.filter_by(username='admin').first():
        admin_user = User(
            username='admin',
            email='happytayengwa702@gmail.com',
            password_hash=generate_password_hash('admin123')
        )
        db.session.add(admin_user)
    
    # Create default service categories
    default_categories = [
        {'name': 'Oil Change', 'description': 'Engine oil and filter change', 'base_price': 450.00},
        {'name': 'Brake Service', 'description': 'Brake pad replacement and system check', 'base_price': 800.00},
        {'name': 'Suspension Repair', 'description': 'Suspension system inspection and repair', 'base_price': 1200.00},
        {'name': 'Engine Diagnosis', 'description': 'Comprehensive engine diagnostic check', 'base_price': 300.00},
        {'name': 'Tire Services', 'description': 'Tire rotation, balancing and replacement', 'base_price': 200.00},
        {'name': 'Battery Service', 'description': 'Battery testing and replacement', 'base_price': 600.00},
        {'name': 'Air Conditioning', 'description': 'AC system service and repair', 'base_price': 750.00},
    ]
    
    for cat_data in default_categories:
        if not ServiceCategory.query.filter_by(name=cat_data['name']).first():
            category = ServiceCategory(
                name=cat_data['name'],
                description=cat_data['description'],
                base_price=cat_data['base_price']
            )
            db.session.add(category)
    
    db.session.commit()

def cleanup_old_backups(days=30):
    """Remove backup files older than specified days"""
    backup_dir = os.path.join(current_app.root_path, 'backups')
    if not os.path.exists(backup_dir):
        return
    
    cutoff_time = datetime.now() - timedelta(days=days)
    
    for filename in os.listdir(backup_dir):
        file_path = os.path.join(backup_dir, filename)
        if os.path.isfile(file_path):
            file_time = datetime.fromtimestamp(os.path.getctime(file_path))
            if file_time < cutoff_time:
                os.remove(file_path)