# 📦 Box Automation Scripts

This repository contains automation scripts that interact with the Box.com API using the official SDK.

## 🔧 Setup

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
For README.md (Short Version)

Re-Downloading Config

If you change your Box app scopes (like enabling "Manage App Users") and your admin approves them, you usually don't need to re-download the JWT config unless the private key was rotated.

✅ If your script runs fine, no action needed.

❌ If you still get 403 insufficient_scope, re-download the config.json from Box Developer Console and replace your local one.

Path example:

/Users/nic/code/box-scripts/config/976402037_cqwg8w2n_config.json

