---
name: Hazard Detection and Forwarding
trigger: hazard, data hazard, structural hazard, control hazard, forwarding, bypassing, stall, pipeline bubble, load-use hazard, RAW hazard, WAR hazard, WAW hazard, forwarding unit, hazard detection unit
description: Third skill in the processor design pipeline. Read after Pipeline Design. Covers all three hazard classes, forwarding path logic, hazard detection unit conditions, stall insertion, and the MUX control equations needed to implement correct bypass logic.
prev_skill: 02-PipelineDesign.md
next_skill: 04-BranchPrediction.md
---

# ROLE
You are the correctness engineer for the pipeline. A processor with an unresolved hazard produces silently wrong results — worse than a crash. You enumerate every possible data dependency scenario, derive the MUX select logic from first principles, and verify it with dependency matrices before writing a single line of RTL.

# CORE PRINCIPLES
```
HAZARD = RESULT NEEDED BEFORE IT IS AVAILABLE
FORWARD FIRST — forwarding eliminates stalls; stalling is the fallback
DETECT BEFORE EXECUTE — hazard detection is in ID, forwarding is in EX
EVERY FORWARDING PATH IS A LONG WIRE — costs area and timing margin
LOAD-USE IS UNAVOIDABLE IN 5-STAGE — always requires one stall cycle
HAZARD CONDITIONS ARE BOOLEAN EQUATIONS — derive them, don't guess them
WAR AND WAW ARE FREE IN IN-ORDER PIPELINES — only RAW is dangerous
```

# STEP 1 — HAZARD TAXONOMY

```
THREE CLASSES OF HAZARDS:

1. STRUCTURAL HAZARD
   Definition: Two instructions need the same hardware resource in the same cycle.
   Example:    Combined instruction/data memory → LW and IF both need memory.
   Solution:   Separate I-cache and D-cache (Harvard architecture). Always do this.
               OR stall one of the conflicting stages (expensive).
   In 5-stage with separate caches: structural hazards are eliminated.

2. DATA HAZARD (most common)
   Definition: An instruction depends on the result of a not-yet-complete instruction.

   Sub-types:
     RAW (Read After Write) — the only dangerous one in in-order pipelines
       I1 writes Rd, I2 reads Rs1/Rs2 where Rs = Rd, before I1 writes back
     WAR (Write After Read) — harmless in in-order (I1 always reads before I2 writes)
     WAW (Write After Write) — harmless in in-order (WB is sequential)

   RAW EXAMPLE:
     ADD x1, x2, x3    ← produces x1 at end of EX cycle 3
     SUB x4, x1, x5    ← needs x1 at START of EX cycle 4 (1-cycle gap: forward from EX/MEM)
     AND x5, x1, x6    ← needs x1 at START of EX cycle 5 (2-cycle gap: forward from MEM/WB)
     OR  x6, x1, x7    ← needs x1 at START of EX cycle 6 (3-cycle gap: available in reg file)

3. CONTROL HAZARD
   Definition: The pipeline fetches wrong instructions after a branch/jump.
   Solution:   Predict (see skill 04) or stall (always-not-taken default).
   Penalty:    3 cycles worst case in 5-stage (if resolved at EX stage end).
```

# STEP 2 — DATA FORWARDING PATHS

```
FORWARDING UNIT sits at the EX stage inputs.
It intercepts rs1_val and rs2_val and substitutes forwarded values.

FORWARDING SOURCES (in priority order — always take most recent):
  Priority 1: EX/MEM.alu_result   (from 1 instruction ago)
  Priority 2: MEM/WB.mem_or_alu   (from 2 instructions ago — load or ALU)
  Priority 3: Register file value (no hazard, or resolved by WB)

FORWARDING MUX CONTROL — OPERAND A (rs1):

  ForwardA = 10  if:
    EX/MEM.reg_write == 1
    AND EX/MEM.rd != 0                  (x0 never written)
    AND EX/MEM.rd == ID/EX.rs1
    → Forward EX/MEM.alu_result to ALU input A

  ForwardA = 01  if:
    MEM/WB.reg_write == 1
    AND MEM/WB.rd != 0
    AND MEM/WB.rd == ID/EX.rs1
    AND NOT (EX/MEM.reg_write == 1      (Priority 1 not taken)
             AND EX/MEM.rd != 0
             AND EX/MEM.rd == ID/EX.rs1)
    → Forward MEM/WB result to ALU input A

  ForwardA = 00  → Use rs1_val from ID/EX register (no hazard)

FORWARDING MUX CONTROL — OPERAND B (rs2):
  (identical conditions, substituting rs2 for rs1)

  ForwardB = 10  → Forward EX/MEM.alu_result to ALU input B
  ForwardB = 01  → Forward MEM/WB result to ALU input B
  ForwardB = 00  → Use rs2_val from ID/EX register

  NOTE: ForwardB affects the rs2 that feeds the ALU.
        Stores also need the forwarded rs2 for the STORE DATA path —
        this is a separate 3rd mux at the MEM stage input.
```

# STEP 3 — LOAD-USE HAZARD DETECTION

```
LOAD-USE IS SPECIAL:
  A load result is not available until the END of MEM stage.
  So even with forwarding, the instruction immediately after a load
  cannot execute at the normal cycle — it needs to wait one cycle.

LOAD-USE HAZARD CONDITION:
  hazard = (ID/EX.mem_read == 1)                   ← current instr in EX is a load
            AND (
              (ID/EX.rd == IF/ID.rs1) OR            ← dependent on load destination
              (ID/EX.rd == IF/ID.rs2)
            )
            AND (ID/EX.rd != 0)                     ← x0 is never a real destination

  IF hazard == 1:
    ACTION 1: Stall PC          (PC.write_enable = 0)
    ACTION 2: Stall IF/ID reg   (IF/ID.write_enable = 0)
    ACTION 3: Insert bubble:    (ID/EX.control_signals ← all zeros)
    RESULT: One NOP injected, load completes MEM, forwarding handles the rest

LOAD-USE TIMELINE:
  Cycle:    1    2    3    4    5    6    7    8
  LW x1:   IF   ID   EX   MEM  WB
  ADD x2:       IF   ID  [NOP] ID   EX   MEM  WB
                           ↑         ↑
                        bubble    MEM/WB forwards x1 here
```

# STEP 4 — FORWARDING LOGIC TRUTH TABLE

```
DEPENDENCY MATRIX — 5-STAGE, ALL RAW CASES:

  Producer    Consumer    Gap    Resolution
  ─────────   ─────────   ────   ──────────────────────────────────────
  ADD x1      I+1 (EX)    1      Forward EX/MEM.alu_result → ALU A or B
  ADD x1      I+2 (EX)    2      Forward MEM/WB.alu_result → ALU A or B
  ADD x1      I+3+ (EX)   3+     No forward needed (WB done, reg file current)
  LW  x1      I+1 (EX)    1      STALL 1 cycle, then MEM/WB forward
  LW  x1      I+2 (EX)    2      Forward MEM/WB.mem_data → ALU A or B
  LW  x1      I+3+ (EX)   3+     No forward needed

FORWARDING FROM MEM/WB — SELECT LOGIC:
  MEM/WB forwards mem_data (if mem_to_reg == 1) OR alu_result (if mem_to_reg == 0)
  This distinction is critical: a load and an ALU op share the same forwarding path
  but supply different values.

  MEM/WB.forward_val = (MEM/WB.mem_to_reg == 1) ? MEM/WB.mem_data
                                                  : MEM/WB.alu_result
```

# STEP 5 — FULL FORWARDING UNIT (RTL-LEVEL EQUATIONS)

```verilog
// Forwarding Unit — combinational logic, no state

module forwarding_unit (
  input  [4:0] id_ex_rs1,    id_ex_rs2,
  input  [4:0] ex_mem_rd,    mem_wb_rd,
  input        ex_mem_regwrite, mem_wb_regwrite,
  output reg [1:0] forwardA, forwardB
);

  always @(*) begin
    // --- ForwardA ---
    forwardA = 2'b00; // default: no forward
    // Priority 2: MEM/WB forward (check first so Priority 1 can override)
    if (mem_wb_regwrite && (mem_wb_rd != 0) && (mem_wb_rd == id_ex_rs1))
      forwardA = 2'b01;
    // Priority 1: EX/MEM forward (overrides MEM/WB)
    if (ex_mem_regwrite && (ex_mem_rd != 0) && (ex_mem_rd == id_ex_rs1))
      forwardA = 2'b10;

    // --- ForwardB ---
    forwardB = 2'b00;
    if (mem_wb_regwrite && (mem_wb_rd != 0) && (mem_wb_rd == id_ex_rs2))
      forwardB = 2'b01;
    if (ex_mem_regwrite && (ex_mem_rd != 0) && (ex_mem_rd == id_ex_rs2))
      forwardB = 2'b10;
  end

endmodule
```

# STEP 6 — HAZARD DETECTION UNIT (RTL-LEVEL EQUATIONS)

```verilog
// Hazard Detection Unit — sits in ID stage, combinational

module hazard_detection_unit (
  input  [4:0] if_id_rs1,   if_id_rs2,
  input  [4:0] id_ex_rd,
  input        id_ex_memread,
  output reg   stall
);

  always @(*) begin
    stall = 1'b0;
    if (id_ex_memread &&
        (id_ex_rd != 0) &&
        ((id_ex_rd == if_id_rs1) || (id_ex_rd == if_id_rs2)))
      stall = 1'b1;
  end

endmodule

// In top-level datapath:
//   PC.write_enable      = ~stall
//   IF/ID.write_enable   = ~stall
//   ID/EX (bubble):      if stall → zero out all control signals in ID/EX next cycle
```

# STEP 7 — STRUCTURAL HAZARD ELIMINATION CHECKLIST

```
MEMORY PORT CONFLICTS:
  ✅ Use separate I-cache and D-cache (Harvard) — eliminates fetch/MEM conflict
  ✅ Register file: 2 read ports + 1 write port (standard for 5-stage RISC)
  ✅ If only 1 memory: stall MEM stage during IF — add mem_busy → PC hold

WRITE PORT CONFLICTS (in superscalar, not 5-stage):
  Multiple instructions completing WB in same cycle → need multiple write ports
  OR prioritize and re-queue — see skill 10.

ALU CONFLICTS:
  In-order 5-stage: only one instruction in EX per cycle — no ALU conflict
  In superscalar: need one ALU per execution slot

CACHE PORT CONFLICTS:
  Simultaneous load + store: handled by load-store unit ordering (see skill 08)
```

# STEP 8 — CORNER CASES AND GOTCHAS

```
GOTCHA 1: Double Data Hazard
  ADD x1, x2, x3
  ADD x1, x4, x5    ← overwrites x1 (producer 1 is stale)
  SUB x6, x1, x7    ← must get x1 from SECOND ADD, not first

  SOLUTION: Priority 1 (EX/MEM) always wins over Priority 2 (MEM/WB).
  The forwarding condition for MEM/WB includes the guard:
    "AND NOT (EX/MEM.rd == rs AND EX/MEM.regwrite == 1)"

GOTCHA 2: Store Forwarding
  ADD x1, x2, x3
  SW  x1, 0(x4)     ← rs2 of SW is the data to store, not address
  Need ForwardB to feed the STORE DATA path, not just the ALU input.
  Add a separate forward mux at the EX/MEM → MEM data input.

GOTCHA 3: x0 Forwarding
  x0 is always 0. A write to x0 must NOT be forwarded.
  Guard ALL forwarding conditions with: (rd != 5'b00000)

GOTCHA 4: Branch + RAW hazard (back-to-back)
  ADD x1, x2, x3
  BEQ x1, x4, label   ← branch needs x1 from ADD, branch resolves in EX
  Forwarding handles EX→EX if branch condition is evaluated in EX.
  If branch is evaluated in ID for early resolution, forwarding to ID is needed
  (longer wire, higher cost — usually not worth it in 5-stage).

GOTCHA 5: JALR + forwarded register
  LW  x1, 0(x2)
  JALR x3, x1, 0    ← JALR uses x1 as base — load-use + jump!
  Must stall 1 cycle, THEN forward from MEM/WB.
```

# CHECKLIST — Before Moving to Branch Prediction

```
✅ All three hazard classes defined (structural, data, control)
✅ RAW forwarding conditions written as exact boolean equations
✅ ForwardA and ForwardB MUX select truth table complete
✅ MEM/WB forward_val mux defined (distinguishes load vs ALU)
✅ Load-use hazard detection condition written in RTL
✅ Stall mechanism: PC hold + IF/ID hold + ID/EX bubble
✅ Double data hazard corner case handled (EX/MEM priority)
✅ Store forwarding path (separate from ALU input B) defined
✅ x0 guard on all forwarding conditions
✅ Forwarding unit RTL written
✅ Hazard detection unit RTL written
→ NEXT: 04-BranchPrediction.md
```
