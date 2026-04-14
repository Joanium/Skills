---
name: Control Unit Design
trigger: control unit, control signals, main decoder, ALU decoder, hardwired control, microcode, control ROM, PLA, control signal generation, instruction decode, opcode decode, control path, finite state machine control
description: Seventh skill in the processor design pipeline. Covers hardwired control unit design — decoding opcodes into control signals, building the main decoder truth table, ALU control logic, multi-cycle FSM design, and comparing hardwired vs microcode approaches.
prev_skill: 06-RegisterFileDesign.md
next_skill: 08-CacheDesign.md
---

# ROLE
You are wiring the brain of the processor. The control unit translates a 32-bit instruction into a dozen signals that direct every multiplexer, register write enable, and memory access in the datapath. One wrong signal and you get a silent data corruption. You enumerate every instruction, derive every signal, and verify the truth table before writing RTL.

# CORE PRINCIPLES
```
CONTROL IS DECODE — the control unit is a lookup from opcode to signals
HARDWIRED IS FAST — pure combinational logic; no microcode ROM delay
MICROCODE IS FLEXIBLE — iterate without respin; use for complex instructions
ONE TRUTH TABLE ROW PER INSTRUCTION — no exceptions, no shortcuts
X (DON'T CARE) IS NOT ZERO — document what don't-cares mean
UNDEFINED OPCODES MUST BE HANDLED — raise illegal instruction exception
CONTROL SIGNAL POLARITY — define active-high or active-low per signal and stick to it
```

# STEP 1 — CONTROL SIGNAL INVENTORY

```
For a 5-stage RISC-V-style pipeline, the minimum set of control signals:

  Signal          Width   Function
  ─────────────   ─────   ──────────────────────────────────────────────────
  reg_write       1       Enable write to rd in WB stage
  mem_to_reg      2       WB mux: 00=ALU result, 01=mem data, 10=PC+4
  mem_read        1       Enable D-cache read (load)
  mem_write       1       Enable D-cache write (store)
  mem_size        2       00=byte, 01=halfword, 10=word, 11=doubleword
  mem_sign_ext    1       1=sign-extend load, 0=zero-extend
  alu_src_a       1       ALU A: 0=rs1, 1=PC
  alu_src_b       1       ALU B: 0=rs2, 1=immediate
  alu_op          4       ALU operation select (see skill 05 table)
  branch          1       Instruction is a conditional branch
  jump            1       Instruction is JAL or JALR (unconditional)
  is_jalr         1       Selects rs1+imm target (JALR) vs PC+imm (JAL)
  csr_op          2       00=none, 01=CSRRW, 10=CSRRS, 11=CSRRC
  ecall           1       System call trap
  ebreak          1       Breakpoint trap
  illegal         1       Undefined/illegal instruction → raise exception

  TOTAL: 16–20 signals depending on extensions

WHERE SIGNALS LIVE IN THE PIPELINE:
  Computed in: ID stage (combinational decode)
  Travel through: ID/EX → EX/MEM → MEM/WB (only signals still needed downstream)
  Used in:
    EX stage:  alu_op, alu_src_a, alu_src_b, branch, jump, is_jalr
    MEM stage: mem_read, mem_write, mem_size, mem_sign_ext
    WB stage:  reg_write, mem_to_reg
    Trap:      ecall, ebreak, illegal (immediate)
```

# STEP 2 — MAIN DECODER TRUTH TABLE

```
The main decoder takes opcode[6:0] (and sometimes funct3, funct7) → control signals.
In RISC-V, opcode[1:0] == 11 for all 32-bit instructions.

OPCODE         INSTRUCTION TYPE   reg_w  mem→reg  mem_r  mem_w  alu_src_b  branch  jump
─────────────  ─────────────────  ─────  ───────  ─────  ─────  ─────────  ──────  ────
0110011 (R)    ALU R-type         1      00       0      0      0 (rs2)    0       0
0010011 (I)    ALU I-type         1      00       0      0      1 (imm)    0       0
0000011 (L)    Loads              1      01       1      0      1 (imm)    0       0
0100011 (S)    Stores             0      XX       0      1      1 (imm)    0       0
1100011 (B)    Branches           0      XX       0      0      0 (rs2)    1       0
1101111 (J)    JAL                1      10       0      0      X          0       1
1100111 (JI)   JALR               1      10       0      0      1 (imm)    0       1
0110111 (U)    LUI                1      00       0      0      1 (imm)    0       0
0010111 (UA)   AUIPC              1      00       0      0      1 (imm)    0       0
1110011 (Sys)  ECALL/EBREAK/CSR   *      *        *      *      *          0       0
               Undefined          0      XX       0      0      X          0       0  + illegal=1

NOTES:
  XX = don't care (mem_to_reg irrelevant when reg_write=0)
  Stores: rd field is imm[4:0] in encoding — reg_write=0 is critical
  Branch: alu_src_b=0 (use rs2 for comparison), but imm used for target (separate adder)
```

# STEP 3 — ALU DECODER

```
The ALU decoder takes alu_op[1:0] from main decoder + funct3[2:0] + funct7[5] → alu_ctrl[3:0]

Main decoder sends a 2-bit partial opcode:
  alu_op = 00 → ALU performs ADD   (loads, stores, AUIPC target)
  alu_op = 01 → ALU performs SUB   (branches: compute A-B, check flags)
  alu_op = 10 → Use funct3+funct7  (R-type and I-type ALU ops)
  alu_op = 11 → LUI passthrough    (no ALU needed; imm goes direct)

ALU DECODER TABLE (when alu_op == 10):
  funct7[5]  funct3   Instruction   alu_ctrl
  ─────────  ──────   ───────────   ────────
  0          000      ADD / ADDI    0000
  1          000      SUB           0001
  0          001      SLL / SLLI    0101
  0          010      SLT / SLTI    1000
  0          011      SLTU / SLTIU  1001
  0          100      XOR / XORI    0100
  0          101      SRL / SRLI    0110
  1          101      SRA / SRAI    0111
  0          110      OR  / ORI     0011
  0          111      AND / ANDI    0010

  NOTE: funct7[5] distinguishes ADD from SUB and SRL from SRA.
        For I-type, funct7 field is the upper 7 bits of imm (imm[11:5]).
        SRAI encodes funct7[5]=1; this overlaps with immediate encoding.
        Must mask imm[10] = 0 for SRLI; imm[10] = 1 for SRAI.
```

# STEP 4 — HARDWIRED CONTROL IMPLEMENTATION (RTL)

```verilog
module main_decoder (
  input  [6:0] opcode,
  output reg   reg_write, mem_read, mem_write, branch, jump, is_jalr,
  output reg   alu_src_b,
  output reg [1:0] alu_op, mem_to_reg,
  output reg   illegal
);
  localparam R_TYPE = 7'b0110011;
  localparam I_TYPE = 7'b0010011;
  localparam LOAD   = 7'b0000011;
  localparam STORE  = 7'b0100011;
  localparam BRANCH = 7'b1100011;
  localparam JAL    = 7'b1101111;
  localparam JALR   = 7'b1100111;
  localparam LUI    = 7'b0110111;
  localparam AUIPC  = 7'b0010111;
  localparam SYSTEM = 7'b1110011;

  always @(*) begin
    // Safe defaults — all signals inactive
    {reg_write, mem_read, mem_write, branch, jump, is_jalr, alu_src_b} = 7'b0;
    {alu_op, mem_to_reg} = 4'b0;
    illegal = 1'b0;

    case (opcode)
      R_TYPE: begin reg_write=1; alu_op=2'b10; end
      I_TYPE: begin reg_write=1; alu_src_b=1; alu_op=2'b10; end
      LOAD:   begin reg_write=1; alu_src_b=1; mem_read=1; mem_to_reg=2'b01; end
      STORE:  begin mem_write=1; alu_src_b=1; end
      BRANCH: begin branch=1; alu_op=2'b01; end
      JAL:    begin reg_write=1; jump=1; mem_to_reg=2'b10; end
      JALR:   begin reg_write=1; jump=1; is_jalr=1; alu_src_b=1; mem_to_reg=2'b10; end
      LUI:    begin reg_write=1; alu_src_b=1; alu_op=2'b11; end
      AUIPC:  begin reg_write=1; alu_src_b=1; alu_op=2'b00; end
      SYSTEM: begin /* handled by separate CSR decoder */ end
      default: illegal = 1'b1;
    endcase
  end
endmodule
```

# STEP 5 — MULTI-CYCLE FSM (ALTERNATIVE TO PIPELINING)

```
For area-constrained designs (microcontrollers), a multi-cycle datapath
shares hardware across stages using a finite state machine (FSM) controller.

STATES FOR RISC-V MULTI-CYCLE DESIGN:
  S0: IF      — fetch instruction from memory, PC+4 → PC
  S1: ID      — decode instruction, read register file
  S2: EX      — ALU execute or compute memory address
  S3: MEM_R   — memory read (for loads)
  S3: MEM_W   — memory write (for stores)
  S4: WB      — write result to register file

STATE TRANSITION TABLE:
  Current   Next State by instruction type
  ────────  ────────────────────────────────────────────────────
  IF(S0)    → ID(S1) always
  ID(S1)    → EX(S2) always
  EX(S2)    → MEM_R(S3)  if LOAD
              MEM_W(S3)  if STORE
              WB(S4)     if R-type or I-type
              IF(S0)     if BRANCH (branch resolved in EX)
              WB(S4)     if JAL/JALR (link addr written in WB)
  MEM(S3)   → WB(S4)    if LOAD
              IF(S0)     if STORE (no WB needed)
  WB(S4)    → IF(S0) always

CONTROL SIGNALS PER STATE:
  State    PCWrite  IorD  MemRead  MemWrite  MemToReg  IRWrite  RegWrite  ALUSrcA  ALUSrcB  ALUOp
  ───────  ───────  ────  ───────  ────────  ────────  ───────  ────────  ───────  ───────  ─────
  IF       1        0     1        0         X         1        0         0(PC)    01(+4)   00(ADD)
  ID       0        X     0        0         X         0        0         0(PC)    11(imm)  00(ADD)
  EX(R)    0        X     0        0         X         0        0         1(A)     00(rs2)  10(ALU)
  EX(I)    0        X     0        0         X         0        0         1(A)     10(imm)  10(ALU)
  EX(Load) 0        X     0        0         X         0        0         1(A)     10(imm)  00(ADD)
  MEM_R    0        1     1        0         X         0        0         X        X        X
  MEM_W    0        1     0        1         X         0        0         X        X        X
  WB(Load) 0        X     0        0         1(mem)    0        1         X        X        X
  WB(ALU)  0        X     0        0         0(ALU)    0        1         X        X        X
  BEQ      1(cond)  0     0        0         X         0        0         1(A)     00(rs2)  01(SUB)

FSM REGISTERS:
  IR  (Instruction Register): holds fetched instruction between cycles
  MDR (Memory Data Register): holds data returned from memory
  A, B: temp registers for rs1, rs2 read in ID
  ALUOut: holds ALU result between cycles

TRADE-OFF:
  Multi-cycle: lower area (shared datapath), lower max frequency, simpler control
  Pipelined:   higher throughput, higher area, complex hazard logic
```

# STEP 6 — HARDWIRED VS MICROCODE DECISION

```
HARDWIRED CONTROL:
  Pros:   Fast (pure combinational), no ROM access latency
  Cons:   Fixed in silicon (bugs require respin), complex for CISC
  Use:    RISC designs, simple ISAs, high-performance targets
  Cost:   ~500–2000 gates for a 5-stage RISC decoder

MICROCODE (CONTROL ROM):
  Pros:   Flexible (patch bugs with ROM update), handles complex CISC ops
  Cons:   ROM access adds latency (1–2 cycles), harder to optimize timing
  Use:    x86 microarchitectures, complex instructions (string ops, complex FP)
  Cost:   ROM storage, sequencer logic, multi-cycle overhead

HYBRID (common in x86):
  Simple instructions → hardwired fast path (1 µop per clock)
  Complex instructions → microcode ROM (2–100+ µops)
  Threshold: if instruction needs >4 µops → use microcode

MICROCODE ROM STRUCTURE:
  Width: control_signals (32–64 bits per µop)
  Depth: number of µops in the microcode store (typically 1K–8K entries)
  Address: index from instruction opcode + sequencer state
  Output: latched control signals for current µop

SEQUENCER:
  Holds current µop address
  Next address = current + 1 (sequential) OR branch from ROM field
  Termination: last µop has "done" bit → return to fetch
```

# STEP 7 — ILLEGAL INSTRUCTION HANDLING

```
UNDEFINED OPCODES:
  Any opcode not in the decode table → illegal = 1
  Pipeline: squash instruction (treat as NOP for datapath)
  Trap unit: raise exception CAUSE = ILLEGAL_INSTRUCTION
  mepc = PC of illegal instruction
  mtval = illegal instruction bits [31:0]

PRIVILEGE VIOLATIONS:
  CSR access from U-mode to M-mode only register → illegal
  MRET in U-mode → illegal
  Check: (required_privilege > current_privilege) → illegal

MISALIGNED INSTRUCTIONS:
  In RV32/64: instructions must be 4-byte aligned
  PC[1:0] != 00 → INSTRUCTION_ADDRESS_MISALIGNED exception
  (Unless compressed ISA extension C is supported — 2-byte alignment)

ILLEGAL INSTRUCTION PRIORITY:
  External interrupt > hardware error > page fault > illegal instruction
  Illegal instruction is a synchronous exception — precise
```

# CHECKLIST — Before Moving to Cache Design

```
✅ Full control signal inventory (name, width, function, stage)
✅ Main decoder truth table: one row per opcode, all signals filled
✅ ALU decoder truth table: funct7[5], funct3 → alu_ctrl
✅ Default signal values defined (all-zero safe defaults)
✅ Illegal opcode path: illegal=1 → exception raised
✅ Privilege violation detection in decode
✅ Hardwired RTL implemented (case statement with safe defaults)
✅ Multi-cycle FSM state table (if applicable)
✅ Hardwired vs microcode decision documented
✅ Every "don't care" (X) has a note on what happens
→ NEXT: 08-CacheDesign.md
```
