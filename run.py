from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash
import os

app = create_app()

@app.cli.command("init-db")
def init_db():
    """Initialize the database with clean setup"""
    with app.app_context():
        db.create_all()
        
        # Create only the admin user
        if not User.query.filter_by(username='admin').first():
            admin_user = User(
                username='admin',
                email='happytayengwa702@gmail.com',
                password_hash=generate_password_hash('admin123')
            )
            db.session.add(admin_user)
            db.session.commit()
            print("✅ Clean database initialized!")
            print("👤 Default admin user created:")
            print("   Username: admin")
            print("   Password: admin123")
            print("⚠️  CHANGE THESE CREDENTIALS IN PRODUCTION!")
        else:
            print("✅ Database already initialized")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)