"""
Activity 8.2 Try It Yourself — Priority-based Election in MongoDB Replica Set
==============================================================================
Purpose:
    Demonstrates how MongoDB uses member PRIORITIES to decide which node
    becomes PRIMARY during an election.

    This script:
      1. Connects to rs0 (localhost:27017,27018,27019) and shows member
         priorities alongside current states.
      2. Predicts which node SHOULD win the next election (highest priority
         secondary).
      3. (With user confirmation) steps down the current primary via
         replSetStepDown and waits for the election to complete.
      4. Verifies whether the prediction was correct.
      5. Prints a final rs.status() summary.

    Expected outcome after init_replicaset_priority.js:
      mongo-rs0-1 (27017) priority=1 → should NOT win
      mongo-rs0-2 (27018) priority=3 → SHOULD win  ← prediction
      mongo-rs0-3 (27019) priority=2 → may win if 27018 unavailable

Usage:
    # Ensure rs0 is initiated with priorities:
    docker-compose up -d
    mongosh --port 27017 init_replicaset_priority.js

    # Then run:
    python activity_8_2_try.py

Requirements:
    pip install pymongo
"""

import sys
import time
from datetime import datetime, timezone

import pymongo
from pymongo import MongoClient
from pymongo.errors import (
    ConnectionFailure,
    OperationFailure,
    ServerSelectionTimeoutError,
)

# ─── Configuration ─────────────────────────────────────────────────────────────
RS_URI = (
    "mongodb://localhost:27017,localhost:27018,localhost:27019/"
    "?replicaSet=rs0&serverSelectionTimeoutMS=10000"
)

SEP = "=" * 70
SEP_THIN = "-" * 70


# ─── Utility ───────────────────────────────────────────────────────────────────

def print_section(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{SEP}")
    print(f"  {title}")
    print(SEP)


def ts() -> str:
    """Return a compact UTC timestamp string."""
    return datetime.now(timezone.utc).strftime("%H:%M:%S UTC")


# ─── Core Functions ────────────────────────────────────────────────────────────

def get_member_priorities(client: MongoClient) -> dict[str, float]:
    """
    Query rs.conf() (replSetGetConfig) and return a mapping of
    {host: priority} for every member in the replica set.

    Returns:
        dict mapping "host:port" strings to their numeric priority,
        or an empty dict if the command fails.
    """
    try:
        conf_result = client.admin.command("replSetGetConfig")
        config = conf_result.get("config", {})
        return {
            m["host"]: m.get("priority", 1.0)
            for m in config.get("members", [])
        }
    except (OperationFailure, ServerSelectionTimeoutError, ConnectionFailure) as exc:
        print(f"  [ERROR] replSetGetConfig failed: {exc}")
        return {}


def get_primary(client: MongoClient) -> str | None:
    """
    Return the hostname:port of the current PRIMARY, or None.
    """
    try:
        status = client.admin.command("replSetGetStatus")
        for m in status.get("members", []):
            if m.get("stateStr") == "PRIMARY":
                return m.get("name")
        return None
    except (OperationFailure, ServerSelectionTimeoutError, ConnectionFailure):
        return None


def print_rs_status_with_priorities(client: MongoClient) -> None:
    """
    Print a formatted table of all replica-set members showing:
    name, state, health, priority, and vote count.
    """
    print_section("CURRENT REPLICA SET STATUS  (with priorities)")
    try:
        status = client.admin.command("replSetGetStatus")
        priorities = get_member_priorities(client)

        print(f"  Replica Set : {status.get('set', '?')}")
        print(f"  My State    : {status.get('myState', '?')}")
        print()
        print(f"  {'Member':<35} {'State':<12} {'Health':<8} {'Priority':<10} Votes")
        print(f"  {SEP_THIN}")

        for m in status.get("members", []):
            host = m.get("name", "?")
            state = m.get("stateStr", "?")
            health = "UP" if m.get("health", 0) == 1 else "DOWN"
            priority = priorities.get(host, "?")
            votes = m.get("configVersion", "?")  # votes not in status; use conf
            marker = "  ◀ PRIMARY" if state == "PRIMARY" else ""
            print(
                f"  {host:<35} {state:<12} {health:<8} {str(priority):<10} {marker}"
            )
    except (OperationFailure, ServerSelectionTimeoutError, ConnectionFailure) as exc:
        print(f"  [ERROR] Cannot read rs.status(): {exc}")


def predict_next_primary(client: MongoClient) -> str | None:
    """
    Determine which member should win the NEXT election:
      - Reads current priorities from rs.conf().
      - Finds the member with the HIGHEST priority that is NOT currently primary.
      - Prints the prediction with reasoning.

    Returns:
        The host:port string of the predicted next primary, or None.
    """
    print_section("PREDICTION — Next Primary After Step-Down")
    priorities = get_member_priorities(client)
    current_primary = get_primary(client)

    if not priorities:
        print("  [ERROR] Cannot read priorities — prediction unavailable.")
        return None

    # Sort non-primary members by priority descending
    candidates = [
        (host, pri)
        for host, pri in priorities.items()
        if host != current_primary
    ]
    candidates.sort(key=lambda x: x[1], reverse=True)

    print(f"  Current PRIMARY    : {current_primary or '(none)'}")
    print()
    print("  Candidate priorities (non-primary members):")
    for host, pri in candidates:
        print(f"    {host:<35} priority={pri}")

    if not candidates:
        print("  No candidates available.")
        return None

    predicted_host, predicted_pri = candidates[0]
    print()
    print(
        f"  PREDICTION: {predicted_host} (priority={predicted_pri}) "
        f"should become the next PRIMARY."
    )
    print(
        "  Reasoning: MongoDB elects the member with the highest priority\n"
        "  that has an up-to-date oplog and can reach a majority of voters."
    )
    return predicted_host


def trigger_stepdown_and_verify(client: MongoClient) -> None:
    """
    1. Record the current primary.
    2. Read priorities and predict the next primary.
    3. Issue replSetStepDown (timeout=30 s).
    4. Wait 10 s for the election.
    5. Check the new primary.
    6. Report whether the prediction was correct.
    """
    print_section("TRIGGERING STEP-DOWN AND VERIFYING ELECTION")

    # ── Pre-flight ────────────────────────────────────────────────────────────
    old_primary = get_primary(client)
    priorities = get_member_priorities(client)

    print(f"  [{ts()}] Current primary  : {old_primary or '(none)'}")

    # Identify predicted winner (highest-priority secondary)
    candidates = sorted(
        [(h, p) for h, p in priorities.items() if h != old_primary],
        key=lambda x: x[1],
        reverse=True,
    )
    predicted = candidates[0][0] if candidates else None
    print(f"  [{ts()}] Predicted next   : {predicted or '(unknown)'}")

    # ── Step down ─────────────────────────────────────────────────────────────
    print(f"\n  [{ts()}] Issuing replSetStepDown (stepdown period = 30 s) …")
    try:
        client.admin.command("replSetStepDown", 30)
        print(f"  [{ts()}] ✓ replSetStepDown accepted.")
    except (ConnectionFailure, ServerSelectionTimeoutError):
        # Expected: the primary closes the connection when it steps down.
        print(
            f"  [{ts()}] Connection reset — this is expected when the primary "
            "steps down. PyMongo will reconnect automatically."
        )
    except OperationFailure as exc:
        print(f"  [{ts()}] [WARN] replSetStepDown error: {exc}")

    # ── Wait for election ─────────────────────────────────────────────────────
    print(f"\n  [{ts()}] Waiting 10 s for election to complete …")
    time.sleep(10)

    # ── Reconnect and check new primary ───────────────────────────────────────
    new_client = MongoClient(RS_URI)
    new_primary = get_primary(new_client)
    print(f"\n  [{ts()}] New primary      : {new_primary or '(still electing)'}")

    # ── Verdict ───────────────────────────────────────────────────────────────
    print()
    if new_primary and predicted and new_primary == predicted:
        print("  ✓ PREDICTION CORRECT!")
        print(f"    {predicted} won the election as expected (highest priority).")
    elif new_primary and new_primary != old_primary:
        print("  ~ FAILOVER SUCCEEDED but prediction missed.")
        print(f"    Expected : {predicted}")
        print(f"    Actual   : {new_primary}")
        print("    This can happen if the predicted node had a stale oplog.")
    elif not new_primary:
        print("  ⚠ No primary yet — election may still be in progress.")
        print("    Wait a few more seconds and check rs.status().")
    else:
        print("  ✗ Unexpected outcome — same primary retained.")

    new_client.close()


# ─── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    """
    Entry point for Activity 8.2 Try It Yourself.

    Steps:
      1. Connect to rs0 and show member states + priorities.
      2. Predict next primary.
      3. Ask user confirmation before triggering step-down.
      4. Trigger step-down and verify outcome.
      5. Print final rs.status().
    """
    print(SEP)
    print("  NoSQL Lab 8.2 — Try It Yourself: Priority-based Election")
    print(f"  PyMongo version : {pymongo.version}")
    print(f"  RS URI          : {RS_URI}")
    print(SEP)

    # ── Connect ───────────────────────────────────────────────────────────────
    print("\n  Connecting to rs0 …")
    try:
        client = MongoClient(RS_URI)
        client.admin.command("ping")
        print("  ✓ Connected to rs0 replica set.\n")
    except (ConnectionFailure, ServerSelectionTimeoutError) as exc:
        print(f"\n  [FATAL] Cannot connect: {exc}")
        print("  Ensure Docker containers are running and rs0 is initiated.")
        sys.exit(1)

    # ── Step 1: Status + priorities ───────────────────────────────────────────
    print_rs_status_with_priorities(client)

    # ── Step 2: Predict ───────────────────────────────────────────────────────
    predict_next_primary(client)

    # ── Step 3: User confirmation ─────────────────────────────────────────────
    print(f"\n{SEP}")
    print("  CAUTION: The next step will step down the current PRIMARY.")
    print("  Writes will be briefly unavailable during the election (~5–10 s).")
    print(SEP)
    try:
        answer = input("\n  Proceed with rs.stepDown()? [y/N] ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        answer = "n"

    if answer not in ("y", "yes"):
        print("\n  Step-down cancelled. Exiting.")
        client.close()
        sys.exit(0)

    # ── Step 4: Trigger step-down and verify ──────────────────────────────────
    trigger_stepdown_and_verify(client)

    # ── Step 5: Final status ──────────────────────────────────────────────────
    print_section("FINAL REPLICA SET STATUS")
    final_client = MongoClient(RS_URI)
    try:
        status = final_client.admin.command("replSetGetStatus")
        priorities = get_member_priorities(final_client)
        print(f"  {'Member':<35} {'State':<12} {'Health':<8} Priority")
        print(f"  {SEP_THIN}")
        for m in status.get("members", []):
            host = m.get("name", "?")
            state = m.get("stateStr", "?")
            health = "UP" if m.get("health", 0) == 1 else "DOWN"
            priority = priorities.get(host, "?")
            marker = "  ◀ PRIMARY" if state == "PRIMARY" else ""
            print(f"  {host:<35} {state:<12} {health:<8} {priority}{marker}")
    except (OperationFailure, ServerSelectionTimeoutError, ConnectionFailure) as exc:
        print(f"  [ERROR] {exc}")
    finally:
        final_client.close()

    client.close()
    print(f"\n{SEP}")
    print("  Lab 8.2 Try It Yourself complete.")
    print(SEP)


if __name__ == "__main__":
    main()
