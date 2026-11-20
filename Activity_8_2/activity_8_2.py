"""
Activity 8.2 — Observe Failover and Election in a MongoDB Replica Set
======================================================================
Purpose:
    Monitors an rs0 replica set across localhost:27017,27018,27019 and
    demonstrates automatic failover behaviour when the primary steps down.

    Two concurrent tasks run:
      1. monitor_replica_set  — polls rs.status() every 2 s for 90 s,
         detects primary changes, and writes a failover_log.txt.
      2. continuous_read_demo — reads from the testdb.replication_test
         collection in a tight loop, showing which host answers each
         request and surviving the brief window when the primary steps down.

Usage:
    # Ensure containers are running and rs0 is initiated:
    docker-compose up -d
    mongosh --port 27017 init_replicaset.js

    # Start monitoring:
    python activity_8_2.py

    # In a SEPARATE terminal, trigger a step-down:
    mongosh --port 27017 --eval "rs.stepDown()"

Requirements:
    pip install pymongo
"""

import os
import sys
import time
import threading
from datetime import datetime, timezone

import pymongo
from pymongo import MongoClient, ReadPreference
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

# Log file is written next to this script
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "failover_log.txt")

SEP = "=" * 70
SEP_THIN = "-" * 70


# ─── Helpers ───────────────────────────────────────────────────────────────────

def ts() -> str:
    """Return a compact UTC timestamp string."""
    return datetime.now(timezone.utc).strftime("%H:%M:%S.%f")[:-3] + "Z"


def print_section(title: str) -> None:
    """Print a formatted section header to stdout."""
    print(f"\n{SEP}")
    print(f"  {title}")
    print(SEP)


def get_primary(client: MongoClient) -> str | None:
    """
    Query rs.status() and return the hostname:port of the current PRIMARY,
    or None if no primary is currently elected.
    """
    try:
        status = client.admin.command("replSetGetStatus")
        for member in status.get("members", []):
            if member.get("stateStr") == "PRIMARY":
                return member.get("name")
        return None
    except (OperationFailure, ServerSelectionTimeoutError, ConnectionFailure):
        return None


# ─── Task 1 — Monitor Replica Set ─────────────────────────────────────────────

def monitor_replica_set(duration: int = 90, interval: int = 2) -> None:
    """
    Poll rs.status() every `interval` seconds for `duration` seconds.

    For each poll:
      - Print timestamp, current primary, and all member states.
      - Detect primary changes and announce FAILOVER events.
      - Append a line to failover_log.txt.

    Args:
        duration: Total monitoring duration in seconds.
        interval: Sleep between polls in seconds.
    """
    print_section("MONITOR REPLICA SET  (90 s)")
    print(f"  Polling rs.status() every {interval} s for {duration} s.")
    print(f"  Failover log → {LOG_FILE}")
    print(f"  {SEP_THIN}")

    client = MongoClient(RS_URI)
    previous_primary: str | None = None
    end_time = time.time() + duration

    with open(LOG_FILE, "a", encoding="utf-8") as log_fh:
        log_fh.write(f"\n{'='*70}\n")
        log_fh.write(f"Session started: {datetime.now(timezone.utc).isoformat()}\n")
        log_fh.write(f"{'='*70}\n")

        while time.time() < end_time:
            now = ts()
            try:
                status = client.admin.command("replSetGetStatus")
                members = status.get("members", [])
                current_primary: str | None = None
                member_lines: list[str] = []

                for m in members:
                    state = m.get("stateStr", "?")
                    name = m.get("name", "?")
                    health = "UP" if m.get("health", 0) == 1 else "DOWN"
                    if state == "PRIMARY":
                        current_primary = name
                    member_lines.append(f"    {name:<35} {state:<12} {health}")

                # ── Detect failover ──────────────────────────────────────────
                if current_primary != previous_primary:
                    if previous_primary is not None:
                        # A genuine change — either new primary elected or
                        # primary went away temporarily.
                        if current_primary:
                            msg = (
                                f"*** FAILOVER DETECTED: "
                                f"{previous_primary} → {current_primary} ***"
                            )
                        else:
                            msg = (
                                f"*** PRIMARY LOST: {previous_primary} stepped down "
                                f"— election in progress ***"
                            )
                        print(f"\n  {msg}")
                        log_fh.write(f"[{now}] {msg}\n")
                    previous_primary = current_primary

                # ── Print poll summary ───────────────────────────────────────
                primary_label = current_primary or "(none — election in progress)"
                print(f"  [{now}]  primary={primary_label}")
                for line in member_lines:
                    print(line)

                log_line = (
                    f"[{now}] primary={primary_label}  "
                    + "  ".join(
                        f"{m.get('name')}:{m.get('stateStr')}"
                        for m in members
                    )
                )
                log_fh.write(log_line + "\n")
                log_fh.flush()

            except (ServerSelectionTimeoutError, ConnectionFailure) as exc:
                warn = f"[{now}] rs.status() unreachable: {exc}"
                print(f"  ⚠ {warn}")
                log_fh.write(warn + "\n")
                log_fh.flush()

            time.sleep(interval)

    client.close()
    print(f"\n  Monitor finished. Log saved to {LOG_FILE}")


# ─── Task 2 — Continuous Read Demo ────────────────────────────────────────────

def continuous_read_demo(duration: int = 60, interval: float = 1.0) -> None:
    """
    Continuously read the most recent document from testdb.replication_test
    with PRIMARY_PREFERRED read preference.

    Demonstrates that:
      - Reads succeed normally during steady-state.
      - PyMongo automatically reconnects after a brief election window.
      - Which host services each read is logged.

    Args:
        duration: Total demo duration in seconds.
        interval: Sleep between reads in seconds.
    """
    print_section("CONTINUOUS READ DEMO  (60 s, PRIMARY_PREFERRED)")
    client = MongoClient(
        RS_URI,
        read_preference=ReadPreference.PRIMARY_PREFERRED,
    )
    collection = client["testdb"]["replication_test"]
    end_time = time.time() + duration
    read_count = 0
    error_count = 0

    while time.time() < end_time:
        now = ts()
        try:
            doc = collection.find_one(sort=[("_id", pymongo.DESCENDING)])
            # Discover which host this connection is using
            host_info = client.primary or "(discovering)"
            read_count += 1
            msg_field = doc.get("message", "(no message)") if doc else "(collection empty)"
            print(
                f"  [READ {read_count:>4}] [{now}]  host={host_info}  "
                f"doc={msg_field[:50]}"
            )
        except (ConnectionFailure, ServerSelectionTimeoutError) as exc:
            error_count += 1
            print(
                f"  [READ ERR ] [{now}]  "
                f"ConnectionFailure — PyMongo will auto-reconnect. ({exc})"
            )
        except OperationFailure as exc:
            error_count += 1
            print(f"  [READ ERR ] [{now}]  OperationFailure: {exc}")

        time.sleep(interval)

    client.close()
    print(
        f"\n  Read demo finished — {read_count} successful reads, "
        f"{error_count} transient errors (reconnected automatically)."
    )


# ─── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    """
    Entry point.

    Starts the continuous-read demo in a background thread and runs the
    replica-set monitor in the main thread for 90 seconds.
    """
    print(SEP)
    print("  NoSQL Lab 8.2 — Observe Failover and Election")
    print(f"  PyMongo version : {pymongo.version}")
    print(f"  RS URI          : {RS_URI}")
    print(SEP)

    # ── Verify connectivity ──────────────────────────────────────────────────
    print("\n  Verifying connection to rs0 …")
    try:
        probe = MongoClient(RS_URI)
        probe.admin.command("ping")
        primary = get_primary(probe)
        probe.close()
        print(f"  ✓ Connected. Current primary: {primary or '(none)'}\n")
    except (ConnectionFailure, ServerSelectionTimeoutError) as exc:
        print(f"\n  [FATAL] Cannot connect: {exc}")
        print("  Make sure Docker containers are up and rs0 is initiated.")
        sys.exit(1)

    # ── Instructions ─────────────────────────────────────────────────────────
    print(f"\n{SEP}")
    print("  HOW TO TRIGGER A FAILOVER")
    print(f"  {SEP_THIN}")
    print("  In another terminal run:")
    print("      mongosh --port 27017 --eval \"rs.stepDown()\"")
    print("  Or run:  mongosh --port 27017 rs_stepdown_commands.js")
    print(f"{SEP}\n")

    # ── Start background read demo ────────────────────────────────────────────
    read_thread = threading.Thread(
        target=continuous_read_demo,
        kwargs={"duration": 60, "interval": 1.0},
        daemon=True,
        name="read-demo",
    )
    read_thread.start()

    # ── Run monitor in main thread ────────────────────────────────────────────
    monitor_replica_set(duration=90, interval=2)

    # ── Wait for read thread to finish ────────────────────────────────────────
    read_thread.join(timeout=10)

    print(f"\n{SEP}")
    print("  Lab 8.2 complete. Check failover_log.txt for the full record.")
    print(SEP)


if __name__ == "__main__":
    main()
