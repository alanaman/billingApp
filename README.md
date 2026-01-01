Quick and dirty local app for GST billing/invoicing using PyQt6 and SQLite.

## Running the app

1. Install dependencies: `python -m pip install -r requirements.txt`
2. Launch: `python -m billing_app`

The application stores its SQLite database at `database/sql.db` (created on first run). A default `admin` user with password `admin` is created when the database is bootstrapped.

## Project layout

- `billing_app/` – application package
	- `core/` – database access, configuration, global state
	- `ui/` – PyQt6 widgets for login, billing, products, bills, users
	- `printing/` – PDF generation and printing
- `config.json` – runtime configuration (e.g., invoice prefix)
- `database/` – SQLite files and bootstrap SQL

Use `python -m PyInstaller app.py` (or your preferred spec) if you need a bundled executable; the thin `app.py` entry wraps the packaged module.