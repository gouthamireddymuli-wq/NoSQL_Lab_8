// ─── Activity 8.2 Try It Yourself — init_replicaset_priority.js ──────────────
// Purpose:
//   Initiates rs0 with DIFFERENT priorities to test MongoDB's priority-based
//   election algorithm:
//
//     Member 0  host.docker.internal:27017  priority=1  (lowest — should NOT win)
//     Member 1  host.docker.internal:27018  priority=3  (HIGHEST — should win)
//     Member 2  host.docker.internal:27019  priority=2  (medium)
//
//   After initiation the script:
//     • Waits 15 s for the initial election.
//     • Prints a prediction about which member will become PRIMARY.
//     • Verifies via rs.status().
//     • Shows priorities via rs.conf().
//
// Usage:
//   mongosh --port 27017 init_replicaset_priority.js
// ──────────────────────────────────────────────────────────────────────────────

print("=".repeat(70));
print("  init_replicaset_priority.js — Priority-based Election Experiment");
print("=".repeat(70));

// ── 1. Initiate replica set with custom priorities ────────────────────────────
var config = {
  _id: "rs0",
  members: [
    {
      _id: 0,
      host: "host.docker.internal:27017",
      priority: 1    // Lowest — will NOT win if 27018 or 27019 are healthy
    },
    {
      _id: 1,
      host: "host.docker.internal:27018",
      priority: 3    // HIGHEST — MongoDB prefers this node as PRIMARY
    },
    {
      _id: 2,
      host: "host.docker.internal:27019",
      priority: 2    // Medium — will win if 27018 is unavailable
    }
  ]
};

print("\n  Calling rs.initiate() with priority configuration …");
try {
  var result = rs.initiate(config);
  print("  rs.initiate() result:");
  printjson(result);
} catch (e) {
  print("  [WARN] rs.initiate() error (may already be initiated): " + e.message);
}

// ── 2. Wait for election ──────────────────────────────────────────────────────
print("\n  Waiting 15 seconds for PRIMARY election based on priorities …");
sleep(15000);

// ── 3. Prediction ─────────────────────────────────────────────────────────────
print("\n" + "=".repeat(70));
print("  PREDICTION");
print("=".repeat(70));
print(
  "  PREDICTION: mongo-rs0-2 (port 27018) should become PRIMARY (priority=3).\n" +
  "\n" +
  "  Reasoning:\n" +
  "    MongoDB elections favour the member with the HIGHEST priority, provided\n" +
  "    that member's oplog is sufficiently up to date.\n" +
  "    Priority 3 > Priority 2 > Priority 1\n" +
  "    → mongo-rs0-2 (27018) should win the election."
);

// ── 4. Verify prediction — rs.status() ────────────────────────────────────────
print("\n" + "=".repeat(70));
print("  VERIFICATION — rs.status()");
print("=".repeat(70));
var status = rs.status();
print("  Replica Set : " + status.set);
print();

var actualPrimary = null;
status.members.forEach(function(m) {
  if (m.stateStr === "PRIMARY") { actualPrimary = m.name; }
  print(
    "  [" + m._id + "] " +
    (m.name + "                              ").slice(0, 32) +
    "  state=" + (m.stateStr + "          ").slice(0, 10) +
    "  health=" + m.health
  );
});

print();
if (actualPrimary) {
  if (actualPrimary.indexOf("27018") !== -1) {
    print("  ✓ PREDICTION CORRECT! Primary is " + actualPrimary + " (priority=3)");
  } else {
    print("  ✗ PREDICTION INCORRECT — Primary is " + actualPrimary);
    print("  This may happen if 27018 had not yet caught up. Wait & recheck.");
  }
} else {
  print("  ⚠ No primary elected yet — wait a few more seconds and retry.");
}

// ── 5. Show priorities — rs.conf() ────────────────────────────────────────────
print("\n" + "=".repeat(70));
print("  PRIORITY SETTINGS — rs.conf()");
print("=".repeat(70));
var conf = rs.conf();
print("  Replica Set : " + conf._id);
print();
conf.members.forEach(function(m) {
  print(
    "  [" + m._id + "] " +
    (m.host + "                              ").slice(0, 32) +
    "  priority=" + m.priority +
    (m.priority === 3 ? "  ← HIGHEST (expected PRIMARY)" :
     m.priority === 2 ? "  ← medium" :
                        "  ← lowest")
  );
});

print("\n" + "=".repeat(70));
print("  Initialisation complete. Run activity_8_2_try.py to interact.");
print("=".repeat(70));
