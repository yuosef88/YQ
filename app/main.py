"""
Main entry point for the Curtain Quotation System.
Handles application initialization and migration.
"""

import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

# Add the app directory to Python path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

from core.database import init_db, get_db_info
from core.migration import run_migration
from core.paths import app_paths
from gui.main_window import MainWindow


def setup_application():
    """Set up the QApplication with proper configuration."""
    app = QApplication(sys.argv)
    app.setApplicationName("Adhlal - Curtain Business Management System")
    app.setApplicationVersion("3.0")
    app.setOrganizationName("Adhlal")
    app.setOrganizationDomain("adhlal.com")
    
    # Set default font to avoid DirectWrite warnings
    for font_family in ["Segoe UI", "Arial", "Helvetica", "sans-serif"]:
        font = QFont(font_family, 9)
        if font.family() == font_family:  # Font is available
            app.setFont(font)
            break
    
    # Use default application style
    pass
    
    return app


def check_and_migrate_database():
    """Check if migration is needed and run it."""
    try:
        # Check if new database exists
        if not app_paths.database_path.exists():
            print("New database not found. Checking for migration...")
            
            # Check if old database exists
            old_db_path = Path("data/app.db")
            if old_db_path.exists():
                print("Old database found. Running migration...")
                run_migration()
            else:
                print("No existing database. Initializing fresh database...")
                init_db()
        else:
            print(f"Database found at: {app_paths.database_path}")
            
        # Print database info
        db_info = get_db_info()
        print("Database Information:")
        for key, value in db_info.items():
            print(f"  {key}: {value}")
            
    except Exception as e:
        print(f"Database initialization error: {e}")
        import traceback
        traceback.print_exc()
        raise


def main():
    """Main application entry point."""
    try:
        print("=" * 60)
        print("ADHLAL CURTAIN BUSINESS MANAGEMENT SYSTEM v3.0")
        print("=" * 60)
        
        # Set up paths and database
        print(f"Application data directory: {app_paths.data_dir}")
        print(f"Media directory: {app_paths.media_dir}")
        
        # Check and migrate database
        check_and_migrate_database()
        
        # Create application
        app = setup_application()
        
        # Create and show main window
        print("Starting application...")
        window = MainWindow()
        window.show()
        
        print("Application ready!")
        
        # Run the application
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"Application startup error: {e}")
        import traceback
        traceback.print_exc()
        
        # Show error dialog if possible
        try:
            app = QApplication.instance() or QApplication(sys.argv)
            QMessageBox.critical(
                None,
                "Startup Error",
                f"Failed to start application:\n\n{str(e)}\n\nCheck console for details."
            )
        except:
            pass
        
        sys.exit(1)


if __name__ == "__main__":
    main()


