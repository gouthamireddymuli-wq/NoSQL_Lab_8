"""
Activity 8.1 Try It Yourself - MongoDB Replica Set with Arbiter
================================================================
Purpose:
    Demonstrates a 3-member replica set (rs0) containing:
      - mongo-rs0-1 (PRIMARY, port 27017)
      - mongo-rs0-2 (SECONDARY, port 27018)
      - mongo-rs0-3 (ARBITER, port 27020)

    This script:
      1. Connects to rs0 and prints rs.status() member list (including arbiter).
      2. Inserts a document on the primary.
      3. Reads from secondary (port 27018) using SECONDARY_PREFERRED.
      4. Demonstrates that arbiters CANNOT serve reads (gracefully caught).
      5. Explains WHY arbiters are useful.

Usage:
    Ensure containers are running:
        docker-compose up -d
        mongosh --port 27017 init_replicaset_arbiter.js

    Then run:
        python activity_8_1_try.py

Requirements:
    pip install pymongo
"""

import sys
from datetime import datetime, timezone

import pymongo
from pymongo import MongoClient, ReadPreference
from pymongo.errors import (
    ConnectionFailure,
    OperationFailure,
    ServerSelectionTimeoutError,
)

# ─── Connection Settings ───────────────────────────────────────────────────────
RS_URI = (
    "mongodb://localhost:27017,localhost:27018,localhost:27020/"
    "?replicaSet=rs0&serverSelectionTimeoutMS=8000"
)
ARBITER_PORT = 27020
SECONDARY_PORT = 27018

SEP = "=" * 70
SEP_THIN = "-" * 70


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{SEP}")
    print(f"  {title}")
    print(SEP)


def print_rs_status(client: MongoClient) -> None:
    """
    Retrieve and print rs.status() member information.
    Highlights which member is PRIMARY, SECONDARY, or ARBITER.
    """
    print_section("REPLICA SET STATUS  (rs.status())")
    try:
        status = client.admin.command("replSetGetStatus")
        set_name = status.get("set", "unknown")
        print(f"  Replica Set : {set_name}")
        print(f"  My State    : {status.get('myState', '?')}")
        print(f"\n  {'Member':<35} {'State':<12} {'Health':<8} {'Arbiter?'}")
        print(f"  {SEP_THIN}")
        for m in status.get("members", []):
            host = m.get("name", "?")
            state = m.get("stateStr", "?")
            health = "UP" if m.get("health", 0) == 1 else "DOWN"
            is_arbiter = "YES ✓" if state == "ARBITER" else ""
            print(f"  {host:<35} {state:<12} {health:<8} {is_arbiter}")
    except (OperationFailure, ServerSelectionTimeoutError) as exc:
        print(f"  [ERROR] Could not retrieve rs.status(): {exc}")


def insert_on_primary(client: MongoClient) -> str | None:
    """
    Insert a sample document into the primary node.
    Returns the inserted document's ID as a string, or None on failure.
    """
    print_section("INSERT DOCUMENT  (on PRIMARY)")
    try:
        doc = {
            "activity": "8.1_TryItYourself",
            "type": "arbiter_demo",
            "message": "Inserted via primary in rs0 with arbiter topology",
            "timestamp": datetime.now(timezone.utc),
        }
        result = client["testdb"]["arbiter_demo"].insert_one(doc)
        inserted_id = str(result.inserted_id)
        print(f"  ✓ Document inserted successfully.")
        print(f"    _id       : {inserted_id}")
        print(f"    collection: testdb.arbiter_demo")
        return inserted_id
    except (ConnectionFailure, OperationFailure) as exc:
        print(f"  [ERROR] Insert failed: {exc}")
        return None


def read_from_secondary(inserted_id: str | None) -> None:
    """
    Open a direct connection to the secondary (port 27018) and read back
    the document just inserted, using SECONDARY_PREFERRED read preference.
    This confirms replication is working.
    """
    print_section("READ FROM SECONDARY  (port 27018, SECONDARY_PREFERRED)")
    try:
        # Connect directly to secondary; still specify replicaSet so PyMongo
        # resolves the topology, but favour secondary reads.
        sec_client = MongoClient(
            "mongodb://localhost:27018/?replicaSet=rs0&serverSelectionTimeoutMS=8000",
            read_preference=ReadPreference.SECONDARY_PREFERRED,
        )
        collection = sec_client["testdb"]["arbiter_demo"]

        query = {} if inserted_id is None else {"_id": pymongo.collection.Collection}

        # Fetch the most recent doc
        doc = collection.find_one(sort=[("_id", pymongo.DESCENDING)])
        if doc:
            print(f"  ✓ Successfully read from secondary!")
            print(f"    _id      : {doc.get('_id')}")
            print(f"    message  : {doc.get('message')}")
            print(f"    timestamp: {doc.get('timestamp')}")
        else:
            print("  ⚠ No document found on secondary yet (replication lag?).")
        sec_client.close()
    except (ConnectionFailure, ServerSelectionTimeoutError, OperationFailure) as exc:
        print(f"  [ERROR] Read from secondary failed: {exc}")


def demonstrate_arbiter_no_data() -> None:
    """
    Attempt to read data directly from the arbiter (port 27020).
    Arbiters hold NO data, so this should fail.
    The error is caught gracefully and explained.
    """
    print_section("ARBITER CANNOT SERVE READS  (port 27020)")
    print("  Attempting a direct read from the arbiter node …")
    try:
        arb_client = MongoClient(
            f"mongodb://localhost:{ARBITER_PORT}/"
            "?directConnection=true&serverSelectionTimeoutMS=5000"
        )
        # Force connection
        doc = arb_client["testdb"]["arbiter_demo"].find_one()
        # If we somehow get here, it is worth noting:
        print(f"  Unexpected document returned: {doc}")
        arb_client.close()
    except (OperationFailure, ServerSelectionTimeoutError, ConnectionFailure) as exc:
        # Expected behaviour – arbiter rejects data reads
        print(f"  ✓ Expected error caught (arbiter cannot serve reads):")
        print(f"    {type(exc).__name__}: {exc}")
        print()
        print("  This is CORRECT behaviour. Arbiters exist solely for")
        print("  elections and do not store any user data.")


def explain_arbiter_purpose() -> None:
    """Print a detailed explanation of why arbiters are useful."""
    print_section("WHY ARBITERS ARE USEFUL")
    explanation = """
  An arbiter participates in elections with 1 vote but stores NO data,
  costs minimal RAM/CPU, and prevents split-brain in 2-data-node sets
  by providing the tie-breaking vote for a quorum majority.

  Detailed breakdown
  ──────────────────
  Quorum requirement:
    MongoDB requires a MAJORITY of voting members to elect a primary.
    With 2 data nodes (rs0-1 and rs0-2), if one node goes down only 1
    of 2 votes remains — not a majority (need 2 of 2). This would leave
    the replica set with NO primary → writes unavailable indefinitely.

  The arbiter's role:
    Adding an arbiter creates a 3-voter set (rs0-1, rs0-2, arbiter).
    Majority = 2 of 3 votes.
    If rs0-1 goes down:  rs0-2 + arbiter = 2 votes → majority → election OK.
    If rs0-2 goes down:  rs0-1 + arbiter = 2 votes → majority → election OK.

  Cost vs benefit:
    ✓ Negligible hardware: an arbiter runs on a tiny VM / cloud micro-instance.
    ✓ No data storage needed: no disk space for data files.
    ✓ No replication overhead: no oplog synchronisation.
    ✗ Provides NO extra redundancy for data (do NOT use if you can afford 3 data nodes).
    ✗ Not recommended for high-availability deployments where data redundancy matters.

  Split-brain prevention:
    Without an arbiter in a 2-node set, a network partition could leave
    both nodes thinking they might still be (or become) primary, causing
    "split-brain" where two primaries accept conflicting writes.
    The arbiter's vote ensures only one side can achieve a majority.

  Topology used in this activity:
    PORT 27017  →  rs0-1  PRIMARY   (data + votes)
    PORT 27018  →  rs0-2  SECONDARY (data + votes)
    PORT 27020  →  rs0-3  ARBITER   (votes ONLY, NO data)
"""
    print(explanation)


def main() -> None:
    """Entry point: run all demonstration steps."""
    print(SEP)
    print("  NoSQL Lab 8.1 — Try It Yourself: Replica Set with Arbiter")
    print(f"  PyMongo version: {pymongo.version}")
    print(SEP)

    # 1. Connect to replica set
    print(f"\n  Connecting to rs0 at: {RS_URI}")
    try:
        client = MongoClient(RS_URI)
        # Verify connectivity
        client.admin.command("ping")
        print("  ✓ Connected to rs0 replica set.\n")
    except (ConnectionFailure, ServerSelectionTimeoutError) as exc:
        print(f"\n  [FATAL] Cannot connect to replica set: {exc}")
        print("  Ensure Docker containers are running and rs0 is initiated.")
        sys.exit(1)

    # 2. Print rs.status()
    print_rs_status(client)

    # 3. Insert on primary
    inserted_id = insert_on_primary(client)

    # 4. Read from secondary
    read_from_secondary(inserted_id)

    # 5. Show arbiter cannot serve reads
    demonstrate_arbiter_no_data()

    # 6. Explain arbiter purpose
    explain_arbiter_purpose()

    # Cleanup
    client.close()
    print(f"\n{SEP}")
    print("  Demo complete. All connections closed.")
    print(SEP)


if __name__ == "__main__":
    main()
