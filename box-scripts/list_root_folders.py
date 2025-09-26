from boxsdk.auth.jwt_auth import JWTAuth
from boxsdk import Client


# === Authenticate using your Box config ===
config_path = '/Users/nic/Code/box-scripts/config/976402037_13exz3x7_config.json'
auth = JWTAuth.from_settings_file(config_path)
client = Client(auth)

# === Show authenticated user
me = client.user().get()
print(f"\n🔐 Authenticated as: {me.name} ({me.login})\n")

# === Helper to format hierarchy
def indent(level):
    return '   ' * level + '└── '

# === Recursive folder listing (up to 3 levels deep)
def list_folders(folder_id, level=0):
    try:
        items = client.folder(folder_id).get_items(limit=1000)
        for item in items:
            if item.type == 'folder':
                print(f"{indent(level)}📁 {item.name} (ID: {item.id})")
                if level < 2:  # 0 = root, 1 = child, 2 = grandchild
                    list_folders(item.id, level + 1)
    except Exception as e:
        print(f"{indent(level)}⚠️ Error accessing folder {folder_id}: {e}")

# === Start from All Files (/)
print("📂 Box Folder Structure from 'All Files':\n")
list_folders('0')
