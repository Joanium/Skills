---
name: ALU and Datapath Design
trigger: ALU, arithmetic logic unit, adder, carry ripple, carry lookahead, carry select, multiplier, divider, shifter, datapath, functional unit, adder design, Booth encoding, barrel shifter, overflow detection, two's complement
description: Fifth skill in the processor design pipeline. Covers the internal microarchitecture of the ALU — adder topologies, multiplier algorithms, divider design, shifter implementation, overflow/carry detection, and wiring the ALU into the full EX-stage datapath.
prev_skill: 04-BranchPrediction.md
next_skill: 06-RegisterFileDesign.md
---

# ROLE
You are designing the arithmetic heart of the processor. Every clock tick, the ALU must produce a correct result within the allotted timing budget. You select adder topologies, understand carry-chain timing, design shifters without barrel-shifter routing nightmares, and define every multiplexer that feeds the ALU inputs.

# CORE PRINCIPLES
```
THE ALU IS ON THE CRITICAL PATH — every gate you add increases cycle time
CARRY PROPAGATION IS THE ENEMY — adder design is carry-chain management
SHIFT IS FREE IN SILICON, EXPENSIVE IN ROUTING — barrel shifters eat area
SEPARATE FAST AND SLOW OPERATIONS — divide is too slow for the main pipeline
INTEGER MULTIPLY CAN BE PIPELINED — 2–4 cycle latency is acceptable
OVERFLOW IS SILENT CORRUPTION — detect and trap; never silently wrap wrong results
DESIGN FOR SYNTHESIS, NOT SCHEMATICS — write behavioral RTL; let tools optimize
```

# STEP 1 — ALU OPERATION TABLE

```
alu_op   Operation           RTL expression
──────   ─────────────────   ──────────────────────────────────────
0000     ADD                 result = A + B
0001     SUB                 result = A + (~B) + 1   (B inverted + carry-in)
0010     AND                 result = A & B
0011     OR                  result = A | B
0100     XOR                 result = A ^ B
0101     SLL  (shift left)   result = A << B[5:0]
0110     SRL  (shift right)  result = A >> B[5:0]   (logical, zero-fill)
0111     SRA  (shift right)  result = A >>> B[5:0]  (arithmetic, sign-fill)
1000     SLT  (set lt)       result = ($signed(A) < $signed(B)) ? 1 : 0
1001     SLTU (set lt uns)   result = (A < B) ? 1 : 0
1010     LUI passthrough     result = B   (pass immediate for LUI)
1011     AUIPC               result = A + B   (PC + upper imm)
1100     MUL                 result = (A × B)[63:0]   (lower word)
1101     MULH                result = (A × B)[127:64] (upper word, signed)
1110     DIV  (handoff)      → sent to separate divide unit, multi-cycle
1111     REM  (handoff)      → sent to separate divide unit, multi-cycle

STATUS FLAGS:
  zero       = (result == 0)      → used by BEQ, BNE
  carry_out  = carry from bit 63  → used by unsigned comparisons, ADDC
  overflow   = carry63 XOR carry64 → used by signed overflow trap
  negative   = result[63]         → used by BLT, BGE
```

# STEP 2 — ADDER TOPOLOGIES

```
RIPPLE CARRY ADDER (RCA):
  Gate delay:   O(n) — n = bit width
  32-bit delay: ~32 gate delays (slow)
  Area:         Minimal
  Use case:     Only for sub-4-bit fields or ASIC synthesis handoff

  Concept:
    carry[0] = cin
    sum[i]   = A[i] XOR B[i] XOR carry[i]
    carry[i+1] = (A[i] AND B[i]) OR (carry[i] AND (A[i] XOR B[i]))

CARRY LOOKAHEAD ADDER (CLA):
  Gate delay:   O(log n) — dramatically faster
  32-bit delay: ~5 gate levels (for 4-bit groups)
  Area:         2–3× ripple
  Use case:     Standard choice for ALU adders

  GENERATE and PROPAGATE:
    G[i] = A[i] AND B[i]         (this bit generates a carry regardless of input)
    P[i] = A[i] XOR B[i]         (this bit propagates carry-in)
    C[i+1] = G[i] OR (P[i] AND C[i])

  GROUP LOOKAHEAD (4-bit block):
    G[3:0] = G3 | P3(G2 | P2(G1 | P1·G0))
    P[3:0] = P3·P2·P1·P0
    C4 = G[3:0] | P[3:0]·C0

  HIERARCHICAL: 4 × 4-bit CLA groups → 16-bit adder, then combine groups → 64-bit

CARRY SELECT ADDER (CSA for partial products):
  Compute both carry=0 and carry=1 simultaneously, select when carry arrives
  Gate delay: O(√n)
  Used inside multipliers and for fast final adders

RECOMMENDATION:
  32-bit ALU:  Two-level CLA (4-bit → 16-bit → 32-bit)
  64-bit ALU:  Three-level CLA or carry-select hybrid
  Let synthesis tools implement when targeting FPGA — use behavioral (+) operator
```

# STEP 3 — SUBTRACTION AND COMPARISON

```
SUBTRACTION VIA ADDER:
  A - B = A + (~B) + 1   (two's complement)
  Implementation: invert B bits, set carry_in = 1
  Same adder, just add an XOR gate on each B input and a carry_in mux

  sub_op   → B_inv[i] = B[i] XOR sub_op   (XOR with 1 = invert)
           → carry_in = sub_op

OVERFLOW DETECTION (signed):
  overflow = carry_in_to_MSB XOR carry_out_of_MSB
  i.e., overflow = carry[N-1] XOR carry[N]
  Overflow when: adding two positives → negative result, OR
                 adding two negatives → positive result

UNSIGNED OVERFLOW:
  Simply carry_out of the MSB adder

SLT (Set Less Than, signed):
  result = (negative XOR overflow)   ← 1 if A < B, signed
  Trick: compute A - B; if result is negative (considering overflow), A < B

SLTU (unsigned):
  result = carry_out of (A - B)     ← actually borrow bit
  If A < B unsigned → subtraction borrows → carry_out = 0
  So SLTU result = ~carry_out of adder when doing A + ~B + 1
```

# STEP 4 — SHIFTER DESIGN

```
BARREL SHIFTER:
  Performs N-bit shift in O(log N) delay using a cascade of mux layers
  For 64-bit shift: 6 layers of 64:1 muxes

  LAYER STRUCTURE (for left shift):
    Layer 0: shift by 1 if shamt[0] == 1, else pass through
    Layer 1: shift by 2 if shamt[1] == 1, else pass through
    Layer 2: shift by 4 if shamt[2] == 1, else pass through
    Layer 3: shift by 8 if shamt[3] == 1, else pass through
    Layer 4: shift by 16 if shamt[4] == 1, else pass through
    Layer 5: shift by 32 if shamt[5] == 1, else pass through

  Total: 6 layers × 64 mux cells = 384 2-to-1 muxes for 64-bit barrel shifter

RIGHT SHIFT UNIFIED DESIGN:
  Compute SRL and SRA with a single shifter:
  Fill bit = SRA ? A[63] : 1'b0   (sign bit for arithmetic, 0 for logical)
  Route fill_bit into vacated positions

  TRICK: Right-shift = left-reverse → shift → right-reverse
         Saves routing complexity; common optimization

LEFT SHIFT:
  Fill bit is always 0 (zeros shift in from LSB side)

RTL IMPLEMENTATION (let synthesis infer barrel shifter):
  case (alu_op[1:0])
    2'b01: result = A << B[5:0];             // SLL
    2'b10: result = A >> B[5:0];             // SRL
    2'b11: result = $signed(A) >>> B[5:0];   // SRA (Verilog >>>)
  endcase
```

# STEP 5 — MULTIPLIER DESIGN

```
NAIVE APPROACH: shift-and-add
  64-bit multiply → 64 additions → 64 cycles → too slow

BOOTH ENCODING (RADIX-2):
  Converts multiplier bits into signed digit representation
  Reduces partial product count by 2×
  Handles negative numbers correctly in two's complement

  BOOTH TABLE:
    B[i+1] B[i] B[i-1]   Operation
    0      0    0         0 (no op)
    0      0    1         +A
    0      1    0         +A
    0      1    1         +2A
    1      0    0         -2A
    1      0    1         -A
    1      1    0         -A
    1      1    1         0 (no op)

RADIX-4 BOOTH (MODIFIED BOOTH):
  Groups of 3 overlapping bits → one partial product per 2 bits
  64-bit multiply → 32 partial products → 5 compression stages

WALLACE TREE REDUCTION:
  Compress 32 partial products to 2 using carry-save adders (CSAs)
  CSA takes 3 inputs → sum + carry (3:2 compressor)
  Tree of CSAs reduces to 2 operands in O(log N) stages
  Final: one 128-bit CLA adder

TIMING:
  Booth encoding:      1 cycle (combinational)
  Wallace tree (32→2): 5 CSA levels
  Final CLA:           1 CLA latency
  Total:               2–4 pipeline stages (depending on clock target)

PIPELINED MULTIPLIER:
  Cut the Wallace tree at natural pipeline register insertion points
  2-stage: Booth + partial products | Wallace tree + CLA
  4-stage: finer cuts for higher clock frequency

SIMPLE 32×32 ITERATIVE MULTIPLIER (for embedded, area-optimized):
  Use shift-and-add, 1 bit per cycle = 32 cycles
  Enough for low-frequency embedded cores; not for performance

HIGH / LOW PRODUCT:
  64×64 → 128-bit result
  MUL   → lower 64 bits [63:0]
  MULH  → upper 64 bits [127:64]  (signed × signed)
  MULHU → upper 64 bits (unsigned × unsigned)
  MULHSU→ upper 64 bits (signed × unsigned)
```

# STEP 6 — DIVIDER DESIGN

```
DIVISION IS ALWAYS MULTI-CYCLE (32–64 cycles for iterative dividers)
NEVER PUT DIVISION IN THE MAIN ALU PIPELINE

DESIGN CHOICE:
  Restoring Division:     Simple, slow (1 bit/cycle)
  Non-Restoring Division: Moderate speed, moderate complexity
  SRT Division (Radix-4): Used in real processors; 2 bits/cycle

INTERFACE WITH PIPELINE:
  DIV instruction issues to a separate functional unit
  Pipeline stalls (or issues other instructions to other units in OoO)
  Result returned after 32–64 cycles
  Hardware interlock: result-valid signal → allow WB

DIVIDE BY ZERO:
  Check operand B == 0 before starting
  Raise exception: cause = DIVIDE_BY_ZERO
  DIV by zero → result = all-ones (RISC-V convention), no trap (optional)
  DIVU by zero → result = MAX_UINT
  REM by zero → result = dividend

DIVIDE EARLY OUT:
  Check if |dividend| < |divisor| → quotient = 0, remainder = dividend (1 cycle)
  Check if divisor == 1 → quotient = dividend (1 cycle)
  These optimizations handle many practical cases fast
```

# STEP 7 — ALU DATAPATH MUX TREE

```
EX STAGE DATAPATH (all multiplexers):

     PC ──────┐
  rs1_val ────┼──[2:1 MUX]─── ALU_A ──┐
  fwd_exmem──┘ (alu_src_a)             │
  fwd_memwb──┘                         ├──[ALU]──→ alu_result
                                        │
  rs2_val ────┐                        │
  imm ────────┼──[2:1 MUX]─── ALU_B ──┘
  fwd_exmem──┤ (alu_src_b)
  fwd_memwb──┘

  ALU_A MUX (3:1 with forwarding):
    sel 00 → ID/EX.rs1_val              (no hazard)
    sel 10 → EX/MEM.alu_result          (forward from EX/MEM)
    sel 01 → MEM/WB.forward_val         (forward from MEM/WB)

  ALU_B MUX (4:1 with forwarding + immediate):
    sel 00 → ID/EX.rs2_val              (no hazard)
    sel 01 → ID/EX.imm                  (ALU-immediate ops)
    sel 10 → EX/MEM.alu_result          (forward)
    sel 11 → MEM/WB.forward_val         (forward)

  WB RESULT MUX (MEM/WB stage):
    sel 0  → alu_result                 (ALU ops, stores)
    sel 1  → mem_data                   (loads)
    sel 2  → pc_plus4                   (JAL/JALR link address)

CONTROL SIGNALS TO ALU:
  alu_op[3:0]:   operation select (from control unit, see skill 07)
  alu_src_a:     0 = rs1, 1 = PC
  alu_src_b:     0 = rs2, 1 = imm
```

# STEP 8 — TIMING AND CRITICAL PATH

```
CRITICAL PATH THROUGH ALU (64-bit):
  Mux delay (forwarding select):   ~2 FO4 delays
  Carry lookahead adder (64-bit):  ~12 FO4 delays
  Overflow + flag logic:           ~2 FO4 delays
  Output mux to pipeline reg:      ~1 FO4 delay
  Setup time of pipeline register: ~1 FO4 delay
  TOTAL:                           ~18 FO4 delays

  FO4 delay at 28nm: ~20 ps → EX stage = ~360 ps → allows ~2.7 GHz clock
  FO4 delay at 7nm:  ~10 ps → EX stage = ~180 ps → allows ~5.5 GHz clock

OPTIMIZATION LEVERS:
  Reduce adder critical path: use carry-select or Kogge-Stone adder
  Reduce mux critical path:   forward earlier (put forwarding mux before, not after)
  Pipeline the EX stage:      split into EX1 (ALU) and EX2 (compare + flag)
  Move flags earlier:         compute zero flag from carry lookahead group signals
```

# CHECKLIST — Before Moving to Register File Design

```
✅ Full ALU operation table with opcodes and RTL expressions
✅ Status flags defined: zero, carry, overflow, negative
✅ Adder topology chosen (CLA recommended), carry logic documented
✅ Subtraction implemented as add-with-invert (shared adder)
✅ Overflow detection formula written (carry[N-1] XOR carry[N])
✅ Barrel shifter layer structure defined
✅ SRA implemented (sign-fill vs zero-fill)
✅ Multiplier algorithm chosen (Booth + Wallace tree recommended)
✅ Divider: separate unit, multi-cycle, stall interface defined
✅ Divide-by-zero behavior specified
✅ All EX-stage muxes listed with select encodings
✅ Critical path estimated (FO4 delays)
→ NEXT: 06-RegisterFileDesign.md
```
