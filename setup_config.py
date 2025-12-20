"""
Interactive Setup Script for Rotogrinders Scraper
This will create your config file with proper permissions
"""

import json
import os
import getpass

def setup_config():
    print("=" * 60)
    print("Rotogrinders Scraper - Configuration Setup")
    print("=" * 60)
    print("\nThis will create your rg_config.json file with your credentials.")
    print("Your password will be hidden as you type.\n")
    
    # Get credentials
    username = input("Enter your Rotogrinders email: ").strip()
    password = getpass.getpass("Enter your Rotogrinders password: ").strip()
    
    # Confirm
    print(f"\nUsername: {username}")
    confirm = input("Is this correct? (yes/no): ").strip().lower()
    
    if confirm not in ['yes', 'y']:
        print("Setup cancelled. Please run again.")
        return
    
    # Create config
    config = {
        "username": username,
        "password": password
    }
    
    # Save to file
    config_file = 'rg_config.json'
    
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=4)
        
        # Set permissions to be readable/writable only by you
        os.chmod(config_file, 0o600)
        
        print(f"\n✓ Configuration saved to {config_file}")
        print("✓ File permissions set (only you can read/write)")
        print("\nYou can now run:")
        print("  python inspect_rotogrinders.py")
        print("  python rotogrinders_scraper.py")
        
    except Exception as e:
        print(f"\n❌ Error saving config: {str(e)}")
        print("\nTry creating the file manually:")
        print(f'{{\n    "username": "{username}",\n    "password": "{password}"\n}}')

if __name__ == "__main__":
    setup_config()
