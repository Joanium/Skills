---
name: Branch Prediction
trigger: branch prediction, branch predictor, BHT, BTB, branch target buffer, bimodal predictor, two-bit saturating counter, gshare, tournament predictor, return address stack, RAS, branch misprediction, branch penalty, taken not taken
description: Fourth skill in the processor design pipeline. Read after Hazard Detection. Covers branch predictor microarchitecture from static prediction through two-bit counters, gshare, and tournament predictors, plus BTB and RAS design. Includes accuracy models and area–accuracy trade-offs.
prev_skill: 03-HazardDetectionForwarding.md
next_skill: 05-ALUDatapathDesign.md
---

# ROLE
You are designing the part of the processor that hides latency by guessing the future. A wrong guess costs cycles. A right guess costs nothing. You understand that every branch predictor is a statistical bet — and you pick the hardware table size and algorithm that wins the most bets per mm² of silicon.

# CORE PRINCIPLES
```
EVERY MISPREDICTION COSTS branch_penalty CYCLES — minimize frequency × penalty
PREDICTION AT FETCH — the predictor must fire at the same cycle as instruction fetch
MOST BRANCHES ARE PREDICTABLE — loops are taken 99%+, function returns are deterministic
BIGGER TABLES ≠ ALWAYS BETTER — cold entries hurt; capacity must match working set
RETURN ADDRESS STACK IS NEARLY PERFECT — use it; don't waste BTB slots on returns
SPECULATIVE EXECUTION REQUIRES RECOVERY — always define the rollback path
MEASURE BEFORE COMMITTING TO HARDWARE — benchmark with real code, not toy loops
```

# STEP 1 — STATIC PREDICTION (BASELINE)

```
ALWAYS-NOT-TAKEN:
  Predict every branch as not taken; fetch PC+4
  If branch is taken → flush 3 instructions, redirect PC to target
  Accuracy: ~60% (loops are usually taken — this loses on loop back edges)
  Penalty on miss: 3 cycles (5-stage, branch in EX)

ALWAYS-TAKEN:
  Predict every branch as taken → need branch target available at fetch time
  Requires BTB (Branch Target Buffer) to supply target before decode
  Accuracy: ~65% (loop back edges win; if-then-else still loses)

PREDICT-BACKWARD-TAKEN, FORWARD-NOT-TAKEN (BTFN):
  Backward branch (negative offset) → predict taken    (loops)
  Forward branch (positive offset)  → predict not taken (if-else)
  Accuracy: ~75%
  Cost: zero hardware — decode sign bit of branch offset
  This is the best static scheme; use as baseline before adding dynamic hardware.
```

# STEP 2 — ONE-BIT PREDICTOR (BIMODAL, DEPTH 1)

```
STRUCTURE:
  Table: 2^k entries, each holding 1 bit (T = taken, N = not taken)
  Index: low k bits of PC (PC[k+1:2] to skip byte-offset bits)
  At fetch: lookup table[PC[k+1:2]] → predict taken or not
  At resolve: update table[PC[k+1:2]] ← actual outcome

ONE-BIT PROBLEM — LOOP PATTERN:
  For a loop that iterates 100× then exits:
    Iterations 1–99: predict T (correct 99×)
    Iteration 100: predict T → actually N → MISS (update to N)
    Re-enter loop: predict N → actually T → MISS (update to T)
  2 misses per loop execution regardless of trip count → bad for tight inner loops
```

# STEP 3 — TWO-BIT SATURATING COUNTER (BIMODAL)

```
STATE MACHINE (per entry):
  Strongly Taken  (11) ──T──→ Strongly Taken
                       ──N──→ Weakly Taken
  Weakly Taken    (10) ──T──→ Strongly Taken
                       ──N──→ Weakly Not Taken
  Weakly Not Taken(01) ──T──→ Weakly Taken
                       ──N──→ Strongly Not Taken
  Strongly Not Taken(00)──T──→ Weakly Not Taken
                        ──N──→ Strongly Not Taken

  Prediction: state[1] == 1 → predict TAKEN
              state[1] == 0 → predict NOT TAKEN

STRUCTURE:
  Table:    2^k entries × 2 bits
  k = 12   → 4096 entries × 2 bits = 1 KB
  k = 14   → 16384 entries × 2 bits = 4 KB   (sweet spot for most benchmarks)
  Index:    PC[k+1:2]

LOOP BEHAVIOR (same 100-iteration loop):
  Steady state: Strongly Taken almost always
  At exit: Strongly Taken → Weakly Taken (miss) → now Weakly Taken
  Re-enter: predict Taken (correct immediately) — only 1 miss vs 2 for 1-bit
  Accuracy: ~85–89% on SPEC CPU workloads
```

# STEP 4 — BRANCH TARGET BUFFER (BTB)

```
PURPOSE:
  The predictor knows TAKEN or NOT TAKEN — but the TAKEN target address
  is not known until decode or EX in a basic pipeline.
  BTB caches the target address so fetch can redirect immediately.

STRUCTURE:
  Fully-associative or set-associative cache
  Each entry:
    Tag:    high bits of branch PC
    Target: 64-bit target address
    Valid:  1 bit

  Size:    512–4096 entries typical
  Lookup:  parallel with instruction fetch (same cycle)

BTB HIT:
  Predictor says TAKEN + BTB hit → use BTB.target as next PC immediately
  No extra cycles wasted

BTB MISS (branch not yet seen, or cold):
  Cannot predict target → fetch PC+4 → take penalty on first encounter
  On resolution: allocate BTB entry with (PC_branch → target)

BTB EVICTION:
  Use LRU or pseudo-LRU for associative BTBs
  Do NOT evict entries for frequently-seen branches
  Cold entries for one-shot branches waste capacity — irrelevant to accuracy

BTB FOR RETURNS:
  Returns have many possible targets (caller-dependent)
  BTB is poor for returns — use RAS instead (see Step 6)
```

# STEP 5 — GLOBAL HISTORY PREDICTOR (GSHARE)

```
MOTIVATION:
  Bimodal sees: each branch independently
  Global history sees: PATTERN of last N branches affects current branch
  Example: if previous branch was "array bounds check failed" → current branch
  for the loop-back is highly correlated.

GLOBAL HISTORY REGISTER (GHR):
  Width: N bits (N = 8–20 typical)
  Update: shift left by 1, insert actual outcome (1=taken, 0=not taken)
  GHR = history of last N branch outcomes, newest at LSB

GSHARE INDEXING:
  Index = GHR XOR PC[k+1:2]    (k = GHR width, N bits)
  Table: 2^N entries × 2-bit saturating counter

  XOR ensures that:
  - Same branch with different history → different table entry
  - Different branches with same history → different table entry (due to PC bits)

GSHARE ACCURACY: ~93–95% on SPEC INT with N=12, 4096-entry table

ALIASING PROBLEM:
  Two different (branch, history) pairs can XOR to same index → corrupt each other
  Solution: Use larger tables, or add partial tags (tagged geometric — TAGE predictor)
```

# STEP 6 — RETURN ADDRESS STACK (RAS)

```
PROBLEM:
  Function returns (JALR x0, x1, 0) are indirect — target is in ra register
  BTB predicts wrong when function called from multiple sites
  Accuracy of BTB for returns: as low as 50%

RAS STRUCTURE:
  Hardware stack, 8–32 entries typical (power-of-2)
  Each entry: 64-bit return address

RAS OPERATION:
  On CALL (JAL/JALR that writes ra):
    Push (PC + 4) onto RAS   ← the return address
    Predict as always-taken (target known from BTB or immediate)

  On RETURN (JALR x0, ra, 0 detected by opcode pattern):
    POP from RAS → use as predicted next PC
    Do NOT consult BTB for returns

RAS OVERFLOW:
  RAS depth exceeded (deeply recursive code) → oldest entry dropped
  Use wraparound: circular buffer with pointer, not a true stack
  Misprediction on underflow/overflow is rare in practice

RAS ACCURACY:
  ~99%+ for standard call/return patterns
  Degrades for longjmp, computed returns, coroutines — must detect + bail out

RAS REPAIR ON MISPREDICT:
  If speculative call was on a mispredicted path, RAS has a junk entry
  Solution: checkpoint RAS top pointer on every branch; restore on mispredict
  Small hardware cost — just save/restore a 5-bit pointer
```

# STEP 7 — TOURNAMENT (HYBRID) PREDICTOR

```
MOTIVATION:
  Bimodal is better for branches with simple, strongly biased behavior
  Global history is better for correlated, history-dependent branches
  Tournament uses a meta-predictor to choose which to trust

STRUCTURE:
  Predictor A: Bimodal (local, 2-bit counters)
  Predictor B: Gshare (global history, 2-bit counters)
  Choice table: 2^k entries × 2-bit saturating counter
    index = PC[k+1:2]
    state 11/10 → use Predictor A (bimodal)
    state 01/00 → use Predictor B (gshare)

UPDATE RULE:
  If A correct AND B wrong → increment choice counter toward A
  If B correct AND A wrong → decrement choice counter toward B
  If both correct OR both wrong → no update to choice table

ACCURACY:
  Alpha 21264-style tournament: ~97–98% on SPEC CPU2000
  Area cost: ~64 KB total table space

MODERN STATE OF THE ART: TAGE (Tagged Geometric)
  Multiple tables indexed by geometrically increasing history lengths
  Partial tags to reduce aliasing
  >99% accuracy on many workloads — used in modern x86 and ARM processors
  Too complex for initial implementation; document as upgrade path
```

# STEP 8 — RECOVERY AND SPECULATIVE EXECUTION

```
MISPREDICT RECOVERY PIPELINE (5-STAGE):

  Cycle N:    Branch reaches EX, condition evaluated, mispredict detected
  Cycle N:    EX raises mispredict signal + correct_pc to IF stage
  Cycle N+1:  IF fetches from correct_pc
              Pipeline flushes: IF/ID, ID/EX pipeline registers → NOP

  FLUSH MECHANISM:
    IF/ID.instruction ← NOP
    ID/EX.control     ← 0 (all-zero control signals = bubble)
    PC ← correct_pc

  CHECKPOINTING (for deeper pipelines / OoO):
    Save architectural state at each branch
    On mispredict: restore saved state
    In 5-stage in-order: simple flush is sufficient — no checkpointing needed

SPECULATIVE STATE:
  During speculation: results of post-branch instructions are in pipeline regs
  On mispredict: those values are discarded (pipeline regs overwritten by flush)
  No register file writes from speculative instructions in 5-stage
  (WB is reached only after branch is resolved — mathematically guaranteed in 5-stage)
```

# STEP 9 — AREA AND ACCURACY TRADE-OFF TABLE

```
  Predictor              Table Size   Area      SPEC Accuracy   Penalty/Kinsn
  ─────────────────────  ───────────  ────────  ──────────────  ─────────────
  Always Not Taken       0 bytes      Minimal   ~60%            ~60 cycles
  BTFN (static)          0 bytes      Minimal   ~75%            ~38 cycles
  Bimodal 1-bit (1K)     1 KB         Small     ~82%            ~27 cycles
  Bimodal 2-bit (4K)     1 KB         Small     ~87%            ~20 cycles
  Gshare N=12 (4K)       1 KB         Small     ~93%            ~11 cycles
  Tournament (Alpha)     64 KB        Medium    ~97%            ~5 cycles
  TAGE                   ~40 KB       Medium    ~99%            ~1.5 cycles

  RECOMMENDATION:
    Embedded, power-constrained:  2-bit bimodal 4K + RAS
    Mid-range processor:          Gshare 12-bit + BTB 1K + RAS 16
    High-performance:             Tournament or TAGE + BTB 4K + RAS 32
```

# CHECKLIST — Before Moving to ALU Design

```
✅ Static fallback baseline defined (BTFN minimum)
✅ 2-bit saturating counter state machine drawn and verified
✅ Bimodal table size chosen with justification (k bits → 2^k entries)
✅ BTB structure defined (entries, tag width, target width, associativity)
✅ RAS depth chosen, overflow/underflow policy defined
✅ RAS repair on mispredict defined (pointer checkpoint)
✅ Global history predictor (gshare) index function written
✅ Tournament meta-predictor update rule specified
✅ Mispredict recovery: flush mechanism described cycle by cycle
✅ Accuracy vs area trade-off table filled for chosen design point
→ NEXT: 05-ALUDatapathDesign.md
```
