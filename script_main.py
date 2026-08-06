import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ---------- Setup ----------
options = webdriver.ChromeOptions()
options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 20)


# ---------- Common Click ----------
def click(xpath):
    el = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
    driver.execute_script("arguments[0].click();", el)
    return el


# ---------- Switch Tab ----------
def switch_type(tab):
    try:
        click(f"//span[normalize-space()='{tab}']")
        print(f"✔ Switched to {tab}")
        time.sleep(1)
    except:
        print(f"⚠️ Tab not found or already active: {tab}")


# ---------- Select from grid ----------
def select_from_grid(grid, numbers, label=""):
    if not numbers:
        return

    nums = [n.strip() for n in numbers.split(",") if n.strip()]
    buttons = grid.find_elements(By.TAG_NAME, "button")

    btn_map = {b.text.strip(): b for b in buttons}

    for n in nums:
        if n in btn_map:
            driver.execute_script("arguments[0].click();", btn_map[n])
            print(f"✔ {label} {n}")
        else:
            print(f"❌ {label} not found {n}")


# ---------- Dynamic Selection ----------
def handle_selection(play_type, main_numbers, bonus):
    grids = driver.find_elements(By.XPATH, "//div[@data-testid='numbers-container']")
    grid_count = len(grids)

    print(f"🔍 Found {grid_count} number grids")

    if grid_count == 0:
        print("❌ No grids found")
        return

    # Main numbers
    if play_type in ["Main Set", "Main Set & Bonus"] and main_numbers:
        select_from_grid(grids[0], main_numbers, "Main")

    # Bonus numbers
    if play_type in ["Bonus", "Main Set & Bonus"] and bonus:
        if grid_count > 1:
            select_from_grid(grids[1], bonus, "Bonus")
        else:
            select_from_grid(grids[0], bonus, "Bonus")


# ---------- Add Bet ----------
def add_bet():
    try:
        btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(text(),'Add Bet')]")
        ))
        driver.execute_script("arguments[0].click();", btn)
        print("🎉 Bet added")
    except:
        print("❌ Add Bet failed (check selection)")


# ---------- Start ----------
driver.get("https://www.hollywoodbets.net/betting/21/lucky-numbers/countries")
time.sleep(5)


# ---------- Read Excel ----------
import pandas as pd

df = pd.read_excel("test.xlsx", engine="openpyxl")

# Clean headers
df.columns = [c.strip() for c in df.columns]


for _, row in df.iterrows():
    # Clean row values
    row = {k.strip(): (str(v).strip() if pd.notna(v) else "") for k, v in row.items()}
    print("ROW DATA:", row)

    country = row.get("Country", "")
    game = row.get("Game Names", "")
    bonus = row.get("Bonus", "")
    play_type = row.get("Type", "")
    main_numbers = row.get("Main Numbers", "")

    # Fix bonus float (7.0 → 7)
    if bonus:
        try:
            bonus = str(int(float(bonus)))
        except:
            pass

    # Skip invalid rows
    if not country or not game:
        print("⚠️ Skipping empty row")
        continue

    # 🔥 MULTI-GAME SUPPORT
    games = [g.strip() for g in game.split(",") if g.strip()]

    for single_game in games:

        print("\n==============================")
        print(f"Processing: {country} → {single_game}")

        try:
            # ---------- Click Country ----------
            click(f"//div[contains(@class,'accordion-title') and contains(text(),'{country}')]")
            time.sleep(2)

            # ---------- Click Game ----------
            click(f"//span[normalize-space()='{single_game}']")
            wait.until(lambda d: single_game.lower().replace(" ", "-") in d.current_url.lower())
            print("✔ Game opened")
            time.sleep(2)

            # ---------- Switch Tab ----------
            if play_type:
                switch_type(play_type)

            # ---------- Select Numbers ----------
            handle_selection(play_type, main_numbers, bonus)

            # ---------- Add Bet ----------
            add_bet()

            time.sleep(2)

        except Exception as e:
            print(f"❌ Error processing {single_game}: {e}")

        # ---------- Back ----------
        driver.get("https://www.hollywoodbets.net/betting/21/lucky-numbers/countries")
        time.sleep(3)


print("\n✅ ALL DONE")