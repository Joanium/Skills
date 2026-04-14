---
name: Consensus Algorithms
trigger: consensus, Raft, Paxos, Byzantine fault tolerance, BFT, PBFT, leader election, distributed consensus, split brain, quorum, log replication, state machine replication, two-phase commit, three-phase commit, viewstamped replication, distributed systems correctness, FLP impossibility, CAP theorem
description: Design and implement distributed consensus algorithms. Covers Raft (leader election, log replication, membership changes), Paxos, Byzantine fault tolerance (PBFT), quorum design, and the theoretical limits of distributed consensus.
---

# ROLE
You are a distributed systems engineer specializing in consensus and fault tolerance. You understand the fundamental limits of distributed computing and implement algorithms that keep clusters consistent despite crashes, network partitions, and (when needed) malicious nodes.

# CORE PRINCIPLES
```
FLP IMPOSSIBILITY — no deterministic consensus in async systems with even one crash
CAP THEOREM — consistent + available + partition-tolerant: pick two
MAJORITY QUORUMS — any two majorities overlap; f failures need 2f+1 nodes
BYZANTINE NEEDS 3f+1 — to tolerate f traitors, need 3f+1 nodes (not 2f+1)
LEADER-BASED SIMPLIFIES — leader handles ordering; followers validate
SAFETY > LIVENESS — never return wrong answer; occasionally return none
```

# THEORETICAL FOUNDATIONS

## FLP Impossibility
```
Fisher, Lynch, Paterson (1985):
  In an asynchronous system where even ONE process may crash,
  there is no deterministic algorithm that always reaches consensus.

Implication: all real consensus algorithms must make additional assumptions:
  → Raft/Paxos: assume partial synchrony (messages eventually delivered)
  → PBFT: assume less than 1/3 of nodes are Byzantine
  → Bitcoin PoW: randomized; probabilistic finality
```

## CAP Theorem
```
CP (Consistent + Partition-tolerant): stop responding during partitions
  → Raft, Paxos, PBFT, HBase
  → "I'll wait until I can guarantee consistency"

AP (Available + Partition-tolerant): respond with possibly stale data
  → Cassandra (tunable), DynamoDB, CouchDB
  → "I'll give you the best answer I have right now"

PRACTICAL NUANCE (PACELC):
  Even when no partition, systems trade off Latency vs Consistency (ELC part)
  This matters more day-to-day than partition handling
```

## Quorum Mathematics
```
n = total nodes
f = max failures to tolerate
w = write quorum
r = read quorum

For fault tolerance:
  n ≥ 2f + 1  (for crash fault tolerance; majority = f+1)
  n ≥ 3f + 1  (for Byzantine fault tolerance)

For consistency (read-your-writes):
  r + w > n   (read and write quorums must overlap)

Examples (n=5, f=2):
  Majority quorum: w=3, r=3  → read + write quorum overlap guaranteed
  Fast read quorum: w=5, r=1 → all writes confirmed, single-node reads OK
```

# RAFT CONSENSUS

## Algorithm Overview
```
Three server states:
  FOLLOWER:  passive; replicate log; become candidate if no heartbeat
  CANDIDATE: seeking votes; sends RequestVote to all peers
  LEADER:    handles all client requests; sends heartbeats; replicates log

Term = logical clock
  Each election increments the term
  Stale messages with old term are rejected

Leader Election:
  1. Follower times out (no heartbeat): becomes candidate, increments term
  2. Votes for self, sends RequestVote(term, candidateId, lastLogIndex, lastLogTerm)
  3. Peers vote YES if: term ≥ their term AND candidate's log is at least as up-to-date
  4. First to get majority (n/2 + 1 votes) wins; sends AppendEntries heartbeats immediately

Log Replication:
  1. Client sends command to leader
  2. Leader appends to local log (uncommitted)
  3. Leader sends AppendEntries to all followers
  4. Once majority ACK: leader commits; applies to state machine; responds to client
  5. Committed entries propagate to followers in next heartbeat

Safety Guarantee:
  Once committed to majority, an entry can never be overwritten
  A leader always has all committed entries (Log Matching Property)
```

## Raft in Python (simplified)
```python
import random, time, threading
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional

class State(Enum):
    FOLLOWER = 'follower'
    CANDIDATE = 'candidate'
    LEADER = 'leader'

@dataclass
class LogEntry:
    term:    int
    command: str
    index:   int

class RaftNode:
    def __init__(self, node_id: str, peers: list[str]):
        self.id           = node_id
        self.peers        = peers
        self.state        = State.FOLLOWER
        self.current_term = 0
        self.voted_for:   Optional[str] = None
        self.log:         list[LogEntry] = []
        self.commit_index = 0
        self.last_applied = 0
        self.votes_received = 0
        
        # Leader-only state
        self.next_index:  dict[str, int] = {}
        self.match_index: dict[str, int] = {}
        
        self.election_timeout = random.uniform(0.15, 0.30)  # 150-300ms
        self.last_heartbeat   = time.time()

    def on_heartbeat_timeout(self):
        if time.time() - self.last_heartbeat > self.election_timeout:
            self.start_election()

    def start_election(self):
        self.state         = State.CANDIDATE
        self.current_term += 1
        self.voted_for     = self.id
        self.votes_received = 1  # vote for self

        last_log_index = len(self.log)
        last_log_term  = self.log[-1].term if self.log else 0

        # Send RequestVote to all peers (in real impl: via RPC)
        for peer in self.peers:
            self._send_request_vote(peer, self.current_term, last_log_index, last_log_term)

    def on_request_vote(self, term, candidate_id, last_log_index, last_log_term) -> bool:
        if term < self.current_term:
            return False  # stale term

        if term > self.current_term:
            self.current_term = term
            self.state = State.FOLLOWER
            self.voted_for = None

        # Grant vote if: haven't voted (or voted for this candidate) AND log is up-to-date
        my_last_term  = self.log[-1].term if self.log else 0
        my_last_index = len(self.log)
        log_ok = (last_log_term > my_last_term or
                  (last_log_term == my_last_term and last_log_index >= my_last_index))

        if (self.voted_for is None or self.voted_for == candidate_id) and log_ok:
            self.voted_for     = candidate_id
            self.last_heartbeat = time.time()
            return True
        return False

    def on_vote_received(self, term, vote_granted):
        if self.state != State.CANDIDATE or term != self.current_term:
            return
        if vote_granted:
            self.votes_received += 1
            if self.votes_received > (len(self.peers) + 1) / 2:
                self.become_leader()

    def become_leader(self):
        self.state = State.LEADER
        for peer in self.peers:
            self.next_index[peer]  = len(self.log) + 1
            self.match_index[peer] = 0
        self.send_heartbeats()

    def append_entries(self, command: str) -> int:
        """Client interface: append command and wait for commit."""
        if self.state != State.LEADER:
            raise Exception("Not leader")
        entry = LogEntry(self.current_term, command, len(self.log) + 1)
        self.log.append(entry)
        self._replicate_to_followers()
        return entry.index
```

## Raft Membership Changes
```
ADDING A NODE (Joint Consensus approach):
  Phase 1: Leader commits C_old,new (joint config: quorum of BOTH old AND new)
  Phase 2: Leader commits C_new (quorum only from new config)
  During joint phase: decisions require majority of both old AND new config

SINGLE-SERVER CHANGES (simpler):
  Only change one server at a time
  Adding a server: add as non-voting learner first, replicate log, then grant vote
  Removing a server: commit config without the server; new leader must be from new config

LEADER STEP-DOWN:
  If leader is removed from cluster:
    After committing C_new, it steps down (won't count its own vote)
    Immediately another server triggers election
```

# PAXOS

## Basic Paxos (Single Value)
```
Roles: Proposers, Acceptors, Learners

Phase 1 (Prepare):
  Proposer sends Prepare(n) to majority of acceptors
  Acceptor promises not to accept proposals numbered < n
  Acceptor returns (n_accepted, v_accepted) if it has accepted any proposal

Phase 2 (Accept):
  If proposer receives promises from majority:
    Propose value = v_accepted from highest n_accepted (if any), else own value
    Send Accept(n, value) to acceptors
  Acceptor accepts if it hasn't promised to ignore n
  Once majority accept: value is chosen

MULTI-PAXOS (for log replication):
  Skip Phase 1 for subsequent slots if leader is stable
  Leader = proposer that won Phase 1 for all future slots
  Effectively becomes similar to Raft once stable leader elected
```

# BYZANTINE FAULT TOLERANCE

## PBFT — Practical Byzantine Fault Tolerance
```
n = 3f + 1 minimum (f = max Byzantine nodes)
Example: 4 nodes tolerates 1 Byzantine; 7 nodes tolerates 2

Three-phase protocol:
  PRE-PREPARE:  Primary sends <PRE-PREPARE, v, n, m> to all replicas
                v = view (election term), n = sequence number, m = request

  PREPARE:      Replica broadcasts <PREPARE, v, n, digest(m)>
                Once 2f+1 PREPARE messages received: "prepared"

  COMMIT:       Replica broadcasts <COMMIT, v, n, digest(m)>
                Once 2f+1 COMMIT messages received: execute and reply to client

VIEW CHANGE (like Raft leader election):
  If primary appears faulty, replicas vote to change the view
  Requires 2f+1 replicas to agree on new view

COST:
  O(n²) messages per request — expensive at large scale
  Modern BFT (HotStuff, Tendermint): O(n) using threshold signatures
```

## When to Use BFT
```
USE BFT WHEN:
  → Public blockchain (unknown, potentially adversarial validators)
  → Auditable systems requiring protection from admin corruption
  → Cross-organization consensus where no single party is trusted

DON'T USE BFT WHEN:
  → Internal cluster (trust your own servers)
  → Crash fault tolerance (CFT) is sufficient
  → Performance matters and you can trust node operators

BFT PROTOCOLS:
  PBFT:       Original; O(n²); works well for n<20
  HotStuff:   Linear BFT; used in Diem/Libra, Tendermint-like
  Tendermint: BFT; used in Cosmos, deterministic finality
  Casper FFG: Ethereum PoS finality gadget
```

# IMPLEMENTATION DECISION GUIDE
```
SYSTEM REQUIREMENTS → RECOMMENDED ALGORITHM

Small cluster (3–7 nodes), crash failures only:
  → Raft (simple, well-documented, etcd/CockroachDB use it)

Large cluster, crash failures only, performance critical:
  → Multi-Paxos or EPaxos (parallel proposals, no leader bottleneck)

Small cluster, Byzantine tolerance needed, private:
  → PBFT or HotStuff

Public blockchain / unknown validators:
  → Tendermint (BFT) or PoS with finality gadget

Eventually consistent, high availability priority:
  → Gossip + CRDTs (no consensus needed; no strong consistency)

QUORUM SIZING:
  3 nodes: tolerates 1 crash   (majority = 2)
  5 nodes: tolerates 2 crashes (majority = 3)
  7 nodes: tolerates 3 crashes (majority = 4)
  BFT: 4 nodes tolerates 1 Byzantine (3f+1=4)
       7 nodes tolerates 2 Byzantine (3f+1=7)
```

# PRODUCTION LIBRARIES
```
Raft:
  etcd (Go):        Production raft via etcd/raft library
  hashicorp/raft:   Go; used by Consul, Vault, Nomad
  openraft (Rust):  Modern Raft implementation
  ratis (Java):     Apache Ratis; high-performance

Paxos:
  Apache ZooKeeper: ZAB protocol (Paxos-like)
  Chubby (Google):  Internal, inspired open-source alternatives

BFT:
  Tendermint (Go):  Used in Cosmos ecosystem
  HotStuff:         Meta's Diem/Libra implementation
  BFT-SMaRt (Java): Research-grade PBFT implementation
```
