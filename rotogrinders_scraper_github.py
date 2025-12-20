"""
Rotogrinders Scraper with GitHub Integration
Scrapes projections and automatically commits to your private GitHub repo
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
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd


class RotogrindersScraperGitHub:
    """Rotogrinders scraper with GitHub integration"""
    
    def __init__(self, config):
        self.config = config
        self.driver = None
        self.data_dir = 'data'
        self.history_dir = 'data/history'
        self.scraped_data = {}
        
        # Create data directories
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.history_dir, exist_ok=True)
    
    def setup_driver(self, headless=True):
        """Setup Chrome webdriver with network logging"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        # Enable network logging to capture API calls
        chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 20)
        print("✓ Browser initialized (with network logging)")
    
    def capture_api_calls(self, keyword=''):
        """Capture and analyze network requests looking for data APIs"""
        try:
            logs = self.driver.get_log('performance')
            api_calls = []
            
            for entry in logs:
                try:
                    message = json.loads(entry['message'])
                    method = message['message']['method']
                    
                    if method == 'Network.responseReceived':
                        url = message['message']['params']['response']['url']
                        mime = message['message']['params']['response'].get('mimeType', '')
                        status = message['message']['params']['response'].get('status', 0)
                        
                        # Look for JSON/API responses
                        if 'json' in mime.lower() or '/api/' in url.lower():
                            if keyword == '' or keyword.lower() in url.lower():
                                api_calls.append({
                                    'url': url,
                                    'mime': mime,
                                    'status': status
                                })
                except:
                    continue
            
            return api_calls
        except Exception as e:
            print(f"  Could not capture network logs: {e}")
            return []
    
    def close_popups(self):
        """Close any popup ads or overlays that might block elements"""
        try:
            # Try to close common popup/overlay elements
            close_selectors = [
                "//button[contains(@class, 'close')]",
                "//button[contains(text(), '×')]",
                "//button[contains(text(), 'Close')]",
                "//*[contains(@class, 'modal-close')]",
                "//*[contains(@class, 'popup-close')]",
            ]
            
            for selector in close_selectors:
                try:
                    close_btns = self.driver.find_elements(By.XPATH, selector)
                    for btn in close_btns:
                        if btn.is_displayed():
                            btn.click()
                            time.sleep(0.5)
                except:
                    continue
            
            # Scroll down to move past sticky headers/ads, then back up
            self.driver.execute_script("window.scrollTo(0, 300);")
            time.sleep(0.5)
            
            # Try to hide sticky CTA elements via JavaScript
            self.driver.execute_script("""
                var stickyCtas = document.querySelectorAll('bam-sticky-cta, .sticky-cta, [class*="sticky"]');
                stickyCtas.forEach(function(el) { 
                    el.style.display = 'none'; 
                });
            """)
            
        except Exception as e:
            pass  # Silently ignore popup closing errors
    
    def parse_nba_csv(self, csv_content):
        """Parse NBA CSV content into player dictionary"""
        import csv
        from io import StringIO
        
        players = {}
        
        try:
            reader = csv.DictReader(StringIO(csv_content))
            
            for row in reader:
                # Get player name - try various column names
                player_name = row.get('Player', row.get('player', row.get('Name', row.get('name', ''))))
                
                if not player_name:
                    continue
                
                # Map CSV columns to our format
                players[player_name] = {
                    'salary': row.get('Salary', row.get('salary', '')),
                    'position': row.get('Position', row.get('Pos', row.get('pos', ''))),
                    'team': row.get('Team', row.get('team', '')),
                    'opponent': row.get('Opp', row.get('Opponent', row.get('opponent', ''))),
                    'injury': row.get('Injury', row.get('injury', '')),
                    'min': row.get('Minutes', row.get('Min', row.get('min', row.get('MINUTES', '')))),
                    'pts': row.get('Points', row.get('Pts', row.get('pts', row.get('PTS', '')))),
                    'reb': row.get('Rebounds', row.get('Reb', row.get('reb', row.get('REB', '')))),
                    'ast': row.get('Assists', row.get('Ast', row.get('ast', row.get('AST', '')))),
                    '3pm': row.get('3PM', row.get('3pm', row.get('Threes', ''))),
                    'to': row.get('Turnovers', row.get('TO', row.get('to', ''))),
                    'stl': row.get('Steals', row.get('Stl', row.get('stl', row.get('STL', '')))),
                    'blk': row.get('Blocks', row.get('Blk', row.get('blk', row.get('BLK', '')))),
                    'pa': row.get('P+A', row.get('PA', row.get('pa', ''))),
                    'pr': row.get('P+R', row.get('PR', row.get('pr', ''))),
                    'pra': row.get('P+R+A', row.get('PRA', row.get('pra', ''))),
                    'bs': row.get('B+S', row.get('BS', row.get('bs', ''))),
                    'ra': row.get('R+A', row.get('RA', row.get('ra', ''))),
                    'fpts': row.get('FPTS', row.get('Fpts', row.get('fpts', row.get('Fantasy Points', '')))),
                }
            
            print(f"  Parsed {len(players)} players from CSV")
            return players
            
        except Exception as e:
            print(f"  Error parsing CSV: {e}")
            return {}
    
    def parse_nfl_csv(self, csv_content):
        """Parse NFL CSV content into player dictionary"""
        import csv
        from io import StringIO
        
        players = {}
        
        try:
            reader = csv.DictReader(StringIO(csv_content))
            
            for row in reader:
                player_name = row.get('Player', row.get('player', row.get('Name', row.get('name', ''))))
                
                if not player_name:
                    continue
                
                players[player_name] = {
                    'salary': row.get('Salary', row.get('salary', '')),
                    'position': row.get('Position', row.get('Pos', row.get('pos', ''))),
                    'team': row.get('Team', row.get('team', '')),
                    'opponent': row.get('Opp', row.get('Opponent', row.get('opponent', ''))),
                    'injury': row.get('Injury', row.get('injury', '')),
                    'pass_att': row.get('Pass Att', row.get('ATT', row.get('att', ''))),
                    'pass_yds': row.get('Pass Yds', row.get('PASS YDS', row.get('pass_yds', ''))),
                    'pass_td': row.get('Pass TD', row.get('PASS TD', row.get('pass_td', ''))),
                    'int': row.get('Int', row.get('INT', row.get('int', ''))),
                    'rush_att': row.get('Rush Att', row.get('RUSH ATT', row.get('rush_att', ''))),
                    'rush_yds': row.get('Rush Yds', row.get('RUSH YDS', row.get('rush_yds', ''))),
                    'rush_td': row.get('Rush TD', row.get('RUSH TD', row.get('rush_td', ''))),
                    'rec': row.get('Rec', row.get('REC', row.get('rec', ''))),
                    'rec_yds': row.get('Rec Yds', row.get('REC YDS', row.get('rec_yds', ''))),
                    'rec_td': row.get('Rec TD', row.get('REC TD', row.get('rec_td', ''))),
                    'fpts': row.get('FPTS', row.get('Fpts', row.get('fpts', ''))),
                }
            
            print(f"  Parsed {len(players)} players from CSV")
            return players
            
        except Exception as e:
            print(f"  Error parsing CSV: {e}")
            return {}
    
    def parse_nhl_csv(self, csv_content):
        """Parse NHL CSV content into player dictionary"""
        import csv
        from io import StringIO
        
        players = {}
        
        try:
            reader = csv.DictReader(StringIO(csv_content))
            
            for row in reader:
                player_name = row.get('Player', row.get('player', row.get('Name', row.get('name', ''))))
                
                if not player_name:
                    continue
                
                players[player_name] = {
                    'salary': row.get('Salary', row.get('salary', '')),
                    'position': row.get('Position', row.get('Pos', row.get('pos', ''))),
                    'team': row.get('Team', row.get('team', '')),
                    'opponent': row.get('Opp', row.get('Opponent', row.get('opponent', ''))),
                    'goals': row.get('Goals', row.get('G', row.get('goals', ''))),
                    'assists': row.get('Assists', row.get('A', row.get('assists', ''))),
                    'points': row.get('Points', row.get('Pts', row.get('points', ''))),
                    'sog': row.get('SOG', row.get('Shots', row.get('sog', ''))),
                    'blocks': row.get('Blocks', row.get('Blk', row.get('blocks', ''))),
                    'pim': row.get('PIM', row.get('pim', '')),
                    'fpts': row.get('FPTS', row.get('Fpts', row.get('fpts', ''))),
                }
            
            print(f"  Parsed {len(players)} players from CSV")
            return players
            
        except Exception as e:
            print(f"  Error parsing CSV: {e}")
            return {}
    
    def login(self):
        """Login to Rotogrinders"""
        print("\nLogging in to Rotogrinders...")
        
        try:
            self.driver.get('https://rotogrinders.com/sign-in')
            print("  Waiting for login page to load...")
            time.sleep(5)
            
            # Wait for username field (it's "username" not "email")
            print("  Looking for username field...")
            email_field = self.wait.until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            print("  ✓ Found username field")
            
            time.sleep(1)
            email_field.clear()
            time.sleep(0.5)
            email_field.send_keys(self.config['rg_username'])
            print(f"  ✓ Filled username")
            time.sleep(1)
            
            # Wait for password field
            print("  Looking for password field...")
            password_field = self.wait.until(
                EC.presence_of_element_located((By.NAME, "password"))
            )
            print("  ✓ Found password field")
            
            time.sleep(1)
            password_field.clear()
            time.sleep(0.5)
            password_field.send_keys(self.config['rg_password'])
            print("  ✓ Filled password")
            time.sleep(1)
            
            # Wait for submit button to be clickable
            print("  Looking for submit button...")
            login_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='submit']"))
            )
            print("  ✓ Found submit button, clicking...")
            login_button.click()
            print("  ✓ Clicked! Waiting for login to complete...")
            
            time.sleep(8)  # Give more time for redirect
            
            # Save a screenshot to verify login status
            self.driver.save_screenshot('debug_after_login.png')
            print("  Saved login verification screenshot to debug_after_login.png")
            
            # Check for successful login indicators
            current_url = self.driver.current_url.lower()
            page_source = self.driver.page_source.lower()
            
            if 'sign-in' in current_url or 'login' in current_url:
                print("❌ Login failed - still on login page")
                return False
            
            # Check if we can see user menu or profile indicator
            if 'sign out' in page_source or 'my account' in page_source or 'profile' in page_source:
                print("✓ Login successful (found user menu)")
                return True
            
            print("⚠️ Login status unclear - continuing anyway")
            print(f"  Current URL: {self.driver.current_url}")
            return True
                
        except Exception as e:
            print(f"❌ Login error: {str(e)}")
            return False
    
    def scrape_nba_projections(self):
        """Scrape NBA projections using the Download CSV button"""
        print("\n=== Scraping NBA Projections ===")
        
        try:
            self.driver.get('https://rotogrinders.com/projected-stats/nba')
            print("Loading page...")
            
            # Wait for page to load
            print("Waiting for data to load...")
            time.sleep(8)
            
            # Close any popups or ads that might be blocking
            self.close_popups()
            
            # Save screenshot for debugging
            self.driver.save_screenshot('debug_nba.png')
            print("Saved screenshot to debug_nba.png")
            
            # Find and click the "Download as CSV" button
            print("Looking for Download CSV button...")
            
            csv_button = None
            button_selectors = [
                "//a[contains(text(), 'Download as CSV')]",
                "//button[contains(text(), 'Download as CSV')]",
                "//a[contains(text(), 'Download')]",
            ]
            
            for selector in button_selectors:
                try:
                    csv_button = self.driver.find_element(By.XPATH, selector)
                    if csv_button and csv_button.is_displayed():
                        print(f"  ✓ Found button")
                        break
                except:
                    continue
            
            if not csv_button:
                print("❌ Could not find Download CSV button")
                return None
            
            # Get the CSV URL - check both href and data-pointer
            csv_url = csv_button.get_attribute('href')
            
            if not csv_url:
                # Check for data-pointer attribute (base64 encoded path)
                data_pointer = csv_button.get_attribute('data-pointer')
                if data_pointer:
                    import base64
                    try:
                        decoded_path = base64.b64decode(data_pointer).decode('utf-8')
                        csv_url = f"https://rotogrinders.com{decoded_path}"
                        print(f"  Decoded CSV URL from data-pointer: {csv_url}")
                    except:
                        print(f"  Could not decode data-pointer: {data_pointer}")
            
            if csv_url:
                print(f"  CSV URL: {csv_url}")
                
                # Download the CSV directly using requests with session cookies
                import requests
                
                # Get cookies from selenium
                cookies = {c['name']: c['value'] for c in self.driver.get_cookies()}
                
                print("  Downloading CSV...")
                response = requests.get(csv_url, cookies=cookies)
                
                if response.status_code == 200:
                    csv_content = response.text
                    
                    # Save raw CSV (current)
                    csv_file = os.path.join(self.data_dir, 'rotogrinders_nba.csv')
                    with open(csv_file, 'w', encoding='utf-8') as f:
                        f.write(csv_content)
                    print(f"  ✓ Saved CSV: {csv_file}")
                    
                    # Save historical copy
                    self.save_historical('nba', csv_content)
                    
                    self.scraped_data['nba'] = {'csv_saved': True, 'bytes': len(csv_content)}
                    return self.scraped_data['nba']
                else:
                    print(f"  ❌ Failed to download CSV: {response.status_code}")
            else:
                print("  ❌ Could not determine CSV URL")
            
            return None
            
        except Exception as e:
            print(f"❌ Error scraping NBA: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def download_csv_for_sport(self, sport, url):
        """Generic function to download CSV for any sport"""
        print(f"\n=== Scraping {sport.upper()} Projections ===")
        
        try:
            self.driver.get(url)
            print("Loading page...")
            time.sleep(8)
            
            # Close any popups
            self.close_popups()
            
            # Save screenshot
            self.driver.save_screenshot(f'debug_{sport}.png')
            
            # Find Download CSV button
            print("Looking for Download CSV button...")
            
            csv_button = None
            button_selectors = [
                "//a[contains(text(), 'Download as CSV')]",
                "//button[contains(text(), 'Download as CSV')]",
                "//a[contains(text(), 'Download')]",
            ]
            
            for selector in button_selectors:
                try:
                    csv_button = self.driver.find_element(By.XPATH, selector)
                    if csv_button and csv_button.is_displayed():
                        print(f"  ✓ Found button")
                        break
                except:
                    continue
            
            if not csv_button:
                print(f"❌ Could not find Download CSV button for {sport}")
                return None
            
            # Get the CSV URL - check both href and data-pointer
            csv_url = csv_button.get_attribute('href')
            
            if not csv_url:
                # Check for data-pointer attribute (base64 encoded path)
                data_pointer = csv_button.get_attribute('data-pointer')
                if data_pointer:
                    import base64
                    try:
                        decoded_path = base64.b64decode(data_pointer).decode('utf-8')
                        csv_url = f"https://rotogrinders.com{decoded_path}"
                        print(f"  Decoded CSV URL: {csv_url}")
                    except:
                        print(f"  Could not decode data-pointer: {data_pointer}")
            
            if csv_url:
                print(f"  CSV URL: {csv_url}")
                import requests
                cookies = {c['name']: c['value'] for c in self.driver.get_cookies()}
                
                print("  Downloading CSV...")
                response = requests.get(csv_url, cookies=cookies)
                
                if response.status_code == 200:
                    return response.text
                else:
                    print(f"  ❌ Failed to download CSV: {response.status_code}")
            else:
                print(f"  ❌ Could not determine CSV URL for {sport}")
            
            return None
            
        except Exception as e:
            print(f"❌ Error scraping {sport}: {str(e)}")
            return None
    
    def scrape_nfl_projections(self):
        """Scrape NFL projections using CSV download"""
        csv_content = self.download_csv_for_sport('nfl', 'https://rotogrinders.com/projected-stats/nfl')
        
        if csv_content:
            # Save raw CSV
            csv_file = os.path.join(self.data_dir, 'rotogrinders_nfl.csv')
            with open(csv_file, 'w', encoding='utf-8') as f:
                f.write(csv_content)
            print(f"  ✓ Saved CSV: {csv_file}")
            
            # Save historical copy
            self.save_historical('nfl', csv_content)
            
            self.scraped_data['nfl'] = {'csv_saved': True, 'bytes': len(csv_content)}
            return self.scraped_data['nfl']
        
        return None
    
    def scrape_nhl_projections(self):
        """Scrape NHL projections using CSV download"""
        csv_content = self.download_csv_for_sport('nhl', 'https://rotogrinders.com/projected-stats/nhl')
        
        if csv_content:
            # Save raw CSV
            csv_file = os.path.join(self.data_dir, 'rotogrinders_nhl.csv')
            with open(csv_file, 'w', encoding='utf-8') as f:
                f.write(csv_content)
            print(f"  ✓ Saved CSV: {csv_file}")
            
            # Save historical copy
            self.save_historical('nhl', csv_content)
            
            self.scraped_data['nhl'] = {'csv_saved': True, 'bytes': len(csv_content)}
            return self.scraped_data['nhl']
        
        return None
    
    def save_historical(self, sport, csv_content):
        """Save a timestamped copy of the projection data for historical analysis"""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        filename = f"rotogrinders_{sport}_{timestamp}.csv"
        filepath = os.path.join(self.history_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(csv_content)
        
        print(f"  ✓ Saved historical: {filepath}")
        return filepath
    
    def git_commit_and_push(self):
        """Commit and push data to GitHub"""
        print("\n=== Pushing to GitHub ===")
        
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Check if we're in a git repo
            result = subprocess.run(['git', 'status'], capture_output=True, text=True)
            if result.returncode != 0:
                print("❌ Not a git repository. Run 'git init' first.")
                return False
            
            # Add all data files
            subprocess.run(['git', 'add', 'data/'], check=True)
            
            # Check if there are changes to commit
            result = subprocess.run(['git', 'diff', '--staged', '--quiet'], capture_output=True)
            if result.returncode == 0:
                print("  No changes to commit")
                return True
            
            # Commit
            subprocess.run(['git', 'commit', '-m', f'Update projections - {timestamp}'], check=True)
            print("  ✓ Committed changes")
            
            # Push
            result = subprocess.run(['git', 'push'], capture_output=True, text=True)
            if result.returncode != 0:
                print(f"  ⚠️ Push failed: {result.stderr}")
                print("  You may need to set up remote: git remote add origin <your-repo-url>")
                return False
            
            print("✓ Data pushed to GitHub successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Git error: {str(e)}")
            return False
        except FileNotFoundError:
            print("❌ Git not found. Make sure git is installed and in PATH.")
            return False
    
    def scrape_all(self, headless=False):
        """Scrape all sports and push to GitHub"""
        results = {
            'nba': None,
            'nfl': None,
            'nhl': None
        }
        
        try:
            self.setup_driver(headless=headless)
            
            if not self.login():
                print("Cannot continue without successful login")
                return results
            
            # Scrape each sport
            results['nba'] = self.scrape_nba_projections()
            results['nfl'] = self.scrape_nfl_projections()
            results['nhl'] = self.scrape_nhl_projections()
            
            # Push to GitHub if any data was scraped
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
    
    parser = argparse.ArgumentParser(description='Scrape RotoGrinders projections')
    parser.add_argument('--headless', action='store_true', 
                        help='Run browser in headless mode (no visible window)')
    parser.add_argument('--sport', choices=['nba', 'nfl', 'nhl', 'all'], default='all',
                        help='Which sport to scrape (default: all)')
    args = parser.parse_args()
    
    print("=" * 60)
    print("Rotogrinders Scraper with GitHub Integration")
    print("=" * 60)
    
    # Load configuration - try both formats
    config = None
    
    if os.path.exists('scraper_config.json'):
        with open('scraper_config.json', 'r') as f:
            config = json.load(f)
        print("✓ Loaded scraper_config.json")
    elif os.path.exists('config.json'):
        with open('config.json', 'r') as f:
            raw_config = json.load(f)
            # Map config.json format to expected format
            config = {
                'rg_username': raw_config.get('username', raw_config.get('rg_username', '')),
                'rg_password': raw_config.get('password', raw_config.get('rg_password', ''))
            }
        print("✓ Loaded config.json")
    else:
        print("\n❌ No config file found!")
        print("Please create scraper_config.json or config.json with your credentials")
        return
    
    if not config.get('rg_username') or config.get('rg_username') == 'your_rotogrinders_email':
        print("\n⚠️  Please update your config file with your credentials!")
        return
    
    print(f"Mode: {'Headless' if args.headless else 'Visible browser'}")
    print(f"Sport: {args.sport}")
    
    # Create scraper and run
    scraper = RotogrindersScraperGitHub(config)
    results = scraper.scrape_all(headless=args.headless)
    
    print("\n" + "=" * 60)
    print("Scraping Complete!")
    print("=" * 60)
    
    # Count files saved
    csv_count = 0
    if results.get('nba'): csv_count += 1
    if results.get('nfl'): csv_count += 1  
    if results.get('nhl'): csv_count += 1
    
    print(f"NBA: {'✓ CSV saved' if results.get('nba') is not None or os.path.exists('data/rotogrinders_nba.csv') else '✗'}")
    print(f"NFL: {'✓ CSV saved' if results.get('nfl') is not None or os.path.exists('data/rotogrinders_nfl.csv') else '✗'}")
    print(f"NHL: {'✓ CSV saved' if results.get('nhl') is not None or os.path.exists('data/rotogrinders_nhl.csv') else '✗'}")
    print(f"\nCSV files saved to: data/")
    print(f"Historical files saved to: data/history/")


if __name__ == "__main__":
    main()
