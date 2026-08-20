# Lucky Numbers Betting Bot

Selenium automation for the Hollywoodbets Lucky Numbers flow. The bot reads an Excel/CSV input file, opens the website in the user's already logged-in Chrome session, selects country/game/numbers, clicks `Add Bet`, and can optionally click `Submit` after each clean bet.

## Real Submit Command

Use this command when one Excel row should be added as Multiple and submitted once:

```bash
USE_MULTIPLE=1 STAKE=1 DRY_RUN=0 SUBMIT_EACH_BET=1 python main.py
```

Meaning:

- `USE_MULTIPLE=1`: add all jobs from one Excel row, click `Multiple`, then submit the row once
- `STAKE=1`: enter stake amount `1` for each bet
- `DRY_RUN=0`: allow non-dry-run actions
- `SUBMIT_EACH_BET=1`: click final `Submit`
- `python main.py`: run the bot

Flow:

```text
Row leg 1 -> Add Bet -> Row leg 2 -> Add Bet -> Click Multiple -> Enter stake -> Submit once -> Next row
```

Use a specific input file:

```bash
USE_MULTIPLE=1 STAKE=1 DRY_RUN=0 SUBMIT_EACH_BET=1 INPUT_FILE=sample_file.xlsx python main.py
```

For single-bet submit mode, use:

```bash
STAKE=1 DRY_RUN=0 SUBMIT_EACH_BET=1 python main.py
```

## What The Bot Does

- Reads betting combinations from Excel or CSV
- Selects country, game, main numbers, and bonus numbers
- Adds valid selections to the betslip
- Optionally enters stake
- Waits for manual login before processing rows
- Asks whether to start from beginning, resume, or manually choose a row
- Keeps betslip in `Single` mode by default
- Can submit each bet immediately after `Add Bet` when explicitly enabled
- Skips entries when required numbers are missing
- Retries if the site shows `Error displaying Lucky Numbers`
- Pauses for manual Cloudflare verification and resumes the same row
- Avoids unnecessary page reloads and uses browser back/fallback reload for faster navigation
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

If you run the bot before login is complete, it will wait until the logged-in session is detected.

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

For a single country / single game file, do not use `USE_MULTIPLE=1`.

```bash
STAKE=1 DRY_RUN=0 SUBMIT_EACH_BET=1 python main.py
```

Single game flow:

```text
Country -> Game -> Main Set -> Numbers -> Add Bet -> Stake -> Submit -> Next row
```

For first controlled testing, use a small file with only 1-2 rows:

```bash
STAKE=1 DRY_RUN=0 SUBMIT_EACH_BET=1 INPUT_FILE=small_test.xlsx python main.py
```

### 6. Enable Multiple Mode

Default is `Single` mode. Enable `Multiple` when one Excel row should be submitted as one Multiple bet:

```bash
USE_MULTIPLE=1 python main.py
```

Real row-wise Multiple submit:

```bash
USE_MULTIPLE=1 STAKE=1 DRY_RUN=0 SUBMIT_EACH_BET=1 python main.py
```

With a specific input file:

```bash
USE_MULTIPLE=1 STAKE=1 DRY_RUN=0 SUBMIT_EACH_BET=1 INPUT_FILE=sample_file.xlsx python main.py
```

### 7. Speed Tuning

Default speed is already optimized. If needed:

```bash
ACTION_DELAY=0.1 NAV_DELAY=0.2 SUBMIT_WAIT=4 SUBMIT_RESULT_TIMEOUT=5 STAKE=1 DRY_RUN=0 SUBMIT_EACH_BET=1 python main.py
```

### 8. Increase Site Error Retries

If the site often shows `Error displaying Lucky Numbers`:

```bash
ERROR_RETRIES=5 python main.py
```

### 9. Start Or Resume Rows

By default, the bot asks where to start:

```text
Where should the script start?
1. Start from beginning: row 1
2. Resume after latest result file (...): row X
3. Enter row number manually
Select 1/2/3 [1]:
```

Options:

- Press `1` or Enter: start from first row.
- Press `2`: resume after the latest `run_results_*.csv`.
- Press `3`: manually enter row number.

Skip the prompt and start from the beginning:

```bash
START_MODE=start USE_MULTIPLE=1 STAKE=1 DRY_RUN=0 SUBMIT_EACH_BET=1 python main.py
```

Skip the prompt and resume after the latest `run_results_*.csv` file:

```bash
START_MODE=resume USE_MULTIPLE=1 STAKE=1 DRY_RUN=0 SUBMIT_EACH_BET=1 python main.py
```

Skip the prompt and start from a specific row:

```bash
START_ROW=25 USE_MULTIPLE=1 STAKE=1 DRY_RUN=0 SUBMIT_EACH_BET=1 python main.py
```

## Important Flags

- `DRY_RUN=1`: default; add to betslip only, never submit
- `DRY_RUN=0`: allow non-dry-run actions
- `SUBMIT_EACH_BET=1`: with `DRY_RUN=0`, click `Submit` after each clean `Add Bet`
- `STAKE=10`: use stake `10` for each bet unless input file has its own stake
- `INPUT_FILE=filename.xlsx`: choose input file
- `USE_MULTIPLE=1`: add all jobs from one Excel row, click `Multiple`, then treat that row as one bet
- `REQUIRE_LOGIN=1`: default; wait for manual login before processing rows
- `LOGIN_WAIT=900`: wait up to 900 seconds for manual login
- `START_MODE=start`: start from first row without prompt
- `START_MODE=resume`: resume after latest result CSV without prompt
- `START_ROW=25`: start from row 25 without prompt

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

If login is not completed before running:

- The bot waits automatically
- Complete login manually in the connected Chrome window
- Default login wait is 900 seconds

Increase login wait time:

```bash
LOGIN_WAIT=1200 python main.py
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
