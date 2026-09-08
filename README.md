# Lucky Numbers Betting Bot

Selenium automation for the Hollywoodbets Lucky Numbers flow. The bot reads an Excel/CSV input file, opens the website in the user's already logged-in Chrome session, selects country/game/numbers, clicks `Add Bet`, and can optionally click `Submit` after each clean bet.

## Recommended: Desktop App

For the client, use the desktop app instead of typing commands manually.

Best client delivery:

```text
LuckyNumbersBot.exe
```

The `.exe` is built by the team on Windows. After that, the client can open it by double-clicking, like a normal desktop application.

Build the Windows `.exe`:

```text
build_windows_exe.bat
```

Run this build on a Windows machine. PyInstaller builds apps for the current operating system.

After build, the app is created here:

```text
dist\LuckyNumbersBot.exe
```

Give this file to the client for daily use.

On Windows, double-click:

```text
start_desktop_app.bat
```

This is useful during development before creating the final `.exe`.

Or run the development app from PowerShell:

```powershell
cd C:\Users\YourName\Documents\Scraping_Project
.\venv\Scripts\Activate.ps1
python desktop_app.py
```

Desktop app flow:

```text
Start Chrome -> complete Cloudflare/login -> select Excel/CSV -> choose mode -> choose start row -> Start Bot
```

Main buttons:

- `Start Chrome`: opens Chrome with Selenium remote debugging
- `Select Excel/CSV`: choose the client input file
- `Run mode`: choose dry run, add-only, single submit, or Multiple row submit
- `Start rows`: start from beginning, resume from latest result file, or start from a specific row
- `Start Bot`: runs the selected bot script and shows live logs
- `Stop Bot`: stops the running bot

Recommended real submit mode in the desktop app:

```text
Run mode: Real submit - Multiple row
Stake: 1
Start rows: Start from beginning / Resume / Specific row
```

## Real Submit Command

Use this command when one Excel row should be added as Multiple and submitted once:

```powershell
$env:USE_MULTIPLE="1"
$env:STAKE="1"
$env:DRY_RUN="0"
$env:SUBMIT_EACH_BET="1"
python main02.py
```

Meaning:

- `USE_MULTIPLE=1`: add all jobs from one Excel row, click `Multiple`, then submit the row once
- `STAKE=1`: enter stake amount `1` for each bet
- `DRY_RUN=0`: allow non-dry-run actions
- `SUBMIT_EACH_BET=1`: click final `Submit`
- `python main02.py`: run the bot

Flow:

```text
Row leg 1 -> Add Bet -> Row leg 2 -> Add Bet -> Click Multiple -> Enter stake -> Submit once -> Next row
```

Use a specific input file:

```powershell
$env:USE_MULTIPLE="1"
$env:STAKE="1"
$env:DRY_RUN="0"
$env:SUBMIT_EACH_BET="1"
$env:INPUT_FILE="sample_file.xlsx"
python main02.py
```

For single-bet submit mode, use:

```powershell
$env:STAKE="1"
$env:DRY_RUN="0"
$env:SUBMIT_EACH_BET="1"
python main02.py
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
- Clears the betslip before moving to the next row if a Multiple row fails or is incomplete
- Retries if the site shows `Error displaying Lucky Numbers`
- Retries if a game page shows `Error in fetching Lucky Numbers data`
- Pauses for manual Cloudflare verification and resumes the same row
- Avoids unnecessary page reloads and uses browser back/fallback reload for faster navigation
- Saves a run report as `run_results_YYYYMMDD_HHMMSS.csv`

## Files

- `main02.py`: final main bot script
- `desktop_app.py`: Tkinter desktop app launcher
- `start_desktop_app.bat`: Windows double-click launcher for the desktop app
- `build_windows_exe.bat`: builds the final Windows `.exe`
- `LuckyNumbersBot.spec`: PyInstaller build configuration
- `1sample_file.xlsx`: current default input file
- `sample_file.xlsx`, `test.xlsx`, `input_data.csv`: sample/test input files
- `requirements.txt`: Python dependencies
- `INSTALL.md`: fresh Windows setup instructions
- `INSTALL_WINDOWS.md`: fresh Windows setup instructions

## Installation Guides

- `INSTALL.md`: Windows setup from scratch
- `INSTALL_WINDOWS.md`: Windows setup from scratch

## One-Time Setup

From the project folder:

```powershell
cd C:\Users\YourName\Documents\Scraping_Project
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Start Chrome

The bot connects to a Chrome session that you control. Start Chrome like this:

```powershell
& "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="$env:TEMP\chrome-debug"
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

```powershell
cd C:\Users\YourName\Documents\Scraping_Project
.\venv\Scripts\Activate.ps1
```

## Commands

### 1. Dry Run

Use this for safe testing. It clicks `Add Bet`, but never clicks final `Submit`.

```powershell
python main02.py
```

### 2. Use A Different Input File

```powershell
$env:INPUT_FILE="sample_file.xlsx"
python main02.py
```

CSV example:

```powershell
$env:INPUT_FILE="input_data.csv"
python main02.py
```

### 3. Add Stake

Use one stake amount for all rows:

```powershell
$env:STAKE="10"
python main02.py
```

With custom input:

```powershell
$env:STAKE="10"
$env:INPUT_FILE="sample_file.xlsx"
python main02.py
```

### 4. Add To Betslip Only, No Submit

This is non-dry-run mode, but final `Submit` is still disabled.

```powershell
$env:STAKE="10"
$env:DRY_RUN="0"
$env:INPUT_FILE="sample_file.xlsx"
python main02.py
```

### 5. Add Bet Then Submit Each Bet

This submits every valid bet one by one after `Add Bet`.

```powershell
$env:STAKE="1"
$env:DRY_RUN="0"
$env:SUBMIT_EACH_BET="1"
$env:INPUT_FILE="sample_file.xlsx"
python main02.py
```

For a single country / single game file, do not use `USE_MULTIPLE=1`.

```powershell
$env:STAKE="1"
$env:DRY_RUN="0"
$env:SUBMIT_EACH_BET="1"
python main02.py
```

Single game flow:

```text
Country -> Game -> Main Set -> Numbers -> Add Bet -> Stake -> Submit -> Next row
```

For first controlled testing, use a small file with only 1-2 rows:

```powershell
$env:STAKE="1"
$env:DRY_RUN="0"
$env:SUBMIT_EACH_BET="1"
$env:INPUT_FILE="small_test.xlsx"
python main02.py
```

### 6. Enable Multiple Mode

Default is `Single` mode. Enable `Multiple` when one Excel row should be submitted as one Multiple bet:

```powershell
$env:USE_MULTIPLE="1"
python main02.py
```

Real row-wise Multiple submit:

```powershell
$env:USE_MULTIPLE="1"
$env:STAKE="1"
$env:DRY_RUN="0"
$env:SUBMIT_EACH_BET="1"
python main02.py
```

With a specific input file:

```powershell
$env:USE_MULTIPLE="1"
$env:STAKE="1"
$env:DRY_RUN="0"
$env:SUBMIT_EACH_BET="1"
$env:INPUT_FILE="sample_file.xlsx"
python main02.py
```

If any leg in a Multiple row fails, the bot skips submitting that row, clicks `Clear All`, and starts the next row fresh.

### 7. Speed Tuning

Default speed is already optimized. If needed:

```powershell
$env:ACTION_DELAY="0.1"
$env:NAV_DELAY="0.2"
$env:SUBMIT_WAIT="4"
$env:SUBMIT_RESULT_TIMEOUT="5"
$env:STAKE="1"
$env:DRY_RUN="0"
$env:SUBMIT_EACH_BET="1"
python main02.py
```

### 8. Increase Site Error Retries

If the site often shows `Error displaying Lucky Numbers`:

```powershell
$env:ERROR_RETRIES="5"
python main02.py
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

```powershell
$env:START_MODE="start"
$env:USE_MULTIPLE="1"
$env:STAKE="1"
$env:DRY_RUN="0"
$env:SUBMIT_EACH_BET="1"
python main02.py
```

Skip the prompt and resume after the latest `run_results_*.csv` file:

```powershell
$env:START_MODE="resume"
$env:USE_MULTIPLE="1"
$env:STAKE="1"
$env:DRY_RUN="0"
$env:SUBMIT_EACH_BET="1"
python main02.py
```

Skip the prompt and start from a specific row:

```powershell
$env:START_ROW="25"
$env:USE_MULTIPLE="1"
$env:STAKE="1"
$env:DRY_RUN="0"
$env:SUBMIT_EACH_BET="1"
python main02.py
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

```powershell
$env:STAKE="10"
python main02.py
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

If `Error in fetching Lucky Numbers data` appears on a game page:

- The bot refreshes the same game page first
- If still failing, it reopens the country/game from the countries page
- If it still fails after retries, that leg fails
- In Multiple mode, the row is skipped and the betslip is cleared before the next row

Increase game data retries:

```powershell
$env:GAME_DATA_RETRIES="5"
python main02.py
```

If Cloudflare / `I am human` appears:

- The bot pauses automatically
- Click `I am human` manually in Chrome
- The bot continues the same row after the page is clear
- Default wait is 900 seconds

Increase or reduce wait time:

```powershell
$env:CLOUDFLARE_WAIT="1200"
python main02.py
```

If login is not completed before running:

- The bot waits automatically
- Complete login manually in the connected Chrome window
- Default login wait is 900 seconds

Increase login wait time:

```powershell
$env:LOGIN_WAIT="1200"
python main02.py
```

If stake is not entered:

- Confirm the betslip is visible
- Confirm `STAKE=...` is provided or input has `Stake` column

If related-leg warnings appear:

- Check whether the selected games can be submitted together by the website
- Use a small test file first
- Review the generated result CSV for `warning` or `submit_failed` rows

## Safety

By default, the bot does not click final `Submit`. Final submission only happens when both are set:

```text
DRY_RUN=0
SUBMIT_EACH_BET=1
```
