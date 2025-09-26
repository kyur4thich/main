from boxsdk import JWTAuth, Client
import pandas as pd
from datetime import datetime
from tqdm import tqdm

# === Authenticate ===
auth = JWTAuth.from_settings_file('/Users/nic/code/box-scripts/config/976402037_13exz3x7_config.json')
client = Client(auth)

# === Define Parent Folders ===
parent_folders = {
    "01": {"id": "316984650859", "name": "01. EME Uploads"},
    "02": {"id": "316982193479", "name": "02. WEM Review"},
    "03": {"id": "316987304563", "name": "03. For Afry Review"},
    "04": {"id": "316988094360", "name": "04. Frozen Files"},
    "05": {"id": "316985039982", "name": "05. Investor Engineering DD"},
    "10": {"id": "319726840600", "name": "10. Engineering"},
}

# === User Date Input ===
input_date_str = input("📅 Enter cutoff date (YYYY-MM-DD): ").strip()
try:
    cutoff_date = datetime.strptime(input_date_str, "%Y-%m-%d")
except ValueError:
    print("❌ Invalid date format. Use YYYY-MM-DD.")
    exit()

summary = {}

# === Recursive Folder Scanner ===
def scan_folder(folder_id, parent_name, subfolder_name):
    try:
        items = client.folder(folder_id).get_items(limit=1000)
        for item in items:
            if item.type == "folder":
                scan_folder(item.id, parent_name, item.name)
            elif item.type == "file":
                file = client.file(item.id).get()
                mod_time = datetime.strptime(file.modified_at[:19], "%Y-%m-%dT%H:%M:%S")
                if mod_time > cutoff_date:
                    key = (parent_name, subfolder_name)
                    summary[key] = summary.get(key, 0) + 1
    except Exception as e:
        print(f"⚠️ Error in {subfolder_name}: {e}")

# === Traverse All Parents ===
print("\n🔍 Starting scan...")
for pf in tqdm(parent_folders.values(), desc="Scanning parent folders"):
    try:
        items = client.folder(pf["id"]).get_items(limit=1000)
        for item in tqdm(items, desc=f"📁 {pf['name']}", leave=False):
            if item.type == "folder":
                scan_folder(item.id, pf["name"], item.name)
    except Exception as e:
        print(f"⚠️ Error accessing {pf['name']}: {e}")

# === Export Results ===
if summary:
    data = [{"Parent Folder": k[0], "Updated Folder": k[1], "Files Added": v} for k, v in summary.items()]
    df = pd.DataFrame(data)
    today = datetime.today().strftime("%Y%m%d")
    output_path = f"/Users/nic/Desktop/boxVDR_UpdatesSince_{input_date_str.replace('-', '')}_{today}.xlsx"
    df.to_excel(output_path, index=False)
    print(f"\n✅ Report saved: {output_path}")
else:
    print("\n✅ No updates found since that date.")
