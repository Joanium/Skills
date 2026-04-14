---
name: Cache Design
trigger: cache, L1 cache, L2 cache, cache miss, cache hit, direct mapped, set associative, fully associative, cache line, cache block, tag index offset, write back, write through, cache replacement, LRU, PLRU, cache coherence, VIPT, PIPT, cache miss penalty
description: Eighth skill in the processor design pipeline. Covers cache geometry decisions, tag/index/offset decomposition, associativity trade-offs, replacement policies, write policies, miss handling, and the structural integration of L1-I and L1-D caches into the pipeline.
prev_skill: 07-ControlUnitDesign.md
next_skill: 09-MemoryHierarchyVirtualMemory.md
---

# ROLE
You are bridging the ~100× speed gap between the processor and main memory. Every cache design decision is a trade-off between hit rate, hit latency, area, and power. You size each cache level to its working set, pick associativity that eliminates conflict misses, and define the exact tag/index/offset split before any RTL is written.

# CORE PRINCIPLES
```
CACHE IS AN ILLUSION OF FAST MEMORY — it only works if it hits
HIT LATENCY IS ON THE CRITICAL PATH — don't add associativity beyond what's needed
MISS PENALTY DOMINATES PERFORMANCE — optimize for miss rate × penalty product
SEPARATE I-CACHE AND D-CACHE — structural hazard elimination (Harvard L1)
WRITE POLICY DETERMINES COHERENCE COMPLEXITY — write-back is standard for L1
CACHE LINE SIZE IS A SPATIAL LOCALITY BET — too small = many misses; too large = wasted bandwidth
COLD VS CONFLICT VS CAPACITY — know which miss type dominates before adding ways
```

# STEP 1 — CACHE GEOMETRY PARAMETERS

```
PARAMETERS TO DECIDE:
  C   = cache capacity (bytes)
  B   = block/line size (bytes)
  E   = associativity (ways per set)
  S   = number of sets = C / (B × E)

ADDRESS DECOMPOSITION:
  For a 64-bit virtual/physical address:
    Offset bits  b = log2(B)    → selects byte within block
    Index  bits  s = log2(S)    → selects cache set
    Tag    bits  t = addr_width - s - b

  EXAMPLE — 32 KB, 4-way, 64-byte lines:
    C = 32768, B = 64, E = 4, S = 32768 / (64×4) = 128
    b = log2(64) = 6   → bits [5:0]
    s = log2(128) = 7  → bits [12:6]
    t = 64 - 7 - 6 = 51 → bits [63:13]

CACHE SIZE SELECTION GUIDELINES:
  Level   Typical Size   Latency Target   Purpose
  ──────  ─────────────  ───────────────  ─────────────────────
  L1-I    16–64 KB       1–4 cycles       Instruction supply
  L1-D    16–64 KB       4–5 cycles       Data loads/stores
  L2      256 KB–2 MB    10–20 cycles     Unified second-level
  L3      4 MB–64 MB     30–60 cycles     Last-level, shared
  LLC     64 MB+         50–100+ cycles   Server-class designs

BLOCK SIZE SELECTION:
  16 bytes   — minimal spatial locality, good for pointer-chasing workloads
  32 bytes   — balanced for mixed workloads
  64 bytes   — standard; matches DRAM burst length on most modern buses
  128 bytes  — high spatial locality (matrix ops, streaming) — more bus bandwidth
```

# STEP 2 — ASSOCIATIVITY TRADE-OFFS

```
DIRECT MAPPED (E=1):
  Each address maps to exactly one cache set
  Pros:   Fastest hit path (no comparator OR tree), lowest area
  Cons:   High conflict miss rate (two addresses with same index → thrash)
  Use:    Instruction caches in deeply embedded systems; L2 tag arrays

2-WAY SET ASSOCIATIVE:
  Each set holds 2 blocks; comparators run in parallel
  Hit rate improvement: significant over direct-mapped
  Latency increase: small (one extra comparator per set)
  Use:    Good all-around choice for embedded L1

4-WAY SET ASSOCIATIVE:
  Standard for high-performance L1 D-cache
  Hit rate within 1–2% of fully associative for most workloads
  Area: 4 comparators per set; manageable

8-WAY:
  Common for L2 and L3 caches
  Diminishing hit rate returns vs 4-way for most workloads
  Higher set-associativity helps with OS page coloring avoidance

FULLY ASSOCIATIVE:
  Any block can go anywhere
  Highest hit rate, lowest conflict misses
  Impractical for large caches (need N comparators where N = total blocks)
  Use:    TLBs (small, 32–128 entries); victim caches (4–16 entries)

RULE OF THUMB:
  Conflict miss-dominated → increase associativity
  Capacity miss-dominated → increase total cache size
  Cold miss-dominated → increase block size (more spatial prefetch)
```

# STEP 3 — TAG ARRAY AND DATA ARRAY ORGANIZATION

```
CACHE ARRAY STRUCTURE (per set):

  SET 0:  [Valid|Dirty|Tag(51b)] [Data(512b)] | [Valid|Dirty|Tag(51b)] [Data(512b)] | ... (E ways)
  SET 1:  ...
  ...
  SET 127:...

TAG ARRAY:
  S × E entries
  Each entry: valid(1) + dirty(1) + tag(t bits)
  Total tag array: 128 × 4 × (1+1+51) = 27,136 bits ≈ 3.3 KB (for 32KB 4-way example)
  Read: all E tags in a set read in parallel, compared with address tag
  Critical path: SRAM read + 4 comparators + priority encoder + hit/miss signal

DATA ARRAY:
  S × E × B entries = 128 × 4 × 64 = 32768 bytes = 32 KB
  Read: all E data blocks in set pre-read OR read only hit way (saves power)
  Options:
    Way-prediction: guess the hit way, read only that way → 1 cycle if right
    All-ways read:  read all E ways in parallel → always 1 cycle, more power

HIT DETECTION TIMELINE (4-way, 64B line, 32KB):
  Cycle 0: Send index[12:6] to cache SRAM → start read
  Cycle 0: Send tag[63:13] into comparator pipeline
  Cycle 1: SRAM output valid; 4 comparators check tag vs stored tags
  Cycle 1: Generate hit_way (one-hot: which of 4 ways hit)
  Cycle 1: Mux data array output for hit way → send to pipeline
  TOTAL: 1-cycle hit (if SRAM is fast enough for the clock period)

SRAM ACCESS TIME AT 28nm:
  32KB SRAM array: ~0.8 ns access time = 2 cycles at 2.5 GHz, 1 cycle at 1 GHz
  L1 must be physically small enough for 1-cycle access at target frequency
```

# STEP 4 — REPLACEMENT POLICIES

```
RANDOM:
  Randomly select a victim way
  Pros: No state needed, simple hardware
  Cons: Occasionally evicts hot lines
  Use: Acceptable for E ≥ 8; uncommon for L1

LEAST RECENTLY USED (LRU):
  Evict the way not accessed for the longest time
  Optimal for recency-based access patterns (Belady-optimal in the limit)
  State: log2(E!) bits per set (for true LRU)
  For 4-way: 4! = 24 states → ceil(log2(24)) = 5 bits per set

PSEUDO-LRU (PLRU) — TREE-BASED:
  Binary tree with E-1 bits per set (E must be power of 2)
  For 4-way: 3 bits per set (tree with 3 internal nodes)
  Update: flip bits on the path to the accessed way (point away)
  Evict: follow bits toward the victim (LRU approximation)
  Hit rate within 1–2% of true LRU; used in most real processors

  PLRU tree for 4-way (bit 0 = root, bit 1 = left subtree, bit 2 = right):
    Access way 0: bit0=1, bit1=1   (point away from way 0)
    Access way 1: bit0=1, bit1=0
    Access way 2: bit0=0, bit2=1
    Access way 3: bit0=0, bit2=0
    Evict: follow 0-bits down tree

NOT-MOST-RECENTLY-USED (NMRU):
  Track only the most recently used way (1 bit per way)
  Evict any way that isn't MRU (random among non-MRU)
  Very cheap state, reasonable performance

RECOMMENDATION:
  L1 (2–4 way):  PLRU (3 bits for 4-way; trivial for 2-way)
  L2 (8 way):    PLRU or LRU approximation
  L3 (8–16 way): Static Re-reference Interval Prediction (RRIP) for mixed workloads
```

# STEP 5 — WRITE POLICIES

```
WRITE HIT POLICIES:
  Write-Through:
    On every store, write both cache AND memory simultaneously
    Pros: Simple, always coherent, no dirty bit needed
    Cons: Memory bus traffic = every store (very high bandwidth demand)
    Use: L1-D in simple embedded designs, or with a write buffer

  Write-Back:
    On store hit: write cache only; mark line dirty
    On eviction: if dirty → write back to next level
    Pros: Much lower bus traffic (amortizes many writes to one line)
    Cons: Requires dirty bit, more complex eviction, coherence harder
    Use: Standard for all performance-oriented caches (L1, L2, L3)

WRITE MISS POLICIES:
  Write-Allocate:
    On store miss: fetch block from memory into cache, then write
    Pairs naturally with write-back (fetch → write in cache → evict later)
    Use: Any write-back cache

  No-Write-Allocate:
    On store miss: write directly to next level, don't fetch to cache
    Pairs with write-through
    Use: Streaming writes (no temporal locality)

DIRTY BIT:
  1 bit per cache line indicating the line has been modified
  Must be written back before eviction if dirty == 1
  Miss with dirty eviction:
    1. Write dirty line to next level (dirty eviction)
    2. Fetch new line from next level
    3. Insert new line into cache

WRITE BUFFER:
  Small FIFO (4–16 entries) between L1 and L2 for write-through caches
  Decouples write latency from pipeline: store enters buffer in 1 cycle
  Buffer drains to L2 in background
  On read miss: check write buffer first (load-store forwarding from WB)
```

# STEP 6 — MISS HANDLING AND MSHR

```
MISS STATUS HOLDING REGISTERS (MSHRs):
  Track outstanding cache misses to memory
  Allow non-blocking cache: pipeline continues on miss if no dependency

  MSHR ENTRY:
    valid           = 1 (entry in use)
    address         = cache line address of outstanding miss
    word_offset     = which word in line caused the miss
    destination_reg = register to write when data returns (for loads)
    type            = load or store (determines action on fill)

  MSHR COUNT:
    In-order 5-stage: only 1 outstanding miss at a time (pipeline stalls)
    → No MSHR needed; just stall pipeline until fill complete
    OoO processor: 8–32 MSHRs to support many in-flight misses

MISS PENALTY:
  L1 miss → L2 hit:       10–20 cycles
  L1 miss → L3 hit:       30–60 cycles
  L1 miss → DRAM access:  100–300 cycles

IN-ORDER MISS HANDLING (5-stage):
  Load issues, misses L1 → stall signal sent to PC, IF/ID, ID/EX
  L2 fetches block (10–20 cycles)
  Fill: write new block into L1 data and tag arrays
  Release stall → pipeline resumes from stalled load
```

# STEP 7 — VIRTUALLY INDEXED, PHYSICALLY TAGGED (VIPT)

```
ADDRESS TRANSLATION CHALLENGE:
  Virtual address available immediately at EX → can index cache
  Physical address from TLB → needed for tag comparison (takes 1 cycle)

  Strategy 1: PIPT (Physically Indexed, Physically Tagged)
    Wait for TLB → then access cache → 2 cycles total
    Simple, no aliasing, no synonym problem
    Too slow for L1 at high frequency

  Strategy 2: VIPT (Virtually Indexed, Physically Tagged) — PREFERRED
    Index cache with virtual address[s+b-1:b] simultaneously with TLB lookup
    Compare physical tag (from TLB) against cache tag (from SRAM) in parallel
    Hit detection: 1 cycle (parallel TLB + cache access)

  VIPT ALIASING CONDITION:
    If index bits overlap the page offset bits → no aliasing risk
    Page offset = 12 bits (4KB page)
    For 32KB 4-way, s+b = 7+6 = 13 bits → bit 12 is in the index
    Bit 12 differs between virtual and physical if VA[12] != PA[12] → ALIASING

  AVOIDING VIPT ALIASING:
    Option A: Increase associativity until index bits fit in page offset
      E = 8-way, S = 64, s = 6, s+b = 12 → all index bits in offset → safe
    Option B: Use page coloring (OS ensures VA[12] == PA[12])
    Option C: Add synonym detection hardware (complex; avoid)

  RECOMMENDATION: Design L1-D as VIPT with index bits within page offset:
    C ≤ E × page_size   → no aliasing
    32KB 8-way: 32KB/8 = 4KB sets × 64B lines = fits in 4KB page → safe
    64KB 4-way: 64KB/4 = 16KB > 4KB → aliasing risk → use 8-way instead
```

# STEP 8 — CRITICAL PATH AND PIPELINE INTEGRATION

```
L1-I CACHE (integrated into IF stage):
  Access: virtual PC → index → SRAM → tag compare → instruction to IF/ID
  Hit: 1 cycle → instruction available for decode next cycle
  Miss: stall pipeline, fetch from L2, fill, retry (10–20 cycle penalty)
  Separate from D-cache (no structural hazard)

L1-D CACHE (integrated into MEM stage):
  Access: ALU result (physical after VIPT) → index → SRAM → tag compare → data
  Hit: 1 cycle → data available at MEM/WB boundary
  Miss: stall pipeline until fill (multi-cycle penalty)

CRITICAL PATH THROUGH MEM STAGE:
  EX/MEM register read:    ~0.1 ns
  Cache index decode:      ~0.1 ns
  SRAM array access:       ~0.8 ns (32KB at 28nm)
  Tag compare + hit:       ~0.2 ns
  Data mux (way select):   ~0.1 ns
  Sign extension (load):   ~0.1 ns
  MEM/WB register setup:   ~0.1 ns
  TOTAL:                   ~1.5 ns → minimum cycle time ~1.5 ns → ~667 MHz (MEM-limited)
  Optimization: pipeline MEM into MEM1 (tag lookup) + MEM2 (data return)
```

# CHECKLIST — Before Moving to Memory Hierarchy

```
✅ L1-I and L1-D capacities chosen (separate caches)
✅ Block size chosen (64 bytes recommended)
✅ Associativity chosen and conflict miss analysis done
✅ Tag/index/offset bit split written for both L1-I and L1-D
✅ VIPT aliasing condition checked (index bits within page offset)
✅ Tag array and data array sizes calculated
✅ Replacement policy chosen (PLRU for L1)
✅ Write policy chosen (write-back + write-allocate)
✅ Dirty bit and dirty eviction flow defined
✅ Miss stall mechanism (in-order) or MSHR (OoO) defined
✅ Miss penalty for each level estimated in cycles
✅ MEM stage critical path estimated
→ NEXT: 09-MemoryHierarchyVirtualMemory.md
```
