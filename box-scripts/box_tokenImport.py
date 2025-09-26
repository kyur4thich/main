from boxsdk import JWTAuth, Client
import os

print("✅ JWTAuth:", JWTAuth)

# Check that config file exists
config_path = '/Users/nic/Downloads/976402037_cqwg8w2n_config.json'
print("✅ Config found:", os.path.exists(config_path))

auth = JWTAuth.from_settings_file(config_path)
client = Client(auth)

me = client.user().get()
print(f'🎉 Logged in as: {me.name}')
