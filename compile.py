import sys
import py_compile
import os
import shutil
from pathlib import Path

def ensure_init_file(directory):
    """Create __init__.py if it doesn't exist"""
    init_file = os.path.join(directory, '__init__.py')
    if not os.path.exists(init_file):
        with open(init_file, 'w') as f:
            f.write('# Auto-generated __init__.py')

def compile_dir(src_dir, dest_dir):
    """Compile all .py files in directory and subdirectories"""
    # Create destination directory if it doesn't exist
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
    
    # Ensure __init__.py exists in source directory
    ensure_init_file(src_dir)
    
    for item in os.listdir(src_dir):
        src_path = os.path.join(src_dir, item)
        dest_path = os.path.join(dest_dir, item)
        
        if os.path.isfile(src_path):
            if src_path.endswith('.py'):
                # Create __pycache__ directory if needed
                cache_dir = os.path.join(os.path.dirname(dest_path), '__pycache__')
                if not os.path.exists(cache_dir):
                    os.makedirs(cache_dir)
                
                # Compile .py to .pyc
                try:
                    py_compile.compile(src_path, dest_path + 'c', optimize=2)
                    print(f"Compiled: {src_path}")
                except Exception as e:
                    print(f"Error compiling {src_path}: {e}")
        
        elif os.path.isdir(src_path):
            # Skip __pycache__ directories
            if item == '__pycache__':
                continue
            compile_dir(src_path, dest_path)

def create_zip_archive():
    """Create ZIP archive of dist folder"""
    import zipfile
    from datetime import datetime
    
    # Get current timestamp for zip name
    zip_name = f'TelegramClient.zip'
    
    print(f"Creating ZIP archive: {zip_name}")
    
    # Create zip file
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Walk through dist directory
        for root, _, files in os.walk('dist'):
            for file in files:
                file_path = os.path.join(root, file)
                # Add file to zip with relative path
                arc_name = os.path.relpath(file_path, 'dist')
                zipf.write(file_path, arc_name)
                # zipf.write(file_path, os.path.join('TelegramClient', arc_name))
    
    print(f"ZIP archive created successfully: {zip_name}")

def build_package():
    """Build the distribution package"""
    print("Starting build process...")
    
    # Clean previous builds
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    os.makedirs('dist')
    
    # Create package structure
    package_dir = os.path.join('dist', 'TelegramClient')
    os.makedirs(package_dir)
    
    # Ensure source directory structure exists
    required_dirs = [
        'src',
        'src/views',
        'src/controllers',
        'src/utils',
        'config',
        'logs'
    ]
    
    for dir_path in required_dirs:
        full_path = os.path.join(package_dir, dir_path)
        os.makedirs(full_path)
        ensure_init_file(os.path.join('.', dir_path))
    
    # Compile source files
    print("Compiling source files...")
    compile_dir('src', os.path.join(package_dir, 'src'))
    
    # Create launcher script
    print("Creating launcher...")
    with open(os.path.join(package_dir, 'start.py'), 'w') as f:
        f.write('''import sys
from src.main import main

if __name__ == "__main__":
    main()
''')
    
    # Create batch launcher with full Python path
    print("Creating launcher with Python path...")
    python_path = sys.executable.replace('\\', '\\\\')
    with open(os.path.join(package_dir, 'TelegramClient.bat'), 'w') as f:
        f.write(f'''
            @echo off
            setlocal

            set "PYTHON_EXE="

            rem Find Python 3.9
            if exist "C:\\Users\\nguye\\AppData\\Local\\Programs\\Python\\Python39\\python.exe" (
                set "PYTHON_EXE=C:\\Users\\nguye\\AppData\\Local\\Programs\\Python\\Python39\\python.exe"
            ) else if exist "C:\\Users\\%USERNAME%\\AppData\\Local\\Programs\\Python\\Python39\\python.exe" (
                set "PYTHON_EXE=C:\\Users\\%USERNAME%\\AppData\\Local\\Programs\\Python\\Python39\\python.exe"
            ) else if exist "C:\\Program Files\\Python39\\python.exe" (
                set "PYTHON_EXE=C:\\Program Files\\Python39\\python.exe"
            ) else if exist "C:\\Python39\\python.exe" (
                set "PYTHON_EXE=C:\\Python39\\python.exe"
            )

            rem Install Python 3.9 if not found
            if not defined PYTHON_EXE (
                echo Downloading Python 3.9...
                curl -o python39.exe https://www.python.org/ftp/python/3.9.13/python-3.9.13-amd64.exe

                echo Installing Python 3.9...
                python39.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0 Include_pip=1

                echo Installation complete!
                del python39.exe

                rem Set PYTHON_EXE to the installed Python path
                set "PYTHON_EXE=python"
            )

            rem Check if telethon is installed
            pip show telethon >nul 2>&1
            if errorlevel 1 (
                echo Installing telethon...
                pip install telethon
            )

            rem Check if flask is installed
            pip show flask >nul 2>&1
            if errorlevel 1 (
                echo Installing flask...
                pip install flask
            )

            rem Check if python-dotenv is installed
            pip show python-dotenv >nul 2>&1
            if errorlevel 1 (
                echo Installing python-dotenv...
                pip install python-dotenv
            )

            endlocal

            rem Check if Python exists in default locations
            if exist "C:\\Users\\nguye\\AppData\\Local\\Programs\\Python\\Python39\\python.exe" (
                "C:\\Users\\nguye\\AppData\\Local\\Programs\\Python\\Python39\\python.exe" start.py
            ) else if exist "C:\\Users\\%USERNAME%\\AppData\\Local\\Programs\\Python\\Python39\\python.exe" (
                "C:\\Users\\%USERNAME%\\AppData\\Local\\Programs\\Python\\Python39\\python.exe" start.py
            ) else if exist "C:\\Program Files\\Python39\\python.exe" (
                "C:\\Program Files\\Python39\\python.exe" start.py
            ) else if exist "C:\\Python39\\python.exe" (
                "C:\\Python39\\python.exe" start.py
            ) else (
                echo Not found Python 3.9...
                echo Please try again!
            )
        ''')
    
    # Copy README
    shutil.copy2('README.md', package_dir)
    
    print("Build completed successfully!")
    
    # Create ZIP archive
    create_zip_archive()

if __name__ == "__main__":
    build_package()