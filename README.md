# Curtain Quoter Application

A professional quotation management system built with Python and PyQt6 for curtain and window treatment businesses.

## Features

- **Customer Management**: Store and manage customer information (individual and company)
- **Product Catalog**: Maintain product database with pricing and specifications
- **Quotation Generation**: Create professional quotes with automatic calculations
- **Database Management**: SQLite-based data storage with backup capabilities
- **Modern UI**: Dark theme interface with professional styling

## Requirements

- Python 3.8 or higher
- PyQt6
- SQLite3

## Installation

### Option 1: From Source
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/curtain-quoter.git
   cd curtain-quoter
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python app/main.py
   ```

### Option 2: Standalone Executable
Download the latest release executable from the releases page.

## Project Structure

```
YQ/
├── app/                    # Main application code
│   ├── core/              # Core functionality (database, models, services)
│   ├── gui/               # User interface components
│   └── main.py            # Application entry point
├── data/                  # Database files (not in git)
├── backup/                # Backup files (not in git)
├── media/                 # Media files (not in git)
└── requirements.txt       # Python dependencies
```

## Database Setup

The application will automatically create the database on first run. Database files are stored in the `data/` directory and are excluded from version control.

## Usage

1. **Start the application** using `python app/main.py`
2. **Add customers** through the customer management interface
3. **Create products** in the product catalog
4. **Generate quotations** by selecting customers and products
5. **Export quotes** as needed

## Development

### Adding New Features
1. Create a feature branch: `git checkout -b feature/new-feature`
2. Make your changes
3. Commit: `git commit -m "Add new feature"`
4. Push: `git push origin feature/new-feature`
5. Create a pull request

### Database Migrations
Database schema changes should be handled through the migration system in `app/core/migration.py`.

## Backup and Data Management

- Database backups are stored in the `backup/` directory
- Media files are stored in the `media/` directory
- These directories are excluded from version control for security

## Troubleshooting

### Common Issues
1. **PyQt6 not found**: Install with `pip install PyQt6`
2. **Database errors**: Check file permissions in the `data/` directory
3. **Import errors**: Ensure you're running from the project root directory

### Getting Help
- Check the issues page for known problems
- Create a new issue for bugs or feature requests
- Review the code comments for implementation details

## License

[Add your license information here]

## Contributing

Contributions are welcome! Please read the contributing guidelines before submitting pull requests.