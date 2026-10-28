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

PROJECT_BASE = Path(os.getenv("BOT_PROJECT_DIR", Path(__file__).resolve().parent)).resolve()


def project_path(value):
    path = Path(value).expanduser()
    if path.is_absolute():
        return path
    return PROJECT_BASE / path


INPUT_FILE = str(project_path(os.getenv("INPUT_FILE", "file.xlsx")))
# DRY_RUN=1: add bets to betslip only, never click final Submit.
# DRY_RUN=0: allow non-dry-run actions; final Submit still needs SUBMIT_EACH_BET=1.
DRY_RUN = os.getenv("DRY_RUN", "1").strip().lower() not in {"0", "false", "no"}
USE_MULTIPLE = os.getenv("USE_MULTIPLE", "0").strip().lower() in {"1", "true", "yes"}
# SUBMIT_EACH_BET=0: do not click final Submit after Add Bet.
# SUBMIT_EACH_BET=1 with DRY_RUN=0: click Submit after each clean Add Bet.
SUBMIT_EACH_BET = os.getenv("SUBMIT_EACH_BET", "0").strip().lower() in {"1", "true", "yes"}
DEFAULT_STAKE = os.getenv("STAKE", "").strip()
ERROR_RETRIES = int(os.getenv("ERROR_RETRIES", "3"))
GAME_DATA_RETRIES = int(os.getenv("GAME_DATA_RETRIES", "3"))
ACTION_DELAY = float(os.getenv("ACTION_DELAY", "0.3"))
NAV_DELAY = float(os.getenv("NAV_DELAY", "0.4"))
ERROR_RETRY_DELAY = float(os.getenv("ERROR_RETRY_DELAY", "2"))
SUBMIT_WAIT = float(os.getenv("SUBMIT_WAIT", "6"))
SUBMIT_RESULT_TIMEOUT = float(os.getenv("SUBMIT_RESULT_TIMEOUT", "5"))
CLOUDFLARE_WAIT = int(os.getenv("CLOUDFLARE_WAIT", "900"))
CLOUDFLARE_CHECK_INTERVAL = float(os.getenv("CLOUDFLARE_CHECK_INTERVAL", "3"))
# REQUIRE_LOGIN=1: wait for manual login before processing any input rows.
# REQUIRE_LOGIN=0: skip the login wait, useful only for UI checks that do not need account access.
REQUIRE_LOGIN = os.getenv("REQUIRE_LOGIN", "1").strip().lower() not in {"0", "false", "no"}
LOGIN_WAIT = int(os.getenv("LOGIN_WAIT", "900"))
LOGIN_CHECK_INTERVAL = float(os.getenv("LOGIN_CHECK_INTERVAL", "2"))
START_MODE = os.getenv("START_MODE", "").strip().lower()
START_ROW = os.getenv("START_ROW", "").strip()
RESULTS_FILE = str(
    project_path(
        os.getenv(
            "RESULTS_FILE",
            f"run_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        )
    )
)

print("🚀 Starting script...")
print(f"👉 Input file: {INPUT_FILE}")
submit_enabled = SUBMIT_EACH_BET and not DRY_RUN
print("👉 Dry run: " f"{'ON - Add Bet is clicked, Submit is never clicked' if DRY_RUN else 'OFF'}")
print(f"👉 Betslip mode: {'Multiple enabled' if USE_MULTIPLE else 'Single only'}")
print(f"👉 Submit each bet: {'YES' if submit_enabled else 'NO'}")
print(f"👉 Manual login required: {'YES' if REQUIRE_LOGIN else 'NO'}")
if SUBMIT_EACH_BET and DRY_RUN:
    print("⚠️ SUBMIT_EACH_BET is ignored while DRY_RUN=1")


# ---------- Setup ----------
options = webdriver.ChromeOptions()
options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 20)
country_wait = WebDriverWait(driver, 120)
short_wait = WebDriverWait(driver, 12)


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


def latest_results_file():
    files = sorted(PROJECT_BASE.glob("run_results_*.csv"), key=lambda path: path.stat().st_mtime, reverse=True)
    return files[0] if files else None


def last_processed_row_from_results(path):
    if not path or not path.exists():
        return 0

    last_row = 0
    try:
        with open(path, newline="", encoding="utf-8") as file:
            for row in csv.DictReader(file):
                try:
                    last_row = max(last_row, int(clean_cell(row.get("row", ""))))
                except ValueError:
                    pass
    except Exception as exc:
        print(f"⚠️ Could not read previous results file {path}: {exc}")

    return last_row


def choose_start_row(available_rows):
    first_row = min(available_rows)
    last_row = max(available_rows)

    if START_ROW:
        try:
            selected = int(START_ROW)
            print(f"👉 Starting from row {selected} from START_ROW")
            return selected
        except ValueError:
            print(f"⚠️ Invalid START_ROW={START_ROW}; showing prompt instead")

    latest_file = latest_results_file()
    last_done = last_processed_row_from_results(latest_file) if latest_file else 0
    resume_row = last_done + 1 if last_done else first_row

    if START_MODE in {"start", "initial", "beginning", "1"}:
        print(f"👉 Starting from initial row {first_row}")
        return first_row

    if START_MODE in {"resume", "last", "2"}:
        print(f"👉 Resuming from row {resume_row}")
        return resume_row

    if START_MODE in {"manual", "row", "3"}:
        value = input(f"Enter start row ({first_row}-{last_row}): ").strip()
        return int(value) if value else first_row

    print("\nWhere should the script start?")
    print(f"1. Start from beginning: row {first_row}")
    if latest_file and last_done:
        print(f"2. Resume after latest result file ({latest_file.name}): row {resume_row}")
    else:
        print("2. Resume from last row: no previous result found, will start from beginning")
    print("3. Enter row number manually")

    choice = input("Select 1/2/3 Enter: ").strip() or "1"
    if choice == "2":
        return resume_row
    if choice == "3":
        value = input(f"Enter start row ({first_row}-{last_row}): ").strip()
        return int(value) if value else first_row
    return first_row


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


def quick_click(xpath, label="", timeout=6, quiet=False):
    try:
        if label and not quiet:
            log(f"Click: {label}")
        el = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
        driver.execute_script("arguments[0].click();", el)
        return True
    except Exception as e:
        if label and not quiet:
            print(f"❌ Failed: {label} → {e}")
        return False


def body_text():
    try:
        return driver.find_element(By.TAG_NAME, "body").text
    except Exception:
        return ""


def lucky_numbers_error_message():
    text = body_text()
    lowered = text.lower()
    messages = [
        "error displaying lucky numbers",
        "error in fetching lucky numbers data",
    ]

    for message in messages:
        if message in lowered:
            for line in text.splitlines():
                if message in line.lower():
                    return line.strip()
            return message

    return ""


def has_lucky_numbers_error():
    return bool(lucky_numbers_error_message())


def has_cloudflare_challenge():
    text = f"{driver.title} {driver.current_url} {body_text()}".lower()
    markers = [
        "cloudflare",
        "just a moment",
        "verify you are human",
        "performing security verification",
        "checking your browser",
        "ray id",
        "i am human",
    ]
    return any(marker in text for marker in markers)


def has_logged_in_session():
    text = body_text().lower()
    has_balance = "balance r" in text or re.search(r"\bbalance\s+r?\s*\d", text)
    has_greeting = re.search(r"\bhi\s+[a-z0-9]", text)
    return bool(has_balance and (has_greeting or "deposit" in text))


def has_countries_content():
    country_xpath = (
        "//*[contains(@class,'accordion-title')] "
        "| //*[contains(normalize-space(.), 'South Africa') and contains(normalize-space(.), 'United States')]"
    )
    try:
        return bool(driver.find_elements(By.XPATH, country_xpath)) and not has_lucky_numbers_error()
    except Exception:
        return False


def is_on_countries_page():
    return "/lucky-numbers/countries" in driver.current_url.lower() and has_countries_content()


def wait_for_manual_cloudflare_clear():
    print(
        "🛑 Cloudflare/security verification detected. "
        "Please click 'I am human' in Chrome. The bot will wait and continue the same row."
    )
    deadline = time.time() + CLOUDFLARE_WAIT

    while time.time() < deadline:
        if has_countries_content() and not has_cloudflare_challenge():
            print("✅ Cloudflare cleared. Continuing.")
            return True
        time.sleep(CLOUDFLARE_CHECK_INTERVAL)

    print("❌ Cloudflare was not cleared before timeout.")
    return False


def wait_for_manual_login():
    if has_logged_in_session():
        print("✅ Logged-in session detected.")
        return True

    print(
        "🛑 Login is not detected yet. "
        "Please log in manually in Chrome. The bot will wait before starting rows."
    )
    deadline = time.time() + LOGIN_WAIT

    while time.time() < deadline:
        if has_cloudflare_challenge() and not wait_for_manual_cloudflare_clear():
            return False

        if has_logged_in_session():
            print("✅ Login detected. Starting automation.")
            return True

        time.sleep(LOGIN_CHECK_INTERVAL)

    print("❌ Login was not detected before timeout.")
    return False


def wait_for_countries_page():
    country_xpath = (
        "//*[contains(@class,'accordion-title')] "
        "| //*[contains(normalize-space(.), 'South Africa') and contains(normalize-space(.), 'United States')]"
    )

    for attempt in range(1, ERROR_RETRIES + 2):
        try:
            if has_cloudflare_challenge():
                return wait_for_manual_cloudflare_clear()

            error_message = lucky_numbers_error_message()
            if error_message:
                print(f"⚠️ Site error detected: {error_message}. Reload attempt {attempt}/{ERROR_RETRIES + 1}")
                driver.get(SITE_URL)
                time.sleep(ERROR_RETRY_DELAY)

            short_wait.until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        country_xpath,
                    )
                )
            )

            if not has_lucky_numbers_error():
                return True
        except Exception:
            if attempt <= ERROR_RETRIES:
                print(f"⚠️ Countries page not ready. Reload attempt {attempt}/{ERROR_RETRIES}")
                driver.get(SITE_URL)
                time.sleep(ERROR_RETRY_DELAY)

    if has_cloudflare_challenge() or not has_countries_content():
        return wait_for_manual_cloudflare_clear()

    print("❌ Countries page did not load. Clear Cloudflare/login or retry later.")
    return False


def open_countries_page(force=False):
    if not force and is_on_countries_page():
        return True

    driver.get(SITE_URL)
    return wait_for_countries_page()


def return_to_countries_page():
    if is_on_countries_page():
        return True

    if has_cloudflare_challenge():
        return wait_for_manual_cloudflare_clear()

    if has_lucky_numbers_error():
        return open_countries_page(force=True)

    try:
        driver.back()
        if wait_for_countries_page():
            return True
    except Exception:
        pass

    return open_countries_page(force=True)


def open_game_with_retries(job):
    last_message = ""
    game_slug = slug(job["game"])

    for attempt in range(1, GAME_DATA_RETRIES + 1):
        if attempt > 1:
            if attempt == 2 and game_slug in driver.current_url.lower():
                print(f"⚠️ Lucky Numbers data error. Refreshing game page attempt {attempt}/{GAME_DATA_RETRIES}")
                driver.refresh()
            else:
                print(f"⚠️ Lucky Numbers data error. Reopening game attempt {attempt}/{GAME_DATA_RETRIES}")
                if not open_countries_page(force=True):
                    last_message = "Lucky Numbers countries page did not recover"
                    continue
            time.sleep(ERROR_RETRY_DELAY)

        try:
            if game_slug not in driver.current_url.lower():
                if not is_on_countries_page() and not return_to_countries_page():
                    last_message = "Lucky Numbers page did not recover"
                    continue

                country_xpath = (
                    "//*[contains(@class,'accordion-title') and "
                    f"contains(normalize-space(.),'{job['country']}')]"
                )
                if not click(country_xpath, f"Country {job['country']}"):
                    last_message = "Country was not found/clickable"
                    continue

                time.sleep(ACTION_DELAY)

                if not click(f"//span[normalize-space()='{job['game']}']", f"Game {job['game']}"):
                    last_message = "Game was not found/clickable"
                    continue

                wait.until(lambda d: game_slug in d.current_url.lower())

            log("Game opened")
            time.sleep(ACTION_DELAY)

            error_message = lucky_numbers_error_message()
            if not error_message:
                return True, ""

            last_message = error_message
        except Exception as exc:
            last_message = str(exc)

    return False, last_message or "Lucky Numbers game data did not load"


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


def select_set_type(set_type):
    labels = {
        "MAIN SET": "Main Set",
        "MAIN SET & BONUS": "Main Set & Bonus",
        "BONUS": "Bonus",
    }
    label = labels.get(set_type, "Main Set")
    log(f"Click: Set Type {label}")

    if set_type == "MAIN SET":
        xpaths = [
            "(//button[@data-testid='styled-button' and .//span[normalize-space()='Main Set']])[1]",
            "(//button[.//span[normalize-space()='Main Set'] and not(.//span[contains(normalize-space(),'Bonus')])])[1]",
            "(//*[@role='button' and .//span[normalize-space()='Main Set'] and not(.//span[contains(normalize-space(),'Bonus')])])[1]",
        ]
    else:
        xpaths = [
            f"(//button[@data-testid='styled-button' and .//span[normalize-space()='{label}']])[1]",
            f"(//button[.//span[normalize-space()='{label}']])[1]",
            f"(//*[@role='button' and .//span[normalize-space()='{label}']])[1]",
        ]

    clicked = False
    for xpath in xpaths:
        try:
            tab = WebDriverWait(driver, 4).until(EC.presence_of_element_located((By.XPATH, xpath)))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", tab)
            driver.execute_script("arguments[0].click();", tab)
            clicked = True
            break
        except Exception:
            pass

    if not clicked:
        return False, f"Set type tab was not found/clickable: {label}"

    time.sleep(ACTION_DELAY)

    if set_type == "MAIN SET":
        try:
            WebDriverWait(driver, 3).until(
                lambda d: len([g for g in d.find_elements(By.XPATH, "//div[@data-testid='numbers-container']") if g.is_displayed()])
                <= 1
            )
        except Exception:
            return False, "Main Set tab did not activate; still seeing bonus grid"

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
        print("🧪 DRY RUN: Clicking Add Bet only; final Submit is not clicked")
    return quick_click("//button[contains(normalize-space(.),'Add Bet')]", "Add Bet", timeout=8)


def clear_betslip():
    return quick_click("(//button[contains(normalize-space(.),'Clear All')])[1]", "Clear All", timeout=3)


def submit_bet():
    if not SUBMIT_EACH_BET:
        return False, "Submit disabled"

    if DRY_RUN:
        return False, "Submit disabled because DRY_RUN=1"

    submit_xpath = "(//button[(normalize-space()='Submit' or contains(normalize-space(.),'Submit')) and not(@disabled)])[1]"

    if quick_click(submit_xpath, "Submit", timeout=SUBMIT_WAIT):
        deadline = time.time() + SUBMIT_RESULT_TIMEOUT

        while time.time() < deadline:
            validation = page_validation_message()
            if validation:
                return False, validation

            lowered = body_text().lower()
            success_words = ["successfully", "success", "accepted", "submitted", "placed"]
            if any(word in lowered for word in success_words):
                return True, "Success message detected"

            time.sleep(0.3)

        return True, "Submit clicked; no error message detected"

    return False, "Submit button was not found/clickable"


def set_stake(stake):
    stake = clean_cell(stake)
    if not stake:
        return True, ""

    lower_from = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    lower_to = "abcdefghijklmnopqrstuvwxyz"
    stake_xpath = (
        f"(//input[contains(translate(@placeholder,'{lower_from}','{lower_to}'),'stake') "
        f"or contains(translate(@aria-label,'{lower_from}','{lower_to}'),'stake') "
        f"or contains(translate(@name,'{lower_from}','{lower_to}'),'stake') "
        "or @type='number' or @inputmode='decimal' or @inputmode='numeric'])[1]"
    )

    try:
        field = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, stake_xpath)))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", field)
        field.clear()
        field.send_keys(stake)
        return True, ""
    except Exception:
        pass

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
            time.sleep(ACTION_DELAY)
            return True

    return False


def switch_to_single():
    single_xpaths = [
        "//*[normalize-space()='Single']",
        "//span[normalize-space()='Single']",
        "//label[.//*[normalize-space()='Single'] or contains(normalize-space(.), 'Single')]",
    ]

    for xpath in single_xpaths:
        if quick_click(xpath, "Single", timeout=1, quiet=True):
            time.sleep(ACTION_DELAY)
            return True

    return False


def page_validation_message():
    keywords = [
        "cannot submit multiple legs",
        "related to leg",
        "related legs found",
        "error submitting bet",
        "insufficient balance",
        "related legs",
        "cannot",
        "not allowed",
        "validation",
        "invalid",
        "failed",
        "error",
    ]
    body = driver.find_element(By.TAG_NAME, "body").text
    lowered = body.lower()

    matched_lines = []
    for line in body.splitlines():
        clean = line.strip()
        if not clean:
            continue
        line_lower = clean.lower()
        if any(keyword in line_lower for keyword in keywords):
            if clean not in matched_lines:
                matched_lines.append(clean)

    if matched_lines:
        priority = [
            line
            for line in matched_lines
            if "cannot submit multiple legs" in line.lower()
            or "error submitting bet" in line.lower()
            or "insufficient balance" in line.lower()
        ]
        other = [line for line in matched_lines if line not in priority]
        return " | ".join(priority + other)

    for keyword in keywords:
        if keyword in lowered:
            return keyword

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
if not open_countries_page(force=True):
    raise SystemExit(1)

if REQUIRE_LOGIN and not wait_for_manual_login():
    raise SystemExit(1)

if not open_countries_page():
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
submitted_count = 0
rows = sorted({job["row"] for job in jobs})
start_row = choose_start_row(rows)
rows = [row for row in rows if row >= start_row]

if not rows:
    raise SystemExit(f"❌ No rows to process from row {start_row}")

print(f"👉 Processing rows {rows[0]} to {rows[-1]}")

if not USE_MULTIPLE:
    switch_to_single()

try:
    for row_number in rows:
        row_jobs = [job for job in jobs if job["row"] == row_number]
        should_use_multiple = USE_MULTIPLE and len(row_jobs) > 1
        row_added_jobs = []
        row_failed = False
        row_failure_message = ""

        print(f"\n====== ROW {row_number} ======")

        for job in row_jobs:
            log(
                f"{job['country']} → {job['game']} → "
                f"{job['set_type']} → main={job['main_numbers']} bonus={job['bonus_numbers']}"
            )

            try:
                if not is_on_countries_page() and not return_to_countries_page():
                    row_failure_message = "Lucky Numbers page did not recover"
                    results.append(result_row(job, "failed", row_failure_message))
                    if should_use_multiple:
                        row_failed = True
                        break
                    continue

                ok, message = open_game_with_retries(job)
                if not ok:
                    row_failure_message = message
                    results.append(result_row(job, "failed", row_failure_message))
                    if should_use_multiple:
                        row_failed = True
                        break
                    continue

                ok, message = select_set_type(job["set_type"])
                if not ok:
                    print(f"❌ Skipping Add Bet: {message}")
                    results.append(result_row(job, "skipped", message))
                    if should_use_multiple:
                        row_failed = True
                        row_failure_message = message
                        break
                    continue

                ok, message = select_numbers(job)
                if not ok:
                    print(f"❌ Skipping Add Bet: {message}")
                    results.append(result_row(job, "skipped", message))
                    if should_use_multiple:
                        row_failed = True
                        row_failure_message = message
                        break
                    continue

                if not add_bet():
                    row_failure_message = "Add Bet failed"
                    results.append(result_row(job, "failed", row_failure_message))
                    if should_use_multiple:
                        row_failed = True
                        break
                    continue

                if DRY_RUN:
                    ready_count += 1
                    log(f"Dry-run bets added to betslip: {ready_count}")
                else:
                    bet_count += 1
                    log(f"Total bets added to betslip: {bet_count}")

                if should_use_multiple:
                    row_added_jobs.append(job)
                    log(f"Multiple row legs added: {len(row_added_jobs)}/{len(row_jobs)}")
                else:
                    ok, message = set_stake(job.get("stake", ""))
                    if not ok:
                        results.append(result_row(job, "failed", message))
                        continue

                    validation = page_validation_message()
                    if validation:
                        print(f"⚠️ Validation warning detected: {validation}")
                        results.append(result_row(job, "warning", validation))
                    elif SUBMIT_EACH_BET and not DRY_RUN:
                        submitted, message = submit_bet()
                        if submitted:
                            submitted_count += 1
                            print(f"✅ Bet submitted successfully: {message}")
                            log(f"Submitted bets: {submitted_count}")
                            results.append(result_row(job, "submitted", message))
                        else:
                            print(f"❌ Bet submit failed: {message}")
                            results.append(result_row(job, "submit_failed", message))
                    elif DRY_RUN:
                        results.append(result_row(job, "dry_run", "Added to betslip; Submit not clicked"))
                    else:
                        results.append(result_row(job, "added", "Added to betslip; Submit not clicked"))

                time.sleep(ACTION_DELAY)

            except Exception as e:
                print(f"❌ Error: {e}")
                results.append(result_row(job, "failed", str(e)))
                if should_use_multiple:
                    row_failed = True
                    row_failure_message = str(e)
                    break
            finally:
                return_to_countries_page()
                time.sleep(NAV_DELAY)

        if should_use_multiple and row_failed:
            message = row_failure_message or "Multiple row failed; Submit skipped"
            print(f"⚠️ Row {row_number} failed/incomplete: {message}")
            if row_added_jobs:
                print("👉 Clearing betslip before next row")
                clear_betslip()
                for added_job in row_added_jobs:
                    results.append(result_row(added_job, "warning", f"Cleared because row failed: {message}"))
            return_to_countries_page()
            time.sleep(NAV_DELAY)
            continue

        if should_use_multiple and row_added_jobs:
            if len(row_added_jobs) != len(row_jobs):
                message = "Multiple row is incomplete; Submit skipped"
                print(f"⚠️ {message}")
                for added_job in row_added_jobs:
                    results.append(result_row(added_job, "warning", message))
                print("👉 Clearing betslip before next row")
                clear_betslip()
                continue

            if not switch_to_multiple():
                message = "Multiple mode was not found/clickable"
                for added_job in row_added_jobs:
                    results.append(result_row(added_job, "failed", message))
                print("👉 Clearing betslip before next row")
                clear_betslip()
                continue

            row_stake = next((clean_cell(job.get("stake", "")) for job in row_added_jobs if clean_cell(job.get("stake", ""))), "")
            ok, message = set_stake(row_stake)
            if not ok:
                for added_job in row_added_jobs:
                    results.append(result_row(added_job, "failed", message))
                print("👉 Clearing betslip before next row")
                clear_betslip()
                continue

            validation = page_validation_message()
            if validation:
                print(f"⚠️ Row {row_number} validation warning detected: {validation}")
                for added_job in row_added_jobs:
                    results.append(result_row(added_job, "warning", validation))
                print("👉 Clearing betslip before next row")
                clear_betslip()
            elif SUBMIT_EACH_BET and not DRY_RUN:
                submitted, message = submit_bet()
                if submitted:
                    submitted_count += 1
                    print(f"✅ Row {row_number} submitted successfully: {message}")
                    log(f"Submitted multiple rows: {submitted_count}")
                    for added_job in row_added_jobs:
                        results.append(result_row(added_job, "submitted", f"Multiple row submitted once: {message}"))
                else:
                    print(f"❌ Row {row_number} submit failed: {message}")
                    for added_job in row_added_jobs:
                        results.append(result_row(added_job, "submit_failed", message))
                    print("👉 Clearing betslip before next row")
                    clear_betslip()
            elif DRY_RUN:
                for added_job in row_added_jobs:
                    results.append(result_row(added_job, "dry_run", "Added to Multiple betslip; Submit not clicked"))
                print("👉 Clearing dry-run betslip before next row")
                clear_betslip()
            else:
                for added_job in row_added_jobs:
                    results.append(result_row(added_job, "added", "Added to Multiple betslip; Submit not clicked"))
                print("👉 Clearing betslip before next row")
                clear_betslip()

            return_to_countries_page()
            time.sleep(NAV_DELAY)
finally:
    write_results(results)
    print(f"\n📝 Results saved to {RESULTS_FILE}")

print("\n✅ DONE")
