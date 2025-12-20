"""
RotoGrinders Debug Inspector
Identifies where projection data is stored on the page
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import json
import time
import os

def debug_rotogrinders():
    print("=" * 60)
    print("RotoGrinders Debug Inspector")
    print("=" * 60)
    
    # Setup Chrome with performance logging
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    
    os.makedirs('debug_output', exist_ok=True)
    
    try:
        # Go directly to NBA projections (often public)
        url = 'https://rotogrinders.com/projected-stats/nba'
        print(f"\n1. Going to: {url}")
        driver.get(url)
        
        # Wait longer for dynamic content
        print("2. Waiting 10 seconds for JavaScript to load data...")
        time.sleep(10)
        
        # Save screenshot
        driver.save_screenshot('debug_output/nba_after_wait.png')
        print("   Saved screenshot: debug_output/nba_after_wait.png")
        
        # Check what elements exist on the page
        print("\n3. Analyzing page structure...")
        
        # Look for common data containers
        selectors_to_check = [
            ("table", "Tables"),
            ("tbody tr", "Table rows"),
            ("[class*='player']", "Player elements"),
            ("[class*='projection']", "Projection elements"),
            ("[class*='stat']", "Stat elements"),
            ("[class*='grid']", "Grid elements"),
            ("[class*='row']", "Row elements"),
            ("[data-player]", "Data-player attributes"),
            ("[data-id]", "Data-id attributes"),
            ("div[class*='Table']", "Table divs (React)"),
            ("[class*='cell']", "Cell elements"),
        ]
        
        for selector, name in selectors_to_check:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                print(f"   Found {len(elements):3d} {name}")
                # Show sample of first element
                if len(elements) > 0:
                    sample = elements[0].text[:80].replace('\n', ' ')
                    if sample:
                        print(f"       Sample: {sample}...")
        
        # Check for React/Vue/Angular data
        print("\n4. Checking for framework data stores...")
        
        js_checks = [
            ("window.__INITIAL_STATE__", "Initial State"),
            ("window.__NUXT__", "Nuxt Data"),
            ("window.__NEXT_DATA__", "Next.js Data"),
            ("window.__data__", "Window Data"),
            ("window.pageData", "Page Data"),
            ("window.__PRELOADED_STATE__", "Preloaded State"),
            ("document.querySelector('[data-reactroot]')", "React Root"),
            ("document.querySelector('[data-vue]')", "Vue Root"),
        ]
        
        for js_code, name in js_checks:
            try:
                result = driver.execute_script(f"return {js_code} ? true : false")
                if result:
                    print(f"   Found: {name}")
            except:
                pass
        
        # Capture network requests
        print("\n5. Analyzing network requests for API calls...")
        
        logs = driver.get_log('performance')
        api_calls = []
        
        for entry in logs:
            try:
                message = json.loads(entry['message'])
                method = message['message']['method']
                
                if method == 'Network.responseReceived':
                    url = message['message']['params']['response']['url']
                    mime = message['message']['params']['response'].get('mimeType', '')
                    
                    # Look for JSON API responses
                    if 'json' in mime.lower() or '/api/' in url.lower():
                        api_calls.append(url)
                        print(f"   API: {url[:80]}...")
            except:
                continue
        
        # Save API calls to file
        with open('debug_output/api_calls.txt', 'w') as f:
            f.write('\n'.join(api_calls))
        print(f"   Saved {len(api_calls)} API URLs to: debug_output/api_calls.txt")
        
        # Get the fully rendered HTML
        print("\n6. Saving fully rendered HTML...")
        
        # Get the outer HTML after JavaScript has run
        rendered_html = driver.execute_script("return document.documentElement.outerHTML")
        
        with open('debug_output/rendered_page.html', 'w', encoding='utf-8') as f:
            f.write(rendered_html)
        print(f"   Saved: debug_output/rendered_page.html ({len(rendered_html):,} chars)")
        
        # Get just the body text
        body_text = driver.find_element(By.TAG_NAME, "body").text
        with open('debug_output/page_text.txt', 'w', encoding='utf-8') as f:
            f.write(body_text)
        print(f"   Saved: debug_output/page_text.txt ({len(body_text):,} chars)")
        
        # Look for player names specifically
        print("\n7. Looking for player names in page text...")
        
        # Common NBA player names to search for
        test_names = ['LeBron', 'Curry', 'Durant', 'Doncic', 'Antetokounmpo', 'Jokic']
        
        for name in test_names:
            if name.lower() in body_text.lower():
                print(f"   Found: {name}")
        
        # Show first part of body text
        print("\n8. First 1000 chars of page content:")
        print("-" * 60)
        print(body_text[:1000] if body_text else "(empty)")
        print("-" * 60)
        
        print("\n" + "=" * 60)
        print("Debug complete! Check the debug_output folder.")
        print("=" * 60)
        
        input("\nPress Enter to close browser...")
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        driver.quit()


if __name__ == "__main__":
    debug_rotogrinders()
