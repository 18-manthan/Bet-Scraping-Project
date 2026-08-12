# Lucky Numbers Betting Bot

This project automates the Lucky Numbers betting flow using Selenium and a Chrome browser session that is already logged in by the user.

The bot can:

- Read betting data from Excel or CSV
- Open the Lucky Numbers page
- Select country, game, main numbers, and bonus numbers
- Skip entries when required numbers are not available
- Run safely in dry-run mode without pressing final Submit
- Optionally enter a stake amount
- Keep the betslip in `Single` mode by default
- Save run results to a CSV report

## Important Safety Note

Dry-run mode is enabled by default. A normal run can click `Add Bet` and add selections to the betslip, but it does not click the final `Submit` button.

```bash
python main.py
```

Non-dry-run mode must be enabled explicitly:

```bash
DRY_RUN=0 python main.py
```

Use this only after the dry-run output has been reviewed. The script still does not click final `Submit`.

By default, the bot does not switch to `Multiple`. To explicitly allow Multiple mode:

```bash
USE_MULTIPLE=1 python main.py
```

## Daily Run Steps

1. Start Chrome with remote debugging:

```bash
google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug
```

2. In that Chrome window, open the betting site and complete any Cloudflare/security verification manually.

3. Log in manually.

4. Make sure the Lucky Numbers countries page is visible.

5. In a second terminal, run:

```bash
cd /home/cis/Documents/Scraping_Project
source venv/bin/activate
python main.py
```

6. Review the generated result file:

```text
run_results_YYYYMMDD_HHMMSS.csv
```

## Input Files

Default input:

```text
sample_file.xlsx
```

Use another file:

```bash
INPUT_FILE=test.xlsx python main.py
```

Supported formats:

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

## Stake

Use one stake for all rows:

```bash
STAKE=10 python main.py
```

Use non-dry-run mode with stake:

```bash
STAKE=10 DRY_RUN=0 python main.py
```

Stake can also be supplied in the Excel/CSV input using a `Stake` column.

## Result Statuses

The result CSV may contain:

- `dry_run`: selection was added to betslip, but final Submit was not clicked
- `added`: Add Bet action completed; final Submit was not clicked
- `skipped`: required numbers were missing
- `failed`: country/game/stake/action failed
- `warning`: site validation warning was detected

## Current Limitation

Cloudflare/security verification and login are manual. The bot starts after the user has opened a verified, logged-in Chrome session.
