# Fresh System Installation

Use this guide to set up the Lucky Numbers betting bot on a new Linux system.

## 1. Install System Requirements

Install Python, pip, venv support, and Google Chrome.

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv
```

Install Google Chrome if it is not already installed:

```bash
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install -y ./google-chrome-stable_current_amd64.deb
```

Check versions:

```bash
python3 --version
google-chrome --version
```

## 2. Copy Project

Copy the project folder to the new system, then enter it:

```bash
cd /path/to/Scraping_Project
```

## 3. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

Upgrade pip:

```bash
pip install --upgrade pip
```

Install Python dependencies:

```bash
pip install -r requirements.txt
```

## 4. Start Chrome for Selenium

The bot connects to an already-open Chrome session. Start Chrome like this:

```bash
google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug
```

Keep this terminal open while the bot runs.

In the Chrome window:

1. Open the betting site.
2. Complete Cloudflare/security verification manually.
3. Log in manually.
4. Open the Lucky Numbers countries page.

## 5. Run Safe Test

Open a second terminal:

```bash
cd /path/to/Scraping_Project
source venv/bin/activate
python main.py
```

This runs in dry-run mode. It can add selections to the betslip, but it should not click final Submit.

Review the output and the generated result file:

```text
run_results_YYYYMMDD_HHMMSS.csv
```

## 6. Run With Custom Input

```bash
INPUT_FILE=sample_file.xlsx python main.py
```

For CSV:

```bash
INPUT_FILE=input_data.csv python main.py
```

## 7. Run With Stake

```bash
STAKE=10 python main.py
```

## 8. Non-Dry-Run

Add selections to betslip without final Submit:

```bash
STAKE=10 DRY_RUN=0 INPUT_FILE=sample_file.xlsx python main.py
```

The script still does not click final Submit.

Submit every valid bet immediately after Add Bet:

```bash
STAKE=1 DRY_RUN=0 SUBMIT_EACH_BET=1 INPUT_FILE=sample_file.xlsx python main.py
```

For first controlled testing, use a small input file with only 1-2 rows:

```bash
STAKE=1 DRY_RUN=0 SUBMIT_EACH_BET=1 INPUT_FILE=small_test.xlsx python main.py
```

The bot keeps the betslip in `Single` mode by default. Enable `Multiple` only if it is required and tested:

```bash
USE_MULTIPLE=1 python main.py
```

## Troubleshooting

If the script cannot find countries:

- Make sure Chrome was started with `--remote-debugging-port=9222`
- Make sure Cloudflare verification is completed
- Make sure the user is logged in
- Make sure the Lucky Numbers countries page is visible
- If the site shows `Error displaying Lucky Numbers`, the bot will retry automatically

Adjust retry count:

```bash
ERROR_RETRIES=5 python main.py
```

If numbers are skipped:

- The input number may not exist for that game
- The wrong `Type of Set` may be selected
- The site may have changed its number grid

If stake entry fails:

- Confirm the user is logged in
- Confirm the bet slip is visible
- Run one dry-run first, then a small non-dry-run test
