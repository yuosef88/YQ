#!/usr/bin/env python3
"""
Launcher script for Curtain Quotation System v3.0
Runs the new version from the app directory.
"""

import os
import sys
from pathlib import Path

def main():
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    app_dir = script_dir / "app"
    
    # Check if app directory exists
    if not app_dir.exists():
        print("Error: app directory not found!")
        print("Make sure you're running this from the project root directory.")
        sys.exit(1)
    
    # Change to app directory
    os.chdir(app_dir)
    
    # Add app directory to Python path
    sys.path.insert(0, str(app_dir))
    
    # Import and run the main application
    try:
        from main import main as app_main
        app_main()
    except ImportError as e:
        print(f"Error importing main application: {e}")
        print("Make sure all required dependencies are installed:")
        print("pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"Error running application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
