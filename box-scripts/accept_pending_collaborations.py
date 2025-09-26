from boxsdk import JWTAuth, Client
import json

# === Authenticate using updated config path ===
config_path = '/Users/nic/code/box-scripts/config/976402037_13exz3x7_config.json'
auth = JWTAuth.from_settings_file(config_path)
client = Client(auth)

# === Get current App User ===
me = client.user().get()
print(f"🔐 Logged in as: {me.name} ({me.login})")

# === Check for pending collaboration invites ===
print("📬 Checking for pending collaboration invites...")

url = 'https://api.box.com/2.0/collaborations?status=pending'
headers = {'Content-Type': 'application/json'}
response = client._session.get(url, headers=headers)
pending = response.json()

accepted = 0
for collab in pending['entries']:
    collab_id = collab['id']
    folder_name = collab['item']['name']
    print(f" - Accepting: {folder_name} (Collab ID: {collab_id})")
    client._session.put(
        f'https://api.box.com/2.0/collaborations/{collab_id}',
        headers=headers,
        data=json.dumps({'status': 'accepted'})
    )
    accepted += 1

if accepted:
    print(f"\n✅ Accepted {accepted} collaboration invite(s).")
else:
    print("\n✅ No pending invites found.")
