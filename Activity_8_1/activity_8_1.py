"""
==============================================================
Lab 8.1 – Deploy a Local Replica Set
Activity: Verify 3-node replica set, insert on primary,
          read from both secondaries, and report rs.status().
==============================================================

Prerequisites
-------------
1. Docker Desktop running.
2. Start the cluster:
      docker compose up -d          (inside Activity_8_1/)
3. Initialise the replica set:
      mongosh --host localhost --port 27017 init_replicaset.js
4. Install PyMongo:
      pip install pymongo

Usage
-----
      python activity_8_1.py
"""

import time
import datetime
import sys

try:
    from pymongo import MongoClient, ReadPreference
    from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
except ImportError:
    sys.exit("PyMongo not installed. Run: pip install pymongo")

# ── Connection settings ────────────────────────────────────────────────────────
RS_URI = (
    "mongodb://localhost:27017,localhost:27018,localhost:27019"
    "/?replicaSet=rs0&serverSelectionTimeoutMS=10000"
)
DB_NAME = "lab8db"
COL_NAME = "replication_test"


def separator(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


# ── Step 1 – Connect ──────────────────────────────────────────────────────────
separator("Step 1 – Connect to Replica Set")
try:
    client = MongoClient(RS_URI)
    client.admin.command("ping")
    print("[OK] Connected to replica set rs0.")
except (ConnectionFailure, ServerSelectionTimeoutError) as exc:
    sys.exit(f"[ERROR] Cannot connect: {exc}\n"
             "Make sure the replica set is running (docker compose up -d).")

# ── Step 2 – rs.status() ─────────────────────────────────────────────────────
separator("Step 2 – Replica Set Status (rs.status())")
status = client.admin.command("replSetGetStatus")
print(f"  Replica Set Name : {status['set']}")
print(f"  My State         : {status['myState']}")
print()
primary_host = None
secondaries = []
for m in status["members"]:
    role_tag = ""
    if m["stateStr"] == "PRIMARY":
        role_tag = "  <--- PRIMARY"
        primary_host = m["name"]
    elif m["stateStr"] == "SECONDARY":
        role_tag = "  <--- SECONDARY"
        secondaries.append(m["name"])
    print(
        f"  [{m['_id']}] {m['name']:<40} "
        f"State: {m['stateStr']:<12} "
        f"Health: {int(m['health'])}{role_tag}"
    )

if not primary_host:
    sys.exit("[ERROR] No PRIMARY found. Wait a bit and re-run.")

# ── Step 3 – Insert on Primary ────────────────────────────────────────────────
separator("Step 3 – Insert Document on Primary")
db_primary = client[DB_NAME]
col_primary = db_primary[COL_NAME]

doc = {
    "lab": "8.1",
    "message": "Replication test document",
    "timestamp": datetime.datetime.utcnow(),
    "inserted_by": "activity_8_1.py"
}
result = col_primary.insert_one(doc)
print(f"  Inserted document _id : {result.inserted_id}")
print(f"  Primary host          : {primary_host}")

# Allow replication lag
print("\n  Waiting 3 seconds for replication to secondaries…")
time.sleep(3)

# ── Step 4 – Read from Secondaries ────────────────────────────────────────────
separator("Step 4 – Verify Replication on Secondaries")

secondary_uris = [
    f"mongodb://localhost:27018/?replicaSet=rs0",
    f"mongodb://localhost:27019/?replicaSet=rs0",
]

for idx, uri in enumerate(secondary_uris, start=1):
    sec_client = MongoClient(
        uri,
        read_preference=ReadPreference.SECONDARY_PREFERRED,
        serverSelectionTimeoutMS=5000,
    )
    try:
        sec_col = sec_client[DB_NAME][COL_NAME]
        found = sec_col.find_one({"_id": result.inserted_id})
        if found:
            print(f"\n  Secondary-{idx} ({uri}):")
            print(f"    _id       : {found['_id']}")
            print(f"    message   : {found['message']}")
            print(f"    timestamp : {found['timestamp']}")
            print(f"    [OK] Document replicated successfully.")
        else:
            print(f"\n  Secondary-{idx}: Document NOT found (replication lag?).")
    except Exception as exc:
        print(f"\n  Secondary-{idx}: Error – {exc}")
    finally:
        sec_client.close()

# ── Step 5 – Full rs.status() summary ────────────────────────────────────────
separator("Step 5 – Full rs.status() Member Summary")
status2 = client.admin.command("replSetGetStatus")
print(f"  {'#':<4} {'Host':<40} {'State':<14} {'Health':<8} {'Optime'}")
print(f"  {'-'*4} {'-'*40} {'-'*14} {'-'*8} {'-'*20}")
for m in status2["members"]:
    optime_str = str(m.get("optimeDate", "N/A"))
    print(
        f"  {m['_id']:<4} {m['name']:<40} "
        f"{m['stateStr']:<14} {int(m['health']):<8} {optime_str}"
    )

separator("Lab 8.1 – Activity Complete")
print("  Summary:")
print(f"    PRIMARY    : {primary_host}")
for i, s in enumerate(secondaries, 1):
    print(f"    SECONDARY-{i}: {s}")
print("\n  All steps completed successfully.")
client.close()
