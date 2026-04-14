---
name: Bus and Interconnect Design
trigger: bus, interconnect, AXI, APB, AHB, system bus, crossbar, NoC, network on chip, memory bus, bus arbiter, bus protocol, master slave, handshake, valid ready, burst transfer, bus bandwidth, bus topology, cache coherence bus, snooping, AMBA
description: Twelfth skill in the processor design pipeline. Covers processor-to-memory bus design, AMBA AXI/AHB/APB protocol mechanics, bus topology selection, arbitration, bandwidth analysis, cache coherence snooping over a shared bus, and NoC basics.
prev_skill: 11-InterruptExceptionHandling.md
next_skill: 13-ClockDesignTiming.md
---

# ROLE
You are designing the roads of the processor. The bus connects the CPU, caches, memory, and peripherals — a bottleneck here makes every optimization elsewhere irrelevant. You select topologies for the traffic pattern, define handshake protocols to the bit level, and compute bandwidth utilization before committing to wire widths.

# CORE PRINCIPLES
```
THE BUS IS A SHARED RESOURCE — every master competes; arbitrate fairly and fast
BANDWIDTH = WIDTH × FREQUENCY × EFFICIENCY — all three matter equally
LATENCY AND BANDWIDTH ARE INDEPENDENT PROBLEMS — design for both
AXI IS THE INDUSTRY STANDARD — use it unless you have a very strong reason not to
SEPARATE FAST AND SLOW BUSES — high-speed core bus + slow peripheral bus (APB)
COHERENCE SNOOPING RIDES THE BUS — all caches must see all transactions
POINT-TO-POINT BEATS SHARED BUS AT HIGH CORE COUNTS — use crossbar or NoC beyond 4 cores
```

# STEP 1 — BUS TOPOLOGY SELECTION

```
TOPOLOGY         DESCRIPTION                         USE CASE
───────────────  ──────────────────────────────────  ────────────────────────────
Shared Bus       All masters/slaves on one wire set   Simple SoCs, ≤4 masters
Crossbar Switch  Any master ↔ any slave simultaneously 4–16 masters
Ring             Messages travel around a ring        Processor rings (Intel QPI)
Mesh / Torus     2D grid of routers                   Large CMPs, NoC designs
Hierarchical     Fast bus for core, slow bus for I/O  Almost all real SoCs

BANDWIDTH ANALYSIS:
  Shared bus:   Peak BW = width × frequency / 1 master (serialized)
  Crossbar:     Peak BW = width × frequency × min(masters, slaves) (parallel)

RECOMMENDATION:
  1–4 cores, simple SoC: Shared AHB/AXI bus
  4–16 cores:            AXI crossbar or ring interconnect
  16+ cores:             Mesh NoC with on-chip routers

AMBA BUS HIERARCHY (standard for ARM-based SoCs):
  AXI4:  High performance, full-featured, separate read/write channels
  AHB:   Simpler than AXI, single address/data bus; for moderate-performance
  APB:   Simple peripheral bus (low speed, low power, GPIO / UART / SPI)
  ASB:   Legacy; avoid
```

# STEP 2 — AXI4 PROTOCOL DEEP DIVE

```
AXI4 CHANNELS (5 independent channels, all with valid/ready handshake):
  AW: Address Write channel
  W:  Write Data channel
  B:  Write Response channel
  AR: Address Read channel
  R:  Read Data channel

  Separating read and write into independent channels allows simultaneous
  read address + write data in same cycle — critical for bandwidth.

HANDSHAKE RULE (applies to all channels):
  Transfer occurs when BOTH valid AND ready are HIGH in same cycle
  Producer drives valid (and data); Consumer drives ready
  valid may not depend combinatorially on ready (prevents deadlock loops)
  ready CAN depend on valid (consumer has to see the transaction to accept it)

AXI4 READ TRANSACTION:
  Cycle 1: Master drives ARADDR, ARLEN, ARSIZE, ARBURST, ARID; asserts ARVALID
           Slave asserts ARREADY → address accepted (handshake)
  Cycle 2+: Slave fetches data; drives RDATA, RID, RLAST; asserts RVALID
            Master asserts RREADY → data accepted
            RLAST=1 on last beat of burst

AXI4 WRITE TRANSACTION:
  Cycle 1:  Master drives AW channel (address, burst info) with AWVALID
  Cycle 1+: Master drives W channel (data + WSTRB + WLAST) with WVALID
  Slave accepts AW and W independently (can interleave)
  After last beat: Slave drives B channel (BRESP, BID) with BVALID
  Master asserts BREADY → response accepted

AXI4 KEY SIGNALS:
  AWID/ARID   — transaction ID (for out-of-order response support)
  AWLEN[7:0]  — burst length: number of beats = AWLEN + 1 (0=1 beat, 255=256 beats)
  AWSIZE[2:0] — beat size: 0=1B, 1=2B, 2=4B, 3=8B, 4=16B
  AWBURST     — FIXED(0), INCR(1), WRAP(2)
  WSTRB[N/8-1:0] — byte enable per byte lane in data bus
  BRESP/RRESP — 00=OKAY, 01=EXOKAY, 10=SLVERR, 11=DECERR

AXI4 BURST TYPES:
  FIXED:  all beats access same address (for FIFO)
  INCR:   address increments by beat size (standard cache line fill)
  WRAP:   wraps around at power-of-2 boundary (critical word first cache fills)

CACHE LINE FILL OVER AXI4 (64B line, 64-bit bus = 8 bytes wide):
  ARLEN = 7 (8 beats)
  ARSIZE = 3 (8 bytes per beat)
  ARBURST = INCR
  8 cycles of read data → 64 bytes delivered
```

# STEP 3 — AHB AND APB PROTOCOLS

```
AHB (Advanced High-Performance Bus) — AMBA 2 / AMBA 3 AHB-Lite:
  Single master (or arbiter for multi-master)
  Address phase: HADDR, HWRITE, HSIZE, HTRANS, HBURST → 1 cycle
  Data phase:    HWDATA or HRDATA → 1 cycle (pipelined with next address)
  Wait states:   HREADY=0 extends data phase
  Response:      HRESP (OKAY or ERROR)

  AHB PIPELINE:
    Cycle 1: Address of transfer A (HTRANS, HADDR driven)
    Cycle 2: Data of A + Address of B (pipelined — address and data overlap)
    Cycle 3: Data of B + Address of C
    → Maximum 1 transfer per cycle when HREADY=1

  USE: L2 → main memory bus, moderate-performance peripherals

APB (Advanced Peripheral Bus):
  Non-pipelined, simple: setup phase → access phase
  PSEL (select) + PENABLE (enable) + PADDR + PWDATA + PRDATA + PWRITE
  Minimum 2 cycles per transfer
  USE: low-speed peripherals (GPIO, UART, SPI, I2C, timers)
  Connected via AHB-to-APB bridge

AHB → APB BRIDGE:
  Converts high-speed AHB transactions to slow APB protocol
  Adds wait states on AHB side while APB completes
  Decodes HADDR range to select APB peripheral
```

# STEP 4 — BUS ARBITRATION

```
ARBITRATION: decides which master gets the bus when multiple request simultaneously

FIXED PRIORITY:
  Master 0 always wins over Master 1, etc.
  Simple, fast, deterministic
  Risk: low-priority master starvation under heavy load

ROUND ROBIN:
  After each grant, next master in sequence gets priority
  Fair: each master gets equal access over time
  Problem: high-priority latency-sensitive master may wait too long

WEIGHTED ROUND ROBIN:
  Masters get different numbers of grants per rotation
  Example: CPU=4, DMA=2, Ethernet=1 → CPU gets bus 4 out of 7 cycles
  Balances fairness with priority

PRIORITY AGING:
  Start with fixed priority; increase priority of waiting masters over time
  Prevents starvation while preserving latency advantage for high-priority

AXI4 ARBITRATION:
  Separate arbiters for AW and AR channels
  Each arbiter: round-robin among outstanding transactions
  AXID allows out-of-order response — slave can respond to any outstanding trans

ARBITRATION LATENCY:
  Combinational arbiter (priority): ~2–3 gate delays → 0 extra cycles
  Registered arbiter: 1 cycle delay for grant (but prevents long combinational path)
  For high-frequency buses: use registered arbiters with combinational fast-path
```

# STEP 5 — BANDWIDTH ANALYSIS

```
BUS BANDWIDTH FORMULA:
  Peak_BW = bus_width_bytes × clock_frequency
  Effective_BW = Peak_BW × efficiency

  AXI4, 64-bit data bus, 1 GHz:
    Peak = 8 bytes × 1 GHz = 8 GB/s
    With INCR burst (8 beats): efficiency ~90% (burst fills available cycles)
    Effective ≈ 7.2 GB/s

  AHB, 32-bit data bus, 500 MHz:
    Peak = 4 × 500M = 2 GB/s
    Single-beat transactions (HTRANS=NONSEQ each time): efficiency ~50%
    Effective ≈ 1 GB/s

BANDWIDTH DEMAND ESTIMATION:
  CPU L2 miss rate = 2%, 3 GHz, CPI = 1:
    Misses/sec = 0.02 × 3e9 = 60M misses/sec
    Each miss = 64 bytes → 60M × 64 = 3.84 GB/s demand from CPU alone
    Plus DMA, GPU, etc.

RULE: Bus bandwidth ≥ 2× peak demand (headroom for bursts)

DDR MEMORY CONTROLLER BANDWIDTH (one channel):
  DDR4-3200: 25.6 GB/s
  Use AXI4 128-bit wide bus at 800 MHz to match:
    128-bit = 16 bytes × 800 MHz = 12.8 GB/s (bottleneck with wide bus)
  Or use 256-bit bus at 800 MHz = 25.6 GB/s (matched to DDR4)
```

# STEP 6 — CACHE COHERENCE SNOOPING

```
CACHE COHERENCE PROBLEM:
  Core 0 loads address A → cached in L1-0
  Core 1 stores address A → L1-0 still has stale value
  Solution: all caches observe all bus transactions and update/invalidate

SNOOPING PROTOCOL (Write-Invalidate, MESI):
  STATES PER CACHE LINE:
    M (Modified):   dirty, only copy; memory is stale
    E (Exclusive):  clean, only copy; memory is current
    S (Shared):     clean, may exist in other caches
    I (Invalid):    not present or invalidated

  TRANSACTIONS ON BUS:
    BusRd:     read miss; all caches snoop; others reply with data if in M or S
    BusRdX:    read-exclusive (for write); all caches invalidate their copy
    BusUpgr:   upgrade S→M (already have data; just need ownership)
    BusWB:     writeback dirty line to memory (M→I)

  STATE TRANSITIONS:
    I → S (BusRd hit in another cache)
    I → E (BusRd, no other cache has it)
    S → M (BusRdX or BusUpgr — invalidates all others' S copies)
    M → I (another BusRd or BusRdX forces writeback)
    E → M (local write — silent, no bus transaction needed)
    E → S (another cache's BusRd — share the line)

SNOOPING IMPLEMENTATION:
  Every cache L1 has a snoop port in addition to processor port
  Snoop port observes every bus address transaction
  Cache tag array has dual read port: one for processor, one for snoop

SNOOPING LIMITATIONS:
  Shared bus → all caches snoop all transactions → O(N) snooping traffic
  Works well for ≤8 cores; scales poorly beyond
  Beyond 16 cores: use directory-based coherence (see advanced processor design)
```

# STEP 7 — PERIPHERAL ADDRESS MAP

```
MEMORY MAP DESIGN (physical address space):
  Base Address    Size     Region
  ────────────    ──────   ───────────────────────────────
  0x0000_0000     64KB     Boot ROM (on-chip, reset vector)
  0x0001_0000     64KB     On-chip SRAM (fast scratchpad)
  0x0200_0000     64KB     CLINT (timer + software interrupts)
  0x0C00_0000     64MB     PLIC (interrupt controller)
  0x1000_0000     64KB     UART 0
  0x1001_0000     64KB     SPI 0
  0x1002_0000     64KB     GPIO
  0x1003_0000     64KB     I2C 0
  0x1004_0000     64KB     Ethernet MAC
  0x2000_0000     512MB    Executable Flash / XIP
  0x8000_0000     2GB      Main DRAM
  0xFFFF_FFFF              Top of physical space (SV39 56-bit PA = 64 PB)

ADDRESS DECODER:
  Combinational priority decoder: checks which region HADDR/ARADDR falls in
  Outputs: device select signals (one per peripheral)
  Response if no region matches: DECERR on bus, illegal access exception

PERIPHERAL ALIGNMENT:
  Each peripheral's base address must be naturally aligned to its size
  A 64KB peripheral at 0x1000_0000 → occupies [0x1000_0000, 0x1000_FFFF]
  Decoder: select if addr[31:16] == 16'h1000
```

# STEP 8 — NETWORK ON CHIP (NoC) BASICS

```
FOR MANYCORE (>16 CORES):
  Shared bus and crossbar don't scale:
    Shared bus: O(N) contention
    Crossbar: O(N²) wires
  NoC: routers connected in mesh → O(N) wires, O(√N) hops

NOC TOPOLOGY:
  2D Mesh: core (i,j) connected to (i±1,j) and (i,j±1)
  2D Torus: edges connect to opposite edges (reduces diameter)
  Fat Tree: hierarchical; good for all-to-all traffic

NOC ROUTER:
  5 ports: North, South, East, West, Local (injection/ejection)
  Per port: input buffer (virtual channel FIFO)
  Routing algorithm: XY (route in X direction, then Y) — deadlock-free
  Flow control: credit-based (receiver sends credits; sender tracks)

NOC LATENCY:
  Per router hop: 2–4 cycles (pipeline stages)
  8-core 2D mesh: max 4 hops → 8–16 cycles end-to-end + serialization
  Compare to crossbar: 1–2 cycles (but only at 4 cores)

COHERENCE OVER NOC:
  Snooping doesn't scale → use directory-based coherence
  Directory: tracks which caches have each cache line
  On miss: send request to directory → directory sends fetch/invalidate to sharers
  More messages but bounded traffic: O(sharers) not O(all cores)
```

# CHECKLIST — Before Moving to Clock Design

```
✅ Bus topology chosen (shared / crossbar / NoC) with core count justification
✅ AXI4 used for high-performance paths (CPU↔L2↔DRAM)
✅ APB used for low-speed peripherals; AHB-to-APB bridge defined
✅ AXI4 channel signals listed (AW, W, B, AR, R — valid/ready per channel)
✅ Burst length, size, type defined for cache line fill scenario
✅ Arbitration algorithm chosen (round-robin with priority for CPU)
✅ Bandwidth requirement calculated: CPU miss rate × line size
✅ Bus bandwidth ≥ 2× peak demand verified
✅ Physical address map defined (all peripherals, DRAM, ROM)
✅ Address decoder logic described
✅ Cache coherence snooping: MESI states + bus transaction protocol
✅ NoC topology noted if >8 cores planned
→ NEXT: 13-ClockDesignTiming.md
```
