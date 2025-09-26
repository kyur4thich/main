from boxsdk import JWTAuth, Client
import sys

# The script below moves the contents (not the folders themselves) from a subfolder in one parent folder 
# (e.g., 01. EME Uploads) to the same-named subfolder in another (e.g., 02. WEM Review). 
# The 21 subfolders remain in all locations
# === Authenticate with Box ===
auth = JWTAuth.from_settings_file('/Users/nic/code/box-scripts/config/976402037_13exz3x7_config.json')
client = Client(auth)

me = client.user().get()
print(f"🔐 Authenticated as: {me.name} ({me.login})\n")

# === Define parent folders with real IDs ===
parent_folders = {
    "01": {"id": "316984650859", "name": "01. EME Uploads"},
    "02": {"id": "316982193479", "name": "02. WEM Review"},
    "03": {"id": "316987304563", "name": "03. For Afry Review"},
    "04": {"id": "316988094360", "name": "04. Frozen Files"},
    "05": {"id": "316985039982", "name": "05. Investor Engineering DD"},
    "10": {"id": "319726840600", "name": "10. Engineering"},
}

# === Display options ===
print("📚 Available Origin/Destination Folders:")
for key, value in parent_folders.items():
    print(f"  {key}: {value['name']}")
print("\n")

# === Prompt for user inputs ===
origin_folder_number = input("🔹 Move FROM (choose 01 to 10): ").zfill(2)
destination_folder_number = input("🔹 Move TO (choose 01 to 10): ").zfill(2)
folders_to_move_input = input("🔹 Which sub-folders to move? (e.g., 01,02,05): ")

# === Validate parent folder inputs ===
if origin_folder_number not in parent_folders or destination_folder_number not in parent_folders:
    print("❌ Invalid folder numbers. Exiting.")
    sys.exit(1)

origin_folder_id = parent_folders[origin_folder_number]["id"]
destination_folder_id = parent_folders[destination_folder_number]["id"]

# === Parse subfolder numbers to move ===
folder_numbers = [f.strip().zfill(2) for f in folders_to_move_input.split(",")]

# === Fetch items from origin and destination ===
origin_items = client.folder(origin_folder_id).get_items(limit=1000)
destination_items = client.folder(destination_folder_id).get_items(limit=1000)
destination_folder_names = {item.name: item for item in destination_items if item.type == 'folder'}

# === Move each requested folder ===
for folder_number in folder_numbers:
    folder_to_move = None
    for item in origin_items:
        if item.type == 'folder' and item.name.startswith(folder_number):
            folder_to_move = item
            break

    if not folder_to_move:
        print(f"❌ Folder starting with {folder_number} not found in origin. Skipping...")
        continue

    # If a folder with the same name exists in destination, delete it
    if folder_to_move.name in destination_folder_names:
        print(f"🗑️ Folder '{folder_to_move.name}' already exists in destination. Deleting old version...")
        try:
            destination_folder_names[folder_to_move.name].delete()
            print(f"✅ Deleted existing '{folder_to_move.name}' from destination.")
        except Exception as e:
            print(f"⚠️ Failed to delete existing folder '{folder_to_move.name}': {e}")
            continue  # Skip move if delete fails

    print(f"\n📦 Moving '{folder_to_move.name}' to '{parent_folders[destination_folder_number]['name']}'...")
    try:
        moved_folder = folder_to_move.move(client.folder(destination_folder_id))
        print(f"✅ Successfully moved as '{moved_folder.name}'")
    except Exception as e:
        print(f"⚠️ Failed to move folder '{folder_to_move.name}': {e}")

print("\n🏁 Batch move operation complete.")
