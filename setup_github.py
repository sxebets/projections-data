"""
GitHub Repository Setup Script
Sets up your private repo and configures everything
"""

import os
import json
import subprocess
import getpass


def check_git_installed():
    """Check if git is installed"""
    try:
        subprocess.run(['git', '--version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def setup_config():
    """Interactive configuration setup"""
    print("=" * 60)
    print("Rotogrinders Scraper - GitHub Setup")
    print("=" * 60)
    
    config = {}
    
    # Rotogrinders credentials
    print("\n1. Rotogrinders Credentials")
    print("-" * 60)
    config['rg_username'] = input("Rotogrinders email: ").strip()
    config['rg_password'] = getpass.getpass("Rotogrinders password: ")
    
    # GitHub info
    print("\n2. GitHub Configuration")
    print("-" * 60)
    config['github_username'] = input("Your GitHub username: ").strip()
    config['repo_name'] = input("Repository name (e.g., 'projections-data'): ").strip()
    
    print("\n3. GitHub Personal Access Token")
    print("-" * 60)
    print("You'll need a GitHub Personal Access Token (classic) with 'repo' permissions.")
    print("\nTo create one:")
    print("1. Go to: https://github.com/settings/tokens")
    print("2. Click 'Generate new token (classic)'")
    print("3. Give it a name like 'Projections Scraper'")
    print("4. Check the 'repo' scope (full control of private repositories)")
    print("5. Click 'Generate token'")
    print("6. Copy the token (you won't be able to see it again!)")
    
    config['github_token'] = getpass.getpass("\nPaste your GitHub token: ")
    
    return config


def create_github_repo(config):
    """Create private GitHub repository using GitHub CLI or API"""
    print("\n4. Creating GitHub Repository")
    print("-" * 60)
    
    repo_name = config['repo_name']
    
    # Try using GitHub CLI first
    try:
        result = subprocess.run(
            ['gh', 'repo', 'create', repo_name, '--private', '--confirm'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"✓ Created private repository: {repo_name}")
            return True
    except FileNotFoundError:
        pass
    
    # Fallback to manual instructions
    print("GitHub CLI not found. Please create the repository manually:")
    print(f"\n1. Go to: https://github.com/new")
    print(f"2. Repository name: {repo_name}")
    print(f"3. Make it PRIVATE")
    print(f"4. Click 'Create repository'")
    
    input("\nPress Enter after you've created the repository...")
    return True


def setup_local_repo(config):
    """Setup local git repository"""
    print("\n5. Setting up local repository")
    print("-" * 60)
    
    # Initialize git if needed
    if not os.path.exists('.git'):
        subprocess.run(['git', 'init'], check=True)
        print("✓ Git repository initialized")
    
    # Create directory structure
    os.makedirs('data', exist_ok=True)
    os.makedirs('tools', exist_ok=True)
    print("✓ Directory structure created")
    
    # Create .gitignore
    gitignore_content = """# Config files with credentials
scraper_config.json
rg_config.json

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.so
*.egg
*.egg-info/
dist/
build/

# Virtual environment
venv/
env/

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db

# Selenium
*.log
page_snapshots/
"""
    
    with open('.gitignore', 'w') as f:
        f.write(gitignore_content)
    print("✓ .gitignore created")
    
    # Create README
    readme_content = f"""# {config['repo_name']}

Private repository for sports betting projection data.

## Data Sources
- Rotogrinders (NBA, NFL, NHL)

## Files
- `data/` - JSON projection files
- `tools/` - HTML analysis tools

Last updated: Automatically via scraper
"""
    
    with open('README.md', 'w') as f:
        f.write(readme_content)
    print("✓ README.md created")
    
    # Set up remote
    username = config['github_username']
    token = config['github_token']
    repo_name = config['repo_name']
    
    remote_url = f"https://{token}@github.com/{username}/{repo_name}.git"
    
    # Remove existing remote if present
    subprocess.run(['git', 'remote', 'remove', 'origin'], 
                   capture_output=True)
    
    # Add new remote
    subprocess.run(['git', 'remote', 'add', 'origin', remote_url], check=True)
    print("✓ Remote repository configured")
    
    # Initial commit
    subprocess.run(['git', 'add', '.gitignore', 'README.md'], check=True)
    subprocess.run(['git', 'commit', '-m', 'Initial commit'], check=True)
    subprocess.run(['git', 'branch', '-M', 'main'], check=True)
    subprocess.run(['git', 'push', '-u', 'origin', 'main'], check=True)
    
    print("✓ Initial commit pushed to GitHub")
    
    return True


def save_config(config):
    """Save configuration file"""
    print("\n6. Saving Configuration")
    print("-" * 60)
    
    # Save full config (with token) - keep this secure
    with open('scraper_config.json', 'w') as f:
        json.dump(config, f, indent=4)
    
    # Set restrictive permissions
    os.chmod('scraper_config.json', 0o600)
    
    print("✓ Configuration saved to scraper_config.json")
    print("✓ File permissions set (only you can read/write)")


def main():
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "Rotogrinders GitHub Integration Setup" + " " * 11 + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    
    # Check prerequisites
    if not check_git_installed():
        print("❌ Git is not installed!")
        print("Please install git first:")
        print("  Mac: brew install git")
        print("  Ubuntu: sudo apt-get install git")
        print("  Windows: https://git-scm.com/download/win")
        return
    
    print("✓ Git is installed")
    
    # Interactive setup
    config = setup_config()
    
    # Create GitHub repo
    if not create_github_repo(config):
        print("\n❌ Repository creation failed")
        return
    
    # Setup local repo
    if not setup_local_repo(config):
        print("\n❌ Local repository setup failed")
        return
    
    # Save config
    save_config(config)
    
    # Success!
    print("\n" + "=" * 60)
    print("✓ Setup Complete!")
    print("=" * 60)
    print(f"\nYour private repository: https://github.com/{config['github_username']}/{config['repo_name']}")
    print("\nNext steps:")
    print("1. Run the inspector: python inspect_rotogrinders.py")
    print("2. After confirming scraper works: python rotogrinders_scraper_github.py")
    print("3. Your HTML tools will auto-fetch from GitHub")
    print("\nYour data is private and only accessible to you with your token.")


if __name__ == "__main__":
    main()
