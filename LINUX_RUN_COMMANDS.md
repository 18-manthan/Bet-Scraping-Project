# Linux Run Commands

Use this guide when running/testing the desktop UI on Linux.

## One-Time Setup

From the project folder:

```bash
cd /home/cis/Documents/Scraping_Project
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Open The Desktop UI

Run:

```bash
cd /home/cis/Documents/Scraping_Project
source venv/bin/activate
python3 desktop_app.py
```

Or, if the virtual environment is already active:

```bash
python3 desktop_app.py
```

## Linux Chrome Command

The desktop app has a `Start Chrome` button. If you want to start Chrome manually instead, run:

```bash
google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug
```

Then:

1. Complete Cloudflare verification if it appears.
2. Log in manually.
3. Go back to the desktop UI.
4. Select the Excel/CSV file.
5. Click `Start Bot`.

