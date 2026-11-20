// ─── Activity 8.2 — init_replicaset.js ───────────────────────────────────────
// Purpose:
//   Initiates the rs0 replica set with 3 data nodes.
//   Node priorities:  rs0-1 = 2 (preferred primary),
//                     rs0-2 = 1,  rs0-3 = 1.
//
// Usage:
//   mongosh --port 27017 init_replicaset.js
//
// Prerequisites:
//   All three containers must be running (docker-compose up -d).
// ──────────────────────────────────────────────────────────────────────────────

print("=".repeat(70));
print("  Initiating rs0 — 3-node replica set");
print("=".repeat(70));

// ── 1. Initiate replica set ───────────────────────────────────────────────────
var config = {
  _id: "rs0",
  members: [
    {
      _id: 0,
      host: "host.docker.internal:27017",
      priority: 2   // Highest priority → becomes PRIMARY first
    },
    {
      _id: 1,
      host: "host.docker.internal:27018",
      priority: 1
    },
    {
      _id: 2,
      host: "host.docker.internal:27019",
      priority: 1
    }
  ]
};

try {
  var result = rs.initiate(config);
  print("\n  rs.initiate() result:");
  printjson(result);
} catch (e) {
  // Replica set may already be initiated — log and continue
  print("\n  [WARN] rs.initiate() error (may already be initiated): " + e.message);
}

// ── 2. Wait for primary election ──────────────────────────────────────────────
print("\n  Waiting 15 seconds for PRIMARY election …");
sleep(15000);

// ── 3. Insert a test document ─────────────────────────────────────────────────
print("\n  Inserting test document into testdb.replication_test …");
try {
  db = db.getSiblingDB("testdb");
  var insertResult = db.replication_test.insertOne({
    source: "init_replicaset.js",
    message: "Replica set initialised successfully",
    activity: "8.2",
    created_at: new Date()
  });
  print("  ✓ Inserted _id: " + insertResult.insertedId);
} catch (e) {
  print("  [ERROR] Insert failed: " + e.message);
}

// ── 4. Print replica set status ───────────────────────────────────────────────
print("\n" + "=".repeat(70));
print("  REPLICA SET STATUS");
print("=".repeat(70));
var status = rs.status();
print("  Set name : " + status.set);
print("  My state : " + status.myState);
print();
status.members.forEach(function(m) {
  print(
    "  [" + m._id + "] " +
    (m.name + "                            ").slice(0, 32) +
    "  state=" + (m.stateStr + "          ").slice(0, 10) +
    "  health=" + m.health
  );
});

print("\n" + "=".repeat(70));
print("  Replica set rs0 is ready. Run activity_8_2.py to begin.");
print("=".repeat(70));
