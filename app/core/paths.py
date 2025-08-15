"""
Application paths management for development and packaged deployment.
Uses platformdirs to ensure data persists in user-writable locations.
"""

import os
from pathlib import Path
from platformdirs import user_data_dir
import sys


class AppPaths:
    """Centralized path management for the application."""
    
    APP_NAME = "CurtainQuoter"
    APP_AUTHOR = "Adhlal"
    
    def __init__(self):
        # Determine if we're running in development or packaged mode
        self.is_packaged = getattr(sys, 'frozen', False)
        
        if self.is_packaged:
            # Running as packaged executable
            self.app_root = Path(sys.executable).parent
        else:
            # Running in development
            self.app_root = Path(__file__).parent.parent.parent
    
    @property
    def data_dir(self) -> Path:
        """User data directory for database and application data."""
        data_path = Path(user_data_dir(self.APP_NAME, self.APP_AUTHOR))
        data_path.mkdir(parents=True, exist_ok=True)
        return data_path
    
    @property
    def database_path(self) -> Path:
        """SQLite database file path."""
        db_dir = self.data_dir / "data"
        db_dir.mkdir(exist_ok=True)
        return db_dir / "app.db"
    
    @property
    def media_dir(self) -> Path:
        """Media directory for uploaded files."""
        media_path = self.data_dir / "media"
        media_path.mkdir(parents=True, exist_ok=True)
        return media_path
    
    @property
    def products_media_dir(self) -> Path:
        """Product images directory."""
        products_path = self.media_dir / "products"
        products_path.mkdir(exist_ok=True)
        return products_path
    
    @property
    def templates_dir(self) -> Path:
        """Templates directory for reports."""
        if self.is_packaged:
            return self.app_root / "app" / "reports"
        else:
            return self.app_root / "app" / "reports"
    
    @property
    def assets_dir(self) -> Path:
        """Assets directory for static files."""
        if self.is_packaged:
            return self.app_root / "assets"
        else:
            return self.app_root / "assets"
    
    def get_relative_media_path(self, absolute_path: str) -> str:
        """Convert absolute media path to relative path for database storage."""
        abs_path = Path(absolute_path)
        try:
            return str(abs_path.relative_to(self.media_dir))
        except ValueError:
            # Path is not under media dir, return as-is
            return str(abs_path)
    
    def get_absolute_media_path(self, relative_path: str) -> Path:
        """Convert relative media path to absolute path for file access."""
        if not relative_path:
            return None
        return self.media_dir / relative_path


# Global instance
app_paths = AppPaths()


