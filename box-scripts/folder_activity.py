from boxsdk import JWTAuth, Client
import pandas as pd
import sys
import os

# Code Purpose:
# This script allows the user to select one of three Box folders.
# It gathers file-level metadata (created date, modified date, file name, file location)
# and exports the information into an Excel file for activity tracking.

# Step 1: Authenticate using Box config file
auth = JWTAuth.from_settings_file('/Users/nic/code/box-scripts/config/976402037_13exz3x7_config.json')
client = Client(auth)

# Step 2: Define folders with IDs (replace with your actual folder IDs)
parent_folders = {
    "01": {"id":"316984976711", "name": "DD Working Folder"},
    "02": {"id":"283328524100", "name": "Wilhelmina Project Data Room - Confidential"},
    "03": {"id":"322833268600", "name": "Wilhelmina TG2 10TPH - Kuantan #1 - Shared Project Files"},
}

# Step 3: Display available folders to the user
print("📚 Available Folders:")
for key, val in parent_folders.items():
    print(f"  {key}: {val['name']}")
print("\n")

# Step 4: Prompt user input
selected = input("🔹 Select folder number to analyze (01, 02, 03): ").zfill(2)
if selected not in parent_folders:
    print("❌ Invalid folder number.")
    sys.exit(1)

folder_id = parent_folders[selected]['id']
folder_name = parent_folders[selected]['name']

# Step 5: Recursive function to gather file metadata
def walk_folder(folder, path_prefix=""):
    data = []
    items = folder.get_items(limit=1000)
    
    for item in items:
        full_path = os.path.join(path_prefix, item.name)
        if item.type == 'folder':
            data.extend(walk_folder(item, full_path))
        elif item.type == 'file':
            file_info = client.file(item.id).get()
            data.append({
                'Date': file_info.created_at,
                'Activity Type': 'Created',
                'File Name': file_info.name,
                'File Location': full_path
            })
            if file_info.modified_at and file_info.modified_at != file_info.created_at:
                data.append({
                    'Date': file_info.modified_at,
                    'Activity Type': 'Modified',
                    'File Name': file_info.name,
                    'File Location': full_path
                })
    return data

# Step 6: Start data collection
print(f"🔎 Gathering data for folder: {folder_name}...")
folder = client.folder(folder_id)
activity_data = walk_folder(folder)

# Step 7: Export to Excel
df = pd.DataFrame(activity_data)
output_file = f"{folder_name.replace(' ', '_')}_Activity_Log.xlsx"
df.sort_values(by='Date', inplace=True)
df.to_excel(output_file, index=False)

print(f"\n✅ Export complete. File saved as: {output_file}")
