#!/usr/bin/env python3
"""
WSGI entry point for production deployment
"""
import os
import sys

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from app import create_app

# Create the Flask app
application = create_app('production')

if __name__ == "__main__":
    application.run()
