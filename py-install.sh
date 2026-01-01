pyinstaller ^
  --noconfirm ^
  --onedir ^
  --windowed ^
  --name BillingApp ^
  --icon bill.ico ^
  --add-data "config.json;." ^
  --add-data "header.png;." ^
  --add-data "gsprint.exe;." ^
  --add-data "bin/gswin32c.exe;./bin/" ^
  --add-data "bin/gsdll32.dll;./bin/" ^
  --add-data "bin/gsdll32.lib;./bin/" ^
  --add-data "bin/gswin32.exe;./bin/" ^
  app.py