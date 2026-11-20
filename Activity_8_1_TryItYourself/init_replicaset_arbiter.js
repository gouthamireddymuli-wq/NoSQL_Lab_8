// ==================================================================
// Lab 8.1 Try It Yourself – Add an Arbiter Node
// Run via:
//   mongosh --host localhost --port 27017 init_replicaset_arbiter.js
// ==================================================================

print("=======================================================");
print("  Lab 8.1 Try It Yourself: Replica Set with Arbiter");
print("=======================================================\n");

// 2 data-bearing nodes + 1 arbiter = 3 votes, odd quorum
const cfg = {
  _id: "rs0",
  members: [
    { _id: 0, host: "host.docker.internal:27017", priority: 2 },   // preferred primary
    { _id: 1, host: "host.docker.internal:27018", priority: 1 },   // secondary
    { _id: 2, host: "host.docker.internal:27020", arbiterOnly: true } // arbiter
  ]
};

print("Initiating replica set with arbiter...");
printjson(rs.initiate(cfg));

print("\nWaiting 15 seconds for election...");
sleep(15000);

print("\nFinal rs.status() member overview:");
rs.status().members.forEach(m => {
  const role = m.arbiterOnly ? "[ARBITER]" : "";
  print(`  [${m._id}] ${m.name}  State: ${m.stateStr}  Health: ${m.health} ${role}`);
});

print("\n------------------------------------------------------");
print("Why use an Arbiter?");
print("------------------------------------------------------");
print("An arbiter participates in elections (providing the");
print("crucial odd vote to break ties) but stores NO data.");
print("Benefits:");
print("  1. Maintains an odd number of voting members so a");
print("     majority can always be established without ties.");
print("  2. Costs almost no storage or RAM – ideal when you");
print("     need quorum without the expense of a full replica.");
print("  3. Prevents split-brain scenarios in a 2-node set.");
print("Limitation:");
print("  An arbiter cannot become primary and cannot serve");
print("  reads, so it offers NO extra redundancy for data.");
print("------------------------------------------------------");
