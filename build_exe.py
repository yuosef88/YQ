#!/usr/bin/env python3
"""
Build script for creating Windows executable using PyInstaller.
Creates a standalone .exe file for the Curtain Quotation System.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def main():
    print("=" * 60)
    print("BUILDING CURTAIN QUOTATION SYSTEM EXECUTABLE")
    print("=" * 60)
    
    # Ensure we're in the right directory
    if not Path("app/main.py").exists():
        print("Error: Please run this script from the project root directory")
        sys.exit(1)
    
    # Clean previous builds
    print("🧹 Cleaning previous builds...")
    for dir_name in ["build", "dist"]:
        if Path(dir_name).exists():
            shutil.rmtree(dir_name)
            print(f"   Removed {dir_name}/")
    
    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--onefile",                    # Single executable file
        "--noconsole",                  # No console window
        "--name=CurtainQuoter",         # Executable name
        "--distpath=dist",              # Output directory
        "--workpath=build",             # Work directory
        "app/main.py"                   # Entry point
    ]
    
    # Only add data directories if they exist and have content
    if Path("assets").exists() and any(Path("assets").iterdir()):
        cmd.extend(["--add-data", "assets;assets"])
        print("   Including assets directory")
    
    if Path("app/reports").exists() and any(Path("app/reports").iterdir()):
        cmd.extend(["--add-data", "app/reports;app/reports"])
        print("   Including reports directory")
    
    # Only add icon if it exists
    if Path("assets/icon.ico").exists():
        cmd.extend(["--icon", "assets/icon.ico"])
        print("   Including icon file")
    
    print("🔨 Building executable...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        # Run PyInstaller
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Build successful!")
        
        # Check if executable was created
        exe_path = Path("dist/CurtainQuoter.exe")
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"📦 Executable created: {exe_path}")
            print(f"📏 Size: {size_mb:.1f} MB")
        else:
            print("❌ Executable not found!")
            sys.exit(1)
            
    except subprocess.CalledProcessError as e:
        print("❌ Build failed!")
        print(f"Error: {e}")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        sys.exit(1)
    
    except FileNotFoundError:
        print("❌ PyInstaller not found!")
        print("Please install PyInstaller: pip install pyinstaller")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("🎉 BUILD COMPLETE!")
    print("=" * 60)
    print(f"Executable location: {Path('dist/CurtainQuoter.exe').absolute()}")
    print("\nNext steps:")
    print("1. Test the executable on a clean Windows machine")
    print("2. Run installer/build_installer.bat to create installer")
    print("3. Distribute CurtainQuoter-Setup.exe to users")

if __name__ == "__main__":
    main()


