// ============================================================
// Lab 8.1 – Replica Set Initialisation Script
// Run via:
//   mongosh --host localhost --port 27017 init_replicaset.js
// ============================================================

print("=================================================");
print("  Lab 8.1: Initialising 3-node Replica Set rs0");
print("=================================================\n");

// Step 1 – Initiate replica set
const cfg = {
  _id: "rs0",
  members: [
    { _id: 0, host: "host.docker.internal:27017", priority: 2 },  // preferred primary
    { _id: 1, host: "host.docker.internal:27018", priority: 1 },
    { _id: 2, host: "host.docker.internal:27019", priority: 1 }
  ]
};

print("Step 1 – rs.initiate():");
printjson(rs.initiate(cfg));

// Wait for election
print("\nWaiting 15 seconds for election to complete...");
sleep(15000);

// Step 2 – Status check
print("\nStep 2 – rs.status():");
const status = rs.status();
status.members.forEach(m => {
  print(`  Member: ${m.name}  |  State: ${m.stateStr}  |  Health: ${m.health}`);
});

// Step 3 – Insert a document on primary
print("\nStep 3 – Inserting test document into primary...");
const db = db.getSiblingDB("lab8db");
const result = db.replication_test.insertOne({
  message: "Hello from Lab 8.1 Replica Set!",
  insertedAt: new Date(),
  node: "primary"
});
print("  Inserted _id:", result.insertedId);

print("\nStep 4 – Verify on secondaries by running activity_8_1.py");
print("\nDone. Replica set is up and replicating.");
