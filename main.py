import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

print("🚀 Starting script...")

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
    if text.endswith(".0"):
        text = text[:-2]
    return text

def value_after_colon(text):
    return text.split(":", 1)[-1].strip()

def click(xpath, label=""):
    try:
        log(f"Click: {label}")
        el = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
        driver.execute_script("arguments[0].scrollIntoView(true);", el)
        driver.execute_script("arguments[0].click();", el)
        return True
    except Exception as e:
        print(f"❌ Failed: {label} → {e}")
        return False

def wait_for_countries_page():
    try:
        country_wait.until(EC.presence_of_element_located(
            (By.XPATH, "//*[contains(normalize-space(.), 'South Africa') or contains(normalize-space(.), 'United States')]")
        ))
        return True
    except Exception:
        print("❌ Countries page did not load. Clear Cloudflare/login in Chrome, then run again.")
        return False

def select_main_numbers(numbers):
    log(f"Selecting MAIN numbers: {numbers}")

    grid = wait.until(EC.presence_of_element_located(
        (By.XPATH, "(//div[@data-testid='numbers-container'])[1]")
    ))

    buttons = grid.find_elements(By.TAG_NAME, "button")
    btn_map = {b.text.strip(): b for b in buttons}

    selected = 0

    for n in numbers:
        if n in btn_map:
            driver.execute_script("arguments[0].click();", btn_map[n])
            print(f"✔ {n}")
            selected += 1
        else:
            print(f"❌ Not found {n}")

    return selected == len(numbers)

def add_bet():
    return click("//button[contains(text(),'Add Bet')]", "Add Bet")

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

# ---------- Open Site ----------
driver.get("https://www.hollywoodbets.net/betting/21/lucky-numbers/countries")
if not wait_for_countries_page():
    raise SystemExit(1)

# ---------- Read Excel ----------
df = pd.read_excel("sample_file.xlsx", header=None, engine="openpyxl")

# ---------- Parse Blocks ----------
blocks = []

for c_idx, cell in enumerate(df.iloc[0]):
    country_text = clean_cell(cell)

    if "COUNTRY:" not in country_text.upper():
        continue

    country = value_after_colon(country_text)
    game_text = clean_cell(df.iat[1, c_idx])
    type_text = clean_cell(df.iat[3, c_idx])
    set_text = clean_cell(df.iat[4, c_idx])

    games = value_after_colon(game_text).replace("/", ",").split(",")
    games = [game.strip() for game in games if game.strip()]

    try:
        number_count = int(value_after_colon(type_text))
    except ValueError:
        print(f"❌ Invalid TYPE for {country}: {type_text}")
        continue

    block = {
        "country": country,
        "games": games,
        "type": number_count,
        "set_type": value_after_colon(set_text),
        "start_col": c_idx,
        "numbers": []
    }

    log(f"COUNTRY: {block['country']}")
    log(f"GAMES: {block['games']}")
    log(f"TYPE: {block['type']}")
    log(f"TYPE OF SET: {block['set_type']}")

    for r_idx in range(5, len(df)):
        nums = []

        for offset in range(number_count):
            read_col = c_idx + offset

            if read_col >= len(df.columns):
                break

            number_text = clean_cell(df.iat[r_idx, read_col])

            if not number_text:
                break

            nums.append(number_text)

        if not nums:
            break

        if len(nums) != number_count:
            print(f"⚠️ Skipping incomplete row {r_idx + 1} for {country}: {nums}")
            continue

        block["numbers"].append(nums)

    if block["numbers"]:
        blocks.append(block)

print("\n📦 FINAL BLOCKS:")
for b in blocks:
    print(b)

if not blocks:
    raise SystemExit("❌ No valid country blocks found in sample_file.xlsx")

# ---------- PROCESS ----------
bet_count = 0
multiple_enabled = False
max_rows = max(len(b["numbers"]) for b in blocks)

for i in range(max_rows):

    print(f"\n====== ROW {i+1} ======")
    row_bet_total = sum(
        len(block["games"])
        for block in blocks
        if i < len(block["numbers"])
    )
    should_use_multiple = row_bet_total > 1

    for block in blocks:

        if i >= len(block["numbers"]):
            continue

        country = block["country"]
        games = block["games"]
        numbers = block["numbers"][i]

        log(f"{country} → {games} → {numbers}")

        for game in games:
            try:
                # ---------- Click Country ----------
                if not click(
                    f"//div[contains(@class,'accordion-title') and contains(text(),'{country}')]",
                    f"Country {country}"
                ):
                    continue

                time.sleep(2)

                # ---------- Click Game ----------
                if not click(
                    f"//span[normalize-space()='{game}']",
                    f"Game {game}"
                ):
                    continue

                wait.until(lambda d: game.lower().replace(" ", "-") in d.current_url.lower())
                log("Game opened")
                time.sleep(2)

                # ---------- Select ONLY MAIN ----------
                if not select_main_numbers(numbers):
                    print(f"❌ Skipping Add Bet because not all numbers were selected: {numbers}")
                    continue

                # ---------- Add Bet ----------
                if add_bet():
                    bet_count += 1
                    log(f"Total Bets: {bet_count}")

                    # ---------- Switch to Multiple only when this row has 2+ bets ----------
                    if should_use_multiple and bet_count >= 2 and not multiple_enabled:
                        multiple_enabled = switch_to_multiple()

                time.sleep(2)

            except Exception as e:
                print(f"❌ Error: {e}")

            # ---------- Back ----------
            driver.get("https://www.hollywoodbets.net/betting/21/lucky-numbers/countries")
            time.sleep(3)

print("\n✅ DONE")
