import sys
import os
import sqlite3

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.core_imports import DB_PATH, configure_console_log
from data.data_locker import DataLocker
from wallets.wallet_service import WalletService
from wallets.wallet_schema import WalletIn

def ensure_wallets_table(db):
    cursor = db.get_cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wallets (
            name TEXT PRIMARY KEY,
            public_address TEXT,
            private_address TEXT,
            image_path TEXT,
            balance REAL DEFAULT 0.0,
            tags TEXT DEFAULT '',
            is_active BOOLEAN DEFAULT 1,
            type TEXT DEFAULT 'personal'
        )
    """)
    db.commit()
    print("✅ Wallets table is ready.")

# ✅ Initialize connection
configure_console_log()
dl = DataLocker(str(DB_PATH))
ensure_wallets_table(dl.db)

# Use higher-level service which validates duplicates
service = WalletService()

wallets_to_add = [
    {
        "name": "R2Vault",
        "public_address": "FhNRk...VALID1",
        "private_address": "privatekey1",
        "image_path": "",
        "balance": 1000.0
    },
    {
        "name": "LandoVault",
        "public_address": "DjsRU...VALID2",
        "private_address": "privatekey2",
        "image_path": "",
        "balance": 2500.0
    }
]

for w in wallets_to_add:
    try:
        if service.repo.get_wallet_by_name(w["name"]):
            service.update_wallet(w["name"], WalletIn(**w))
            print(f"🔄 Updated wallet: {w['name']}")
        else:
            service.create_wallet(WalletIn(**w))
            print(f"✅ Inserted wallet: {w['name']}")
    except Exception as e:
        print(f"❌ Failed to upsert {w['name']}: {e}")

dl.close()
