from boxsdk import JWTAuth, Client

# Authenticate
auth = JWTAuth.from_settings_file('/Users/nic/code/box-scripts/config/976402037_13exz3x7_config.json')
client = Client(auth)

# Get App User
me = client.user().get()
print(f"🔐 Current user name: {me.name}")

# Target new name
new_name = "WilhnaOps"

# Only update if necessary
if me.name != new_name:
    print(f"✏️ Updating name to '{new_name}'...")
    updated_user = me.update_info(data={"name": new_name})  # <<< Must pass as 'data' dictionary
    print(f"✅ User name updated to: {updated_user.name}")
else:
    print(f"✅ No update needed. Already named '{new_name}'.")
