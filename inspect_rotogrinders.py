"""
Rotogrinders Page Inspector
This script logs into RG and saves the HTML of each projection page
so we can analyze the structure and build better scrapers
"""

import os
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


def inspect_rotogrinders(username, password):
    """
    Logs in and saves HTML snapshots of each projection page
    """
    
    # Setup browser
    chrome_options = Options()
    # Run visible so you can see what's happening
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 20)
    
    output_dir = 'page_snapshots'
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        print("=" * 60)
        print("Rotogrinders Page Inspector")
        print("=" * 60)
        
        # Login
        print("\n1. Going to login page...")
        driver.get('https://rotogrinders.com/sign-in')
        time.sleep(3)
        
        # Save login page first
        print("2. Saving login page HTML...")
        with open(os.path.join(output_dir, 'login_page.html'), 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        driver.save_screenshot(os.path.join(output_dir, 'login_page.png'))
        print("✓ Login page saved - check page_snapshots/login_page.png to see what's there")
        
        # Try to find login fields
        print("\n3. Looking for login form...")
        try:
            # Wait longer for page to load
            print("   Waiting for page to fully load...")
            time.sleep(5)
            
            # Wait for username field to be present and visible
            print("   Looking for username field...")
            email_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            print("   ✓ Found username field")
            
            # Wait a bit more to ensure it's interactive
            time.sleep(1)
            email_field.clear()
            time.sleep(0.5)
            email_field.send_keys(username)
            print(f"   ✓ Filled username: {username}")
            time.sleep(1)
            
            # Wait for password field
            print("   Looking for password field...")
            password_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "password"))
            )
            print("   ✓ Found password field")
            
            # Wait to ensure it's interactive
            time.sleep(1)
            password_field.clear()
            time.sleep(0.5)
            password_field.send_keys(password)
            print("   ✓ Filled password")
            time.sleep(1)
            
            # Find and click submit button
            print("   Looking for submit button...")
            login_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='submit']"))
            )
            print("   ✓ Found submit button, clicking...")
            login_button.click()
            print("   ✓ Clicked! Waiting for login to complete...")
            time.sleep(8)  # Give more time for redirect
            
            if 'sign-in' not in driver.current_url.lower():
                print("✓ Login successful - redirected from sign-in page!")
            else:
                print("⚠️ Still on sign-in page - login may have failed")
                print("   Check page_snapshots/after_login.png")
                driver.save_screenshot(os.path.join(output_dir, 'after_login.png'))
            
        except Exception as e:
            print(f"⚠️ Error during login attempt: {e}")
        
        print("\nCheck page_snapshots/login_page.png to see what the form looks like")
        print("Continuing to projection pages...")
        
        # Inspect NBA page
        print("\n4. Inspecting NBA projections page...")
        driver.get('https://rotogrinders.com/projected-stats/nba')
        time.sleep(5)  # Give it time to load
        
        with open(os.path.join(output_dir, 'nba_page.html'), 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print(f"✓ Saved NBA page HTML")
        
        # Take screenshot
        driver.save_screenshot(os.path.join(output_dir, 'nba_page.png'))
        print(f"✓ Saved NBA screenshot")
        
        # Inspect NFL page
        print("\n5. Inspecting NFL projections page...")
        driver.get('https://rotogrinders.com/projected-stats/nfl')
        time.sleep(5)
        
        with open(os.path.join(output_dir, 'nfl_page.html'), 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print(f"✓ Saved NFL page HTML")
        
        driver.save_screenshot(os.path.join(output_dir, 'nfl_page.png'))
        print(f"✓ Saved NFL screenshot")
        
        # Inspect NHL page
        print("\n6. Inspecting NHL projections page...")
        driver.get('https://rotogrinders.com/projected-stats/nhl')
        time.sleep(5)
        
        with open(os.path.join(output_dir, 'nhl_page.html'), 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print(f"✓ Saved NHL page HTML")
        
        driver.save_screenshot(os.path.join(output_dir, 'nhl_page.png'))
        print(f"✓ Saved NHL screenshot")
        
        print("\n" + "=" * 60)
        print("Inspection Complete!")
        print("=" * 60)
        print(f"Files saved to: {output_dir}/")
        print("\nYou can now:")
        print("1. Open the .html files to see the page structure")
        print("2. View the .png screenshots")
        print("3. Look for table structures, export buttons, or download links")
        
        # Keep browser open for manual inspection
        input("\nPress Enter to close the browser...")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        driver.quit()


if __name__ == "__main__":
    # Load credentials
    if os.path.exists('rg_config.json'):
        with open('rg_config.json', 'r') as f:
            config = json.load(f)
            username = config['username']
            password = config['password']
    else:
        print("❌ rg_config.json not found!")
        print("Please create it with your credentials first.")
        exit(1)
    
    if username == "your_rotogrinders_email":
        print("❌ Please update rg_config.json with your actual credentials!")
        exit(1)
    
    inspect_rotogrinders(username, password)
