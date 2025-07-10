#!/usr/bin/env python
"""
Helper script to set up bower components for django-admin-charts
Run this script after installing the requirements
"""

import os
import subprocess
import sys
from pathlib import Path

def check_nodejs():
    """Check if Node.js and npm are installed"""
    try:
        subprocess.run(['node', '--version'], check=True, stdout=subprocess.PIPE)
        subprocess.run(['npm', '--version'], check=True, stdout=subprocess.PIPE)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def check_bower():
    """Check if Bower is installed"""
    try:
        subprocess.run(['bower', '--version'], check=True, stdout=subprocess.PIPE)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_bower():
    """Install Bower globally"""
    try:
        print("Installing Bower globally...")
        subprocess.run(['npm', 'install', '-g', 'bower'], check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def setup_bower_components():
    """Set up bower components for django-admin-charts"""
    # Get the project root directory
    BASE_DIR = Path(__file__).resolve().parent
    
    # Create the bower_components directory if it doesn't exist
    bower_dir = BASE_DIR / 'components'
    os.makedirs(bower_dir, exist_ok=True)
    
    # Create a bower.json file if it doesn't exist
    bower_json = bower_dir / 'bower.json'
    if not bower_json.exists():
        with open(bower_json, 'w') as f:
            f.write('''{
  "name": "tracegpt-bower",
  "dependencies": {
    "d3": "3.3.13",
    "nvd3": "1.7.1"
  }
}
''')
    
    # Run bower install
    try:
        print("Installing bower components...")
        os.chdir(bower_dir)
        subprocess.run(['bower', 'install', '--allow-root'], check=True)
        print("Bower components installed successfully.")
        return True
    except subprocess.CalledProcessError:
        print("Error installing bower components.")
        return False

def main():
    """Main function"""
    # Check if Node.js and npm are installed
    if not check_nodejs():
        print("Error: Node.js and npm are required to run this script.")
        print("Please install Node.js from https://nodejs.org/")
        sys.exit(1)
    
    # Check if Bower is installed
    if not check_bower():
        print("Bower not found. Installing Bower...")
        if not install_bower():
            print("Error installing Bower. Please install Bower manually:")
            print("npm install -g bower")
            sys.exit(1)
    
    # Set up bower components
    if setup_bower_components():
        print("\nSetup completed successfully!")
        print("You can now run the Django server:")
        print("python manage.py runserver")
    else:
        print("\nSetup failed. Please fix the errors above and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main() 