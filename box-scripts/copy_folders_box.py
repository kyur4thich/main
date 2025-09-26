from boxsdk import JWTAuth, Client
import sys

# Code Purpose:
# This script automates the copying of all contents from one Box folder to another.
# It uses JWT authentication to access Box services securely and allows the user to select
# the source and destination folders from a predefined list. The script then copies all items
# within the selected source folder to the destination folder, providing real-time feedback.

# Step 1: Authenticate using Box config file
# The script uses JWT authentication to access Box services via the SDK.
auth = JWTAuth.from_settings_file('/Users/nic/code/box-scripts/config/976402037_13exz3x7_config.json')
client = Client(auth)

# Step 2: Retrieve the authenticated user information
me = client.user().get()
print(f"🔐 Authenticated as: {me.name} ({me.login})\n")

# Step 3: Define a mapping of folder numbers to Box folder IDs and names
# This dictionary maps short codes (like "01", "02") to Box folder IDs for easy reference.
parent_folders = {
    "01": {"id": "316984650859", "name": "01. EME Uploads"},
    "02": {"id": "316982193479", "name": "02. WEM Review"},
    "03": {"id": "316987304563", "name": "03. For Afry Review"},
    "04": {"id": "316988094360", "name": "04. Frozen Files"},
    "05": {"id": "316985039982", "name": "05. Investor Engineering DD"},
    "10": {"id": "319726840600", "name": "10. Engineering"},
}

# Step 4: Display available folders to the user
print("📚 Available Folders:")
for key, val in parent_folders.items():
    print(f"  {key}: {val['name']}")
print("\n")

# Step 5: Prompt the user to input source and destination folder numbers
# The input is zero-padded to maintain a uniform two-digit format.
src_number = input("🔹 Copy FROM (folder number 01 to 10): ").zfill(2)
dst_number = input("🔹 Copy TO (folder number 01 to 10): ").zfill(2)

# Step 6: Validate the folder numbers entered by the user
if src_number not in parent_folders or dst_number not in parent_folders:
    print("❌ Invalid folder numbers.")
    sys.exit(1)

# Step 7: Fetch the Box folder IDs for the source and destination folders
src_id = parent_folders[src_number]['id']
dst_id = parent_folders[dst_number]['id']

# Step 8: Retrieve Box folder objects for source and destination
src_folder = client.folder(src_id)
dst_folder = client.folder(dst_id)

try:
    # Step 9: Retrieve all items from the source folder (up to 1000 items)
    src_items = list(src_folder.get_items(limit=1000))
    print(f"\n📁 Copying all contents from '{parent_folders[src_number]['name']}' → '{parent_folders[dst_number]['name']}'")

    # Step 10: Loop through each item in the source folder and copy it to the destination folder
    for item in src_items:
        try:
            copied = item.copy(dst_folder)
            print(f"   ✅ Copied: {item.name}")
        except Exception as e:
            print(f"   ⚠️ Failed to copy {item.name}: {e}")

    # Step 11: Confirm the copy operation completion
    print("\n🏁 Copy operation complete.")
except Exception as e:
    # Step 12: Handle errors that occur while accessing the source folder items
    print(f"❌ Error accessing folder items: {e}")
