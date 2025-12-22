"""
Stokastic Scraper with GitHub Integration
Scrapes NBA, NHL, and NFL projections from tools.stokastic.com
"""

import os
import sys
import time
import json
import subprocess
import base64
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import requests


class StokasticScraper:
    """Stokastic scraper with GitHub integration"""
    
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
        
        # Get absolute path for downloads
        self.download_dir = os.path.abspath(self.data_dir)
        os.makedirs(self.download_dir, exist_ok=True)
        
        # Set download preferences - use absolute path
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
        """Login to Stokastic via Auth0"""
        print("\nLogging in to Stokastic...")
        
        try:
            # Go to the main site first
            self.driver.get('https://tools.stokastic.com/datahub/NBA')
            time.sleep(4)
            
            # Check if we see "You must be logged in" page
            page_source = self.driver.page_source
            
            if 'You must be logged in' in page_source or 'LOG IN' in page_source:
                print("  Found login required page...")
                self.driver.save_screenshot('debug_step1_login_page.png')
                
                # Try multiple ways to click LOG IN button
                clicked = False
                
                # Method 1: Find by text content using JavaScript
                try:
                    self.driver.execute_script("""
                        var buttons = document.querySelectorAll('button, a');
                        for (var i = 0; i < buttons.length; i++) {
                            if (buttons[i].textContent.trim().toUpperCase() === 'LOG IN') {
                                buttons[i].click();
                                return true;
                            }
                        }
                        return false;
                    """)
                    print("  ✓ Clicked LOG IN via JS")
                    clicked = True
                except Exception as e:
                    print(f"  JS click failed: {e}")
                
                # Method 2: Try CSS selectors
                if not clicked:
                    css_selectors = [
                        "button.bg-blue-600",
                        "button[class*='blue']",
                        "a[class*='blue']",
                        ".btn-primary",
                        "button:not([class*='trouble'])",
                    ]
                    for selector in css_selectors:
                        try:
                            btns = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            for btn in btns:
                                if 'LOG IN' in btn.text.upper():
                                    btn.click()
                                    print(f"  ✓ Clicked LOG IN via CSS: {selector}")
                                    clicked = True
                                    break
                            if clicked:
                                break
                        except:
                            continue
                
                # Method 3: Find all clickable elements
                if not clicked:
                    try:
                        elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'LOG IN') or contains(text(), 'Log In') or contains(text(), 'Log in')]")
                        for el in elements:
                            if el.is_displayed() and 'TROUBLE' not in el.text.upper():
                                el.click()
                                print("  ✓ Clicked LOG IN via XPath")
                                clicked = True
                                break
                    except:
                        pass
                
                if not clicked:
                    print("  ❌ Could not click LOG IN button")
                    self.driver.save_screenshot('debug_stokastic_no_login_btn.png')
                    return False
                
                time.sleep(4)
            
            # Now we should be on Auth0 login page
            current_url = self.driver.current_url
            print(f"  Current URL: {current_url[:70]}...")
            self.driver.save_screenshot('debug_step2_auth0.png')
            
            # Check if we're on Auth0
            if 'auth0' not in current_url and 'login' not in current_url.lower():
                # Maybe already logged in?
                if 'datahub' in current_url and 'You must be logged in' not in self.driver.page_source:
                    print("✓ Already logged in!")
                    return True
            
            # Wait for the Auth0 form to appear
            time.sleep(2)
            
            # Find and fill email field
            email_field = None
            email_selectors = [
                "input[name='username']",
                "input[name='email']", 
                "input[type='email']",
                "input[type='text'][name='username']",
                "input[placeholder*='mail']",
                "input[placeholder*='Email']",
            ]
            
            for selector in email_selectors:
                try:
                    fields = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for field in fields:
                        if field.is_displayed():
                            email_field = field
                            print(f"  ✓ Found email field")
                            break
                    if email_field:
                        break
                except:
                    continue
            
            if not email_field:
                print("  ❌ Could not find email field")
                self.driver.save_screenshot('debug_stokastic_no_email.png')
                return False
            
            email_field.clear()
            email_field.send_keys(self.config.get('stokastic_username', ''))
            print("  ✓ Filled email")
            time.sleep(0.5)
            
            # Find and fill password field
            password_field = None
            try:
                password_field = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            except:
                pass
            
            if not password_field:
                print("  ❌ Could not find password field")
                return False
            
            password_field.clear()
            password_field.send_keys(self.config.get('stokastic_password', ''))
            print("  ✓ Filled password")
            time.sleep(0.5)
            
            # Find and click Continue/Submit button
            clicked = False
            
            # Try JavaScript first
            try:
                self.driver.execute_script("""
                    var buttons = document.querySelectorAll('button');
                    for (var i = 0; i < buttons.length; i++) {
                        var text = buttons[i].textContent.toLowerCase();
                        if (text.includes('continue') || text.includes('log in') || text.includes('sign in')) {
                            buttons[i].click();
                            return true;
                        }
                    }
                    // Try submit button
                    var submit = document.querySelector('button[type="submit"]');
                    if (submit) { submit.click(); return true; }
                    return false;
                """)
                print("  ✓ Clicked Continue via JS")
                clicked = True
            except:
                pass
            
            if not clicked:
                try:
                    submit_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                    submit_btn.click()
                    print("  ✓ Clicked submit button")
                    clicked = True
                except:
                    pass
            
            if not clicked:
                print("  ❌ Could not click submit button")
                return False
            
            # Wait for redirect
            time.sleep(6)
            
            # Verify login
            current_url = self.driver.current_url
            page_source = self.driver.page_source
            
            self.driver.save_screenshot('debug_step3_after_login.png')
            
            if 'datahub' in current_url and 'You must be logged in' not in page_source:
                print("✓ Login successful!")
                return True
            else:
                print(f"  ⚠️ Login may have failed. URL: {current_url[:60]}...")
                return False
                
        except Exception as e:
            print(f"❌ Login error: {str(e)}")
            import traceback
            traceback.print_exc()
            self.driver.save_screenshot('debug_stokastic_login_error.png')
            return False
    
    def click_export_button(self):
        """Find and click the EXPORT button, return the CSV content"""
        try:
            # Get list of existing CSV files before clicking
            existing_files = set()
            downloads_folder = os.path.join(os.path.expanduser('~'), 'Downloads')
            for folder in [self.download_dir, downloads_folder]:
                if os.path.exists(folder):
                    existing_files.update([os.path.join(folder, f) for f in os.listdir(folder) if f.endswith('.csv')])
            
            # Method 1: Use JavaScript to find EXPORT button
            clicked = self.driver.execute_script("""
                var elements = document.querySelectorAll('button, a, div, span');
                for (var i = 0; i < elements.length; i++) {
                    var text = elements[i].textContent.trim().toUpperCase();
                    if (text === 'EXPORT' || text.includes('EXPORT')) {
                        // Make sure it's clickable and visible
                        if (elements[i].offsetParent !== null) {
                            elements[i].click();
                            return true;
                        }
                    }
                }
                return false;
            """)
            
            if clicked:
                print(f"  ✓ Found EXPORT button")
                print(f"  ✓ Clicked EXPORT")
                
                # Wait for download - check multiple times
                csv_path = None
                downloads_folder = os.path.join(os.path.expanduser('~'), 'Downloads')
                for attempt in range(10):
                    time.sleep(1)
                    
                    # Check both data folder and Downloads folder
                    for folder in [self.download_dir, downloads_folder]:
                        if not os.path.exists(folder):
                            continue
                        
                        for f in os.listdir(folder):
                            if f.endswith('.csv') and not f.endswith('.crdownload'):
                                full_path = os.path.join(folder, f)
                                if full_path not in existing_files:
                                    # Found new file
                                    csv_path = full_path
                                    print(f"  ✓ Found downloaded file: {f}")
                                    break
                        
                        if csv_path:
                            break
                    
                    if csv_path:
                        break
                
                if csv_path:
                    with open(csv_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Clean up the downloaded file
                    try:
                        os.remove(csv_path)
                        print(f"  ✓ Cleaned up: {os.path.basename(csv_path)}")
                    except:
                        pass
                    
                    return content
                else:
                    print("  ⚠️ No CSV file found after export (waited 10 seconds)")
                    print(f"  Checked folders: {self.download_dir}, {downloads_folder}")
            else:
                print("  ❌ Could not find EXPORT button")
                
                # Debug: list what buttons are visible
                buttons = self.driver.execute_script("""
                    var buttons = document.querySelectorAll('button');
                    var texts = [];
                    for (var i = 0; i < buttons.length; i++) {
                        if (buttons[i].offsetParent !== null) {
                            texts.push(buttons[i].textContent.trim().substring(0, 30));
                        }
                    }
                    return texts;
                """)
                print(f"  Visible buttons: {buttons}")
            
            return None
            
        except Exception as e:
            print(f"  ❌ Export error: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def select_stat_type(self, stat_type):
        """Select stat type from dropdown (for NFL/NHL)"""
        try:
            time.sleep(2)
            self.driver.save_screenshot(f'debug_before_select_{stat_type.lower()}.png')
            
            # First, click the STATS tab to make sure we're on the right tab
            try:
                stats_tab = self.driver.execute_script("""
                    var tabs = document.querySelectorAll('button, a');
                    for (var i = 0; i < tabs.length; i++) {
                        if (tabs[i].textContent.trim() === 'STATS') {
                            tabs[i].click();
                            return true;
                        }
                    }
                    return false;
                """)
                if stats_tab:
                    print(f"  ✓ Clicked STATS tab")
                    time.sleep(2)
            except:
                pass
            
            # Find the dropdown - look for "Stat Type" label or the dropdown button
            dropdown_opened = self.driver.execute_script(f"""
                // Method 1: Find dropdown by looking for container with "Stat Type" text
                var containers = document.querySelectorAll('div');
                for (var i = 0; i < containers.length; i++) {{
                    var text = containers[i].textContent;
                    if (text.includes('Stat Type')) {{
                        // Found the container, now find the button inside it
                        var btn = containers[i].querySelector('button');
                        if (btn) {{
                            btn.click();
                            return 'container';
                        }}
                    }}
                }}
                
                // Method 2: Look for any dropdown button that contains stat type names
                var buttons = document.querySelectorAll('button');
                for (var i = 0; i < buttons.length; i++) {{
                    var text = buttons[i].textContent.trim();
                    if (text === 'Passing' || text === 'Rushing' || text === 'Receiving' || 
                        text === 'Skater' || text === 'Goalie') {{
                        buttons[i].click();
                        return 'button';
                    }}
                }}
                
                // Method 3: Look for select-like elements
                var selects = document.querySelectorAll('[class*="select"], [class*="dropdown"], [role="listbox"], [role="combobox"]');
                for (var i = 0; i < selects.length; i++) {{
                    selects[i].click();
                    return 'select';
                }}
                
                return null;
            """)
            
            if dropdown_opened:
                print(f"  ✓ Opened dropdown via: {dropdown_opened}")
                time.sleep(1)
                self.driver.save_screenshot(f'debug_dropdown_open_{stat_type.lower()}.png')
                
                # Now click the desired option
                option_clicked = self.driver.execute_script(f"""
                    // Wait a moment for dropdown to render
                    var items = document.querySelectorAll('li, div[role="option"], button, span, div');
                    for (var i = 0; i < items.length; i++) {{
                        var text = items[i].textContent.trim();
                        if (text === '{stat_type}') {{
                            items[i].click();
                            return true;
                        }}
                    }}
                    
                    // Try clicking by partial match
                    for (var i = 0; i < items.length; i++) {{
                        var text = items[i].textContent.trim();
                        if (text.includes('{stat_type}')) {{
                            items[i].click();
                            return true;
                        }}
                    }}
                    
                    return false;
                """)
                
                if option_clicked:
                    print(f"  ✓ Selected {stat_type}")
                    time.sleep(2)
                    return True
            else:
                print(f"  Could not find dropdown to open")
                
                # Debug: Print all buttons on page
                buttons_text = self.driver.execute_script("""
                    var buttons = document.querySelectorAll('button');
                    var texts = [];
                    for (var i = 0; i < buttons.length; i++) {
                        texts.push(buttons[i].textContent.trim().substring(0, 50));
                    }
                    return texts.slice(0, 20);
                """)
                print(f"  Buttons found: {buttons_text}")
            
            # If we couldn't select, try to export anyway - might already be on the right stat
            return False
            
        except Exception as e:
            print(f"  ⚠️ Error selecting {stat_type}: {str(e)}")
            return False
    
    def save_historical(self, sport, stat_type, csv_content):
        """Save a timestamped copy for historical analysis"""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        filename = f"stokastic_{sport}_{stat_type}_{timestamp}.csv" if stat_type else f"stokastic_{sport}_{timestamp}.csv"
        filepath = os.path.join(self.history_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(csv_content)
        
        print(f"  ✓ Saved historical: {filename}")
        return filepath
    
    def scrape_nba(self):
        """Scrape NBA projections"""
        print("\n=== Scraping Stokastic NBA ===")
        
        try:
            self.driver.get('https://tools.stokastic.com/datahub/NBA')
            print("  Loading page...")
            time.sleep(5)
            
            # Make sure we're on STATS tab
            try:
                stats_tab = self.driver.find_element(By.XPATH, "//button[contains(text(), 'STATS')] | //a[contains(text(), 'STATS')]")
                stats_tab.click()
                time.sleep(2)
            except:
                pass
            
            self.driver.save_screenshot('debug_stokastic_nba.png')
            
            # Click export
            csv_content = self.click_export_button()
            
            if csv_content:
                # Save current file
                csv_file = os.path.join(self.data_dir, 'stokastic_nba.csv')
                with open(csv_file, 'w', encoding='utf-8') as f:
                    f.write(csv_content)
                print(f"  ✓ Saved: {csv_file}")
                
                # Save historical
                self.save_historical('nba', None, csv_content)
                
                self.scraped_data['nba'] = {'csv_saved': True, 'bytes': len(csv_content)}
                return self.scraped_data['nba']
            
            return None
            
        except Exception as e:
            print(f"❌ Error scraping NBA: {str(e)}")
            return None
    
    def scrape_nhl(self):
        """Scrape NHL projections (Skater stats)"""
        print("\n=== Scraping Stokastic NHL ===")
        
        try:
            self.driver.get('https://tools.stokastic.com/datahub/NHL')
            print("  Loading page...")
            time.sleep(5)
            
            # Make sure we're on STATS tab
            try:
                stats_tab = self.driver.find_element(By.XPATH, "//button[contains(text(), 'STATS')] | //a[contains(text(), 'STATS')]")
                stats_tab.click()
                time.sleep(2)
            except:
                pass
            
            # Select Skater stat type
            self.select_stat_type('Skater')
            
            self.driver.save_screenshot('debug_stokastic_nhl.png')
            
            # Click export
            csv_content = self.click_export_button()
            
            if csv_content:
                csv_file = os.path.join(self.data_dir, 'stokastic_nhl.csv')
                with open(csv_file, 'w', encoding='utf-8') as f:
                    f.write(csv_content)
                print(f"  ✓ Saved: {csv_file}")
                
                self.save_historical('nhl', 'skater', csv_content)
                
                self.scraped_data['nhl'] = {'csv_saved': True, 'bytes': len(csv_content)}
                return self.scraped_data['nhl']
            
            return None
            
        except Exception as e:
            print(f"❌ Error scraping NHL: {str(e)}")
            return None
    
    def scrape_nfl(self):
        """Scrape NFL projections (Passing, Rushing, Receiving)"""
        print("\n=== Scraping Stokastic NFL ===")
        
        results = {}
        stat_types = ['Passing', 'Rushing', 'Receiving']
        
        try:
            self.driver.get('https://tools.stokastic.com/datahub/NFL')
            print("  Loading page...")
            time.sleep(5)
            
            self.driver.save_screenshot('debug_nfl_before_stats.png')
            
            # Click STATS tab using Selenium directly
            from selenium.webdriver.common.by import By
            
            clicked_stats = False
            
            # Method 1: Find by exact text using XPath
            try:
                stats_tab = self.driver.find_element(By.XPATH, "//div[text()='STATS'] | //span[text()='STATS'] | //button[text()='STATS'] | //a[text()='STATS']")
                stats_tab.click()
                clicked_stats = True
                print("  ✓ Clicked STATS tab (XPath exact)")
            except Exception as e:
                print(f"  XPath exact failed: {e}")
            
            # Method 2: Try partial text
            if not clicked_stats:
                try:
                    stats_tab = self.driver.find_element(By.XPATH, "//*[contains(text(),'STATS')]")
                    stats_tab.click()
                    clicked_stats = True
                    print("  ✓ Clicked STATS tab (XPath contains)")
                except Exception as e:
                    print(f"  XPath contains failed: {e}")
            
            # Method 3: Use JavaScript with more specific targeting
            if not clicked_stats:
                clicked_stats = self.driver.execute_script("""
                    // Find all elements and look for one that's just "STATS"
                    var walker = document.createTreeWalker(
                        document.body,
                        NodeFilter.SHOW_TEXT,
                        null,
                        false
                    );
                    
                    while (walker.nextNode()) {
                        if (walker.currentNode.textContent.trim() === 'STATS') {
                            var parent = walker.currentNode.parentElement;
                            console.log('Found STATS, parent tag:', parent.tagName);
                            parent.click();
                            return true;
                        }
                    }
                    return false;
                """)
                if clicked_stats:
                    print("  ✓ Clicked STATS tab (JS TreeWalker)")
            
            # Method 4: Click by position - STATS is the 3rd tab
            if not clicked_stats:
                try:
                    # Get all tab-like elements near PROJECTIONS
                    tabs = self.driver.execute_script("""
                        var projTab = null;
                        var all = document.querySelectorAll('*');
                        for (var i = 0; i < all.length; i++) {
                            if (all[i].textContent.trim() === 'PROJECTIONS' && 
                                all[i].childNodes.length === 1) {
                                projTab = all[i];
                                break;
                            }
                        }
                        if (projTab) {
                            // Get siblings
                            var parent = projTab.parentElement;
                            var children = parent.children;
                            for (var i = 0; i < children.length; i++) {
                                if (children[i].textContent.trim() === 'STATS') {
                                    children[i].click();
                                    return true;
                                }
                            }
                        }
                        return false;
                    """)
                    if tabs:
                        clicked_stats = True
                        print("  ✓ Clicked STATS tab (sibling method)")
                except:
                    pass
            
            if not clicked_stats:
                print("  ❌ Could not click STATS tab")
                # List what we found
                tab_info = self.driver.execute_script("""
                    var results = [];
                    var all = document.querySelectorAll('*');
                    for (var i = 0; i < all.length; i++) {
                        var text = all[i].textContent.trim();
                        if (text === 'STATS' || text === 'PROJECTIONS' || text === 'TOP STACKS') {
                            results.push({
                                tag: all[i].tagName,
                                text: text,
                                children: all[i].childNodes.length
                            });
                        }
                    }
                    return results.slice(0, 10);
                """)
                print(f"  Tab elements found: {tab_info}")
            
            time.sleep(4)
            self.driver.save_screenshot('debug_nfl_after_stats_click.png')
            
            # Verify we're on STATS tab
            has_stat_type = 'Stat Type' in self.driver.page_source
            if has_stat_type:
                print("  ✓ Confirmed: On STATS tab")
            else:
                print("  ⚠️ May not be on STATS tab")
            
            for stat_type in stat_types:
                print(f"\n  --- {stat_type} ---")
                
                # Click the Stat Type dropdown
                dropdown_opened = self.driver.execute_script("""
                    var buttons = document.querySelectorAll('button');
                    for (var i = 0; i < buttons.length; i++) {
                        var text = buttons[i].textContent.trim();
                        if (text === 'Passing' || text === 'Rushing' || text === 'Receiving') {
                            buttons[i].click();
                            return text;
                        }
                    }
                    return null;
                """)
                
                if dropdown_opened:
                    print(f"  ✓ Opened dropdown (was: {dropdown_opened})")
                    time.sleep(1)
                    
                    selected = self.driver.execute_script(f"""
                        var options = document.querySelectorAll('li, [role="option"], [role="menuitem"]');
                        for (var i = 0; i < options.length; i++) {{
                            if (options[i].textContent.trim() === '{stat_type}') {{
                                options[i].click();
                                return true;
                            }}
                        }}
                        return false;
                    """)
                    
                    if selected:
                        print(f"  ✓ Selected {stat_type}")
                    time.sleep(2)
                else:
                    print(f"  ⚠️ Could not find stat type dropdown")
                
                self.driver.save_screenshot(f'debug_nfl_{stat_type.lower()}.png')
                
                csv_content = self.click_export_button()
                
                if csv_content:
                    filename = f'stokastic_nfl_{stat_type.lower()}.csv'
                    csv_file = os.path.join(self.data_dir, filename)
                    with open(csv_file, 'w', encoding='utf-8') as f:
                        f.write(csv_content)
                    print(f"  ✓ Saved: {filename}")
                    
                    self.save_historical('nfl', stat_type.lower(), csv_content)
                    results[stat_type.lower()] = {'csv_saved': True, 'bytes': len(csv_content)}
            
            if results:
                self.scraped_data['nfl'] = results
                return results
            
            return None
            
        except Exception as e:
            print(f"❌ Error scraping NFL: {str(e)}")
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
            
            subprocess.run(['git', 'commit', '-m', f'Update Stokastic projections - {timestamp}'], check=True)
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
            sports = ['nba', 'nhl', 'nfl']
        
        results = {}
        
        try:
            self.setup_driver(headless=headless)
            
            if not self.login():
                print("Cannot continue without successful login")
                return results
            
            if 'nba' in sports:
                results['nba'] = self.scrape_nba()
            
            if 'nhl' in sports:
                results['nhl'] = self.scrape_nhl()
            
            if 'nfl' in sports:
                results['nfl'] = self.scrape_nfl()
            
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
    
    parser = argparse.ArgumentParser(description='Scrape Stokastic projections')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    parser.add_argument('--sport', choices=['nba', 'nfl', 'nhl', 'all'], default='all', help='Sport to scrape')
    args = parser.parse_args()
    
    print("=" * 60)
    print("Stokastic Scraper with GitHub Integration")
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
        print('  {"stokastic_username": "your_email", "stokastic_password": "your_password"}')
        return
    
    if not config.get('stokastic_username'):
        print("\n⚠️ Please add stokastic_username and stokastic_password to your config!")
        return
    
    sports = ['nba', 'nhl', 'nfl'] if args.sport == 'all' else [args.sport]
    
    print(f"Mode: {'Headless' if args.headless else 'Visible browser'}")
    print(f"Sports: {', '.join(sports)}")
    
    scraper = StokasticScraper(config)
    results = scraper.scrape_all(headless=args.headless, sports=sports)
    
    print("\n" + "=" * 60)
    print("Scraping Complete!")
    print("=" * 60)
    print(f"NBA: {'✓' if results.get('nba') else '✗'}")
    print(f"NHL: {'✓' if results.get('nhl') else '✗'}")
    print(f"NFL: {'✓' if results.get('nfl') else '✗'}")
    print(f"\nCSV files saved to: data/")


if __name__ == "__main__":
    main()
