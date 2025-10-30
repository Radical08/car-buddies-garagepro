from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file, current_app
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import func, extract
from app import db
from app.models import User, CarOwner, Car, ServiceJob, ServiceItem, Transaction, ServiceCategory
from app.forms import LoginForm, CarOwnerForm, CarForm, ServiceJobForm, ServiceItemForm, PaymentForm, SearchForm, UserProfileForm, BackupForm, EmailForm, QuickServiceItemForm
from app.utils import send_email, generate_quotation_pdf, generate_invoice_pdf, generate_receipt_pdf
from app.utils import send_quotation_email, send_invoice_email, backup_database, format_currency, get_dashboard_stats
from datetime import datetime, date, timedelta
import io
import json
import os
import csv

main = Blueprint('main', __name__)

# ========== AUTHENTICATION ROUTES ==========
@main.route('/')
@main.route('/dashboard')
@login_required
def dashboard():
    stats = get_dashboard_stats()
    return render_template('pages/dashboard.html', **stats, now=datetime.now())

@main.route('/splash')
def splash():
    return render_template('pages/splash.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and user.check_password(form.password.data) and user.is_active:
            login_user(user)
            flash('🎉 Login successful!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
        else:
            flash('❌ Invalid username or password', 'error')
    
    return render_template('pages/login.html', form=form)

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('👋 You have been logged out successfully.', 'info')
    return redirect(url_for('main.login'))

# ========== CAR OWNER ROUTES ==========
@main.route('/car_owners')
@login_required
def car_owners():
    owners = CarOwner.query.order_by(CarOwner.name).all()
    total_outstanding = sum(owner.balance for owner in owners)
    owners_with_balance = len([owner for owner in owners if owner.balance > 0])
    
    return render_template('pages/car_owners.html', 
                         owners=owners, 
                         total_outstanding=total_outstanding,
                         owners_with_balance=owners_with_balance)

@main.route('/car_owners/add', methods=['GET', 'POST'])
@login_required
def add_car_owner():
    form = CarOwnerForm()
    if form.validate_on_submit():
        owner = CarOwner(
            name=form.name.data,
            phone=form.phone.data,
            email=form.email.data,
            address=form.address.data
        )
        db.session.add(owner)
        db.session.commit()
        flash('✅ Car owner added successfully!', 'success')
        return redirect(url_for('main.car_owners'))
    
    return render_template('pages/car_owner_form.html', form=form, title='Add Car Owner')

@main.route('/car_owners/<int:owner_id>')
@login_required
def car_owner_detail(owner_id):
    owner = CarOwner.query.get_or_404(owner_id)
    return render_template('pages/car_owner_detail.html', owner=owner)

# ========== CAR ROUTES ==========
@main.route('/cars')
@login_required
def cars():
    cars = Car.query.order_by(Car.make, Car.model).all()
    total_cars = len(cars)
    cars_with_services = len([car for car in cars if car.service_jobs])
    unique_owners = len(set(car.owner_id for car in cars))
    
    return render_template('pages/cars.html', 
                         cars=cars,
                         total_cars=total_cars,
                         cars_with_services=cars_with_services,
                         unique_owners=unique_owners)

@main.route('/cars/add', methods=['GET', 'POST'])
@login_required
def add_car():
    form = CarForm()
    form.owner_id.choices = [(owner.id, owner.name) for owner in CarOwner.query.order_by('name')]
    
    if form.validate_on_submit():
        car = Car(
            license_plate=form.license_plate.data.upper(),
            make=form.make.data,
            model=form.model.data,
            year=form.year.data,
            color=form.color.data,
            vin=form.vin.data,
            owner_id=form.owner_id.data
        )
        db.session.add(car)
        db.session.commit()
        flash('✅ Car added successfully!', 'success')
        return redirect(url_for('main.cars'))
    
    return render_template('pages/car_form.html', form=form, title='Add Car')

@main.route('/cars/<int:car_id>')
@login_required
def car_detail(car_id):
    car = Car.query.get_or_404(car_id)
    return render_template('pages/car_detail.html', car=car)

# ========== SERVICE JOB ROUTES ==========
@main.route('/jobs')
@login_required
def jobs():
    status_filter = request.args.get('status', 'all')
    
    query = ServiceJob.query
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    jobs = query.order_by(ServiceJob.date_in.desc()).all()
    
    active_jobs_count = ServiceJob.query.filter_by(status='in_progress').count()
    completed_jobs_count = ServiceJob.query.filter_by(status='completed').count()
    total_jobs = ServiceJob.query.count()
    total_revenue = db.session.query(func.sum(Transaction.amount)).filter_by(transaction_type='payment').scalar() or 0
    
    return render_template('pages/jobs.html', 
                         jobs=jobs,
                         active_jobs_count=active_jobs_count,
                         completed_jobs_count=completed_jobs_count,
                         total_jobs=total_jobs,
                         total_revenue=total_revenue,
                         current_filter=status_filter)

@main.route('/jobs/add', methods=['GET', 'POST'])
@login_required
def add_job():
    form = ServiceJobForm()
    form.car_id.choices = [(car.id, f"{car.license_plate} - {car.make} {car.model}") for car in Car.query.order_by('license_plate')]
    
    if form.validate_on_submit():
        job = ServiceJob(
            date_in=form.date_in.data,
            mileage_in=form.mileage_in.data,
            car_id=form.car_id.data,
            notes=form.notes.data
        )
        db.session.add(job)
        db.session.commit()
        flash('✅ Service job created successfully!', 'success')
        return redirect(url_for('main.job_detail', job_id=job.id))
    
    return render_template('pages/job_form.html', form=form, title='New Service Job')

@main.route('/jobs/<int:job_id>')
@login_required
def job_detail(job_id):
    job = ServiceJob.query.get_or_404(job_id)
    service_item_form = ServiceItemForm()
    quick_service_form = QuickServiceItemForm()
    return render_template('pages/job_detail.html', 
                         job=job, 
                         service_item_form=service_item_form,
                         quick_service_form=quick_service_form,
                         now=datetime.now())

@main.route('/jobs/<int:job_id>/add_service', methods=['POST'])
@login_required
def add_service_item(job_id):
    job = ServiceJob.query.get_or_404(job_id)
    form = ServiceItemForm()
    
    if form.validate_on_submit():
        service_item = ServiceItem(
            description=form.description.data,
            cost=float(form.cost.data),
            is_fixed=form.is_fixed.data,
            service_job_id=job_id
        )
        db.session.add(service_item)
        db.session.commit()
        flash('✅ Service item added successfully!', 'success')
    
    return redirect(url_for('main.job_detail', job_id=job_id))

@main.route('/jobs/<int:job_id>/add_quick_service', methods=['POST'])
@login_required
def add_quick_service_item(job_id):
    job = ServiceJob.query.get_or_404(job_id)
    form = QuickServiceItemForm()
    
    if form.validate_on_submit():
        service_type = form.description.data
        custom_desc = form.custom_description.data
        
        service_descriptions = {
            'oil_change': 'Oil Change Service',
            'brake_service': 'Brake System Service',
            'suspension': 'Suspension Repair',
            'engine_diagnosis': 'Engine Diagnosis',
            'tire_rotation': 'Tire Rotation & Balancing',
            'battery_replacement': 'Battery Replacement',
            'aircon_service': 'Air Conditioning Service',
            'custom': custom_desc or 'Custom Service'
        }
        
        service_item = ServiceItem(
            description=service_descriptions[service_type],
            cost=float(form.cost.data),
            is_fixed=form.is_fixed.data,
            service_job_id=job_id
        )
        db.session.add(service_item)
        db.session.commit()
        flash('✅ Quick service item added successfully!', 'success')
    
    return redirect(url_for('main.job_detail', job_id=job_id))

@main.route('/jobs/service/<int:service_id>/toggle', methods=['POST'])
@login_required
def toggle_service_item(service_id):
    try:
        service_item = ServiceItem.query.get_or_404(service_id)
        data = request.get_json()
        service_item.is_fixed = data.get('is_fixed', False)
        db.session.commit()
        
        return jsonify({'success': True, 'is_fixed': service_item.is_fixed})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@main.route('/jobs/service/<int:service_id>/delete', methods=['POST'])
@login_required
def delete_service_item(service_id):
    try:
        service_item = ServiceItem.query.get_or_404(service_id)
        db.session.delete(service_item)
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@main.route('/jobs/<int:job_id>/complete', methods=['POST'])
@login_required
def complete_job(job_id):
    job = ServiceJob.query.get_or_404(job_id)
    
    if request.form.get('mileage_out'):
        job.mileage_out = int(request.form.get('mileage_out'))
    
    job.date_out = date.today()
    job.status = 'completed'
    
    # Create invoice transaction
    if job.total_cost > 0:
        invoice = Transaction(
            amount=job.total_cost,
            transaction_type='invoice',
            description=f'Service for {job.car.license_plate}',
            date=date.today(),
            owner_id=job.car.owner_id,
            service_job_id=job.id
        )
        db.session.add(invoice)
    
    db.session.commit()
    flash('✅ Job marked as completed!', 'success')
    return redirect(url_for('main.job_detail', job_id=job_id))

@main.route('/jobs/<int:job_id>/quotation')
@login_required
def generate_quotation(job_id):
    job = ServiceJob.query.get_or_404(job_id)
    pdf_bytes = generate_quotation_pdf(job)
    
    return send_file(
        io.BytesIO(pdf_bytes),
        download_name=f'quotation_{job.car.license_plate}_{date.today()}.pdf',
        as_attachment=True,
        mimetype='application/pdf'
    )

@main.route('/jobs/<int:job_id>/invoice')
@login_required
def generate_invoice(job_id):
    job = ServiceJob.query.get_or_404(job_id)
    pdf_bytes = generate_invoice_pdf(job)
    
    return send_file(
        io.BytesIO(pdf_bytes),
        download_name=f'invoice_{job.car.license_plate}_{date.today()}.pdf',
        as_attachment=True,
        mimetype='application/pdf'
    )

@main.route('/jobs/<int:job_id>/send_quotation', methods=['POST'])
@login_required
def send_quotation_email_route(job_id):
    job = ServiceJob.query.get_or_404(job_id)
    recipient_email = request.form.get('recipient_email', job.car.owner.email)
    
    if not recipient_email:
        flash('❌ No email address provided for the car owner', 'error')
        return redirect(url_for('main.job_detail', job_id=job_id))
    
    try:
        success = send_quotation_email(job, recipient_email)
        if success:
            flash('✅ Quotation sent successfully!', 'success')
        else:
            flash('❌ Failed to send quotation email', 'error')
    except Exception as e:
        flash(f'❌ Error sending email: {str(e)}', 'error')
    
    return redirect(url_for('main.job_detail', job_id=job_id))

@main.route('/jobs/<int:job_id>/send_invoice', methods=['POST'])
@login_required
def send_invoice_email_route(job_id):
    job = ServiceJob.query.get_or_404(job_id)
    recipient_email = request.form.get('recipient_email', job.car.owner.email)
    
    if not recipient_email:
        flash('❌ No email address provided for the car owner', 'error')
        return redirect(url_for('main.job_detail', job_id=job_id))
    
    try:
        success = send_invoice_email(job, recipient_email)
        if success:
            flash('✅ Invoice sent successfully!', 'success')
        else:
            flash('❌ Failed to send invoice email', 'error')
    except Exception as e:
        flash(f'❌ Error sending email: {str(e)}', 'error')
    
    return redirect(url_for('main.job_detail', job_id=job_id))

# ========== PAYMENT ROUTES ==========
@main.route('/payments')
@login_required
def payments():
    payments = Transaction.query.filter_by(transaction_type='payment').order_by(Transaction.date.desc()).all()
    all_owners = CarOwner.query.all()
    form = PaymentForm()
    form.owner_id.choices = [(owner.id, f"{owner.name} (Balance: R{owner.balance:.2f})") for owner in all_owners if owner.balance > 0]
    
    return render_template('pages/payments.html', 
                         payments=payments, 
                         form=form,
                         all_owners=all_owners)

@main.route('/payments/add', methods=['POST'])
@login_required
def add_payment():
    form = PaymentForm()
    form.owner_id.choices = [(owner.id, owner.name) for owner in CarOwner.query.all()]
    
    if form.validate_on_submit():
        payment = Transaction(
            amount=float(form.amount.data),
            transaction_type='payment',
            description=form.description.data or 'Payment received',
            date=form.date.data,
            owner_id=form.owner_id.data
        )
        db.session.add(payment)
        db.session.commit()
        flash('✅ Payment recorded successfully!', 'success')
    
    return redirect(url_for('main.payments'))

@main.route('/payments/<int:payment_id>/receipt')
@login_required
def generate_receipt(payment_id):
    payment = Transaction.query.get_or_404(payment_id)
    pdf_bytes = generate_receipt_pdf(payment)
    
    return send_file(
        io.BytesIO(pdf_bytes),
        download_name=f'receipt_{payment.id}_{date.today()}.pdf',
        as_attachment=True,
        mimetype='application/pdf'
    )

# ========== SEARCH & REPORTS ROUTES ==========
@main.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    form = SearchForm()
    results = []
    
    if form.validate_on_submit():
        query = form.search_query.data
        search_type = form.search_type.data
        
        if search_type == 'license_plate':
            results = Car.query.filter(Car.license_plate.ilike(f'%{query}%')).all()
        elif search_type == 'owner_name':
            results = CarOwner.query.filter(CarOwner.name.ilike(f'%{query}%')).all()
        elif search_type == 'car_make':
            results = Car.query.filter(
                (Car.make.ilike(f'%{query}%')) | (Car.model.ilike(f'%{query}%'))
            ).all()
        elif search_type == 'phone':
            results = CarOwner.query.filter(CarOwner.phone.ilike(f'%{query}%')).all()
    
    return render_template('pages/search.html', form=form, results=results)

@main.route('/reports/<report_type>')
@login_required
def generate_report(report_type):
    if report_type == 'outstanding_balances':
        owners_with_balance = CarOwner.query.all()
        owners_with_balance = [owner for owner in owners_with_balance if owner.balance > 0]
        return render_template('pages/reports/outstanding_balances.html', owners=owners_with_balance)
    
    elif report_type == 'recent_payments':
        thirty_days_ago = date.today() - timedelta(days=30)
        recent_payments = Transaction.query.filter(
            Transaction.transaction_type == 'payment',
            Transaction.date >= thirty_days_ago
        ).order_by(Transaction.date.desc()).all()
        return render_template('pages/reports/recent_payments.html', payments=recent_payments)
    
    elif report_type == 'active_jobs':
        active_jobs = ServiceJob.query.filter_by(status='in_progress').all()
        return render_template('pages/reports/active_jobs.html', jobs=active_jobs)
    
    elif report_type == 'service_history':
        all_jobs = ServiceJob.query.order_by(ServiceJob.date_in.desc()).all()
        return render_template('pages/reports/service_history.html', jobs=all_jobs)
    
    else:
        flash('❌ Invalid report type', 'error')
        return redirect(url_for('main.dashboard'))

@main.route('/export/<data_type>')
@login_required
def export_data(data_type):
    if data_type == 'customers':
        owners = CarOwner.query.all()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Name', 'Phone', 'Email', 'Address', 'Balance'])
        
        for owner in owners:
            writer.writerow([
                owner.name,
                owner.phone,
                owner.email or '',
                owner.address or '',
                owner.balance
            ])
        
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            download_name=f'customers_export_{date.today()}.csv',
            as_attachment=True,
            mimetype='text/csv'
        )
    
    elif data_type == 'jobs':
        jobs = ServiceJob.query.all()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Job ID', 'License Plate', 'Date In', 'Date Out', 'Status', 'Total Cost'])
        
        for job in jobs:
            writer.writerow([
                job.id,
                job.car.license_plate,
                job.date_in,
                job.date_out or '',
                job.status,
                job.total_cost
            ])
        
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            download_name=f'jobs_export_{date.today()}.csv',
            as_attachment=True,
            mimetype='text/csv'
        )
    
    else:
        flash('❌ Invalid export type', 'error')
        return redirect(url_for('main.dashboard'))

# ========== SETTINGS & PROFILE ROUTES ==========
@main.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = UserProfileForm(obj=current_user)
    
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        
        if form.new_password.data:
            if form.current_password.data and current_user.check_password(form.current_password.data):
                if form.new_password.data == form.confirm_password.data:
                    current_user.set_password(form.new_password.data)
                    flash('✅ Password updated successfully!', 'success')
                else:
                    flash('❌ New passwords do not match', 'error')
            else:
                flash('❌ Current password is incorrect', 'error')
        
        db.session.commit()
        flash('✅ Profile updated successfully!', 'success')
        return redirect(url_for('main.profile'))
    
    return render_template('pages/profile.html', form=form)

@main.route('/settings')
@login_required
def settings():
    return render_template('pages/settings.html')

@main.route('/backup', methods=['GET', 'POST'])
@login_required
def backup():
    form = BackupForm()
    
    if form.validate_on_submit():
        try:
            backup_file = backup_database(form.backup_type.data, form.include_attachments.data)
            flash(f'✅ Backup created successfully: {backup_file}', 'success')
        except Exception as e:
            flash(f'❌ Backup failed: {str(e)}', 'error')
    
    return render_template('pages/backup.html', form=form)

# ========== API ROUTES ==========
@main.route('/api/dashboard_stats')
@login_required
def dashboard_stats():
    stats = get_dashboard_stats()
    return jsonify(stats)

@main.route('/api/search')
@login_required
def api_search():
    query = request.args.get('q', '')
    search_type = request.args.get('type', 'all')
    
    if not query or len(query) < 2:
        return jsonify([])
    
    results = []
    
    if search_type == 'license_plate' or search_type == 'all':
        cars = Car.query.filter(Car.license_plate.ilike(f'%{query}%')).all()
        for car in cars:
            results.append({
                'type': 'car',
                'id': car.id,
                'license_plate': car.license_plate,
                'make': car.make,
                'model': car.model,
                'owner_name': car.owner.name
            })
    
    if search_type == 'owner_name' or search_type == 'all':
        owners = CarOwner.query.filter(CarOwner.name.ilike(f'%{query}%')).all()
        for owner in owners:
            results.append({
                'type': 'owner',
                'id': owner.id,
                'name': owner.name,
                'phone': owner.phone,
                'balance': owner.balance
            })
    
    return jsonify(results)

@main.route('/api/chart_data')
@login_required
def chart_data():
    # Revenue by month for the last 6 months
    six_months_ago = date.today() - timedelta(days=180)
    
    revenue_data = db.session.query(
        extract('year', Transaction.date).label('year'),
        extract('month', Transaction.date).label('month'),
        func.sum(Transaction.amount).label('total')
    ).filter(
        Transaction.transaction_type == 'payment',
        Transaction.date >= six_months_ago
    ).group_by('year', 'month').order_by('year', 'month').all()
    
    months = []
    revenue = []
    
    for data in revenue_data:
        months.append(f"{int(data.month)}/{int(data.year)}")
        revenue.append(float(data.total or 0))
    
    return jsonify({
        'revenue_chart': {
            'months': months,
            'revenue': revenue
        }
    })

# ========== ERROR HANDLERS ==========
@main.app_errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@main.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

@main.app_errorhandler(403)
def forbidden_error(error):
    return render_template('errors/403.html'), 403

@main.app_errorhandler(400)
def bad_request_error(error):
    return render_template('errors/400.html'), 400

@main.app_errorhandler(429)
def too_many_requests_error(error):
    return render_template('errors/429.html'), 429


# ========== REPORT ROUTES ==========
@main.route('/reports/outstanding_balances')
@login_required
def report_outstanding_balances():
    owners_with_balance = [owner for owner in CarOwner.query.all() if owner.balance > 0]
    total_outstanding = sum(owner.balance for owner in owners_with_balance)
    
    return render_template('pages/reports/outstanding_balances.html', 
                         owners=owners_with_balance,
                         total_outstanding=total_outstanding,
                         now=datetime.now())

@main.route('/reports/recent_payments')
@login_required
def report_recent_payments():
    thirty_days_ago = date.today() - timedelta(days=30)
    recent_payments = Transaction.query.filter(
        Transaction.transaction_type == 'payment',
        Transaction.date >= thirty_days_ago
    ).order_by(Transaction.date.desc()).all()
    
    total_received = sum(payment.amount for payment in recent_payments)
    
    return render_template('pages/reports/recent_payments.html', 
                         payments=recent_payments,
                         total_received=total_received,
                         now=datetime.now(),
                         timedelta=timedelta)

@main.route('/reports/active_jobs')
@login_required
def report_active_jobs():
    active_jobs = ServiceJob.query.filter_by(status='in_progress').all()
    total_quoted = sum(job.quoted_cost for job in active_jobs)
    
    # Calculate average days in shop
    if active_jobs:
        total_days = sum((date.today() - job.date_in).days for job in active_jobs)
        average_days = total_days // len(active_jobs)
    else:
        average_days = 0
    
    return render_template('pages/reports/active_jobs.html', 
                         jobs=active_jobs,
                         total_quoted=total_quoted,
                         average_days=average_days,
                         now=datetime.now())

@main.route('/reports/service_history')
@login_required
def report_service_history():
    all_jobs = ServiceJob.query.order_by(ServiceJob.date_in.desc()).all()
    
    completed_jobs = [job for job in all_jobs if job.status == 'completed']
    in_progress_jobs = [job for job in all_jobs if job.status == 'in_progress']
    
    total_services = sum(len(job.service_items) for job in all_jobs)
    total_revenue = sum(job.total_cost for job in completed_jobs)
    
    if all_jobs:
        average_job_value = total_revenue / len(completed_jobs) if completed_jobs else 0
    else:
        average_job_value = 0
    
    return render_template('pages/reports/service_history.html', 
                         jobs=all_jobs,
                         completed_jobs=len(completed_jobs),
                         in_progress_jobs=len(in_progress_jobs),
                         total_services=total_services,
                         total_revenue=total_revenue,
                         average_job_value=average_job_value,
                         now=datetime.now())

# ========== PDF ROUTES ==========
@main.route('/jobs/<int:job_id>/quotation/html')
@login_required
def view_quotation_html(job_id):
    job = ServiceJob.query.get_or_404(job_id)
    return render_template('pages/quotation.html', job=job, now=datetime.now())

@main.route('/jobs/<int:job_id>/invoice/html')
@login_required
def view_invoice_html(job_id):
    job = ServiceJob.query.get_or_404(job_id)
    return render_template('pages/invoice.html', job=job, now=datetime.now())