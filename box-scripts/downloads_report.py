from boxsdk import JWTAuth, Client
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from openpyxl.worksheet.hyperlink import Hyperlink
from datetime import datetime, timedelta
import pandas as pd
import os
import sys

# === Config ===
CONFIG_PATH = '/Users/nic/code/box-scripts/config/976402037_13exz3x7_config.json'
DOWNLOAD_LOOKBACK_MONTHS = 3

# === Authenticate ===
auth = JWTAuth.from_settings_file(CONFIG_PATH)
client = Client(auth)

me = client.user().get()
print(f"🔐 Authenticated as: {me.name} ({me.id})")
print(f"📧 App User login: {me.login}\n")

# === Define folders ===
parent_folders = {
    "01": {"id":"316984976711", "name": "DD Working Folder"},
    "02": {"id":"283328524100", "name": "Wilhelmina Project Data Room - Confidential"},
    "03": {"id":"322833268600", "name": "Wilhelmina TG2 10TPH - Kuantan #1 - Shared Project Files"},
}

# === Folder Selection ===
print("📚 Available Folders:")
for key, val in parent_folders.items():
    print(f"  {key}: {val['name']}")
print()

selected = input("🔹 Select folder number to analyze (01, 02, 03): ").zfill(2)
if selected not in parent_folders:
    print("❌ Invalid folder number.")
    sys.exit(1)

folder_id = parent_folders[selected]['id']
folder_name = parent_folders[selected]['name']
print(f"\n📂 Scanning: {folder_name} (ID: {folder_id})")

# === Gather File IDs ===
file_map = {}

def traverse(folder_id, path=""):
    items = client.folder(folder_id).get_items(limit=1000)
    for item in items:
        if item.type == 'folder':
            traverse(item.id, path + "/" + item.name)
        elif item.type == 'file':
            file_map[item.id] = {
                "File Name": item.name,
                "File Link": f"https://app.box.com/file/{item.id}",
                "Path": path or "/"
            }

print("📁 Gathering files...")
traverse(folder_id)
print(f"📄 Found {len(file_map)} files.")

# === Fetch Download Events ===
start_time = datetime.utcnow() - timedelta(days=30 * DOWNLOAD_LOOKBACK_MONTHS)
stream_position = '0'
download_counts = {}

print(f"🔄 Fetching download events since {start_time.date()}...")
while True:
    events = client.events().get_events(limit=500, stream_position=stream_position)
    for event in events['entries']:
        if event['event_type'] == 'DOWNLOAD' and 'source' in event:
            file_id = event['source'].get('id')
            if file_id in file_map:
                download_counts[file_id] = download_counts.get(file_id, 0) + 1

    if events['next_stream_position'] == stream_position:
        break
    stream_position = events['next_stream_position']

print(f"\n✅ Total downloads found: {sum(download_counts.values())}")

# === Prepare DataFrame ===
records = []
for file_id, file_info in file_map.items():
    records.append({
        "File Name": file_info['File Name'],
        "Folder Path": file_info['Path'],
        "File Link": file_info['File Link'],
        "Download Count": download_counts.get(file_id, 0)
    })

df = pd.DataFrame(records)
df.sort_values(by="Download Count", ascending=False, inplace=True)

# === Export to Excel ===
today = datetime.today().strftime('%Y%m%d')
output_path = f"/Users/nic/Desktop/boxVDR_DownloadSummary_{selected}_{today}.xlsx"

wb = Workbook()
ws = wb.active
ws.title = "Download Summary"

# Write headers
for col_idx, col_name in enumerate(df.columns, start=1):
    ws.cell(row=1, column=col_idx, value=col_name)

# Write rows
for row_idx, (_, row) in enumerate(df.iterrows(), start=2):
    for col_idx, col_name in enumerate(df.columns, start=1):
        value = row[col_name]
        cell = ws.cell(row=row_idx, column=col_idx)
        if col_name == "File Link":
            cell.value = "View File"
            cell.hyperlink = Hyperlink(ref=cell.coordinate, target=value)
            cell.font = Font(color="0563C1", underline="single")
            cell.alignment = Alignment(horizontal="left")
        else:
            cell.value = value

# Autofit columns
for col in ws.columns:
    max_len = 0
    col_letter = col[0].column_letter
    for cell in col:
        if cell.value:
            try:
                max_len = max(max_len, len(str(cell.value)))
            except:
                pass
    ws.column_dimensions[col_letter].width = max_len + 5

wb.save(output_path)
print(f"\n📊 Download report saved: {output_path}")
