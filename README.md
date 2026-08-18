# Lucky Numbers Betting Bot

Selenium automation for the Hollywoodbets Lucky Numbers flow. The bot reads an Excel/CSV input file, opens the website in the user's already logged-in Chrome session, selects country/game/numbers, clicks `Add Bet`, and can optionally click `Submit` after each clean bet.

## Real Submit Command

Use this command when you want the bot to submit bets one by one in real time:

```bash
STAKE=1 DRY_RUN=0 SUBMIT_EACH_BET=1 python main.py
```

Meaning:

- `STAKE=1`: enter stake amount `1` for each bet
- `DRY_RUN=0`: allow non-dry-run actions
- `SUBMIT_EACH_BET=1`: after each clean `Add Bet`, click final `Submit`
- `python main.py`: run the bot

Flow:

```text
Select numbers -> Add Bet -> Enter stake -> Submit -> Next bet
```

Use a specific input file:

```bash
STAKE=1 DRY_RUN=0 SUBMIT_EACH_BET=1 INPUT_FILE=sample_file.xlsx python main.py
```

## What The Bot Does

- Reads betting combinations from Excel or CSV
- Selects country, game, main numbers, and bonus numbers
- Adds valid selections to the betslip
- Optionally enters stake
- Keeps betslip in `Single` mode by default
- Can submit each bet immediately after `Add Bet` when explicitly enabled
- Skips entries when required numbers are missing
- Retries if the site shows `Error displaying Lucky Numbers`
- Pauses for manual Cloudflare verification and resumes the same row
- Saves a run report as `run_results_YYYYMMDD_HHMMSS.csv`

## Files

- `main.py`: main bot script
- `1sample_file.xlsx`: current default input file
- `sample_file.xlsx`, `test.xlsx`, `input_data.csv`: sample/test input files
- `requirements.txt`: Python dependencies
- `INSTALL.md`: fresh-system setup instructions

## One-Time Setup

From the project folder:

```bash
cd /home/cis/Documents/Scraping_Project
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Start Chrome

The bot connects to a Chrome session that you control. Start Chrome like this:

```bash
google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug
```

In that Chrome window:

1. Open Hollywoodbets.
2. Complete Cloudflare/security verification manually.
3. Log in manually.
4. Open the Lucky Numbers countries page.

Keep this Chrome window open while running the bot.

## Daily Start

Open a second terminal:

```bash
cd /home/cis/Documents/Scraping_Project
source venv/bin/activate
```

## Commands

### 1. Dry Run

Use this for safe testing. It clicks `Add Bet`, but never clicks final `Submit`.

```bash
python main.py
```

### 2. Use A Different Input File

```bash
INPUT_FILE=sample_file.xlsx python main.py
```

CSV example:

```bash
INPUT_FILE=input_data.csv python main.py
```

### 3. Add Stake

Use one stake amount for all rows:

```bash
STAKE=10 python main.py
```

With custom input:

```bash
STAKE=10 INPUT_FILE=sample_file.xlsx python main.py
```

### 4. Add To Betslip Only, No Submit

This is non-dry-run mode, but final `Submit` is still disabled.

```bash
STAKE=10 DRY_RUN=0 INPUT_FILE=sample_file.xlsx python main.py
```

### 5. Add Bet Then Submit Each Bet

This submits every valid bet one by one after `Add Bet`.

```bash
STAKE=1 DRY_RUN=0 SUBMIT_EACH_BET=1 INPUT_FILE=sample_file.xlsx python main.py
```

For first controlled testing, use a small file with only 1-2 rows:

```bash
STAKE=1 DRY_RUN=0 SUBMIT_EACH_BET=1 INPUT_FILE=small_test.xlsx python main.py
```

### 6. Enable Multiple Mode

Default is `Single` mode. Enable `Multiple` only if required:

```bash
USE_MULTIPLE=1 python main.py
```

### 7. Speed Tuning

Default speed is already optimized. If needed:

```bash
ACTION_DELAY=0.1 NAV_DELAY=0.2 SUBMIT_WAIT=4 SUBMIT_RESULT_DELAY=0.8 STAKE=1 DRY_RUN=0 SUBMIT_EACH_BET=1 python main.py
```

### 8. Increase Site Error Retries

If the site often shows `Error displaying Lucky Numbers`:

```bash
ERROR_RETRIES=5 python main.py
```

## Important Flags

- `DRY_RUN=1`: default; add to betslip only, never submit
- `DRY_RUN=0`: allow non-dry-run actions
- `SUBMIT_EACH_BET=1`: with `DRY_RUN=0`, click `Submit` after each clean `Add Bet`
- `STAKE=10`: use stake `10` for each bet unless input file has its own stake
- `INPUT_FILE=filename.xlsx`: choose input file
- `USE_MULTIPLE=1`: allow Multiple mode

## Input Format

Supported files:

- `.xlsx`
- `.xls`
- `.csv`

Supported tabular columns:

- `Country`
- `Game Names` or `Game`
- `Type of Set`
- `Main Numbers`
- `Bonus` or `Bonus Number`
- `Stake` or `Stake Amount`

Supported set types:

- `MAIN SET`
- `BONUS`
- `MAIN SET & BONUS`

If the input file has no stake column, pass stake from the command:

```bash
STAKE=10 python main.py
```

## Result Report

Each run creates:

```text
run_results_YYYYMMDD_HHMMSS.csv
```

Possible statuses:

- `dry_run`: added to betslip, final Submit not clicked
- `added`: Add Bet completed, final Submit not clicked
- `submitted`: Submit clicked after Add Bet
- `submit_failed`: Submit enabled but failed or blocked
- `skipped`: required numbers were missing
- `failed`: country/game/stake/action failed
- `warning`: site warning was detected

## Troubleshooting

If countries are not found:

- Confirm Chrome was started with `--remote-debugging-port=9222`
- Complete Cloudflare verification manually
- Log in manually
- Make sure Lucky Numbers countries page is visible

If `Error displaying Lucky Numbers` appears:

- The bot retries automatically
- Increase retries with `ERROR_RETRIES=5`

If Cloudflare / `I am human` appears:

- The bot pauses automatically
- Click `I am human` manually in Chrome
- The bot continues the same row after the page is clear
- Default wait is 900 seconds

Increase or reduce wait time:

```bash
CLOUDFLARE_WAIT=1200 python main.py
```

If stake is not entered:

- Confirm the betslip is visible
- Confirm `STAKE=...` is provided or input has `Stake` column

If related-leg warnings appear:

- Keep default `Single` mode
- Avoid `USE_MULTIPLE=1` unless tested
- Submit each bet individually with `SUBMIT_EACH_BET=1`

## Safety

By default, the bot does not click final `Submit`. Final submission only happens when both are set:

```bash
DRY_RUN=0 SUBMIT_EACH_BET=1
```
