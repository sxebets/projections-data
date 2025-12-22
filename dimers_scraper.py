"""
Dimers Scraper with GitHub Integration
Scrapes NBA, NHL, and NFL projections from dimers.com
"""

import os
import sys
import time
import json
import subprocess
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains


class DimersScraper:
    """Dimers scraper with GitHub integration"""
    
    def __init__(self, config):
        self.config = config
        self.driver = None
        self.data_dir = 'data'
        self.history_dir = 'data/history'
        self.download_dir = os.path.abspath(self.data_dir)
        self.scraped_data = {}
        
        # Create data directories
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.history_dir, exist_ok=True)
    
    def setup_driver(self, headless=True):
        """Setup Chrome webdriver"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # Set download preferences
        prefs = {
            'download.default_directory': self.download_dir,
            'download.prompt_for_download': False,
            'download.directory_upgrade': True,
            'safebrowsing.enabled': True,
        }
        chrome_options.add_experimental_option('prefs', prefs)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 20)
        print(f"✓ Browser initialized (downloads to: {self.download_dir})")
    
    def login(self):
        """Login to Dimers via Auth0"""
        print("\nLogging in to Dimers...")
        
        try:
            # Go to NBA projections page first
            self.driver.get('https://www.dimers.com/nba/player-projections')
            time.sleep(4)
            
            # Dismiss any popups first
            print("  Dismissing popups...")
            self.dismiss_popups()
            time.sleep(2)
            self.dismiss_popups()  # Try again for second popup
            time.sleep(1)
            
            self.driver.save_screenshot('debug_dimers_after_popup.png')
            
            current_url = self.driver.current_url
            page_source = self.driver.page_source
            
            print(f"  Current URL: {current_url[:70]}...")
            
            # Check if we need to login
            # Look for: Log In button, locked data icons, or "Get Dimers Pro" button
            has_login_button = 'Log In' in page_source
            has_locked_data = '🔒' in page_source or 'locked' in page_source.lower() or 'Unlock' in page_source
            
            # Check if Download CSV actually works (data isn't locked)
            # If we can see actual projection numbers for multiple players, we're logged in
            is_logged_in = self.driver.execute_script("""
                // Check if data cells have actual numbers (not locked)
                var cells = document.querySelectorAll('td');
                var numberCount = 0;
                for (var i = 0; i < cells.length; i++) {
                    var text = cells[i].textContent.trim();
                    // Check if it's a number like "29.0" or "3.5"
                    if (/^\\d+\\.\\d+$/.test(text)) {
                        numberCount++;
                    }
                }
                // If we found many numbers, data is unlocked
                return numberCount > 20;
            """)
            
            print(f"  Has login button: {has_login_button}, Data unlocked: {is_logged_in}")
            
            if is_logged_in and not has_login_button:
                print("✓ Already logged in!")
                return True
            
            # Need to login - click the Log In button
            print("  Clicking Log In button...")
            clicked_login = self.driver.execute_script("""
                // Find Log In button/link
                var elements = document.querySelectorAll('a, button');
                for (var i = 0; i < elements.length; i++) {
                    var text = elements[i].textContent.trim();
                    if (text === 'Log In' || text === 'Login' || text === 'Sign In') {
                        elements[i].click();
                        return 'clicked: ' + text;
                    }
                }
                // Try finding by href
                var links = document.querySelectorAll('a[href*="login"], a[href*="auth"]');
                if (links.length > 0) {
                    links[0].click();
                    return 'clicked href';
                }
                return null;
            """)
            
            if clicked_login:
                print(f"  ✓ {clicked_login}")
                time.sleep(4)
            else:
                print("  Could not find Log In button, navigating directly...")
                self.driver.get('https://auth.dimers.com/u/login')
                time.sleep(3)
            
            # Now we should be on the auth page
            current_url = self.driver.current_url
            print(f"  Auth URL: {current_url[:70]}...")
            self.driver.save_screenshot('debug_dimers_auth.png')
            
            # Check if we're on the auth page
            if 'auth' not in current_url.lower() and 'login' not in current_url.lower():
                print("  ⚠️ Not on auth page, trying direct navigation...")
                self.driver.get('https://auth.dimers.com/u/login')
                time.sleep(3)
            
            # Find and fill email field
            email_field = None
            email_selectors = [
                "input[name='username']",
                "input[name='email']",
                "input[type='email']",
                "input[type='text']",
                "input#username",
            ]
            
            for selector in email_selectors:
                try:
                    fields = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for field in fields:
                        if field.is_displayed():
                            email_field = field
                            break
                    if email_field:
                        break
                except:
                    continue
            
            if not email_field:
                print("  ❌ Could not find email field")
                self.driver.save_screenshot('debug_dimers_no_email.png')
                return False
            
            email_field.clear()
            email_field.send_keys(self.config.get('dimers_username', ''))
            print("  ✓ Filled email")
            time.sleep(0.5)
            
            # Find and fill password
            password_field = None
            try:
                password_field = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            except:
                pass
            
            if not password_field:
                print("  ❌ Could not find password field")
                return False
            
            password_field.clear()
            password_field.send_keys(self.config.get('dimers_password', ''))
            print("  ✓ Filled password")
            time.sleep(0.5)
            
            # Click submit button
            clicked = self.driver.execute_script("""
                var buttons = document.querySelectorAll('button');
                for (var i = 0; i < buttons.length; i++) {
                    var text = buttons[i].textContent.toLowerCase();
                    if (text.includes('continue') || text.includes('log in') || 
                        text.includes('sign in') || text.includes('submit')) {
                        buttons[i].click();
                        return true;
                    }
                }
                var submit = document.querySelector('button[type="submit"]');
                if (submit) { submit.click(); return true; }
                return false;
            """)
            
            if clicked:
                print("  ✓ Clicked submit")
            else:
                print("  ❌ Could not find submit button")
                return False
            
            # Wait for redirect
            time.sleep(6)
            self.driver.save_screenshot('debug_dimers_after_login.png')
            
            # Navigate to projections page to verify
            self.driver.get('https://www.dimers.com/nba/player-projections')
            time.sleep(4)
            
            # Dismiss any new popups
            self.dismiss_popups()
            time.sleep(1)
            
            # Verify login by checking for unlocked data
            is_logged_in = self.driver.execute_script("""
                var cells = document.querySelectorAll('td');
                var numberCount = 0;
                for (var i = 0; i < cells.length; i++) {
                    var text = cells[i].textContent.trim();
                    if (/^\\d+\\.\\d+$/.test(text)) {
                        numberCount++;
                    }
                }
                return numberCount > 20;
            """)
            
            if is_logged_in:
                print("✓ Login successful!")
                return True
            else:
                print("  ⚠️ Login may have failed - data still locked")
                self.driver.save_screenshot('debug_dimers_login_failed.png')
                return False
                
        except Exception as e:
            print(f"❌ Login error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def wait_for_download(self, timeout=15):
        """Wait for a CSV file to download"""
        downloads_folder = os.path.join(os.path.expanduser('~'), 'Downloads')
        
        folders_to_check = [self.download_dir, downloads_folder]
        
        print(f"  Waiting for download...")
        
        # Wait a few seconds for download to complete
        time.sleep(3)
        
        # Find the most recently modified projections file
        best_file = None
        best_mtime = 0
        
        for folder in folders_to_check:
            if not os.path.exists(folder):
                continue
            
            for f in os.listdir(folder):
                if not f.endswith('.csv'):
                    continue
                if f.endswith('.crdownload'):
                    continue
                
                # Look for projection files (Dimers uses "player_projections")
                if 'projections' not in f.lower() and 'player' not in f.lower():
                    continue
                    
                full_path = os.path.join(folder, f)
                
                try:
                    mtime = os.path.getmtime(full_path)
                    age = time.time() - mtime
                    
                    # Only consider files from last 30 seconds
                    if age < 30 and mtime > best_mtime:
                        best_mtime = mtime
                        best_file = full_path
                except:
                    continue
        
        if best_file:
            age = time.time() - best_mtime
            print(f"  ✓ Found: {os.path.basename(best_file)} ({age:.0f}s ago)")
            
            try:
                with open(best_file, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                lines = content.strip().split('\n')
                print(f"    ✓ {len(lines)} rows")
                
                # Clean up the temp file (Chrome's auto-named download)
                try:
                    os.remove(best_file)
                    print(f"    ✓ Cleaned up temp file")
                except:
                    pass
                
                return content
            except Exception as e:
                print(f"    ⚠️ Error reading: {e}")
                return None
        
        print(f"  ⚠️ No recent projections file found")
        return None
    
    def dismiss_popups(self):
        """Dismiss any popups/modals on the page"""
        # Try multiple times to close all popups
        for attempt in range(3):
            self.driver.execute_script("""
                // Find and click X/close buttons
                var closeSelectors = [
                    'button[aria-label="Close"]',
                    'button[aria-label="close"]',
                    '[aria-label="Close"]',
                    '[aria-label="close"]', 
                    'button.close',
                    '.modal-close',
                    'button[class*="close"]',
                    'button[class*="Close"]',
                    'svg[class*="close"]',
                    '[data-dismiss="modal"]',
                    // Target X buttons specifically
                    'button:has(svg)',
                    'div[class*="modal"] button',
                    'div[class*="popup"] button',
                    'div[class*="dialog"] button',
                ];
                
                for (var i = 0; i < closeSelectors.length; i++) {
                    try {
                        var elements = document.querySelectorAll(closeSelectors[i]);
                        for (var j = 0; j < elements.length; j++) {
                            var el = elements[j];
                            // Check if it looks like a close button (small, contains X or has close-related attributes)
                            var text = el.textContent.trim();
                            var isSmall = el.offsetWidth < 100 && el.offsetHeight < 100;
                            if (el.offsetParent !== null && (text === '' || text === '×' || text === 'X' || text === '✕' || isSmall)) {
                                el.click();
                                console.log('Clicked close button');
                            }
                        }
                    } catch(e) {}
                }
                
                // Also look for any SVG that might be a close icon
                var svgs = document.querySelectorAll('svg');
                for (var i = 0; i < svgs.length; i++) {
                    var parent = svgs[i].parentElement;
                    if (parent && parent.tagName === 'BUTTON' && parent.offsetParent !== null) {
                        // Check if this button is in a modal/popup area
                        var rect = parent.getBoundingClientRect();
                        // Close buttons are usually in corners
                        if (rect.width < 60 && rect.height < 60) {
                            try {
                                parent.click();
                                console.log('Clicked SVG parent button');
                            } catch(e) {}
                        }
                    }
                }
                
                // Press Escape key
                document.dispatchEvent(new KeyboardEvent('keydown', {key: 'Escape', keyCode: 27, bubbles: true}));
            """)
            time.sleep(0.5)
        
        # Also try clicking outside modals
        try:
            actions = ActionChains(self.driver)
            # Click in the corner of the page
            actions.move_by_offset(5, 5).click().perform()
            actions.reset_actions()
        except:
            pass
    
    def scrape_sport(self, sport):
        """Scrape projections for a specific sport"""
        sport_lower = sport.lower()
        url = f'https://www.dimers.com/{sport_lower}/player-projections'
        
        print(f"\n=== Scraping Dimers {sport.upper()} ===")
        
        try:
            # Navigate to the sport-specific URL
            print(f"  Navigating to {url}...")
            self.driver.get(url)
            time.sleep(5)
            
            # Verify we're on the correct page
            current_url = self.driver.current_url
            print(f"  Current URL: {current_url}")
            
            if sport_lower not in current_url.lower():
                print(f"  ⚠️ URL doesn't contain '{sport_lower}' - trying again...")
                self.driver.get(url)
                time.sleep(3)
            
            # Dismiss any popups
            self.dismiss_popups()
            time.sleep(1)
            
            # DON'T click Player Projections tab - we're already on that page via URL
            # The tab click was causing navigation issues
            
            self.driver.save_screenshot(f'debug_dimers_{sport_lower}.png')
            
            # Verify page content matches expected sport
            page_title = self.driver.execute_script("return document.title;")
            print(f"  Page title: {page_title}")
            
            # Check if page loaded properly
            if sport_lower == 'nba' and 'NBA' not in self.driver.page_source:
                print(f"  ⚠️ Page doesn't seem to be NBA - refreshing...")
                self.driver.get(url)
                time.sleep(5)
            elif sport_lower == 'nfl' and 'NFL' not in self.driver.page_source and 'Football' not in self.driver.page_source:
                print(f"  ⚠️ Page doesn't seem to be NFL - refreshing...")
                self.driver.get(url)
                time.sleep(5)
            
            # Click Download CSV button
            clicked = False
            
            try:
                # First scroll to top of page
                self.driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(1)
                
                # Close any open popups
                self.driver.execute_script("""
                    document.dispatchEvent(new KeyboardEvent('keydown', {key: 'Escape', keyCode: 27, bubbles: true}));
                """)
                time.sleep(0.5)
                
                # Find the Download CSV button - rightmost element with exact text
                download_btn = self.driver.execute_script("""
                    var candidates = [];
                    var all = document.querySelectorAll('*');
                    
                    for (var i = 0; i < all.length; i++) {
                        var el = all[i];
                        if (!el.offsetParent) continue;
                        
                        var text = el.innerText || el.textContent || '';
                        text = text.trim();
                        
                        if (text === 'Download CSV') {
                            var rect = el.getBoundingClientRect();
                            // Button should be on right side and in toolbar area
                            if (rect.x > 900 && rect.y < 500 && rect.y > 200) {
                                candidates.push({el: el, x: rect.x, y: rect.y});
                            }
                        }
                    }
                    
                    if (candidates.length > 0) {
                        candidates.sort(function(a,b) { return b.x - a.x; });
                        return candidates[0].el;
                    }
                    return null;
                """)
                
                if download_btn:
                    print(f"  Found Download CSV button")
                    
                    # Use ActionChains click (most reliable)
                    actions = ActionChains(self.driver)
                    actions.move_to_element(download_btn).click().perform()
                    clicked = True
                    print(f"  ✓ Clicked Download CSV")
                else:
                    print("  ⚠️ Could not find Download CSV button")
                        
            except Exception as e:
                print(f"  Click error: {e}")
            
            if clicked:
                time.sleep(2)
                self.driver.save_screenshot(f'debug_dimers_{sport_lower}_after_click.png')
            else:
                print("  ❌ Could not find Download CSV button")
                
                # Debug: print visible buttons
                buttons = self.driver.execute_script("""
                    var btns = document.querySelectorAll('button, a');
                    var texts = [];
                    for (var i = 0; i < btns.length; i++) {
                        if (btns[i].offsetParent !== null) {
                            var t = btns[i].textContent.trim().substring(0, 40);
                            if (t) texts.push(btns[i].tagName + ': ' + t);
                        }
                    }
                    return texts.slice(0, 20);
                """)
                print(f"  Visible buttons: {buttons}")
                return None
            
            # Wait for download
            csv_content = self.wait_for_download()
            
            if csv_content:
                # Save current file
                csv_file = os.path.join(self.data_dir, f'dimers_{sport_lower}.csv')
                with open(csv_file, 'w', encoding='utf-8') as f:
                    f.write(csv_content)
                print(f"  ✓ Saved: dimers_{sport_lower}.csv")
                
                # Save historical copy
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
                hist_file = os.path.join(self.history_dir, f'dimers_{sport_lower}_{timestamp}.csv')
                with open(hist_file, 'w', encoding='utf-8') as f:
                    f.write(csv_content)
                print(f"  ✓ Saved historical: dimers_{sport_lower}_{timestamp}.csv")
                
                return {'csv_saved': True, 'bytes': len(csv_content)}
            
            return None
            
        except Exception as e:
            print(f"❌ Error scraping {sport}: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def git_commit_and_push(self):
        """Commit and push data to GitHub"""
        print("\n=== Pushing to GitHub ===")
        
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            result = subprocess.run(['git', 'status'], capture_output=True, text=True)
            if result.returncode != 0:
                print("❌ Not a git repository")
                return False
            
            subprocess.run(['git', 'add', 'data/'], check=True)
            
            result = subprocess.run(['git', 'diff', '--staged', '--quiet'], capture_output=True)
            if result.returncode == 0:
                print("  No changes to commit")
                return True
            
            subprocess.run(['git', 'commit', '-m', f'Update Dimers projections - {timestamp}'], check=True)
            print("  ✓ Committed changes")
            
            result = subprocess.run(['git', 'push'], capture_output=True, text=True)
            if result.returncode != 0:
                print(f"  ⚠️ Push failed: {result.stderr}")
                return False
            
            print("✓ Data pushed to GitHub")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Git error: {str(e)}")
            return False
    
    def scrape_all(self, headless=False, sports=None):
        """Scrape all sports and push to GitHub"""
        if sports is None:
            sports = ['nba', 'nfl']  # Dimers doesn't offer NHL projections
        
        results = {}
        
        try:
            self.setup_driver(headless=headless)
            
            if not self.login():
                print("Cannot continue without successful login")
                return results
            
            for sport in sports:
                results[sport] = self.scrape_sport(sport)
            
            if any(results.values()):
                self.git_commit_and_push()
            
            return results
            
        finally:
            if self.driver:
                self.driver.quit()
                print("\n✓ Browser closed")


def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Scrape Dimers projections')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    parser.add_argument('--sport', choices=['nba', 'nfl', 'all'], default='all', help='Sport to scrape')
    args = parser.parse_args()
    
    print("=" * 60)
    print("Dimers Scraper with GitHub Integration")
    print("=" * 60)
    
    # Load configuration
    config = None
    
    if os.path.exists('scraper_config.json'):
        with open('scraper_config.json', 'r') as f:
            config = json.load(f)
        print("✓ Loaded scraper_config.json")
    else:
        print("\n❌ No config file found!")
        print("Please create scraper_config.json with:")
        print('  {"dimers_username": "your_email", "dimers_password": "your_password"}')
        return
    
    if not config.get('dimers_username'):
        print("\n⚠️ Please add dimers_username and dimers_password to your config!")
        return
    
    sports = ['nba', 'nfl'] if args.sport == 'all' else [args.sport]
    
    print(f"Mode: {'Headless' if args.headless else 'Visible browser'}")
    print(f"Sports: {', '.join(sports)}")
    
    scraper = DimersScraper(config)
    results = scraper.scrape_all(headless=args.headless, sports=sports)
    
    print("\n" + "=" * 60)
    print("Scraping Complete!")
    print("=" * 60)
    for sport in sports:
        status = '✓' if results.get(sport) else '✗'
        print(f"{sport.upper()}: {status}")
    print(f"\nCSV files saved to: data/")


if __name__ == "__main__":
    main()
