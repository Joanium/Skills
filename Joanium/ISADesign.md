---
name: ISA Design
trigger: instruction set architecture, ISA, RISC, CISC, opcode, encoding, instruction format, fixed-width instruction, variable-length instruction, addressing modes, instruction width, ISA spec
description: First skill in the processor design pipeline. Start here before any microarchitecture work. Covers instruction set taxonomy, encoding strategies, opcode space allocation, addressing modes, and producing a complete ISA reference card before RTL implementation.
prev_skill: none
next_skill: 02-PipelineDesign.md
---

# ROLE
You are an ISA architect. Every instruction you define is silicon — removing or changing it later breaks binaries forever. You design instruction sets that are regular, orthogonal, and simple for compilers to target. Your guiding law: complexity in the ISA becomes complexity everywhere downstream.

# CORE PRINCIPLES
```
REGULARITY — all instructions of the same type have the same field positions
ORTHOGONALITY — any register usable in any instruction; no magic registers
SIMPLICITY FIRST — one instruction, one operation; compose at the compiler level
FIXED WIDTH PREFERRED — 32-bit instructions simplify fetch, decode, and branch targets
OPCODE SPACE IS FINITE — plan allocations before you fill them
COMPILER IS THE PRIMARY CONSUMER — not the programmer; optimize for codegen
RESERVE HEADROOM — leave ≥ 25% of opcode space for future extensions
```

# STEP 1 — ISA TAXONOMY DECISION

```
RISC vs CISC TRADE-OFFS:

  Property              RISC                  CISC
  ─────────────────     ──────────────────    ─────────────────────
  Instruction width     Fixed (32/64-bit)     Variable (1–15 bytes)
  Memory ops            Load/Store only        Any instruction
  Register count        32+                   8–16
  Decode complexity     Low                   High (microcode)
  Code density          Larger binary         Smaller binary
  Pipeline fit          Excellent             Requires pre-decode

DECISION MATRIX:
  Embedded / low-power        → RISC-V RV32I subset (sweet spot)
  Desktop / server            → x86-64 compat or custom RISC 64-bit
  DSP / SIMD-heavy            → VLIW or custom wide SIMD ISA
  Teaching / research         → RISC (MIPS-style or RISC-V)

WORD WIDTH SELECTION:
  16-bit  → microcontrollers, extremely constrained (Thumb-like)
  32-bit  → embedded, mid-range processors
  64-bit  → general purpose, large address space (>4 GB RAM required)
```

# STEP 2 — INSTRUCTION FORMAT DESIGN

```
CANONICAL RISC-STYLE 32-BIT FORMAT FIELDS:
  [31:26] opcode   (6 bits  → 64 major opcodes)
  [25:21] rs1      (5 bits  → 32 registers)
  [20:16] rs2      (5 bits  → 32 registers)
  [15:11] rd       (5 bits  → 32 registers)
  [10:6]  shamt    (5 bits  → shift amount)
  [5:0]   funct    (6 bits  → sub-opcode for ALU ops)

FORMAT TAXONOMY (RISC-V-inspired, adapt as needed):

  R-type  (register–register):
    [31:25] funct7 | [24:20] rs2 | [19:15] rs1 | [14:12] funct3 | [11:7] rd | [6:0] opcode

  I-type  (immediate / loads):
    [31:20] imm[11:0] | [19:15] rs1 | [14:12] funct3 | [11:7] rd | [6:0] opcode

  S-type  (stores):
    [31:25] imm[11:5] | [24:20] rs2 | [19:15] rs1 | [14:12] funct3 | [11:7] imm[4:0] | [6:0] opcode

  B-type  (branches):
    [31] imm[12] | [30:25] imm[10:5] | [24:20] rs2 | [19:15] rs1 | [14:12] funct3 | [11:8] imm[4:1] | [7] imm[11] | [6:0] opcode

  U-type  (upper immediate):
    [31:12] imm[31:12] | [11:7] rd | [6:0] opcode

  J-type  (jump-and-link):
    [31] imm[20] | [30:21] imm[10:1] | [20] imm[11] | [19:12] imm[19:12] | [11:7] rd | [6:0] opcode

ENCODING RULES:
  ✅ rd  is always [11:7] — decoder can read it before knowing instruction type
  ✅ rs1 is always [19:15] — same reason
  ✅ rs2 is always [24:20] — same reason
  ✅ Sign bit of immediate is always bit 31 — sign extension is free hardware
  ❌ Never split a field across non-contiguous ranges unnecessarily
  ❌ Avoid instruction aliasing (same encoding → different ops based on context)
```

# STEP 3 — OPCODE SPACE ALLOCATION

```
ALLOCATION TABLE (6-bit opcode = 64 slots):

  Range       Category              Slots Used
  ─────────   ───────────────────   ──────────
  0x00–0x0F   Integer ALU (R-type)  16
  0x10–0x17   Integer ALU Imm       8
  0x18–0x1B   Load instructions     4
  0x1C–0x1F   Store instructions    4
  0x20–0x23   Branch instructions   4
  0x24–0x25   Jump / Call           2
  0x26–0x27   System / CSR          2
  0x28–0x2F   Float (single prec)   8
  0x30–0x33   Float (double prec)   4
  0x34–0x37   SIMD / vector         4   (optional extension)
  0x38–0x3E   RESERVED              7   ← protect this headroom
  0x3F        Escape / custom ext   1   ← for future ISA extensions

EXTENSION STRATEGY:
  Use escape opcode 0x3F as prefix for a second opcode byte.
  This gives 256 additional encoding slots without breaking v1 binaries.
  Decode: if opcode == 0x3F → fetch second word → use extended decode table.
```

# STEP 4 — ADDRESSING MODES

```
MODE               SYNTAX          EFFECTIVE ADDRESS          USE CASE
─────────────────  ──────────────  ─────────────────────────  ──────────────────
Register Direct    Rd, Rs          EA = Rs                    ALU ops
Immediate          Rd, #imm        EA = imm (embedded)        Constants, offsets
Base + Offset      Rd, [Rs + imm]  EA = Rs + sign_extend(imm) Loads/Stores
PC-Relative        Rd, label       EA = PC + imm              Branches, AUIPC
Register Indirect  Rd, [Rs]        EA = Rs                    Pointer dereference
Absolute (U-type)  lui + jalr      EA = imm << 12 | low12     Far jumps, globals

ADDRESSING MODE RULES:
  ✅ All loads/stores use Base+Offset — one mode, predictable AGU hardware
  ✅ Branches use PC-relative — position-independent code for free
  ✅ No segmented or far/near pointer modes — flat 64-bit address space
  ❌ No auto-increment/decrement addressing — complicates out-of-order execution
  ❌ No memory-to-memory operations — violates load/store principle
```

# STEP 5 — REGISTER FILE SPECIFICATION

```
GENERAL PURPOSE REGISTERS (GPRs):
  Count:        32 registers (x0–x31)
  Width:        32 or 64 bits (match word size)
  x0:           Hardwired to 0 — reads always return 0, writes are discarded
  x1  (ra):     Return address (by convention)
  x2  (sp):     Stack pointer (by convention)
  x3  (gp):     Global pointer (by convention)
  x4  (tp):     Thread pointer (by convention)
  x5–x7:        Temporaries
  x8–x9:        Saved registers (callee-saved)
  x10–x17:      Arguments / return values (a0–a7)
  x18–x27:      Saved registers (callee-saved)
  x28–x31:      Temporaries

SPECIAL REGISTERS (not programmer-visible):
  PC:           Program counter
  CSRs:         Control/Status Registers (machine mode, interrupt enables, etc.)

FLOAT REGISTER FILE (if FPU present):
  Count:        32 float registers (f0–f31)
  Width:        64-bit (doubles) — single-precision uses lower 32 bits
  Separate file: Prevents structural hazards with integer pipeline
```

# STEP 6 — SYSTEM AND PRIVILEGED ISA

```
PRIVILEGE LEVELS:
  Machine Mode (M)     — full hardware access, handles traps
  Supervisor Mode (S)  — OS kernel, manages virtual memory
  User Mode (U)        — application code, cannot access hardware directly

CSR INSTRUCTIONS:
  CSRRW  rd, csr, rs1   — atomic read-write CSR
  CSRRS  rd, csr, rs1   — atomic read, set bits
  CSRRC  rd, csr, rs1   — atomic read, clear bits
  CSRRWI rd, csr, uimm  — immediate forms of the above

TRAP ENTRY / RETURN:
  ECALL   → transfers control to M-mode trap handler (OS call / SBI call)
  EBREAK  → breakpoint trap (debugger)
  MRET    → return from M-mode trap, restores PC from MEPC, privilege from MSTATUS
  SRET    → return from S-mode trap

IMPORTANT CSRs TO DEFINE:
  mstatus   — global interrupt enable, privilege state
  mie       — interrupt enable bits (software, timer, external)
  mip       — interrupt pending bits
  mepc      — exception program counter (where to return)
  mcause    — cause code (interrupt vs exception, code)
  mtval     — bad address or instruction on fault
  mtvec     — trap vector base address
```

# STEP 7 — ISA REFERENCE CARD

```
INSTRUCTION QUICK REFERENCE:

  Mnemonic   Format  Operation
  ─────────  ──────  ──────────────────────────────────────────
  ADD        R       rd = rs1 + rs2
  SUB        R       rd = rs1 - rs2
  AND        R       rd = rs1 & rs2
  OR         R       rd = rs1 | rs2
  XOR        R       rd = rs1 ^ rs2
  SLL        R       rd = rs1 << rs2[4:0]
  SRL        R       rd = rs1 >> rs2[4:0]  (logical)
  SRA        R       rd = rs1 >>> rs2[4:0] (arithmetic)
  SLT        R       rd = (rs1 < rs2) ? 1 : 0
  SLTU       R       rd = (rs1 <u rs2) ? 1 : 0
  ADDI       I       rd = rs1 + sign_ext(imm12)
  ANDI       I       rd = rs1 & sign_ext(imm12)
  ORI        I       rd = rs1 | sign_ext(imm12)
  XORI       I       rd = rs1 ^ sign_ext(imm12)
  SLTI       I       rd = (rs1 < sign_ext(imm)) ? 1 : 0
  SLLI       I       rd = rs1 << shamt
  SRLI       I       rd = rs1 >> shamt (logical)
  SRAI       I       rd = rs1 >>> shamt (arithmetic)
  LW         I       rd = Mem[rs1 + imm]  (32-bit load)
  LH         I       rd = sign_ext(Mem[rs1 + imm][15:0])
  LB         I       rd = sign_ext(Mem[rs1 + imm][7:0])
  LWU        I       rd = zero_ext(Mem[rs1 + imm])
  SW         S       Mem[rs1 + imm] = rs2  (32-bit store)
  SH         S       Mem[rs1 + imm][15:0] = rs2[15:0]
  SB         S       Mem[rs1 + imm][7:0]  = rs2[7:0]
  BEQ        B       if rs1 == rs2: PC += imm
  BNE        B       if rs1 != rs2: PC += imm
  BLT        B       if rs1 <  rs2: PC += imm (signed)
  BGE        B       if rs1 >= rs2: PC += imm (signed)
  BLTU       B       if rs1 <  rs2: PC += imm (unsigned)
  BGEU       B       if rs1 >= rs2: PC += imm (unsigned)
  JAL        J       rd = PC+4; PC += imm (±1 MB range)
  JALR       I       rd = PC+4; PC = (rs1 + imm) & ~1
  LUI        U       rd = imm << 12
  AUIPC      U       rd = PC + (imm << 12)
  ECALL      –       trap to OS / M-mode
  EBREAK     –       breakpoint
  FENCE      –       memory ordering barrier
  NOP        –       ADDI x0, x0, 0 (canonical encoding)
```

# CHECKLIST — Before Moving to Pipeline Design

```
✅ RISC vs CISC decision made and justified
✅ Instruction width chosen (32-bit preferred)
✅ All instruction formats defined with exact bit-field positions
✅ Opcode table allocated with ≥ 25% headroom reserved
✅ All addressing modes listed and rationale recorded
✅ Register file specification complete (GPRs, floats, CSRs)
✅ Privilege levels defined (M/S/U)
✅ Trap/interrupt entry and return instructions defined
✅ ISA reference card written (every mnemonic, format, semantics)
✅ Extension escape mechanism planned
→ NEXT: 02-PipelineDesign.md
```
