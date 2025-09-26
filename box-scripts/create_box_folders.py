from boxsdk import JWTAuth, Client

# ✅ Use your actual Box config file path
config_path = '/Users/nic/code/box-scripts/config/976402037_13exz3x7_config.json'

# 🔐 Authenticate using JWT
auth = JWTAuth.from_settings_file(config_path)
client = Client(auth)

# ✅ Confirm login
me = client.user().get()
print(f"\n🔐 Authenticated as: {me.name} ({me.login})")

# ✅ Define your folder mapping
folder_map = {
    "01": {"id": "316984650859", "name": "01. EME Uploads"},
    "02": {"id": "316982193479", "name": "02. WEM Review"},
    "03": {"id": "316987304563", "name": "03. For Afry Review"},
    "04": {"id": "316988094360", "name": "04. Frozen Files"},
    "05": {"id": "316985039982", "name": "05. Investor Engineering DD"},
    "10": {"id": "319726840600", "name": "10. Engineering"},
}

# 🔢 Prompt user to select target folder
print("\n📚 Available target folders:")
for key, val in folder_map.items():
    print(f"  {key}: {val['name']}")

choice = input("\n🔹 Enter folder number to add 21 subfolders (e.g. 01, 02, 10): ").strip()
folder_info = folder_map.get(choice)

if not folder_info:
    print("❌ Invalid folder number. Exiting.")
    exit()

parent_folder_id = folder_info['id']
print(f"\n📂 Creating folders in: {folder_info['name']} (ID: {parent_folder_id})\n")

# 📁 Subfolders to create (with dots)
subfolders = [
    "01. Project Management",
    "02. Investment Cost Estimation",
    "03. Planning",
    "04. Procurement",
    "05. Process Engineering",
    "06. Mechanical Engineering",
    "07. Piping Engineering",
    "08. Electrical Engineering",
    "09. Process Control Engineering",
    "10. ICT Infrastructure Engineering",
    "11. Structural Engineering",
    "12. Architectural Engineering",
    "13. Infrastructural Engineering",
    "14. Processing Area Geotechnical",
    "15. HVAC Engineering",
    "16. Construction Management",
    "17. HSE Engineering",
    "18. Sustainability",
    "19. Fire Protection Engineering",
    "20. Logistics",
    "21. Engineering Tools"
]

# 🚀 Create each folder
for name in subfolders:
    try:
        new_folder = client.folder(parent_folder_id).create_subfolder(name)
        print(f"✅ Created: {name} (ID: {new_folder.id})")
    except Exception as e:
        print(f"⚠️ Could not create '{name}': {e}")
