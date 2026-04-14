---
name: Register File Design
trigger: register file, register bank, read port, write port, multi-port register, register array, SRAM register file, flip-flop register file, register forwarding, register bypass, x0 hardwired, register file timing, physical register file, PRF
description: Sixth skill in the processor design pipeline. Covers register file port requirements, flip-flop vs SRAM implementation, multi-port design, x0 hardwiring, write-before-read in same cycle, and the physical register file for out-of-order designs.
prev_skill: 05-ALUDatapathDesign.md
next_skill: 07-ControlUnitDesign.md
---

# ROLE
You are designing the fastest, most frequently accessed storage in the processor. The register file is read every cycle by decode, written every cycle by writeback, and its read latency is on the critical path through the ID stage. You understand port counts, multi-ported SRAM cell design, and why x0 being hardwired to zero saves more hardware than you'd expect.

# CORE PRINCIPLES
```
REGISTER FILE IS THE INNER LOOP OF EVERY INSTRUCTION — make it fast
PORT COUNT DETERMINES AREA — each additional port ≈ 2× cell size
SRAM FOR LARGE FILES, FLIP-FLOPS FOR SMALL — crossover at ~64 entries
x0 IS NOT A REGISTER — hardwire it; eliminate a write port check
WRITE-BEFORE-READ IN SAME CYCLE — if WB and ID share cycle, WB wins
FORWARDING REDUCES PRESSURE — fewer stall cycles but no port savings
PHYSICAL REGISTER FILE SIZE = LOGICAL + IN-FLIGHT WINDOW — size for OoO
```

# STEP 1 — PORT REQUIREMENTS

```
IN-ORDER 5-STAGE PIPELINE PORT REQUIREMENTS:

  READ PORTS:
    ID stage reads up to 2 source registers per cycle (rs1, rs2)
    → Minimum: 2 read ports

  WRITE PORTS:
    WB stage writes up to 1 destination register per cycle (rd)
    → Minimum: 1 write port

  STANDARD CONFIGURATION: 2R / 1W (2 read, 1 write)

SUPERSCALAR PORT REQUIREMENTS:
  Issue width = N → N×2 read ports, N write ports
  Example, 2-wide: 4 read ports, 2 write ports
  Example, 4-wide: 8 read ports, 4 write ports

PORT COUNT VS AREA:
  Each additional read port adds: 1 additional bitline pair per cell → ~linear area
  Each additional write port adds: 1 additional wordline per cell → ~linear area
  Multi-port SRAM cells are physically larger than single-port cells
  32 registers × 64 bits × (2R+1W) cell: ~0.5–1 KB area equivalent
  32 registers × 64 bits × (8R+4W): ~3–4 KB → significant but manageable

WORKAROUNDS TO REDUCE PORTS:
  Banking: split register file into two banks, each serving half the ports
  Replication: duplicate read copies (2R becomes two 1R arrays read simultaneously)
  Time-multiplexing: read both operands on consecutive sub-cycles (slower clock → not used)
```

# STEP 2 — IMPLEMENTATION: FLIP-FLOP ARRAY

```
FLIP-FLOP REGISTER FILE (for ≤ 32 registers):

  STRUCTURE:
    32 registers × 64 bits = 2048 flip-flops
    Read: combinational (async) — output = reg[addr] immediately
    Write: synchronous — updates on rising clock edge

  ADVANTAGE:
    Async read — no latency, result available within propagation delay
    Simple: plain Verilog array of registers

  DISADVANTAGE:
    FFs are larger than SRAM bitcells (6T SRAM vs ~20T flip-flop)
    Not practical for >64 registers (area too large)

  VERILOG IMPLEMENTATION:
    module reg_file #(parameter W=64, parameter N=32) (
      input              clk,
      input  [4:0]       rs1_addr, rs2_addr,
      input  [4:0]       rd_addr,
      input  [W-1:0]     wr_data,
      input              wr_en,
      output [W-1:0]     rs1_data, rs2_data
    );
      reg [W-1:0] regs [1:N-1];   // x0 excluded — not stored

      // Async read (combinational)
      assign rs1_data = (rs1_addr == 5'b0) ? {W{1'b0}} : regs[rs1_addr];
      assign rs2_data = (rs2_addr == 5'b0) ? {W{1'b0}} : regs[rs2_addr];

      // Synchronous write with x0 guard
      always @(posedge clk) begin
        if (wr_en && rd_addr != 5'b0)
          regs[rd_addr] <= wr_data;
      end
    endmodule
```

# STEP 3 — IMPLEMENTATION: MULTI-PORT SRAM CELL

```
6T SRAM CELL (single-port):
  6 transistors: 2 cross-coupled inverters (4T) + 2 access transistors
  1 wordline (WL), 1 bitline pair (BL, BLB)
  Read: precharge BL/BLB, enable WL, sense differential voltage → sense amp
  Write: drive BL/BLB to desired value, enable WL, force cell

MULTI-PORT SRAM CELL (for register files):
  2-read-port cell: add 2 extra read wordlines + 2 extra read bitline pairs
  Cell size: 6T + 2R×2T + 1W×2T = 12T for 2R/1W

  BITCELL ORGANIZATION:
    Row (word line): selects one 64-bit register
    Column (bit line): selects one bit plane
    Read: activate row → sense all 64 bit columns simultaneously
    Write: drive 64 bitlines, activate wordline

SENSE AMPLIFIER:
  Located at bottom of each bitline pair
  Amplifies small differential voltage (50–100 mV) to full CMOS logic level
  Latency: 150–300 ps in 28nm technology
  One sense amp per bit column per read port

PRECHARGE CIRCUIT:
  Before each read: precharge BL and BLB to VDD/2 or VDD
  Controlled by precharge signal (complement of clock)
  Precharge must complete before wordline is asserted
```

# STEP 4 — x0 HARDWIRING

```
x0 RULE: Register x0 always reads as 0, writes are silently discarded.

IMPLEMENTATION OPTIONS:

Option A: Mux at read output:
  rs1_data = (rs1_addr == 0) ? 64'b0 : array_out_port1
  Cost: 64 mux gates (fast, minimal)
  PREFERRED for flip-flop implementations

Option B: Don't allocate storage for x0:
  Physical array has only 31 entries (x1–x31)
  Index mapping: addr → addr-1 for rd/rs logic
  Gate write: if (wr_en && rd_addr != 0) → write
  Cost: slightly more logic in address decode, saves 64 FF or 64 SRAM bits

Option C: Wire to ground:
  Tie x0 bitlines to GND (SRAM) — read always returns 0
  Write: WL[0] never asserted (decoded away)
  PREFERRED for SRAM implementations (zero extra logic in read path)

BENEFITS OF HARDWIRED x0:
  NOP = ADDI x0, x0, 0 — encodes simply and discards write
  Store source can be x0 → write zeros to memory cheaply
  Compare with zero: BEQ rs1, x0, label → branch if rs1 == 0
  Return from function to /dev/null: JAL x0, offset
```

# STEP 5 — WRITE-BEFORE-READ (SAME-CYCLE FORWARDING)

```
PROBLEM:
  WB stage writes rd in same cycle that ID stage reads rs1/rs2
  If WB.rd == ID.rs1 or WB.rd == ID.rs2 → ID needs the just-written value
  Without care: ID reads the OLD value (MEM/WB stale)

SOLUTION — INTERNAL BYPASS (write-before-read):

  Option A: First-half write, second-half read
    Write port active in first half-cycle (before clock edge in some designs)
    Read port active second half-cycle → sees new value
    Requires careful timing; risky in high-frequency designs

  Option B: Write-through mux (recommended):
    Forward WB data to ID read output if addresses match
    Same as forwarding but happens inside the register file interface

    rs1_out = (wr_en && wr_addr == rs1_addr && rs1_addr != 0)
                  ? wr_data       // write-through: use new value
                  : array[rs1_addr]   // normal read

  Option C: Don't rely on it — use MEM/WB forwarding path:
    The existing MEM/WB forwarding in the EX stage handles this case too
    Slightly later in the pipeline but correct — standard 5-stage approach

  RISC-V CONVENTION: Use Option C (MEM/WB forwarding handles WB-to-EX).
  If computing in ID (e.g., for early branch resolution), use Option B.
```

# STEP 6 — PHYSICAL REGISTER FILE (OUT-OF-ORDER)

```
For out-of-order processors (see skill 10), the architectural register file
is insufficient — rename table maps logical → physical register numbers.

PHYSICAL REGISTER FILE (PRF):
  Size: logical_regs + in_flight_instructions
  Example: 32 logical + 128 in-flight → 192 physical registers
  Each physical register holds a value that may not yet be committed

  ACCESS PATTERNS IN OoO:
    Issue:   read 2 physical source regs → PRF read port
    Execute: write 1 physical destination reg → PRF write port
    Issue width N → 2N read ports, N write ports
    4-wide OoO → 8 read + 4 write → large, power-hungry PRF

  PRF ORGANIZATION (clustered for port count reduction):
    Split into 2–4 clusters, each serving a subset of execution units
    Copies of values that span clusters → value duplication, more storage
    Trade-off: lower port count vs higher storage

  RETIREMENT vs SPECULATIVE STATE:
    PRF holds both committed (safe) and speculative values
    Commit: update architectural mapping (RAT) to point to committed PRF entry
    Mispredict: restore RAT snapshot, free speculative physical registers
    (detailed in skill 10 — OoO Execution)
```

# STEP 7 — FLOATING POINT REGISTER FILE

```
FLOAT REGISTER FILE SPECIFICATION:
  32 float registers (f0–f31)
  Width: 64 bits (double precision contains single)
  Separate from integer register file (separate array, no port sharing)

  Single precision (FSINGLE): occupies lower 32 bits; upper 32 undefined (NaN-boxed)
  Double precision (FDOUBLE): full 64 bits

PORT REQUIREMENTS:
  FPU typically: 3 source reads (FMA: A×B+C needs 3 operands), 1 write
  → 3R / 1W float register file

  Combined load/store address: float rs1 not needed (address from integer rs1)
  → float file read only for FP operands, not for address calculation

REGISTER FILE INTEGRATION:
  FP instructions: read from float RF
  FP load (FLD): result written to float RF (from D-cache)
  FP store (FSD): read float RS2 for data, integer RS1 for address
  FMVXF / FMVFX: move between integer and float RF (cross-file move)
```

# STEP 8 — POWER OPTIMIZATION

```
REGISTER FILE POWER REDUCTION:

Clock Gating per Register:
  Only clock registers that will be written this cycle
  Saves dynamic power on 31 out of 32 registers every cycle

Read Enable Gating:
  Disable read wordline if instruction doesn't need both operands
  (e.g., LUI only needs 1 source; SW needs both but special case)

Half-Select Avoidance (SRAM):
  In multi-ported arrays, un-selected cells can disturb due to partial bitline swing
  Use write assist (negative bitline voltage) and read-assist (low VDD read) circuits
  Critical for multi-port stability at low supply voltage

Banking for Power:
  Split 32-register file into 2 banks of 16
  Instruction decode selects which bank to activate
  Reduces total bitline switching energy per access by ~2×
```

# CHECKLIST — Before Moving to Control Unit Design

```
✅ Read port count determined (2 for in-order, 2×N for N-wide superscalar)
✅ Write port count determined (1 for in-order, N for N-wide)
✅ Implementation chosen: FF array (≤32 regs) or multi-port SRAM (>32)
✅ x0 hardwiring method chosen and RTL written
✅ Same-cycle write-before-read policy defined
✅ Write-through mux (or MEM/WB forwarding reliance) documented
✅ Async read latency accounted for in ID stage critical path
✅ Float register file ports listed (3R/1W for FMA)
✅ PRF size estimated for OoO (if applicable)
✅ Power gating strategy noted
→ NEXT: 07-ControlUnitDesign.md
```
