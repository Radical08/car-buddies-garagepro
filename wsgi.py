import sys
import os

# Add your app directory to the Python path
path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path:
    sys.path.append(path)

from app import create_app
application = create_app()