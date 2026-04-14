---
name: Interrupt and Exception Handling
trigger: interrupt, exception, trap, IRQ, NMI, precise exception, interrupt vector, mtvec, mcause, mepc, interrupt handler, exception handler, timer interrupt, external interrupt, software interrupt, PLIC, CLINT, nested interrupt, interrupt latency, trap frame
description: Eleventh skill in the processor design pipeline. Covers the taxonomy of interrupts and exceptions, RISC-V trap CSR mechanics, precise exception guarantees, interrupt controller design (PLIC/CLINT), interrupt latency analysis, and nested interrupt handling.
prev_skill: 10-OutOfOrderExecution.md
next_skill: 12-BusInterconnectDesign.md
---

# ROLE
You are designing the processor's emergency response system. Interrupts and exceptions must be handled precisely — the processor must appear to have stopped at exactly the right instruction, with no side effects from partially-completed work. You define every CSR, every priority level, every latency constraint, and every protocol so the OS can trust the hardware completely.

# CORE PRINCIPLES
```
PRECISE EXCEPTIONS — all instructions before the faulting one are fully committed
INTERRUPTS ARE ASYNC — they arrive independent of the instruction stream
EXCEPTIONS ARE SYNC — caused by the instruction currently executing
PRIORITY IS TOTAL — no two sources are equal; priority order is silicon law
LATENCY IS A CONTRACT — OS designers need an upper bound; define and meet it
NESTED INTERRUPTS — disable by default; enable explicitly with care
EVERY TRAP MUST BE RECOVERABLE — save enough state to resume or report error
```

# STEP 1 — TAXONOMY

```
EXCEPTIONS (synchronous — caused by current instruction):
  Code  Name                          Cause
  ────  ──────────────────────────    ─────────────────────────────────────────
  0     Instruction Address Misalign  PC not 4-byte aligned (non-C ISA)
  1     Instruction Access Fault      PMP/PMA violation on instruction fetch
  2     Illegal Instruction           Undefined opcode, bad CSR, wrong privilege
  3     Breakpoint                    EBREAK instruction
  4     Load Address Misaligned       Load to non-aligned address
  5     Load Access Fault             PMP/PMA violation on load
  6     Store/AMO Address Misalign    Store to non-aligned address
  7     Store/AMO Access Fault        PMP/PMA violation on store
  8     Environment Call (U-mode)     ECALL from user mode
  9     Environment Call (S-mode)     ECALL from supervisor mode
  11    Environment Call (M-mode)     ECALL from machine mode
  12    Instruction Page Fault        Page not present / no-execute during fetch
  13    Load Page Fault               Page not present / no-read during load
  15    Store/AMO Page Fault          Page not present / no-write during store

INTERRUPTS (asynchronous — triggered by external or timer events):
  Code  Name                   Source
  ────  ──────────────────────  ───────────────────────────────────────────────
  1     Supervisor SW Interrupt CLINT: ssip bit set via software
  3     Machine SW Interrupt    CLINT: msip bit set via software (inter-core IPI)
  5     Supervisor Timer Int.   CLINT: stimer compare match
  7     Machine Timer Interrupt CLINT: mtime >= mtimecmp
  9     Supervisor External Int PLIC: external device interrupt (S-mode)
  11    Machine External Int.   PLIC: external device interrupt (M-mode)

  Bit 63 of mcause = 1 → interrupt
  Bit 63 of mcause = 0 → exception
  Bits [62:0] = cause code from table above
```

# STEP 2 — TRAP CSR MECHANICS (RISC-V)

```
ON TRAP ENTRY (hardware actions, in this exact order):

  1. mepc    ← PC of trapping instruction (or PC+4 for ECALL/EBREAK return)
  2. mcause  ← {interrupt_bit, cause_code}
  3. mtval   ← bad address, bad instruction bits, or 0
  4. mstatus.MPP   ← current privilege mode (2 bits: U=0, S=1, M=3)
  5. mstatus.MPIE  ← mstatus.MIE  (save current interrupt enable)
  6. mstatus.MIE   ← 0            (DISABLE interrupts — prevent nested by default)
  7. PC      ← mtvec.BASE if mtvec.MODE==Direct
                 mtvec.BASE + cause*4 if mtvec.MODE==Vectored (and interrupt)

  mtvec MODES:
    MODE=0 (Direct):   all traps go to BASE
    MODE=1 (Vectored): exceptions → BASE, interrupts → BASE + 4×cause

ON TRAP RETURN (MRET instruction):
  1. PC       ← mepc
  2. privilege ← mstatus.MPP
  3. mstatus.MIE  ← mstatus.MPIE  (restore interrupt enable)
  4. mstatus.MPIE ← 1
  5. mstatus.MPP  ← U-mode (least-privileged; prevents return-to-M exploit)

SUPERVISOR MODE TRAPS (S-mode analog):
  sepc, scause, stval, sstatus (subset of mstatus), stvec
  M-mode can delegate traps to S-mode: write cause bitmask to medeleg/mideleg

KEY TRAP-RELATED CSRs:
  CSR         Function
  ──────────  ──────────────────────────────────────────────────────────
  mstatus     MIE, MPIE, MPP, SIE, SPIE, SPP, FS (float state), XS
  mie         Interrupt Enable: MSIE, MTIE, MEIE, SSIE, STIE, SEIE
  mip         Interrupt Pending: MSIP, MTIP, MEIP, SSIP, STIP, SEIP
  mtvec       Trap Vector Base Address + MODE[1:0]
  mepc        Machine Exception PC
  mcause      Cause register (interrupt flag + code)
  mtval       Trap value (bad addr, bad instr)
  mscratch    Scratch register for M-mode (save/restore tp or gp)
  medeleg     Exception delegation to S-mode bitmask
  mideleg     Interrupt delegation to S-mode bitmask
```

# STEP 3 — PRECISE EXCEPTION GUARANTEE

```
DEFINITION: An exception is PRECISE if, at the moment of exception delivery:
  1. All instructions before the faulting instruction have completed (committed)
  2. No instructions after the faulting instruction have any visible effect
  3. mepc correctly points to the faulting instruction
  4. Architectural state is consistent with sequential execution up to (but not including) mepc

IN 5-STAGE PIPELINE:
  When exception detected at stage S:
    Flush all pipeline stages after the faulting instruction's entry stage
    Prevent write-back of any later instructions (zero out their write-enable signals)
    Allow all earlier instructions to complete normally (they're ahead in the pipe)
  Result: architectural state = committed state of all instructions before fault

IN OoO PROCESSOR:
  Exception detected at execution → mark ROB entry with exception
  Instruction WAITS at ROB head (not committed yet)
  When ROB head reaches exception → commit all prior instructions → take exception
  Speculative instructions after exception in ROB → all squashed
  Result: fully precise — expensive in hardware, mandatory for correctness

IMPRECISE EXCEPTIONS (historical, avoid):
  Some old processors (MIPS R8000) allowed imprecise floating-point exceptions
  OS cannot resume — must restart entire computation
  NEVER do this for integer exceptions; FP imprecise requires special OS support
```

# STEP 4 — INTERRUPT CONTROLLER: CLINT

```
CLINT (Core-Local Interrupt Controller):
  Provides: machine timer interrupt (MTIP) and software interrupt (MSIP)
  Memory-mapped registers, one set per hart (hardware thread)

  REGISTERS:
    mtime[63:0]     — free-running 64-bit timer, increments at fixed frequency
                      (typically 1 MHz or real-time frequency, not core clock)
    mtimecmp[63:0]  — compare register, one per hart
    msip[31:0]      — machine software interrupt pending register (bit 0 = MSIP)

  INTERRUPT GENERATION:
    MTIP: mtime >= mtimecmp → set mip.MTIP → interrupt if mie.MTIE and mstatus.MIE
    MSIP: msip[0] = 1 → set mip.MSIP → interrupt if mie.MSIE and mstatus.MIE

  CLEARING INTERRUPTS:
    MTIP: clear by writing mtimecmp > mtime (schedule next timer event)
    MSIP: clear by writing 0 to msip register

  TIMER RESOLUTION:
    mtime at 1 MHz: 1 µs resolution, rolls over in 584,542 years — sufficient
    OS scheduler tick: typically 1–10 ms → mtimecmp = mtime + (1ms × freq)
```

# STEP 5 — INTERRUPT CONTROLLER: PLIC

```
PLIC (Platform-Level Interrupt Controller):
  Routes external interrupts (UART, NIC, disk, GPIO) to harts
  Supports up to 1023 interrupt sources, multiple harts

  KEY CONCEPTS:
    Source:    a device interrupt (numbered 1–1023; source 0 = no interrupt)
    Target:    a (hart, privilege mode) pair (e.g., hart0-M, hart0-S, hart1-M...)
    Priority:  per-source 32-bit register (0 = disabled, 1 = lowest, 7 = highest)
    Threshold: per-target minimum priority (ignore interrupts below threshold)
    Pending:   per-source bit showing interrupt is active and awaiting claim
    Enable:    per-target-per-source bit enabling delivery to that target

  PLIC PROTOCOL (per external interrupt):
    1. Device asserts interrupt line to PLIC
    2. PLIC sets pending bit for that source
    3. PLIC computes max priority of enabled pending interrupts per target
    4. If max priority > target threshold → assert EIP (external interrupt pending)
    5. Hart sees mip.MEIP set → enters trap handler (if MIE enabled)
    6. Trap handler: read PLIC claim register → returns winning source ID
    7. Claim atomically clears pending bit for that source
    8. Handler services the device
    9. Handler writes source ID to PLIC complete register → deasserts EIP
    10. PLIC reasserts EIP if another pending source remains above threshold

  MEMORY MAP (PLIC base address = platform-defined, e.g., 0x0C000000):
    +0x000000: Priority registers (4 bytes × 1024 sources)
    +0x001000: Pending array (4 bytes × 32 words = 1024 bits)
    +0x002000: Enable registers per target (4 bytes × 32 × N_targets)
    +0x200000: Per-target threshold and claim/complete registers
```

# STEP 6 — INTERRUPT LATENCY ANALYSIS

```
INTERRUPT LATENCY = time from interrupt assertion to first instruction of handler

LATENCY COMPONENTS (in-order 5-stage pipeline):
  Component                          Cycles
  ────────────────────────────────   ──────
  PLIC/CLINT propagation delay       1
  mip sampling (checked each cycle)  0–1
  Current instruction completes      0–4  (must drain pipeline for precise delivery)
  PC redirect to mtvec               1
  Fetch first handler instruction    1
  Decode handler instruction         1
  TOTAL                              4–9 cycles

LATENCY COMPONENTS (OoO processor):
  Interrupt sampled at commit:  add ROB drain time (could be 10–100 cycles)
  OoO interrupt latency: 20–200 cycles (much higher than in-order)
  Trade-off: OoO gains IPC but loses interrupt latency

JITTER (variable latency):
  Sources: pipeline depth, ROB occupancy, cache miss on handler fetch
  Real-time systems need bounded jitter: define maximum latency guarantee
  For hard real-time: use in-order processor, disable caches (or lock-step)

WORST-CASE INTERRUPT LATENCY BUDGET:
  PLIC sampling:              1 µs    (at 1 MHz PLIC poll)
  Pipeline drain (OoO):      100 cycles = 33 ns at 3 GHz
  Handler fetch (L1 hit):     4 cycles = 1.3 ns
  Total worst-case:           ~35 ns (in-order) to ~1 µs (OoO with PLIC polling)
```

# STEP 7 — TRAP FRAME AND CONTEXT SAVE

```
TRAP FRAME — data structure saved by the interrupt handler:

  On trap entry, handler saves ALL registers to stack:
    (because compiler may use any register; must restore for preemptive scheduling)

  TRAP FRAME LAYOUT (kernel stack, grows downward):
    Offset   Register   Width
    ───────  ─────────  ─────
    +0       ra (x1)    8
    +8       sp (x2)    8    ← saved USER sp (before switching to kernel stack)
    +16      gp (x3)    8
    +24      tp (x4)    8
    +32      t0 (x5)    8
    ...
    +240     t6 (x31)   8
    +248     mepc       8    ← return address
    +256     mstatus    8    ← machine status (to restore privilege)

  SAVE SEQUENCE (at handler entry):
    addi sp, sp, -256      # allocate trap frame
    sd   ra, 0(sp)
    sd   gp, 16(sp)
    ...   (all registers)
    csrr t0, mepc
    sd   t0, 248(sp)
    csrr t0, mstatus
    sd   t0, 256(sp)

  RESTORE SEQUENCE (before MRET):
    ld   t0, 248(sp)
    csrw mepc, t0
    ld   t0, 256(sp)
    csrw mstatus, t0
    ld   ra, 0(sp)
    ...   (all registers)
    addi sp, sp, 256
    mret

  SCRATCH REGISTER TRICK:
    mscratch holds kernel sp when in user mode
    At trap entry: csrrw sp, mscratch, sp  (swap user sp and kernel sp atomically)
    Now sp points to kernel stack; mscratch holds old user sp
    Save user sp from mscratch to trap frame
```

# STEP 8 — NESTED INTERRUPTS

```
DEFAULT: interrupts disabled on entry (mstatus.MIE ← 0 on trap)
  → No nesting by default; handler runs to completion uninterrupted

ENABLING NESTING:
  Handler saves mepc, mstatus, mcause to stack (not just registers)
  Handler re-enables interrupts: csrsi mstatus, (1<<3)  (set MIE bit)
  Now higher-priority interrupts can preempt this handler

NESTED INTERRUPT REQUIREMENTS:
  Fully re-entrant handler code
  Kernel stack must be large enough for N levels of nesting
  mepc, mcause, mstatus must be stacked (N copies on stack)
  csrrw/csrrs/csrrc are atomic → safe for saving CSRs

PRIORITY INVERSION RISK:
  Lower-priority interrupt handler runs, high-priority interrupt arrives
  If MIE disabled → high-priority must wait until low-priority handler returns
  Solution: use PLIC threshold register to mask lower-priority interrupts
    Handler entry: set PLIC threshold = source_priority → only higher can preempt
    Handler exit: reset PLIC threshold to previous value

INTERRUPT STORM PROTECTION:
  If a device asserts interrupt faster than handler can clear it:
    PLIC pending stays set → handler loops forever
    Solution: disable source at PLIC enable register inside handler
              re-enable after device is serviced (acknowledged)
```

# CHECKLIST — Before Moving to Bus and Interconnect Design

```
✅ Full exception cause code table written (sync + async)
✅ Trap entry hardware actions listed in order (mepc, mcause, mtval, mstatus)
✅ Trap return (MRET) actions listed in order
✅ Precise exception guarantee described for in-order and OoO pipelines
✅ CLINT registers defined (mtime, mtimecmp, msip)
✅ PLIC protocol steps 1–10 written out
✅ PLIC memory map base addresses defined
✅ Interrupt latency budget: components and worst-case total
✅ Trap frame layout (all fields, offsets)
✅ Trap entry/exit assembly sequence written
✅ Nested interrupt policy defined (disabled by default; opt-in via MIE)
✅ Interrupt storm protection mechanism documented
→ NEXT: 12-BusInterconnectDesign.md
```
