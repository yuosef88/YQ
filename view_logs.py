#!/usr/bin/env python3
"""
Log viewer for the Curtain Quotation System.
Quick way to view and analyze application logs.
"""

import os
import sys
from pathlib import Path
from datetime import datetime

def get_logs_directory():
    """Get the logs directory path."""
    # Try to find the logs directory
    possible_paths = [
        Path("app/data/logs"),  # Development
        Path.home() / "AppData/Local/Adhlal/CurtainQuoter/logs",  # Production
        Path("data/logs"),  # Alternative
    ]
    
    for path in possible_paths:
        if path.exists():
            return path
    
    return None

def list_log_files(logs_dir):
    """List all available log files."""
    if not logs_dir or not logs_dir.exists():
        print("❌ Logs directory not found!")
        return []
    
    log_files = list(logs_dir.glob("*.log"))
    log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    print(f"📁 Logs directory: {logs_dir}")
    print(f"📊 Found {len(log_files)} log files:\n")
    
    for i, log_file in enumerate(log_files, 1):
        stat = log_file.stat()
        size_mb = stat.st_size / (1024 * 1024)
        modified = datetime.fromtimestamp(stat.st_mtime)
        
        print(f"{i:2d}. {log_file.name}")
        print(f"    Size: {size_mb:.2f} MB")
        print(f"    Modified: {modified.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
    
    return log_files

def view_log_file(log_file, lines=50, follow=False):
    """View a specific log file."""
    if not log_file.exists():
        print(f"❌ Log file not found: {log_file}")
        return
    
    print(f"📖 Viewing: {log_file.name}")
    print(f"📏 Total size: {log_file.stat().st_size / 1024:.1f} KB")
    print("=" * 80)
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            # Read all lines and get the last N lines
            all_lines = f.readlines()
            total_lines = len(all_lines)
            
            if lines > total_lines:
                lines = total_lines
            
            # Show last N lines
            start_line = total_lines - lines
            print(f"Showing last {lines} lines (of {total_lines} total):")
            print("-" * 40)
            
            for i, line in enumerate(all_lines[start_line:], start_line + 1):
                print(f"{i:4d}: {line.rstrip()}")
            
            if follow:
                print("\n🔄 Following log file (Ctrl+C to stop)...")
                try:
                    while True:
                        line = f.readline()
                        if line:
                            print(f"{total_lines + 1:4d}: {line.rstrip()}")
                            total_lines += 1
                        else:
                            import time
                            time.sleep(0.1)
                except KeyboardInterrupt:
                    print("\n⏹️  Stopped following log file.")
                    
    except Exception as e:
        print(f"❌ Error reading log file: {e}")

def search_logs(logs_dir, search_term, case_sensitive=False):
    """Search for a term across all log files."""
    if not logs_dir or not logs_dir.exists():
        print("❌ Logs directory not found!")
        return
    
    log_files = list(logs_dir.glob("*.log"))
    if not log_files:
        print("❌ No log files found!")
        return
    
    print(f"🔍 Searching for '{search_term}' across {len(log_files)} log files...")
    print("=" * 80)
    
    found_count = 0
    for log_file in log_files:
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    if case_sensitive:
                        if search_term in line:
                            print(f"📄 {log_file.name}:{line_num}: {line.rstrip()}")
                            found_count += 1
                    else:
                        if search_term.lower() in line.lower():
                            print(f"📄 {log_file.name}:{line_num}: {line.rstrip()}")
                            found_count += 1
        except Exception as e:
            print(f"❌ Error reading {log_file.name}: {e}")
    
    print(f"\n✅ Found {found_count} matches")

def main():
    """Main function."""
    print("=" * 60)
    print("CURTAIN QUOTER - LOG VIEWER")
    print("=" * 60)
    
    logs_dir = get_logs_directory()
    if not logs_dir:
        print("❌ Could not find logs directory!")
        print("Make sure the application has been run at least once.")
        return
    
    while True:
        print("\n" + "=" * 60)
        print("Choose an option:")
        print("1. List log files")
        print("2. View latest log file")
        print("3. View specific log file")
        print("4. Search logs")
        print("5. Follow latest log (real-time)")
        print("0. Exit")
        
        choice = input("\nEnter your choice (0-5): ").strip()
        
        if choice == "0":
            print("👋 Goodbye!")
            break
        elif choice == "1":
            list_log_files(logs_dir)
        elif choice == "2":
            log_files = list(logs_dir.glob("*.log"))
            if log_files:
                latest = max(log_files, key=lambda x: x.stat().st_mtime)
                view_log_file(latest, lines=100)
            else:
                print("❌ No log files found!")
        elif choice == "3":
            log_files = list(logs_dir.glob("*.log"))
            if log_files:
                print("\nAvailable log files:")
                for i, log_file in enumerate(logs_dir.glob("*.log"), 1):
                    print(f"{i}. {log_file.name}")
                
                try:
                    file_choice = int(input("\nEnter file number: ")) - 1
                    if 0 <= file_choice < len(log_files):
                        lines = input("Number of lines to show (default 50): ").strip()
                        lines = int(lines) if lines.isdigit() else 50
                        view_log_file(log_files[file_choice], lines=lines)
                    else:
                        print("❌ Invalid file number!")
                except ValueError:
                    print("❌ Invalid input!")
            else:
                print("❌ No log files found!")
        elif choice == "4":
            search_term = input("Enter search term: ").strip()
            if search_term:
                case_sensitive = input("Case sensitive? (y/N): ").strip().lower() == 'y'
                search_logs(logs_dir, search_term, case_sensitive)
            else:
                print("❌ Search term cannot be empty!")
        elif choice == "5":
            log_files = list(logs_dir.glob("*.log"))
            if log_files:
                latest = max(log_files, key=lambda x: x.stat().st_mtime)
                view_log_file(latest, lines=50, follow=True)
            else:
                print("❌ No log files found!")
        else:
            print("❌ Invalid choice! Please enter 0-5.")

if __name__ == "__main__":
    main()
