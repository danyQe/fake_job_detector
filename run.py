import subprocess
import sys
import os
import pkg_resources
from pkg_resources import DistributionNotFound, VersionConflict

def check_and_install_dependencies():
    """Check if all required packages are installed, and install any that are missing."""
    print("Checking dependencies...")
    try:
        # Read requirements file
        with open('requirements.txt', 'r') as f:
            requirements = [line.strip() for line in f.readlines() if line.strip() and not line.strip().startswith('#')]
        
        # Check which packages need to be installed
        missing_packages = []
        for requirement in requirements:
            try:
                pkg_resources.require(requirement)
            except (DistributionNotFound, VersionConflict):
                missing_packages.append(requirement)
        
        # Install missing packages
        if missing_packages:
            print(f"Installing missing dependencies: {', '.join(missing_packages)}")
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
            print("All dependencies installed successfully.")
        else:
            print("All dependencies are already installed.")
            
        return True
    except Exception as e:
        print(f"Error checking/installing dependencies: {str(e)}")
        return False

def main():
    """Main entry point to start the application."""
    # Ensure all dependencies are installed
    if not check_and_install_dependencies():
        print("Failed to verify dependencies. Exiting.")
        sys.exit(1)
    
    # Check if we need to create database tables
    if not os.path.exists('data.db') and os.path.exists('create_db.py'):
        print("Setting up database...")
        try:
            subprocess.check_call([sys.executable, "create_db.py"])
        except Exception as e:
            print(f"Warning: Database setup failed: {str(e)}")
    
    # Run the FastAPI application
    try:
        print("Starting the application...")
        from app.main import app
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except Exception as e:
        print(f"Failed to start application: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 