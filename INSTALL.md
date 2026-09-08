# Windows Installation Guide

Use this guide to set up and run the Lucky Numbers betting bot on a fresh Windows system.

## 1. Install Requirements

Install these first:

- Python 3.11 or newer
- Google Chrome
- The project folder `Scraping_Project`

When installing Python, enable:

```text
Add python.exe to PATH
```

After installation, open PowerShell and check:

```powershell
python --version
pip --version
```

If `python` is not found, close PowerShell, reopen it, and try again.

## 2. Copy Project

Copy the full project folder to the Windows system.

Example location:

```text
C:\Users\YourName\Documents\Scraping_Project
```

Open PowerShell and go to the project folder:

```powershell
cd C:\Users\YourName\Documents\Scraping_Project
```

## 3. Create Virtual Environment

Create the virtual environment:

```powershell
python -m venv venv
```

Activate it:

```powershell
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Then activate again:

```powershell
.\venv\Scripts\Activate.ps1
```

When activated, you should see:

```text
(venv)
```

## 4. Install Python Packages

Install dependencies:

```powershell
pip install -r requirements.txt
```

Optional check:

```powershell
pip list
```

## 5. Run The Desktop App

The easiest way for the client is to use the desktop app.

For final client delivery, build the Windows `.exe` first:

```text
build_windows_exe.bat
```

After the build finishes, the final app is:

```text
dist\LuckyNumbersBot.exe
```

The client can open `LuckyNumbersBot.exe` directly by double-clicking it.

For development/testing before building the `.exe`, double-click this file from the project folder:

```text
start_desktop_app.bat
```

Or run it from PowerShell:

```powershell
cd C:\Users\YourName\Documents\Scraping_Project
.\venv\Scripts\Activate.ps1
python desktop_app.py
```

In the desktop app:

1. Click `Start Chrome`.
2. Complete Cloudflare/security verification manually.
3. Log in manually.
4. Select the Excel/CSV input file.
5. Choose the run mode.
6. Choose whether to start from beginning, resume, or start from a specific row.
7. Click `Start Bot`.

Recommended client mode for row-wise Multiple submit:

```text
Run mode: Real submit - Multiple row
Stake: 1
```

## 6. Start Chrome Manually For Selenium

Close all existing Chrome windows first.

Then start Chrome with remote debugging:

```powershell
& "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="$env:TEMP\chrome-debug"
```

If Chrome is installed in the 32-bit program folder, use:

```powershell
& "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="$env:TEMP\chrome-debug"
```

Keep this Chrome window open while the bot runs.

In that Chrome window:

1. Open Hollywoodbets.
2. Complete Cloudflare / security verification manually.
3. Log in manually.
4. Open the Lucky Numbers countries page.

If the bot starts before login is complete, it will wait for manual login before processing rows.

## 7. Run Safe Test From PowerShell

Open a second PowerShell window.

Go to the project folder:

```powershell
cd C:\Users\YourName\Documents\Scraping_Project
```

Activate the virtual environment:

```powershell
.\venv\Scripts\Activate.ps1
```

Run a safe dry run:

```powershell
python main02.py
```

Dry run means:

- The bot can click `Add Bet`
- The bot does not click final `Submit`

Review the output and generated result file:

```text
run_results_YYYYMMDD_HHMMSS.csv
```

## 8. Run With Custom Input

```powershell
$env:INPUT_FILE="sample_file.xlsx"
python main02.py
```

For CSV:

```powershell
$env:INPUT_FILE="input_data.csv"
python main02.py
```

## 9. Real Row-Wise Multiple Submit

Use this when one Excel row should be added as a Multiple bet and submitted once:

```powershell
$env:USE_MULTIPLE="1"
$env:STAKE="1"
$env:DRY_RUN="0"
$env:SUBMIT_EACH_BET="1"
python main02.py
```

Flow:

```text
Row leg 1 -> Add Bet -> Row leg 2 -> Add Bet -> Click Multiple -> Enter stake -> Submit once -> Next row
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

## 10. Single Country / Single Game Submit

Use this when the file contains a single country / single game flow:

```powershell
$env:STAKE="1"
$env:DRY_RUN="0"
$env:SUBMIT_EACH_BET="1"
python main02.py
```

Do not set `USE_MULTIPLE=1` for a single game flow.

Flow:

```text
Country -> Game -> Main Set -> Numbers -> Add Bet -> Stake -> Submit -> Next row
```

## 11. Start Or Resume Rows

By default, the bot asks:

```text
Where should the script start?
1. Start from beginning: row 1
2. Resume after latest result file (...): row X
3. Enter row number manually
Select 1/2/3 [1]:
```

Options:

- Press `1` or Enter: start from first row
- Press `2`: resume after the latest `run_results_*.csv`
- Press `3`: manually enter row number

Start from beginning without prompt:

```powershell
$env:START_MODE="start"
python main02.py
```

Resume without prompt:

```powershell
$env:START_MODE="resume"
python main02.py
```

Start from a specific row:

```powershell
$env:START_ROW="25"
python main02.py
```

## 12. Clear PowerShell Environment Variables

PowerShell environment variables stay active in the same terminal window.

To clear values:

```powershell
Remove-Item Env:\USE_MULTIPLE -ErrorAction SilentlyContinue
Remove-Item Env:\STAKE -ErrorAction SilentlyContinue
Remove-Item Env:\DRY_RUN -ErrorAction SilentlyContinue
Remove-Item Env:\SUBMIT_EACH_BET -ErrorAction SilentlyContinue
Remove-Item Env:\INPUT_FILE -ErrorAction SilentlyContinue
Remove-Item Env:\START_MODE -ErrorAction SilentlyContinue
Remove-Item Env:\START_ROW -ErrorAction SilentlyContinue
Remove-Item Env:\LOGIN_WAIT -ErrorAction SilentlyContinue
Remove-Item Env:\ERROR_RETRIES -ErrorAction SilentlyContinue
```

Or close PowerShell and open a new one.

## 13. Troubleshooting

If Chrome connection fails:

- Make sure Chrome was started with `--remote-debugging-port=9222`
- Close all Chrome windows and start Chrome again using the command in this guide
- Keep the remote-debugging Chrome window open

If PowerShell says scripts are disabled:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

If login is not detected:

- Log in manually in the Chrome window
- Make sure the page shows account balance
- Increase login wait if needed:

```powershell
$env:LOGIN_WAIT="1200"
python main02.py
```

If Cloudflare appears:

- Click the manual verification in Chrome
- The bot will wait and continue

If the site shows `Error displaying Lucky Numbers`:

```powershell
$env:ERROR_RETRIES="5"
python main02.py
```

If a game page shows `Error in fetching Lucky Numbers data`, the bot refreshes the same game page first, then reopens the country/game from the countries page. Increase game data retries if needed:

```powershell
$env:GAME_DATA_RETRIES="5"
python main02.py
```

If numbers are skipped:

- Confirm the numbers exist for that game
- Confirm `TYPE OF SET` is correct
- Confirm the correct input file is being used

If stake entry fails:

- Confirm the user is logged in
- Confirm the betslip is visible
- Run one dry run first, then a small non-dry-run test

## 14. Safety

By default:

```powershell
python main02.py
```

does not click final `Submit`.

Real submit happens only when both are set:

```text
DRY_RUN=0
SUBMIT_EACH_BET=1
```
