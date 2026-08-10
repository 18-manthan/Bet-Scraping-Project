import csv
import os
import re
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


SITE_URL = "https://www.hollywoodbets.net/betting/21/lucky-numbers/countries"
INPUT_FILE = os.getenv("INPUT_FILE", "sample_file.xlsx")
DRY_RUN = os.getenv("DRY_RUN", "1").strip().lower() not in {"0", "false", "no"}
DEFAULT_STAKE = os.getenv("STAKE", "").strip()
RESULTS_FILE = os.getenv(
    "RESULTS_FILE",
    f"run_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
)

print("🚀 Starting script...")
print(f"👉 Input file: {INPUT_FILE}")
print(f"👉 Dry run: {'ON - Add Bet and stake entry are skipped' if DRY_RUN else 'OFF - live Add Bet is enabled'}")


# ---------- Setup ----------
options = webdriver.ChromeOptions()
options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 20)
country_wait = WebDriverWait(driver, 120)


# ---------- Helpers ----------
def log(msg):
    print(f"👉 {msg}")


def clean_cell(value):
    if pd.isna(value):
        return ""

    text = str(value).strip()
    if text.lower() == "nan":
        return ""
    if text.endswith(".0"):
        text = text[:-2]
    return text.strip()


def value_after_colon(text):
    return text.split(":", 1)[-1].strip()


def split_values(text):
    text = clean_cell(text)
    if not text or text.upper() in {"N/A", "NA", "NONE"}:
        return []
    return [part.strip() for part in re.split(r"[,/;\n]+", text) if part.strip()]


def normalize_set_type(text):
    text = clean_cell(text).upper()
    text = text.replace("&", " AND ")
    text = re.sub(r"\s+", " ", text)

    if "MAIN" in text and "BONUS" in text:
        return "MAIN SET & BONUS"
    if "BONUS" in text:
        return "BONUS"
    return "MAIN SET"


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def result_row(job, status, message=""):
    return {
        "row": job.get("row", ""),
        "country": job.get("country", ""),
        "game": job.get("game", ""),
        "set_type": job.get("set_type", ""),
        "main_numbers": ",".join(job.get("main_numbers", [])),
        "bonus_numbers": ",".join(job.get("bonus_numbers", [])),
        "stake": job.get("stake", ""),
        "status": status,
        "message": message,
    }


def write_results(rows):
    if not rows:
        return

    fields = [
        "row",
        "country",
        "game",
        "set_type",
        "main_numbers",
        "bonus_numbers",
        "stake",
        "status",
        "message",
    ]
    with open(RESULTS_FILE, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def click(xpath, label=""):
    try:
        log(f"Click: {label}")
        el = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
        driver.execute_script("arguments[0].click();", el)
        return True
    except Exception as e:
        print(f"❌ Failed: {label} → {e}")
        return False


def wait_for_countries_page():
    try:
        country_wait.until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//*[contains(normalize-space(.), 'South Africa') "
                    "or contains(normalize-space(.), 'United States') "
                    "or contains(normalize-space(.), 'Lucky Numbers')]",
                )
            )
        )
        return True
    except Exception:
        print("❌ Countries page did not load. Clear Cloudflare/login in Chrome, then run again.")
        return False


def select_from_grid(grid_index, numbers, label):
    numbers = [clean_cell(n) for n in numbers if clean_cell(n)]
    if not numbers:
        return True, ""

    log(f"Selecting {label} numbers: {numbers}")
    grid = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, f"(//div[@data-testid='numbers-container'])[{grid_index}]")
        )
    )
    buttons = grid.find_elements(By.TAG_NAME, "button")
    btn_map = {b.text.strip(): b for b in buttons}
    missing = []

    for number in numbers:
        button = btn_map.get(number)
        if button:
            driver.execute_script("arguments[0].click();", button)
            print(f"✔ {label} {number}")
        else:
            missing.append(number)
            print(f"❌ {label} not found {number}")

    if missing:
        return False, f"Missing {label.lower()} numbers: {', '.join(missing)}"
    return True, ""


def select_numbers(job):
    set_type = job["set_type"]

    if set_type in {"MAIN SET", "MAIN SET & BONUS"}:
        ok, message = select_from_grid(1, job["main_numbers"], "Main")
        if not ok:
            return False, message

    if set_type in {"BONUS", "MAIN SET & BONUS"}:
        bonus_numbers = job["bonus_numbers"]
        if not bonus_numbers:
            return False, "Bonus set requested, but no bonus number was supplied"

        grids = driver.find_elements(By.XPATH, "//div[@data-testid='numbers-container']")
        bonus_grid = 2 if len(grids) > 1 else 1
        ok, message = select_from_grid(bonus_grid, bonus_numbers, "Bonus")
        if not ok:
            return False, message

    return True, ""


def add_bet():
    if DRY_RUN:
        print("🧪 DRY RUN: Skipping Add Bet")
        return True
    return click("//button[contains(normalize-space(.),'Add Bet')]", "Add Bet")


def set_stake(stake):
    stake = clean_cell(stake)
    if not stake:
        return True, ""

    if DRY_RUN:
        print(f"🧪 DRY RUN: Skipping stake entry ({stake})")
        return True, ""

    stake_xpaths = [
        "//input[contains(translate(@placeholder,'STAKE','stake'),'stake')]",
        "//input[contains(translate(@aria-label,'STAKE','stake'),'stake')]",
        "//input[contains(translate(@name,'STAKE','stake'),'stake')]",
        "(//input[@type='number' or @inputmode='decimal' or @inputmode='numeric'])[1]",
    ]

    for xpath in stake_xpaths:
        try:
            field = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", field)
            field.clear()
            field.send_keys(stake)
            return True, ""
        except Exception:
            continue

    return False, "Stake field was not found"


def switch_to_multiple():
    toggle_xpaths = [
        "//*[normalize-space()='Multiple']",
        "//span[normalize-space()='Multiple']",
        "//label[.//*[normalize-space()='Multiple'] or contains(normalize-space(.), 'Multiple')]",
        "//label[contains(@class,'MultipleToggleContainer')]",
    ]

    for xpath in toggle_xpaths:
        if click(xpath, "Multiple"):
            time.sleep(1)
            return True

    return False


def page_validation_message():
    keywords = ["related legs", "cannot", "not allowed", "validation", "invalid"]
    body = driver.find_element(By.TAG_NAME, "body").text
    lowered = body.lower()
    for keyword in keywords:
        if keyword in lowered:
            lines = [line.strip() for line in body.splitlines() if keyword in line.lower()]
            return lines[0] if lines else keyword
    return ""


# ---------- Input Parsing ----------
def read_input(path):
    path = Path(path)
    if not path.exists():
        raise SystemExit(f"❌ Input file not found: {path}")

    if path.suffix.lower() == ".csv":
        return parse_tabular(pd.read_csv(path))

    if path.suffix.lower() in {".xlsx", ".xls"}:
        raw = pd.read_excel(path, header=None, engine="openpyxl")
        if raw.shape[0] and any("COUNTRY:" in clean_cell(v).upper() for v in raw.iloc[0]):
            return parse_block_excel(raw)
        return parse_tabular(pd.read_excel(path, engine="openpyxl"))

    raise SystemExit("❌ Only .xlsx, .xls, and .csv input files are supported")


def parse_block_excel(df):
    jobs = []

    for c_idx, cell in enumerate(df.iloc[0]):
        country_text = clean_cell(cell)
        if "COUNTRY:" not in country_text.upper():
            continue

        country = value_after_colon(country_text)
        game_text = clean_cell(df.iat[1, c_idx]) if len(df) > 1 else ""
        bonus_text = clean_cell(df.iat[2, c_idx]) if len(df) > 2 else ""
        type_text = clean_cell(df.iat[3, c_idx]) if len(df) > 3 else ""
        set_text = clean_cell(df.iat[4, c_idx]) if len(df) > 4 else ""
        stake_text = ""
        data_start = 5

        for r_idx in range(5, min(len(df), 10)):
            cell_text = clean_cell(df.iat[r_idx, c_idx])
            if "STAKE" in cell_text.upper():
                stake_text = value_after_colon(cell_text)
                data_start = r_idx + 1
                break

        games = split_values(value_after_colon(game_text))
        bonus_numbers = split_values(value_after_colon(bonus_text))

        try:
            number_count = int(value_after_colon(type_text))
        except ValueError:
            print(f"❌ Invalid TYPE for {country}: {type_text}")
            continue

        set_type = normalize_set_type(value_after_colon(set_text))
        stake = stake_text or DEFAULT_STAKE
        row_count = 0

        log(f"COUNTRY: {country}")
        log(f"GAMES: {games}")
        log(f"TYPE: {number_count}")
        log(f"TYPE OF SET: {set_type}")
        if stake:
            log(f"STAKE: {stake}")

        for r_idx in range(data_start, len(df)):
            main_numbers = []

            for offset in range(number_count):
                read_col = c_idx + offset
                if read_col >= len(df.columns):
                    break

                number_text = clean_cell(df.iat[r_idx, read_col])
                if not number_text:
                    break
                main_numbers.append(number_text)

            if not main_numbers:
                break

            if len(main_numbers) != number_count:
                print(f"⚠️ Skipping incomplete row {r_idx + 1} for {country}: {main_numbers}")
                continue

            row_count += 1
            for game in games:
                jobs.append(
                    {
                        "row": row_count,
                        "country": country,
                        "game": game,
                        "set_type": set_type,
                        "main_numbers": main_numbers,
                        "bonus_numbers": bonus_numbers,
                        "stake": stake,
                    }
                )

    return jobs


def parse_tabular(df):
    df.columns = [clean_cell(c) for c in df.columns]
    header_map = {re.sub(r"[^a-z0-9]+", "", c.lower()): c for c in df.columns}

    def col(*names):
        for name in names:
            key = re.sub(r"[^a-z0-9]+", "", name.lower())
            if key in header_map:
                return header_map[key]
        return None

    country_col = col("Country")
    game_col = col("Game Names", "Game Name", "Game")
    set_col = col("Type of Set", "Set Type", "Type")
    main_col = col("Main Numbers", "Main Number", "Numbers")
    bonus_col = col("Bonus", "Bonus Number", "Bonus Numbers")
    stake_col = col("Stake", "Stake Amount", "Amount")

    if not country_col or not game_col:
        raise SystemExit("❌ Tabular input must include Country and Game/Game Names columns")

    jobs = []
    for idx, row in df.iterrows():
        country = clean_cell(row.get(country_col, ""))
        games = split_values(row.get(game_col, ""))
        if not country or not games:
            continue

        set_type = normalize_set_type(row.get(set_col, "MAIN SET")) if set_col else "MAIN SET"
        main_numbers = split_values(row.get(main_col, "")) if main_col else []
        bonus_numbers = split_values(row.get(bonus_col, "")) if bonus_col else []
        stake = clean_cell(row.get(stake_col, "")) if stake_col else DEFAULT_STAKE
        stake = stake or DEFAULT_STAKE

        for game in games:
            jobs.append(
                {
                    "row": idx + 1,
                    "country": country,
                    "game": game,
                    "set_type": set_type,
                    "main_numbers": main_numbers,
                    "bonus_numbers": bonus_numbers,
                    "stake": stake,
                }
            )

    return jobs


# ---------- Open Site ----------
driver.get(SITE_URL)
if not wait_for_countries_page():
    raise SystemExit(1)


# ---------- Read Input ----------
jobs = read_input(INPUT_FILE)

print("\n📦 FINAL JOBS:")
for job in jobs:
    print(job)

if not jobs:
    raise SystemExit(f"❌ No valid jobs found in {INPUT_FILE}")


# ---------- Process ----------
results = []
bet_count = 0
ready_count = 0
multiple_enabled = False
rows = sorted({job["row"] for job in jobs})

try:
    for row_number in rows:
        row_jobs = [job for job in jobs if job["row"] == row_number]
        should_use_multiple = len(row_jobs) > 1

        print(f"\n====== ROW {row_number} ======")

        for job in row_jobs:
            log(
                f"{job['country']} → {job['game']} → "
                f"{job['set_type']} → main={job['main_numbers']} bonus={job['bonus_numbers']}"
            )

            try:
                country_xpath = (
                    "//*[contains(@class,'accordion-title') and "
                    f"contains(normalize-space(.),'{job['country']}')]"
                )
                if not click(country_xpath, f"Country {job['country']}"):
                    results.append(result_row(job, "failed", "Country was not found/clickable"))
                    continue

                time.sleep(2)

                if not click(f"//span[normalize-space()='{job['game']}']", f"Game {job['game']}"):
                    results.append(result_row(job, "failed", "Game was not found/clickable"))
                    continue

                wait.until(lambda d: slug(job["game"]) in d.current_url.lower())
                log("Game opened")
                time.sleep(2)

                ok, message = select_numbers(job)
                if not ok:
                    print(f"❌ Skipping Add Bet: {message}")
                    results.append(result_row(job, "skipped", message))
                    continue

                if not add_bet():
                    results.append(result_row(job, "failed", "Add Bet failed"))
                    continue

                if DRY_RUN:
                    ready_count += 1
                    log(f"Dry-run selections ready: {ready_count}")
                else:
                    bet_count += 1
                    log(f"Total Bets: {bet_count}")

                ok, message = set_stake(job.get("stake", ""))
                if not ok:
                    results.append(result_row(job, "failed", message))
                    continue

                if DRY_RUN:
                    results.append(result_row(job, "dry_run" if DRY_RUN else "added", ""))
                else:
                    validation = page_validation_message()
                    if validation:
                        print(f"⚠️ Validation warning detected: {validation}")
                        results.append(result_row(job, "warning", validation))
                    else:
                        results.append(result_row(job, "added", ""))

                if not DRY_RUN and should_use_multiple and bet_count >= 2 and not multiple_enabled:
                    multiple_enabled = switch_to_multiple()

                time.sleep(2)

            except Exception as e:
                print(f"❌ Error: {e}")
                results.append(result_row(job, "failed", str(e)))
            finally:
                driver.get(SITE_URL)
                wait_for_countries_page()
                time.sleep(3)
finally:
    write_results(results)
    print(f"\n📝 Results saved to {RESULTS_FILE}")

print("\n✅ DONE")
