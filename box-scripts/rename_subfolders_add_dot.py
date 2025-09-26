from boxsdk import JWTAuth, Client

# === Authenticate with Box JWT ===
auth = JWTAuth.from_settings_file('/Users/nic/code/box-scripts/config/976402037_13exz3x7_config.json')
client = Client(auth)

me = client.user().get()
print(f"🔐 Authenticated as: {me.name} ({me.login})\n")

# === Define the parent folder ID where the 21 folders exist ===
parent_folder_id = '319726840600'  # Your folder ID

# === Fetch subfolders under parent ===
print(f"📂 Fetching folders under parent ID {parent_folder_id}...")
items = client.folder(parent_folder_id).get_items(limit=1000)

# === Rename folders ===
for item in items:
    if item.type == 'folder':
        original_name = item.name

        # Check if a dot already exists after the first two digits
        if len(original_name) > 2 and original_name[2] != '.':
            # Insert a dot after the two numbers
            if original_name[2] == ' ':
                new_name = f"{original_name[:2]}. {original_name[3:]}"
            else:
                new_name = f"{original_name[:2]}. {original_name[2:]}"

            print(f"✏️ Renaming: '{original_name}' → '{new_name}'...")
            try:
                item.update_info(data={"name": new_name})
                print(f"✅ Renamed: '{original_name}' → '{new_name}'")
            except Exception as e:
                print(f"⚠️ Failed to rename '{original_name}': {e}")
        else:
            print(f"➖ No change needed: '{original_name}'")

print("\n🏁 Rename operation complete.")
