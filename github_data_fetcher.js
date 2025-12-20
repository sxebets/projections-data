/**
 * GitHub Data Fetcher for Bottom Up Props Tools
 * Add this to your HTML tools to auto-load Rotogrinders data
 */

// Configuration - Update these with your info
const GITHUB_CONFIG = {
    username: 'YOUR_GITHUB_USERNAME',
    repo: 'YOUR_REPO_NAME',
    token: 'YOUR_GITHUB_TOKEN', // Keep this secure!
    branch: 'main'
};

/**
 * Fetch data from private GitHub repository
 */
async function fetchFromGitHub(filename) {
    const url = `https://raw.githubusercontent.com/${GITHUB_CONFIG.username}/${GITHUB_CONFIG.repo}/${GITHUB_CONFIG.branch}/data/${filename}`;
    
    try {
        const response = await fetch(url, {
            headers: {
                'Authorization': `token ${GITHUB_CONFIG.token}`,
                'Accept': 'application/vnd.github.v3.raw'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error(`Error fetching ${filename}:`, error);
        return null;
    }
}

/**
 * Auto-load Rotogrinders data when page loads
 */
async function autoLoadRotogrindersData() {
    console.log('🔄 Loading Rotogrinders data from GitHub...');
    
    const sport = state.sport; // Assumes your HTML tool has a state.sport variable
    let filename;
    
    if (sport === 'nba') {
        filename = 'rotogrinders_nba.json';
    } else if (sport === 'nfl') {
        filename = 'rotogrinders_nfl.json';
    } else if (sport === 'nhl') {
        filename = 'rotogrinders_nhl.json';
    } else {
        console.log('Unknown sport, skipping auto-load');
        return;
    }
    
    const data = await fetchFromGitHub(filename);
    
    if (data && Object.keys(data).length > 0) {
        // Load into your tool's state
        state.sources['rotogrinders'] = data;
        
        console.log(`✅ Loaded Rotogrinders data: ${Object.keys(data).length} players`);
        
        // Update UI
        updateSources();
        aggregateData();
        render(); // Or whatever your render function is called
        
        showNotification(`✓ Auto-loaded Rotogrinders: ${Object.keys(data).length} players`);
    } else {
        console.log('⚠️ No Rotogrinders data found or error loading');
        showNotification('⚠️ Could not auto-load Rotogrinders data', 'warning');
    }
}

/**
 * Manual refresh button handler
 */
async function refreshRotogrindersData() {
    showNotification('🔄 Refreshing Rotogrinders data...', 'info');
    await autoLoadRotogrindersData();
}

/**
 * Check when data was last updated
 */
async function getLastUpdateTime() {
    const apiUrl = `https://api.github.com/repos/${GITHUB_CONFIG.username}/${GITHUB_CONFIG.repo}/commits?path=data&page=1&per_page=1`;
    
    try {
        const response = await fetch(apiUrl, {
            headers: {
                'Authorization': `token ${GITHUB_CONFIG.token}`
            }
        });
        
        if (response.ok) {
            const commits = await response.json();
            if (commits.length > 0) {
                const lastUpdate = new Date(commits[0].commit.author.date);
                return lastUpdate;
            }
        }
    } catch (error) {
        console.error('Error getting last update time:', error);
    }
    
    return null;
}

/**
 * Display last update time in UI
 */
async function showLastUpdateTime() {
    const lastUpdate = await getLastUpdateTime();
    if (lastUpdate) {
        const timeAgo = getTimeAgo(lastUpdate);
        const element = document.getElementById('lastUpdateTime');
        if (element) {
            element.textContent = `Last updated: ${timeAgo}`;
        }
        console.log(`📅 Data last updated: ${timeAgo}`);
    }
}

/**
 * Helper function to format time ago
 */
function getTimeAgo(date) {
    const seconds = Math.floor((new Date() - date) / 1000);
    
    let interval = seconds / 31536000;
    if (interval > 1) return Math.floor(interval) + " years ago";
    
    interval = seconds / 2592000;
    if (interval > 1) return Math.floor(interval) + " months ago";
    
    interval = seconds / 86400;
    if (interval > 1) return Math.floor(interval) + " days ago";
    
    interval = seconds / 3600;
    if (interval > 1) return Math.floor(interval) + " hours ago";
    
    interval = seconds / 60;
    if (interval > 1) return Math.floor(interval) + " minutes ago";
    
    return Math.floor(seconds) + " seconds ago";
}

/**
 * Initialize GitHub integration
 * Call this when your page loads
 */
function initializeGitHubIntegration() {
    // Check if config is set
    if (GITHUB_CONFIG.username === 'YOUR_GITHUB_USERNAME') {
        console.warn('⚠️ GitHub integration not configured. Update GITHUB_CONFIG with your details.');
        return;
    }
    
    console.log('✅ GitHub integration initialized');
    
    // Auto-load data on page load
    autoLoadRotogrindersData();
    
    // Show last update time
    showLastUpdateTime();
}

// Export functions for use in HTML
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        autoLoadRotogrindersData,
        refreshRotogrindersData,
        getLastUpdateTime,
        initializeGitHubIntegration
    };
}
