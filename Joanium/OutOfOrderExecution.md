---
name: Out-of-Order Execution
trigger: out of order execution, OoO, reorder buffer, ROB, reservation station, Tomasulo, register renaming, rename table, RAT, issue queue, commit, retirement, speculative execution, dynamic scheduling, in-flight instructions, ROB entry, superscalar
description: Tenth skill in the processor design pipeline. Covers the full OoO engine — frontend decode width, rename stage, reservation stations, reorder buffer, execution units, load/store queue, commit/retirement, and precise exceptions under speculation.
prev_skill: 09-MemoryHierarchyVirtualMemory.md
next_skill: 11-InterruptExceptionHandling.md
---

# ROLE
You are building a time machine. Out-of-order execution lets the processor look ahead, find independent work, and do it now — hiding the latency of cache misses, long-latency multiplies, and branch mispredictions. You understand that all speculative state must be recoverable, and that the commit point is the boundary between speculation and reality.

# CORE PRINCIPLES
```
INSTRUCTIONS EXECUTE OUT OF ORDER — they COMMIT in order (always)
REGISTER RENAMING ELIMINATES FALSE DEPENDENCIES — only RAW hazards remain real
ROB IS THE SPECULATIVE STATE CONTAINER — uncommitted results live here
RESERVATION STATIONS WAIT FOR OPERANDS — fire when all sources ready
PRECISE EXCEPTIONS REQUIRE IN-ORDER COMMIT — ROB head is the commit boundary
LOAD-STORE ORDERING IS THE HARDEST PROBLEM IN OoO — memory has dependencies
FRONT-END WIDTH DETERMINES IPC CEILING — you cannot issue what you don't decode
```

# STEP 1 — OoO ENGINE OVERVIEW

```
FRONTEND:              BACKEND:
  Fetch → Decode → Rename → Dispatch → [Issue Queues] → Execute → Complete → Commit

STAGE DETAIL:
  Fetch:     N instructions per cycle from I-cache (N = issue width)
  Decode:    Decode N instructions; expand macro-ops to micro-ops
  Rename:    Map logical registers → physical registers; eliminate false deps
  Dispatch:  Insert micro-ops into ROB and Reservation Stations
  Issue:     Fire micro-ops to execution units when operands ready
  Execute:   ALU, Load/Store Unit, FPU, Branch Unit execute
  Complete:  Write result to Physical Register File; broadcast to waiting RSes
  Commit:    ROB head retires in program order; update architectural state

TYPICAL WIDTHS (modern in-order OoO comparison):
  Intel Skylake:  4-wide decode, 4-wide issue, 97-entry ROB
  AMD Zen 4:      4-wide decode, 6-wide issue, 320-entry ROB
  Apple M2:       8-wide decode, 12-wide issue, 300+ entry ROB
  ARM Cortex-A55: 2-wide (for comparison, this is in-order)

DESIGN DECISION FOR IMPLEMENTATION:
  2-wide issue:  Easy; good starting point; achieves IPC ~1.5–2.0 on real code
  4-wide issue:  Standard; requires 32-entry ROB, 24-entry RS; IPC ~2.5–3.5
  8-wide issue:  Research/high-end; front-end bottleneck is dominant challenge
```

# STEP 2 — REGISTER RENAMING

```
PROBLEM REGISTER RENAMING SOLVES:
  WAR  (Write After Read):  I1 reads R1, I2 writes R1 → no real dep, but wrong order
  WAW  (Write After Write): I1 writes R1, I2 writes R1 → only last write matters
  These are false dependencies — renaming eliminates them

PHYSICAL REGISTER FILE (PRF):
  Size = architectural registers + in-flight instructions
  32 logical + 128 ROB entries = 160 physical registers minimum
  Each physical register: 64 bits + valid bit + ready bit

REGISTER ALIAS TABLE (RAT) — maps logical → physical:
  32 entries (one per architectural register)
  Each entry: physical register number (7–8 bits for 128-256 PRF entries)
  Updated: every time a new instruction writes a logical register

RENAME ALGORITHM (per instruction, per cycle, for N-wide):
  FOR EACH source register rs1, rs2:
    p_rs1 = RAT[rs1]   (look up current physical mapping)
  FOR destination register rd:
    p_rd = allocate_free_PRF_entry()   (from free list)
    old_mapping = RAT[rd]              (save to free at commit)
    RAT[rd] = p_rd                     (update RAT with new mapping)
    ROB.entry.old_phys = old_mapping   (store for freeing on commit)

  FREE LIST: FIFO of unused physical register indices
  Allocation: pop from free list; deallocation: push at commit

DEPENDENCY TRACKING:
  After rename: instruction knows its physical sources (p_rs1, p_rs2)
  Check PRF ready bit: is p_rs1 ready? → operand available
  If not ready: reservation station waits; wakeup on CDB broadcast

ARCHITECTURAL STATE (committed):
  Maintained implicitly as: follow RAT at commit boundary
  OR: keep a separate committed RAT that updates only on commit
  Committed RAT is used for mispredict recovery (restore from commit point)
```

# STEP 3 — REORDER BUFFER (ROB)

```
ROB STRUCTURE (circular buffer, in-program-order):
  Head pointer → oldest (next to commit)
  Tail pointer → newest (most recently dispatched)
  Size:    64–320 entries (larger = more ILP exposed; diminishing returns after ~128)

ROB ENTRY FIELDS:
  pc[63:0]         — program counter of instruction
  instruction[31:0]— original instruction (for precise exceptions)
  phys_rd[7:0]     — physical destination register
  old_phys_rd[7:0] — previous physical mapping (to free on commit)
  result[63:0]     — computed result (or written to PRF directly)
  ready            — execution complete; result valid
  exception        — exception pending (type + info)
  is_load          — instruction is a load
  is_store         — instruction is a store
  store_data[63:0] — data to write to memory (stores commit to memory at head)
  store_addr[63:0] — effective address of store

ROB OPERATIONS:
  Dispatch:  allocate ROB entry at tail; ROB index = instruction's "tag"
  Complete:  set ROB[tag].ready = 1; write result to PRF; broadcast on CDB
  Commit:    advance head; write to architectural state; free old physical reg
  Flush:     on mispredict or exception → restore RAT, reset tail to head

COMMIT CONDITIONS:
  ROB[head].ready == 1   (instruction has completed)
  No exception at ROB[head]
  Commit up to N instructions per cycle (= issue width)

EXCEPTION HANDLING:
  If ROB[head].exception set → take exception (precise — all prior instructions committed)
  Save mepc, mcause, mtval; flush ROB tail → head; restore RAT; jump to handler
```

# STEP 4 — RESERVATION STATIONS

```
RESERVATION STATION (RS) — Tomasulo-style:
  Holds instruction waiting for operands; issues to execution unit when ready

RS ENTRY FIELDS:
  valid         — entry in use
  opcode        — operation to perform
  p_rs1         — physical source reg 1 tag
  p_rs2         — physical source reg 2 tag
  rs1_val       — captured operand 1 value (if already ready)
  rs2_val       — captured operand 2 value (if already ready)
  rs1_ready     — operand 1 available
  rs2_ready     — operand 2 available
  rob_tag       — which ROB entry this instruction belongs to
  imm           — immediate value

RS SIZE:
  4-wide issue: 32–48 RS entries (8–12 per execution unit cluster)
  Larger RS → more instructions considered for issue → higher ILP

WAKEUP-AND-SELECT LOGIC:
  WAKEUP: When execution unit completes (broadcasts p_rd on CDB):
    All RS entries compare: if (p_rs1 == CDB.tag) → rs1_ready=1; capture value
    Same for p_rs2
  SELECT: Each cycle, pick which ready RS entry issues to which EU:
    Ready = rs1_ready && rs2_ready
    Priority: oldest ready instruction (age-based) or round-robin

UNIFIED vs DISTRIBUTED RS:
  Unified:      One large RS, any EU pulls from it; maximum flexibility
  Distributed:  One RS per EU type (integer RS, FP RS, LD/ST RS)
                Less flexible; simpler routing; used in most modern processors

ISSUE PORTS:
  Each execution unit has one issue port
  N EUs → N issue ports → N instructions can issue simultaneously
  Must not issue more than one instruction to the same EU per cycle
```

# STEP 5 — EXECUTION UNITS AND WAKEUP

```
TYPICAL EXECUTION UNIT COMPLEMENT (4-wide integer OoO):
  Port 0: Integer ALU 0 (add, logic, shifts)
  Port 1: Integer ALU 1 (add, logic, shifts) — second ALU for ILP
  Port 2: Load/Store Unit (address calc → D-cache access)
  Port 3: Branch Unit + Integer ALU 3
  Port 4: Multiply Unit (2–4 cycle latency, pipelined)
  Port 5: Divide Unit (16–64 cycle latency, non-pipelined)

EXECUTION LATENCIES (affects RS scheduling):
  Integer ALU:  1 cycle  (result ready next cycle — fast wakeup)
  Load (hit):   4–5 cycles (cache access)
  Load (miss):  10–300 cycles (L2 or DRAM — non-blocking)
  Multiply:     3–5 cycles (pipelined)
  FP add/mul:   3–5 cycles
  Divide:       16–64 cycles
  Branch:       1 cycle (condition eval)

COMMON DATA BUS (CDB):
  Broadcast medium connecting execution units to RS wakeup logic and PRF
  Every cycle: completed results broadcast (tag, value, ready)
  CDB width: 1 broadcast per execution port per cycle
  4 EUs → 4 CDB slots; RS must compare against all 4 in parallel

OUT-OF-ORDER COMPLETION ORDER:
  A fast ALU instruction can complete before a slow load that was issued earlier
  This is fine — PRF updated out of order
  But COMMIT happens in order (ROB enforces program order at retirement)
```

# STEP 6 — LOAD/STORE QUEUE (LSQ)

```
MEMORY ORDERING IS THE HARDEST PART OF OoO:
  Loads and stores must appear to execute in program order to memory
  BUT: loads can speculatively read before earlier stores resolve (if no alias)

LOAD QUEUE (LQ):
  Holds all in-flight loads (dispatched but not committed)
  Fields per entry: valid, pc, phys_addr, data, ready, rob_tag

STORE QUEUE (SQ):
  Holds all in-flight stores (address and data may arrive at different times)
  Fields per entry: valid, phys_addr (may be unknown), data (may be unknown),
                    addr_ready, data_ready, committed, rob_tag

MEMORY DEPENDENCY DETECTION:
  When a load executes:
    Search SQ for older stores with same address (store-to-load forwarding)
    If older store with same addr has data ready → forward data (no D-cache needed)
    If older store same addr but data not ready → must wait (stall load)
    If no alias → proceed to D-cache (speculative load)

  MEMORY ORDERING VIOLATION:
    Store completes address after a younger load already executed with same address
    → Must squash younger load and all subsequent instructions
    → Reload from correct value, reissue from squash point
    This is a memory ordering misspeculation — expensive; must minimize

STORE-TO-LOAD FORWARDING:
  SQ ordered search: newest matching store wins (most recent program-order store)
  Partial forwarding: handle byte/halfword subsets of a full store (complex)
  Simplification: if sizes don't match → stall; don't forward

COMMIT OF STORES:
  Stores must NOT write to memory until they reach ROB head (committed)
  Before commit: store data lives only in SQ
  At commit: move store from SQ to store buffer → drain to D-cache in order
```

# STEP 7 — MISPREDICT AND EXCEPTION RECOVERY

```
BRANCH MISPREDICT RECOVERY:
  1. Branch detected in ROB (or Branch Unit)
  2. Flush all ROB entries after the mispredicted branch
     → Reset ROB tail to (branch ROB index + 1)
  3. Restore RAT from committed RAT checkpoint (saved at dispatch or commit)
  4. Free physical registers allocated after the branch (from free list)
  5. Flush all RS entries with rob_tag > branch_rob_tag
  6. Flush pipeline stages (fetch, decode, rename buffers)
  7. Set PC to correct target → resume fetch

  RECOVERY LATENCY:
    Detection at execute: ~5–10 cycles (frontend decode → rename → execute)
    Add: ROB flush + RAT restore: ~2–4 cycles
    Total: 10–20 cycles of wasted work (branch penalty in OoO)

PRECISE EXCEPTION:
  Exception detected at ROB head → all prior instructions committed → precise
  Flush entire ROB tail → free all speculative physical registers
  Restore RAT to committed RAT state
  Save mepc, mcause; jump to trap handler
  On return (MRET): restore speculative state from OS-restored context

CHECKPOINT-BASED RECOVERY (alternative for wide/deep OoO):
  At every branch dispatch: take snapshot of full RAT state
  On mispredict: restore full RAT snapshot in 1 cycle (no need to walk ROB)
  Trade-off: snapshot storage = N_branches_in_flight × 32 × log2(PRF) bits
  For 40 in-flight branches × 32 entries × 8 bits = 10 KB — feasible
```

# STEP 8 — FRONT-END BOTTLENECK

```
FRONT-END IS THE IPC CEILING:
  OoO backend can only execute what the front-end supplies
  Branch mispredicts, I-cache misses, decode complexity all limit supply

FETCH UNIT:
  Fetch N instructions aligned to cache line boundary (complex in variable-width ISA)
  RISC: straightforward (fixed 32-bit)
  x86: pre-decode to find instruction boundaries before decode

BRANCH PREDICTION AT FETCH:
  Predict direction + target BEFORE decode (BTB + predictor, see skill 04)
  Fetch from predicted target next cycle (speculative)
  Must handle: taken branch mid-fetch-group (partial fetch groups)

DECODE:
  Decode N instructions per cycle → N µops per cycle
  For simple ISA: 1 instruction = 1 µop (easy)
  For complex ISA: 1 instruction = 1–N µops (micro-op expansion; variable throughput)

INSTRUCTION QUEUE (between decode and rename):
  Absorbs bubbles from branch mispredicts during recovery
  Size: 16–32 entries; larger = more misprediction hiding

LOOP STREAM DETECTOR (LSD):
  Small buffer of ~28 µops that re-executes tight loops without fetching
  Powers Intel's loop stream detector (LSD) — reduces I-cache pressure for hot loops
```

# CHECKLIST — Before Moving to Interrupt/Exception Handling

```
✅ Issue width chosen (2, 4, or 8-wide) with IPC target
✅ PRF size = logical_regs + ROB_size; free list implemented
✅ RAT structure: 32 entries → physical reg index; committed RAT for recovery
✅ ROB size chosen; all entry fields listed
✅ ROB commit: up to N per cycle in order; exception check at head
✅ RS size and per-EU distribution chosen
✅ Wakeup logic: CDB broadcast → RS tag match → capture value
✅ Execution units listed with latencies
✅ LQ and SQ sizes chosen; store-to-load forwarding defined
✅ Memory ordering violation: squash + reload procedure
✅ Branch mispredict recovery: RAT restore + ROB flush procedure
✅ Precise exception: commit-point guarantee → trap
✅ Front-end width = backend width (no fetch bottleneck)
→ NEXT: 11-InterruptExceptionHandling.md
```
