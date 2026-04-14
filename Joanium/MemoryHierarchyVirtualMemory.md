---
name: Memory Hierarchy and Virtual Memory
trigger: virtual memory, TLB, page table, page fault, address translation, MMU, memory hierarchy, DRAM, page size, virtual address, physical address, translation lookaside buffer, TLB miss, page walk, satp, PTW, sv39, sv48
description: Ninth skill in the processor design pipeline. Covers the full memory hierarchy from registers to DRAM, address translation mechanics, TLB design, page table walker microarchitecture, and RISC-V Sv39/Sv48 paging schemes.
prev_skill: 08-CacheDesign.md
next_skill: 10-OutOfOrderExecution.md
---

# ROLE
You are designing the illusion of infinite, private, fast memory for every process. Virtual memory is not optional — it is the foundation of process isolation, security, and the OS memory abstraction. You design TLBs that translate in 1 cycle, page table walkers that handle misses in hardware, and memory hierarchies where every level hides the latency of the next.

# CORE PRINCIPLES
```
VIRTUAL MEMORY IS ABOUT ISOLATION — every process believes it owns all of memory
TLB IS THE CACHE FOR ADDRESS TRANSLATION — make it fast; a TLB miss is a mini page walk
PAGE TABLE WALKER RUNS ON THE SAME MEMORY SYSTEM IT IS TRANSLATING — careful ordering
PAGE FAULT IS NOT AN ERROR — it is a normal mechanism for lazy allocation and swap
DRAM IS ~1000× SLOWER THAN L1 — never touch DRAM on the critical path without prefetch
HIERARCHY LEVELS MULTIPLY LATENCY — budget carefully; miss penalty is not additive but product
ADDRESS TRANSLATION MUST COMPLETE BEFORE CACHE TAG COMPARE — VIPT hides this (see skill 08)
```

# STEP 1 — MEMORY HIERARCHY OVERVIEW

```
FULL HIERARCHY (typical 64-bit high-performance processor):

  Level          Size        Latency       Bandwidth       Technology
  ────────────   ─────────   ───────────   ─────────────   ─────────────
  Registers      32 × 64b    0 cycles      unlimited       Flip-flops / SRAM
  L1-I cache     32–64 KB    1–4 cycles    64–256 GB/s     SRAM (6T)
  L1-D cache     32–64 KB    4–5 cycles    64–256 GB/s     SRAM (6T)
  L2 (unified)   256KB–4MB   10–20 cycles  200–400 GB/s    SRAM (6T, denser)
  L3 (LLC)       4–64 MB     30–60 cycles  100–200 GB/s    SRAM (high-density)
  DRAM           4GB–TBs     60–200 ns     25–100 GB/s     DRAM (capacitor)
  NVMe SSD       TBs         50–100 µs     5–15 GB/s       NAND Flash
  HDD            PBs         5–10 ms       100–300 MB/s    Magnetic disk

EFFECTIVE ACCESS TIME (EAT) FORMULA:
  EAT = hit_rate_L1 × T_L1
      + (1 - hit_rate_L1) × hit_rate_L2 × (T_L1 + T_L2)
      + (1 - hit_rate_L1)(1 - hit_rate_L2) × (T_L1 + T_L2 + T_DRAM)

  Example: L1 hit rate = 95%, L2 hit rate = 90%, DRAM latency = 200 cycles
    EAT = 0.95×4 + 0.05×0.90×(4+15) + 0.05×0.10×(4+15+200)
        = 3.8 + 0.855 + 1.095
        = 5.75 cycles  (vs 200 cycles without cache — 35× speedup)
```

# STEP 2 — VIRTUAL ADDRESS SPACES

```
RISC-V ADDRESS SPACE OPTIONS:
  Sv32:  32-bit virtual, 34-bit physical (RV32 with MMU)
  Sv39:  39-bit virtual, 56-bit physical (common 64-bit choice)
  Sv48:  48-bit virtual, 56-bit physical (large server systems)
  Sv57:  57-bit virtual, 57-bit physical (future-proofed)
  Bare:  No translation (physical = virtual; machine mode default)

SV39 ADDRESS STRUCTURE:
  Virtual address [38:0] = 39 bits → 512 GB virtual space per process
  Physical address [55:0] = 56 bits → 64 PB physical memory

  VA[38:30] = VPN[2]  9-bit  (level-3 index, 512 entries)
  VA[29:21] = VPN[1]  9-bit  (level-2 index, 512 entries)
  VA[20:12] = VPN[0]  9-bit  (level-1 index, 512 entries)
  VA[11:0]  = offset  12-bit (byte offset within 4KB page)

  Signs extension: VA[63:39] must all equal VA[38] (canonical form)
  Non-canonical virtual address → page fault (CAUSE = LOAD/STORE_PAGE_FAULT)

SV39 PAGE TABLE ENTRY (PTE) — 8 bytes:
  Bits [63:54]: Reserved (must be zero)
  Bits [53:10]: PPN[2:0] — 44-bit Physical Page Number
  Bit  [7]:     D — dirty (page has been written)
  Bit  [6]:     A — accessed (page has been read or written)
  Bit  [5]:     G — global (shared across address spaces)
  Bit  [4]:     U — user accessible (0 = kernel only)
  Bit  [3]:     X — execute permission
  Bit  [2]:     W — write permission
  Bit  [1]:     R — read permission
  Bit  [0]:     V — valid (0 = page fault)
  R=0,W=0 → pointer to next-level page table (non-leaf PTE)
  R=1 or X=1 → leaf PTE (maps an actual page)
```

# STEP 3 — SV39 ADDRESS TRANSLATION WALK

```
HARDWARE PAGE TABLE WALKER (PTW) STEPS:

  INPUT: virtual address VA, SATP register

  SATP register (Supervisor Address Translation and Protection):
    Bits [63:60]: MODE (8 = Sv39, 9 = Sv48, 0 = Bare)
    Bits [59:44]: ASID — Address Space Identifier (for TLB tagged flushes)
    Bits [43:0]:  PPN — physical page number of root page table

  STEP 1: a = satp.PPN × 4096;  i = 2  (start at top level)

  STEP 2: pte_addr = a + VA.VPN[i] × 8  (each PTE is 8 bytes)
          pte = Memory[pte_addr]         (fetch PTE — one memory access)

  STEP 3: if pte.V == 0 → PAGE FAULT

  STEP 4: if pte.R || pte.X  (leaf PTE — this is the mapping)
            → check permissions (R/W/X vs access type)
            → check U bit vs privilege mode
            → if permissions OK: PA = pte.PPN × 4096 + VA.offset
            → if i > 0 and lower VPN bits non-zero: MISALIGNED SUPERPAGE FAULT

  STEP 5: if not leaf (R=0,W=0) → a = pte.PPN × 4096; i = i - 1; goto STEP 2

  SUPERPAGE SUPPORT:
    i=1 leaf: 2MB superpage (VA[20:0] is offset, ignore VPN[0])
    i=2 leaf: 1GB gigapage  (VA[29:0] is offset, ignore VPN[1], VPN[0])
    Superpages reduce TLB pressure for large mappings (kernel, huge heap)

  TOTAL MEMORY ACCESSES FOR FULL WALK:
    Sv39: 3 accesses (L3, L2, L1 page table levels)
    These accesses hit the data cache if PTEs are cached there (common)
    Sv48: 4 accesses; Sv57: 5 accesses
```

# STEP 4 — TLB DESIGN

```
TLB = CACHE OF (VA → PA) MAPPINGS — avoids full page walk on every memory access

TLB STRUCTURE:
  Fully associative (small TLBs: 16–64 entries)
  Set-associative (larger TLBs: 4–8-way, 256–1024 entries)

TYPICAL TLB CONFIGURATION:
  L1 ITLB:  32–64 entries, fully associative, 1-cycle lookup
  L1 DTLB:  32–64 entries, fully associative, 1-cycle lookup
  Unified L2 TLB: 512–4096 entries, 4-8 way, 5–10 cycle lookup
  (L2 TLB fills on L1 TLB miss; reduces PTW frequency by 10–100×)

TLB ENTRY FIELDS:
  VPN[38:12]   — virtual page number (27 bits for Sv39)
  PPN[55:12]   — physical page number (44 bits for Sv39)
  ASID[15:0]   — address space ID (allows multiple processes without full flush)
  R, W, X      — permission bits
  U            — user accessible
  G            — global (ASID-independent; shared kernel mappings)
  D, A         — dirty/accessed bits
  page_size    — 4KB, 2MB, or 1GB (for superpage entries)
  valid        — entry is live

TLB LOOKUP:
  Parallel compare all tags: (entry.VPN == VA.VPN[38:12]) && (entry.ASID == satp.ASID || entry.G)
  If hit: return PPN, check permission → generate physical address
  If miss: invoke page table walker → fill TLB → retry

TLB REPLACEMENT:
  Fully associative: PLRU or random (both acceptable at 64 entries)
  Large TLBs: PLRU or LFU approximation

TLB SHOOTDOWN (MULTICORE):
  When OS remaps a page: must invalidate TLB entries on ALL cores with that mapping
  Inter-processor interrupt (IPI) → each core executes SFENCE.VMA → confirms to OS
  Critical for correctness in multiprocessor systems
  RISC-V instruction: SFENCE.VMA rs1, rs2  (rs1=VA, rs2=ASID; 0=broadcast flush)
```

# STEP 5 — PAGE TABLE WALKER MICROARCHITECTURE

```
PTW IMPLEMENTATION OPTIONS:

Option A: Microcode-Driven (software PTW)
  TLB miss → trap to OS → OS walks table in software → refills TLB
  Simple hardware; used in RISC-V with software-managed TLBs (bare implementations)
  Penalty: hundreds of cycles per miss (OS overhead)

Option B: Hardware PTW (standard for performance)
  Dedicated state machine issues memory requests to cache hierarchy
  Runs in background; pipeline may continue (if non-blocking) or stall (simpler)

HARDWARE PTW STATE MACHINE (Sv39):
  IDLE       → wait for TLB miss signal
  L3_FETCH   → issue load for L3 PTE (PPN from satp × 4096 + VPN[2]×8)
  L3_WAIT    → wait for L3 PTE from cache (hits L1-D if warm)
  L3_CHECK   → check valid; if superpage → DONE; else proceed to L2
  L2_FETCH   → issue load for L2 PTE
  L2_WAIT    → wait
  L2_CHECK   → check valid; if superpage → DONE; else proceed to L1
  L1_FETCH   → issue load for L1 PTE
  L1_WAIT    → wait
  L1_CHECK   → check valid; check permissions; compute PA
  FILL       → write new mapping into TLB (evict PLRU entry)
  DONE       → signal pipeline to retry; return to IDLE

  PAGE FAULT: At any CHECK state → valid=0 → raise page fault exception

PTW CACHE INTERACTION:
  PTW uses the D-cache read port to fetch PTEs
  PTEs in L1-D cache: PTW hit rate ~80–90% in practice (locality of PTEs)
  PTW competes with processor loads for D-cache read port → arbitration needed
  Solution: PTW has lower priority than processor; stalls if cache busy

PTW-INITIATED PAGE FAULT:
  mepc  = VA of faulting instruction
  mcause= LOAD_PAGE_FAULT (5), STORE_PAGE_FAULT (7), or INST_PAGE_FAULT (12)
  mtval = faulting virtual address
  → jump to trap handler (OS page fault handler)
```

# STEP 6 — DRAM FUNDAMENTALS

```
DRAM ORGANIZATION:
  Row (wordline) × Column (bitline) arrays; each cell = 1 capacitor + 1 transistor
  Destructive read: reading discharges capacitor → must restore (precharge + write)

DRAM COMMANDS AND TIMING:
  RAS (Row Address Strobe):    open a row (copy row to sense amplifiers)
  CAS (Column Address Strobe): read/write a column within the open row
  PRE (Precharge):             close row, prepare for next RAS

CRITICAL DRAM TIMING PARAMETERS:
  tRCD (RAS to CAS delay):       ~12–16 ns  (open row → access column)
  tCAS (CAS latency):            ~14–18 ns  (column address → data out)
  tRP  (row precharge):          ~12–16 ns  (close row)
  tRAS (row active time):        ~32–40 ns  (minimum time row must stay open)
  TOTAL first access:            tRCD + tCAS ≈ 30–35 ns → ~90–110 cycles at 3 GHz

ROW BUFFER (page mode):
  After RAS: entire row (4–8 KB) loaded into sense amplifiers
  Subsequent accesses to same row: only CAS needed (~14 ns) — "row hit"
  Row hit rate in practice: 60–90% (depends on working set vs row size)

REFRESH:
  DRAM capacitors leak → must refresh every 64 ms (all rows)
  During refresh: DRAM unavailable (~100 ns per refresh command)
  Modern DRAM: 8192 refresh operations spread across 64 ms

DDR4 / DDR5 BANDWIDTH:
  DDR4-3200: 3200 MT/s × 64-bit bus = 25.6 GB/s peak
  DDR5-6400: 6400 MT/s × 64-bit bus = 51.2 GB/s peak
  Effective bandwidth (considering overhead): ~60–70% of peak
```

# STEP 7 — PREFETCHING

```
SPATIAL PREFETCHER (hardware):
  On any cache miss at address X → prefetch X + cache_line_size
  Works for sequential access patterns (array traversal, instruction streams)
  Simple to implement; low overhead if prefetch buffer used

STRIDE PREFETCHER:
  Track stride pattern: if two misses at X and X+S → predict next at X+2S
  Requires stride table: PC → (last_addr, stride, confidence)
  Effective for loop-based array accesses with non-unit stride

STREAM PREFETCHER:
  Detect sequential stream: if 4+ sequential misses → open prefetch stream
  Prefetch several lines ahead (prefetch depth = 4–8 lines typical)
  Used in all modern processors for memory bandwidth utilization

SOFTWARE PREFETCH:
  ISA instruction: PREFETCH.R addr or PREFETCH.W addr
  Compiler inserts prefetch instructions N iterations ahead of use
  Good for known access patterns (matrix multiply, linked list traversal)

RISC-V PREFETCH HINT:
  PREFETCH.R: encoded as ORI x0, rs1, imm  (rd=0 = no result, treated as hint)
  PREFETCH.W: similar encoding variant
  Hardware may ignore if prefetch buffer full (hint, not command)
```

# CHECKLIST — Before Moving to Out-of-Order Execution

```
✅ Full memory hierarchy table (size, latency, bandwidth per level)
✅ EAT formula applied with realistic hit rates → estimated CPI impact
✅ Address space mode chosen (Sv39 for most 64-bit designs)
✅ VA decomposition written (VPN[2], VPN[1], VPN[0], offset)
✅ PTE format fields documented (V, R, W, X, U, G, D, A, PPN)
✅ 3-level walk algorithm written step by step
✅ Superpage support noted (1GB, 2MB)
✅ TLB entry fields listed (VPN, PPN, ASID, permissions, page_size)
✅ TLB replacement policy chosen (PLRU or random)
✅ TLB shootdown mechanism defined (SFENCE.VMA + IPI)
✅ Hardware PTW state machine states listed
✅ PTW-cache port arbitration noted
✅ DRAM timing parameters listed (tRCD, tCAS, tRP)
✅ Prefetch strategy chosen (stream + stride recommended)
→ NEXT: 10-OutOfOrderExecution.md
```
