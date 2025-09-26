from boxsdk import JWTAuth, Client
import pandas as pd
import json
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from openpyxl.worksheet.hyperlink import Hyperlink
from datetime import datetime

# === Authenticate using Box JWT config ===
auth = JWTAuth.from_settings_file('/Users/nic/code/box-scripts/config/976402037_13exz3x7_config.json')
client = Client(auth)

me = client.user().get()
print(f"🔐 Authenticated as: {me.name} ({me.id})")
print(f"📧 App User login: {me.login}")

# === Force-accept pending collaboration invites via raw API ===
print("📬 Force-checking for pending invites via direct API...")

url = 'https://api.box.com/2.0/collaborations?status=pending'
headers = {'Content-Type': 'application/json'}
response = client._session.get(url, headers=headers)
pending = response.json()

accepted_any = False
for collab in pending['entries']:
    collab_id = collab['id']
    folder_name = collab['item']['name']
    print(f" - Accepting: {folder_name} (Collaboration ID: {collab_id})")

    client._session.put(
        f'https://api.box.com/2.0/collaborations/{collab_id}',
        headers=headers,
        data=json.dumps({'status': 'accepted'})
    )
    accepted_any = True

if accepted_any:
    print("✅ Pending invites accepted.")
else:
    print("✅ No invites needed accepting.")

# === Preview contents of root folder ===
custom_root_id = '316984650859'  # Custom root: 01. EME Uploads
print(f"\n📂 Scanning from Root Folder ID: {custom_root_id}")
root_items = client.folder(custom_root_id).get_items(limit=1000)
for item in root_items:
    print(f" - [{item.type}] {item.name} (ID: {item.id})")

# === Traverse folders and record file inventory ===
file_records = []

def traverse_folder(folder_id, path):
    items = client.folder(folder_id).get_items(limit=1000)
    for item in items:
        if item.type == 'folder':
            traverse_folder(item.id, f"{path}/{item.name}")
        elif item.type == 'file':
            file = client.file(item.id).get()
            file_records.append({
                "Folder Path": path,
                "File Name": file.name,
                "File ID": file.id,
                "File Link": f"https://app.box.com/file/{file.id}",
                "Size (KB)": round(file.size / 1024, 2),
                "Owner": file.created_by['name'] if file.created_by else None,
                "Uploaded At": file.created_at,
                "Modified At": file.modified_at,
                "Last Downloaded At": "N/A"
            })

print("\n🔍 Scanning Box folders recursively...")
traverse_folder(custom_root_id, "/")

# === Export to Excel ===
df = pd.DataFrame(file_records)
today = datetime.today().strftime('%Y%m%d')
output_path = f"/Users/nic/Desktop/boxVDR_inventory_{today}.xlsx"

# Create workbook
wb = Workbook()
ws = wb.active
ws.title = "BoxVDR Inventory"

# Write headers
for col_idx, col_name in enumerate(df.columns, start=1):
    ws.cell(row=1, column=col_idx, value=col_name)

# Write rows
for row_idx, (_, row) in enumerate(df.iterrows(), start=2):
    for col_idx, col_name in enumerate(df.columns, start=1):
        value = row[col_name]
        cell = ws.cell(row=row_idx, column=col_idx)
        if col_name == "File Link" and isinstance(value, str) and value.startswith("http"):
            cell.value = "View File"
            cell.hyperlink = Hyperlink(ref=cell.coordinate, location=value, target=value)
            cell.font = Font(color="0563C1", underline="single")
            cell.alignment = Alignment(horizontal="left")
        else:
            cell.value = value

# Auto-fit column widths
for col in ws.columns:
    max_length = 0
    col_letter = col[0].column_letter
    for cell in col:
        if cell.value:
            try:
                max_length = max(max_length, len(str(cell.value)))
            except:
                pass
    ws.column_dimensions[col_letter].width = max_length + 5

# Save Excel file
wb.save(output_path)
print(f"\n✅ Export complete with visible 'View File' links: {output_path}")

