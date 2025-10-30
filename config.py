import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'
    
    # Railway provides PORT environment variable
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///garage.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Email configuration
    EMAIL_SERVER = os.environ.get('EMAIL_SERVER', 'smtp.gmail.com')
    EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
    EMAIL_USERNAME = os.environ.get('EMAIL_USERNAME')
    EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')
    EMAIL_USE_TLS = True
    
    # Garage details
    GARAGE_NAME = os.environ.get('GARAGE_NAME', 'THE CAR BUDDIES')
    GARAGE_ADDRESS = os.environ.get('GARAGE_ADDRESS', '661 Baobab Road')
    GARAGE_PHONE = os.environ.get('GARAGE_PHONE', '0789292789 / 0772576803')
    GARAGE_EMAIL = os.environ.get('GARAGE_EMAIL', 'happytayengwa702@gmail.com')
    
    # Currency
    CURRENCY = 'ZAR'
    CURRENCY_SYMBOL = 'R'