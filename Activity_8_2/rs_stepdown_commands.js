// ─── Activity 8.2 — rs_stepdown_commands.js ──────────────────────────────────
// Purpose:
//   Triggers a replica-set election by stepping down the current PRIMARY.
//   Run this script while activity_8_2.py is monitoring so you can observe
//   the failover being detected in real time.
//
// Usage:
//   mongosh --port 27017 rs_stepdown_commands.js
//
// What happens:
//   1. The current primary is identified.
//   2. rs.stepDown() forces the primary to become a secondary and starts
//      an election among the remaining members.
//   3. After ~5 s the new primary is confirmed.
// ──────────────────────────────────────────────────────────────────────────────

print("=".repeat(70));
print("  rs_stepdown_commands.js — Trigger an Election");
print("=".repeat(70));

// ── Step 1: Check current state before step-down ─────────────────────────────
print("\n  BEFORE STEP-DOWN — rs.status():");
print("-".repeat(70));
var statusBefore = rs.status();
print("  Replica Set : " + statusBefore.set);
statusBefore.members.forEach(function(m) {
  print(
    "  [" + m._id + "] " +
    (m.name + "                             ").slice(0, 32) +
    "  state=" + (m.stateStr + "          ").slice(0, 10) +
    "  health=" + m.health
  );
});

// Identify current primary for the log
var currentPrimary = null;
statusBefore.members.forEach(function(m) {
  if (m.stateStr === "PRIMARY") { currentPrimary = m.name; }
});
print("\n  Current PRIMARY: " + (currentPrimary || "(none)"));

// ── Step 2: Step down the primary ────────────────────────────────────────────
print("\n  Calling rs.stepDown() — primary will step down for 60 s …");
print("  An election will be triggered immediately.");

try {
  rs.stepDown(60);   // stepdown period = 60 s
  print("  ✓ rs.stepDown() completed (connection may drop briefly).");
} catch (e) {
  // The shell connection is forcibly closed when the primary steps down;
  // this is expected and not a real error.
  if (e.message && e.message.match(/network|connection/i)) {
    print("  ✓ Connection reset — this is expected when the primary steps down.");
  } else {
    print("  [WARN] rs.stepDown() error: " + e.message);
  }
}

// ── Step 3: Wait for the election to complete ─────────────────────────────────
print("\n  Waiting 5 s for election to complete …");
sleep(5000);

// ── Step 4: Check new state after step-down ───────────────────────────────────
print("\n  AFTER STEP-DOWN — rs.status():");
print("-".repeat(70));
try {
  var statusAfter = rs.status();
  print("  Replica Set : " + statusAfter.set);

  var newPrimary = null;
  statusAfter.members.forEach(function(m) {
    if (m.stateStr === "PRIMARY") { newPrimary = m.name; }
    print(
      "  [" + m._id + "] " +
      (m.name + "                             ").slice(0, 32) +
      "  state=" + (m.stateStr + "          ").slice(0, 10) +
      "  health=" + m.health
    );
  });

  print("\n  New PRIMARY : " + (newPrimary || "(election still in progress)"));

  if (newPrimary && newPrimary !== currentPrimary) {
    print("  *** FAILOVER CONFIRMED: " + currentPrimary + " → " + newPrimary + " ***");
  } else if (!newPrimary) {
    print("  ⚠ No primary yet — wait a few more seconds and check rs.status().");
  }
} catch (e) {
  print("  [ERROR] Could not read status after step-down: " + e.message);
  print("  Wait a few seconds and run:  mongosh --port 27018 --eval 'rs.status()'");
}

print("\n" + "=".repeat(70));
print("  Election script complete.");
print("=".repeat(70));
