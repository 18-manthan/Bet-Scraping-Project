import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# ---------- Setup ----------
options = uc.ChromeOptions()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--start-maximized")

driver = uc.Chrome(options=options, version_main=147)
wait = WebDriverWait(driver, 20)


try:
    # ---------- Open page ----------
    driver.get("https://www.hollywoodbets.net/betting/21/lucky-numbers/countries")
    print("Loading page...")
    time.sleep(3)

    # ---------- Click South Africa ----------
    print("Clicking South Africa...")

    south_africa = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//div[contains(@class,'accordion-title') and contains(text(),'South Africa')]")
    ))

    driver.execute_script("arguments[0].click();", south_africa)
    print("South Africa clicked")

    time.sleep(2)

    # ---------- Click Correct Game ----------
    print("Opening SA POWA NUMBAS...")

    game = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//span[text()='SA POWA NUMBAS']")
    ))

    driver.execute_script("arguments[0].click();", game)

    # Wait for correct URL
    wait.until(lambda d: "powa-numbas" in d.current_url.lower())

    print("Game opened")
    print("URL:", driver.current_url)

    time.sleep(2)

    # ---------- Ensure MY NUMBERS ----------
    print("👉 Ensuring MY NUMBERS mode...")

    try:
        my_numbers = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//*[text()='MY NUMBERS']")
        ))
        driver.execute_script("arguments[0].click();", my_numbers)
        print("MY NUMBERS active")
    except:
        print("Already active")

    time.sleep(1)

    # ---------- Get ALL number buttons ONCE ----------
    print("Fetching number buttons...")

    buttons = wait.until(lambda d: d.find_elements(
        By.XPATH, "//button[contains(@data-testid,'numbers-button')]"
    ))

    # Map text -> element
    btn_map = {b.text.strip(): b for b in buttons}

    # ---------- Select numbers FAST ----------
    print("Selecting numbers...")

    numbers = ['4', '5', '29', '30']

    for num in numbers:
        btn = btn_map.get(num)

        if btn:
            driver.execute_script("arguments[0].click();", btn)
            print(f"Clicked {num}")
        else:
            print(f"Not found {num}")

    # ---------- Click Add Bet ----------
    print("👉 Clicking Add Bet...")

    add_bet = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//button[contains(text(),'Add Bet')]")
    ))

    driver.execute_script("arguments[0].click();", add_bet)

    print("🎉 Bet added successfully")

    # ---------- Betslip ----------
    try:
        betslip = wait.until(EC.presence_of_element_located(
            (By.XPATH, "//*[contains(text(),'Stake')]")
        ))
        print("Betslip:")
        print(betslip.text)
    except:
        print("⚠️ Betslip not found")


except Exception as e:
    print("❌ Error:", e)


# # ---------- Keep open ----------
# print("\n✅ Done. Browser stays open.")
# while True:
#     time.sleep(60)