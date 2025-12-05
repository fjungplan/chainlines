"""
Quick script to create test edits via API for testing the moderation queue.
This simulates what the frontend wizards would do.
"""

import requests
import sys

API_BASE = "http://localhost:8000"

def get_token():
    """Get JWT token - you'll need to login first via the web UI."""
    print("⚠️  You need to get your access token from the browser:")
    print("   1. Login to http://localhost:5173")
    print("   2. Open browser DevTools (F12) → Console")
    print("   3. Type: localStorage.getItem('accessToken')")
    print("   4. Copy the token (without quotes)\n")
    return input("Paste your access token here: ").strip()

def create_metadata_edit(token, era_id, changes, reason):
    """Create a metadata edit."""
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "era_id": era_id,
        "changes": changes,
        "reason": reason
    }
    
    response = requests.post(
        f"{API_BASE}/api/v1/edits/metadata",
        json=data,
        headers=headers
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Edit created successfully!")
        print(f"   Edit ID: {result['edit_id']}")
        print(f"   Status: {result['status']}")
        if result['status'] == 'PENDING':
            print(f"   📋 Edit is pending moderation")
        else:
            print(f"   ✨ Edit was auto-approved (trusted user)")
        return result
    else:
        print(f"❌ Failed to create edit: {response.status_code}")
        print(f"   {response.text}")
        return None

def main():
    print("=" * 60)
    print("🛠️  Create Test Edit for Moderation Queue")
    print("=" * 60)
    print()
    
    # Get token
    token = get_token()
    print()
    
    # Get era_id (you can get this from the database or use a known one)
    print("Enter the era_id to edit (or press Enter for default):")
    era_id = input("era_id: ").strip()
    if not era_id:
        era_id = "cb0be3a8-3b66-45a8-b72e-eceea5ec8f26"  # From our test data
        print(f"Using default: {era_id}")
    print()
    
    # Example edit
    print("Creating a test metadata edit...")
    changes = {
        "registered_name": "Test Team Name Change",
        "tier_level": 1
    }
    reason = "Testing the moderation queue feature"
    
    result = create_metadata_edit(token, era_id, changes, reason)
    
    if result:
        print()
        print("=" * 60)
        print("✅ Done! Now go to http://localhost:5173/moderation")
        print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        sys.exit(1)
