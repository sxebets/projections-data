# Rotogrinders GitHub Integration - Complete Guide

## Overview

This system automatically scrapes Rotogrinders projections and makes them available to your HTML tools through a private GitHub repository. Everything stays private and only you can access the data.

## How It Works

```
┌─────────────────────┐
│  Your Computer      │
│  ┌───────────────┐  │
│  │ Python Scraper│──┼──> Login to Rotogrinders
│  └───────┬───────┘  │    Scrape NBA/NFL/NHL
│          │          │    Convert to JSON
│          ▼          │
│  ┌───────────────┐  │
│  │  data/*.json  │  │
│  └───────┬───────┘  │
│          │          │
│    git commit/push  │
└──────────┼──────────┘
           │
           ▼
    ┌──────────────┐
    │   GitHub     │◄───── Private Repository
    │  (Private)   │       Only you can access
    └──────┬───────┘
           │
           │ Authenticated fetch
           │ (using your token)
           ▼
    ┌──────────────┐
    │  HTML Tools  │
    │  Auto-load   │
    └──────────────┘
```

## Step-by-Step Setup

### Step 1: Install Prerequisites

```bash
# Install Python packages
pip install selenium pandas lxml html5lib

# Install ChromeDriver
# Mac:
brew install chromedriver

# Ubuntu/Linux:
sudo apt-get install chromium-chromedriver

# Windows:
# Download from https://chromedriver.chromium.org/
```

### Step 2: Run GitHub Setup

```bash
python setup_github.py
```

This interactive script will:
1. Ask for your Rotogrinders credentials
2. Ask for your GitHub username
3. Guide you through creating a Personal Access Token
4. Create a private GitHub repository
5. Set up git and push initial commit
6. Save your configuration securely

**Important**: When creating your GitHub token:
- Go to: https://github.com/settings/tokens
- Click "Generate new token (classic)"
- Name it "Projections Scraper"
- Check the **"repo"** scope (gives full control of private repositories)
- Copy the token immediately (you can't see it again!)

### Step 3: Test the Inspector

Before running the full scraper, test that login works:

```bash
python inspect_rotogrinders.py
```

This will:
- Open a browser window
- Login to Rotogrinders
- Save HTML snapshots of each sport's page
- Take screenshots
- Keep browser open for manual inspection

**Look for**:
- Do you see the projection data?
- Is there a "Download CSV" button?
- What does the table structure look like?

### Step 4: Run the Scraper

Once you've confirmed the inspector works:

```bash
python rotogrinders_scraper_github.py
```

This will:
1. Login to Rotogrinders
2. Scrape NBA projections → save to `data/rotogrinders_nba.json`
3. Scrape NFL projections → save to `data/rotogrinders_nfl.json`
4. Scrape NHL projections → save to `data/rotogrinders_nhl.json`
5. Commit and push to your private GitHub repo

### Step 5: Update Your HTML Tools

Add the GitHub fetcher to your HTML tools:

1. Open `bottom-up-props-black-theme.html`
2. Add before the closing `</body>` tag:

```html
<script src="github_data_fetcher.js"></script>
<script>
    // Update with your info
    GITHUB_CONFIG.username = 'your_github_username';
    GITHUB_CONFIG.repo = 'your_repo_name';
    GITHUB_CONFIG.token = 'your_github_token';
    
    // Initialize on page load
    document.addEventListener('DOMContentLoaded', function() {
        initializeGitHubIntegration();
    });
</script>
```

3. Repeat for `nhl_bottom_up_props_ev_v2.html`

Now when you open your HTML tools, they'll automatically fetch the latest Rotogrinders data!

## Security Notes

### What's Private:
- ✅ Your GitHub repository is private
- ✅ `scraper_config.json` is in `.gitignore` (never committed)
- ✅ Only you can access the data with your token
- ✅ Token has permissions only for your private repos

### Keep Secure:
- 🔒 Never share your `scraper_config.json`
- 🔒 Never commit your GitHub token to git
- 🔒 Use a separate token just for this project
- 🔒 You can revoke the token anytime at github.com/settings/tokens

### If Token is Compromised:
1. Go to https://github.com/settings/tokens
2. Delete the compromised token
3. Generate a new one
4. Update `scraper_config.json` with the new token
5. Update your HTML tools with the new token

## Daily Usage

### Manual Run:
```bash
python rotogrinders_scraper_github.py
```

### Automated Daily Run:

**Mac/Linux (using cron):**
```bash
# Edit crontab
crontab -e

# Add this line to run daily at 9 AM
0 9 * * * cd /path/to/scraper && python rotogrinders_scraper_github.py
```

**Windows (using Task Scheduler):**
1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily at 9 AM
4. Action: Start a program
5. Program: `python`
6. Arguments: `C:\path\to\rotogrinders_scraper_github.py`

## Troubleshooting

### "Login failed"
- Check credentials in `scraper_config.json`
- Try running inspector to see what's happening
- Rotogrinders may have changed their login page

### "Can't find table"
- Run the inspector and examine the HTML
- The page structure may differ from expected
- Share the `page_snapshots/` files with me to debug

### "Git push failed"
- Check your GitHub token has repo permissions
- Verify the token hasn't expired
- Try: `git remote -v` to confirm remote is set correctly

### "HTML tool not loading data"
- Check browser console (F12) for errors
- Verify GitHub token in `github_data_fetcher.js` is correct
- Confirm the JSON files exist in your GitHub repo
- Try fetching manually: `https://raw.githubusercontent.com/username/repo/main/data/rotogrinders_nba.json`

## File Structure

```
your-scraper-folder/
├── rotogrinders_scraper_github.py  # Main scraper
├── setup_github.py                 # Initial setup
├── inspect_rotogrinders.py         # Page inspector
├── github_data_fetcher.js          # Add to HTML tools
├── scraper_config.json             # Your credentials (keep private!)
├── .gitignore                      # Git ignore file
├── README.md                       # Repo readme
├── data/                           # JSON output files
│   ├── rotogrinders_nba.json
│   ├── rotogrinders_nfl.json
│   └── rotogrinders_nhl.json
└── tools/                          # Your HTML tools
    ├── bottom-up-props-black-theme.html
    └── nhl_bottom_up_props_ev_v2.html
```

## Next Steps After Setup

1. **Verify data quality** - Check that the JSON files have the right format
2. **Adjust column mapping** - If Rotogrinders' table structure differs, we'll update the scraper
3. **Add other sources** - Once Rotogrinders works, we can add Stokastic, Dimers, etc.
4. **Automate scheduling** - Set up daily auto-runs
5. **Add refresh button** - I can add a "Refresh Data" button to your HTML tools

## Benefits of This Setup

✅ **Fully Automated** - No manual CSV downloads
✅ **Always Fresh** - Schedule daily scrapes
✅ **Accessible Anywhere** - Your HTML tools work on any device
✅ **Version Control** - History of all your projection data
✅ **Private & Secure** - Only you can access with your token
✅ **Expandable** - Easy to add more data sources

## Questions?

After running the setup and inspector, let me know:
1. Did login work?
2. What does the Rotogrinders page structure look like?
3. Any errors or issues?
4. Ready to refine the scraper based on actual data?
