---
name: Pipeline Design
trigger: pipeline, 5-stage pipeline, IF ID EX MEM WB, instruction pipeline, fetch decode execute, pipeline stages, pipeline depth, pipeline throughput, CPI, pipeline registers, structural hazard, pipeline architecture
description: Second skill in the processor design pipeline. Read after ISA Design. Covers classic 5-stage pipeline construction, pipeline register definitions, stage responsibilities, throughput analysis, and stage boundary decisions before hazard logic is layered on.
prev_skill: 01-ISADesign.md
next_skill: 03-HazardDetectionForwarding.md
---

# ROLE
You are a microarchitect designing the pipeline backbone of a processor. Every stage you define is a latency commitment. Every register boundary you draw is a wire that must be routed. You balance throughput, latency, and silicon area — knowing that adding stages reduces cycle time but multiplies the hazard complexity that must be solved downstream.

# CORE PRINCIPLES
```
PIPELINE IS A FACTORY LINE — one instruction per stage per cycle at steady state
STAGE COUNT IS A TRADE-OFF — more stages → higher clock frequency, more hazards
PIPELINE REGISTERS HOLD ALL STATE — no implicit state between stages
CRITICAL PATH SETS YOUR CLOCK — every stage must finish within one cycle period
BALANCED STAGES — uneven stage latency is dead time; the slowest stage is your clock
FLUSH IS CHEAPER THAN STALL WHEN FREQUENT — branch mispredicts flush, data hazards stall
EVERY WIRE COSTS AREA AND POWER — forward only what you need through pipeline regs
```

# STEP 1 — STAGE COUNT DECISION

```
PIPELINE DEPTH TRADE-OFF TABLE:

  Depth   Clock Speed   Hazard Complexity   Branch Penalty   Use Case
  ─────   ───────────   ─────────────────   ──────────────   ─────────────────
  3       Low           Very Low            1–2 cycles       Microcontrollers
  5       Medium        Medium              3–4 cycles       Classic RISC (MIPS)
  8–10    High          High                6–8 cycles       Modern embedded
  14–20   Very High     Very High           10–15 cycles     Desktop CPUs (OoO)
  31+     Extreme       Extreme             20+ cycles       Netburst (cautionary tale)

DECISION:
  For a teaching / research processor: 5 stages (canonical)
  For high-performance in-order:       8–10 stages
  For out-of-order superscalar:        see 10-OutOfOrderExecution.md

CANONICAL 5-STAGE PIPELINE:
  IF   → Instruction Fetch
  ID   → Instruction Decode / Register Read
  EX   → Execute (ALU / Address Calc)
  MEM  → Memory Access
  WB   → Write Back
```

# STEP 2 — STAGE-BY-STAGE RESPONSIBILITIES

```
┌─────────────────────────────────────────────────────────┐
│  STAGE 1: IF — Instruction Fetch                        │
├─────────────────────────────────────────────────────────┤
│  INPUTS:  PC register                                   │
│  ACTIONS:                                               │
│    1. Send PC to instruction cache / memory             │
│    2. Receive 32-bit instruction word                   │
│    3. Compute PC+4 (next sequential PC)                 │
│    4. Mux between PC+4, branch target, jump target      │
│    5. Update PC register                                │
│  OUTPUTS (to IF/ID pipeline register):                  │
│    instruction[31:0]                                    │
│    pc_plus4[63:0]                                       │
│    pc[63:0]             (for branch target calc in ID)  │
│  CRITICAL PATH: I-cache hit latency + PC mux           │
│  HAZARD INVOLVEMENT: Branch → flush IF on mispredict    │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  STAGE 2: ID — Instruction Decode / Register Read       │
├─────────────────────────────────────────────────────────┤
│  INPUTS:  IF/ID pipeline register                       │
│  ACTIONS:                                               │
│    1. Decode opcode → control signals (9–14 signals)    │
│    2. Extract rs1, rs2, rd field indices                │
│    3. Read rs1, rs2 from register file (async read)     │
│    4. Sign-extend immediate (I/S/B/U/J-type)            │
│    5. Detect hazards → stall or forward                 │
│    6. Compute branch target: PC + sign_ext(imm<<1)      │
│  OUTPUTS (to ID/EX pipeline register):                  │
│    rs1_val[63:0], rs2_val[63:0]                         │
│    imm[63:0]                                            │
│    rd[4:0]                                              │
│    control_signals (alu_op, mem_read, mem_write,        │
│                     reg_write, branch, jump,            │
│                     mem_to_reg, alu_src)                │
│    pc[63:0], pc_plus4[63:0]                             │
│  CRITICAL PATH: Register file read + decode logic       │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  STAGE 3: EX — Execute                                  │
├─────────────────────────────────────────────────────────┤
│  INPUTS:  ID/EX pipeline register                       │
│  ACTIONS:                                               │
│    1. Select ALU operand A: rs1_val or PC               │
│    2. Select ALU operand B: rs2_val or imm              │
│    3. Execute ALU operation (add/sub/and/or/shift/cmp)  │
│    4. Apply forwarding from EX/MEM and MEM/WB regs      │
│    5. Evaluate branch condition (beq/bne/blt etc.)      │
│    6. Compute branch/jump target address                │
│    7. Signal branch taken/not-taken to IF stage         │
│  OUTPUTS (to EX/MEM pipeline register):                 │
│    alu_result[63:0]                                     │
│    rs2_val_fwd[63:0]    (for store data)                │
│    rd[4:0]                                              │
│    control_signals (mem_read, mem_write,                │
│                     reg_write, mem_to_reg)              │
│    zero_flag, branch_taken                              │
│  CRITICAL PATH: ALU carry chain (longest stage)         │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  STAGE 4: MEM — Memory Access                           │
├─────────────────────────────────────────────────────────┤
│  INPUTS:  EX/MEM pipeline register                      │
│  ACTIONS:                                               │
│    1. For loads:  send alu_result as address to D-cache │
│    2. For stores: send alu_result as addr, rs2 as data  │
│    3. Handle byte/halfword/word size from funct3        │
│    4. Sign or zero extend loaded value                  │
│    5. For non-memory ops: pass alu_result through       │
│  OUTPUTS (to MEM/WB pipeline register):                 │
│    mem_data[63:0]       (loaded value or alu_result)    │
│    alu_result[63:0]     (pass-through for non-loads)    │
│    rd[4:0]                                              │
│    control_signals (reg_write, mem_to_reg)              │
│  CRITICAL PATH: D-cache hit latency                     │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  STAGE 5: WB — Write Back                               │
├─────────────────────────────────────────────────────────┤
│  INPUTS:  MEM/WB pipeline register                      │
│  ACTIONS:                                               │
│    1. Mux: select mem_data (load) or alu_result (ALU)   │
│    2. Write selected value to register file at rd       │
│    3. reg_write control gate prevents spurious writes   │
│  OUTPUTS:                                               │
│    write_data → register file write port                │
│    rd[4:0]    → register file write address             │
│  NOTE: WB writes in first half of cycle;               │
│        ID reads in second half → resolves WB hazard     │
└─────────────────────────────────────────────────────────┘
```

# STEP 3 — PIPELINE REGISTER DEFINITIONS

```
Pipeline registers must capture ALL state needed by downstream stages.
Missing even one signal causes a bug impossible to find at simulation.

IF/ID REGISTER:
  Field           Width    Source
  ─────────────   ──────   ──────────────────
  instruction     32       I-cache output
  pc              64       PC register
  pc_plus4        64       PC + 4 adder

ID/EX REGISTER:
  Field           Width    Source
  ─────────────   ──────   ──────────────────
  rs1_val         64       Register file port A
  rs2_val         64       Register file port B
  imm             64       Immediate generator
  rs1             5        Instruction[19:15]
  rs2             5        Instruction[24:20]
  rd              5        Instruction[11:7]
  pc              64       Passed from IF/ID
  pc_plus4        64       Passed from IF/ID
  alu_op          4        Control unit
  alu_src         1        Control unit (rs2 vs imm)
  mem_read        1        Control unit
  mem_write       1        Control unit
  mem_size        2        funct3[1:0]
  mem_sign        1        funct3[2]
  reg_write       1        Control unit
  mem_to_reg      1        Control unit
  branch          1        Control unit
  jump            1        Control unit

EX/MEM REGISTER:
  Field           Width    Source
  ─────────────   ──────   ──────────────────
  alu_result      64       ALU output
  rs2_val_fwd     64       Forwarded rs2 (store data)
  rd              5        Passed from ID/EX
  mem_read        1        Passed
  mem_write       1        Passed
  mem_size        2        Passed
  mem_sign        1        Passed
  reg_write       1        Passed
  mem_to_reg      1        Passed

MEM/WB REGISTER:
  Field           Width    Source
  ─────────────   ──────   ──────────────────
  mem_data        64       D-cache output
  alu_result      64       Passed from EX/MEM
  rd              5        Passed
  reg_write       1        Passed
  mem_to_reg      1        Passed (selects mem_data vs alu_result)
```

# STEP 4 — THROUGHPUT AND LATENCY ANALYSIS

```
THROUGHPUT:
  Ideal CPI (cycles per instruction) = 1.0
  Real CPI = 1.0 + stall_cycles_avg + flush_cycles_avg

  stall_cycles_avg  ≈ load-use hazard rate × 1 cycle
  flush_cycles_avg  ≈ branch rate × misprediction rate × branch_penalty

  Example:
    Branch rate = 15%, misprediction rate = 30%, penalty = 3 cycles
    Load-use rate = 10%
    CPI ≈ 1.0 + 0.10 + (0.15 × 0.30 × 3) = 1.0 + 0.10 + 0.135 = 1.235

LATENCY (single instruction, cold):
  5-stage × 1 cycle/stage = 5 cycles from fetch to result
  (For out-of-order this becomes much more complex — see skill 10)

CLOCK PERIOD:
  T_clock = max(T_IF, T_ID, T_EX, T_MEM, T_WB) + T_setup + T_hold
  Pipeline registers add ~100–200 ps overhead per stage boundary
  Target: balance stages so no single stage is >20% longer than average
```

# STEP 5 — PC AND BRANCH MANAGEMENT

```
PC UPDATE LOGIC (priority order, highest first):
  1. Exception/trap target    (mepc → mtvec)     [highest]
  2. JALR target              (rs1 + imm)
  3. JAL target               (PC + imm)
  4. Branch taken target      (PC + imm<<1)
  5. PC + 4                   (sequential)       [default]

BRANCH RESOLUTION POINT:
  In 5-stage: branch condition evaluated at END of EX stage
  Branch target computed in EX stage
  → Branch penalty = 3 cycles (IF, ID, EX already in flight)
  → On mispredict: flush instructions in IF, ID, EX pipeline registers

FLUSH MECHANISM:
  When branch taken (or mispredict detected):
    IF/ID.instruction  ← NOP (0x00000013 = ADDI x0,x0,0)
    ID/EX.control_sigs ← all zeros (prevents register writes, memory ops)
    EX/MEM.control_sigs ← all zeros
  (Don't reset pipeline registers; just zero out control signals — cheaper)

STALL MECHANISM:
  When load-use hazard detected (see skill 03):
    PC ← hold (no increment)
    IF/ID ← hold (no advance)
    ID/EX ← insert bubble (zero control signals)
    EX/MEM, MEM/WB ← advance normally
```

# STEP 6 — PIPELINE TIMING DIAGRAM

```
CYCLE:          1    2    3    4    5    6    7    8    9
──────────────────────────────────────────────────────────
ADD x1,x2,x3:  IF   ID   EX   MEM  WB
SUB x4,x1,x5:       IF   ID   EX   MEM  WB
LW  x6,0(x1):            IF   ID   EX   MEM  WB
AND x7,x6,x8:                 IF   ID  ***  EX   MEM  WB
                                       ↑
                              Load-use stall (1 cycle bubble)

PIPELINE WITH BRANCH (branch at EX, taken):
CYCLE:          1    2    3    4    5    6    7    8
──────────────────────────────────────────────────────────
BEQ x1,x2:     IF   ID   EX   MEM  WB
I₁ (flushed):       IF   ID  [NOP] ← flushed
I₂ (flushed):            IF  [NOP] ← flushed
TARGET:                       IF   ID   EX   MEM  WB
                         ↑
              Branch resolved at end of EX → 2 wasted cycles
```

# CHECKLIST — Before Moving to Hazard Detection

```
✅ Pipeline depth chosen with justification
✅ All 5 stage responsibilities written out in full
✅ Every pipeline register field listed (name, width, source stage)
✅ PC update priority mux defined
✅ Branch penalty quantified
✅ Flush mechanism described (which registers, what gets zeroed)
✅ Stall mechanism described (hold logic for PC and IF/ID)
✅ Ideal CPI and estimated real CPI calculated
✅ Timing diagram drawn for normal flow, stall, and flush
→ NEXT: 03-HazardDetectionForwarding.md
```
