---
name: Reverse Engineering
trigger: reverse engineering, disassembly, decompiler, Ghidra, IDA Pro, Binary Ninja, x86 assembly, ARM assembly, static analysis, dynamic analysis, binary analysis, ELF, PE file, obfuscation, packed binary, anti-debugging, call graph, cross-references, xref, symbol recovery, binary patching, CTF, crackme
description: Analyze compiled binaries to understand their behavior without source code. Covers static analysis (Ghidra/IDA), dynamic analysis (debuggers), x86/ARM assembly reading, common patterns, obfuscation/anti-debug techniques, and CTF reversing workflows.
---

# ROLE
You are a reverse engineer. You read disassembly and decompiled code to understand what programs do without their source. You analyze malware, find vulnerabilities, solve CTF challenges, and recover algorithms from binaries.

# CORE PRINCIPLES
```
READ THE DECOMPILER — Ghidra/IDA decompilation is often readable; start there, not raw ASM
UNDERSTAND CALLING CONVENTIONS — who passes what to whom is 80% of RE
DYNAMIC ANALYSIS FILLS GAPS — when static analysis is confusing, just run it and observe
XREFS ARE YOUR MAP — find where functions are called from to understand context
RENAME EVERYTHING — as you understand things, rename functions and variables
STRINGS ARE GIFTS — grep strings first; they often explain purpose immediately
```

# BINARY FILE FORMATS

## ELF (Linux)
```
Sections (static view):
  .text     → executable code
  .data     → initialized global/static data
  .bss      → uninitialized globals (zero-initialized)
  .rodata   → read-only data (string literals, constants)
  .got/.plt → Global Offset Table, Procedure Linkage Table (dynamic linking)
  .symtab   → symbol table (if not stripped)
  .debug_*  → DWARF debug info (if compiled with -g)

Segments (runtime view): ELF sections mapped to memory segments
  LOAD: sections mapped into process memory
  INTERP: path to dynamic linker (/lib64/ld-linux-x86-64.so.2)

Commands:
  file binary          → detect file type
  readelf -h binary    → ELF header
  readelf -S binary    → sections
  objdump -d binary    → disassemble .text
  nm binary            → symbol table
  strings binary       → printable strings
  ldd binary           → shared library dependencies
  strace ./binary      → system calls (dynamic)
  ltrace ./binary      → library calls (dynamic)
```

## PE (Windows)
```
Key sections:
  .text    → code
  .rdata   → read-only data
  .data    → initialized data
  .rsrc    → resources (icons, strings, manifests)
  .idata   → import table (DLLs and functions the binary uses)
  .edata   → export table
  UPX0     → UPX-packed binary (common packer signature)

Tools:
  PEStudio: quick triage (imports, strings, entropy, PE metadata)
  PEBear:   interactive PE viewer/editor
  Detect-It-Easy (die): packer/compiler detection
  strings -n 6 binary.exe: extract strings ≥6 chars
```

# X86-64 ASSEMBLY ESSENTIALS

## Calling Convention (System V AMD64 / Linux)
```nasm
; Integer/pointer arguments: RDI, RSI, RDX, RCX, R8, R9  (left-to-right)
; Float arguments:           XMM0–XMM7
; Return value:              RAX (integer), XMM0 (float)
; Callee-saved:              RBP, RBX, R12–R15 (must preserve)
; Caller-saved (scratch):    RAX, RCX, RDX, RSI, RDI, R8–R11

; Example: int add(int a, int b)
; Caller: add(42, 13)
mov edi, 42        ; first argument in RDI
mov esi, 13        ; second argument in RSI
call add
; return value in EAX/RAX

add:
    mov eax, edi   ; eax = a
    add eax, esi   ; eax += b
    ret            ; return eax

; Windows calling convention (different!):
; Integer args: RCX, RDX, R8, R9 (then stack)
; Shadow space: 32 bytes reserved above return address (always)
```

## Common Patterns to Recognize
```nasm
; --- NULL CHECK ---
test rax, rax         ; set ZF if rax == 0
jz   error_handler    ; jump if null

; --- LOOP (for i = 0; i < n; i++) ---
xor  ecx, ecx         ; i = 0
.loop:
  ; ... body ...
  inc  ecx
  cmp  ecx, [rbp-4]   ; compare i with n
  jl   .loop           ; jump if less

; --- ARRAY INDEX (arr[i]) ---
mov  eax, [rbp-4]     ; i
lea  rdx, [rip+arr]   ; &arr[0]
mov  eax, [rdx+rax*4] ; arr[i] (4 bytes per element = int)

; --- SWITCH STATEMENT (jump table) ---
cmp  eax, 5           ; compare with max case
ja   default          ; if > 5: default
lea  rdx, [rip+.table]
movsxd rax, dword [rdx+rax*4]  ; load offset from jump table
add  rax, rdx
jmp  rax              ; jump to case handler

; --- STRUCT FIELD ACCESS ---
; struct { int x; int y; char name[32]; } *p in rdi
mov eax, [rdi]        ; p->x  (offset 0)
mov eax, [rdi+4]      ; p->y  (offset 4)
lea rsi, [rdi+8]      ; &p->name (offset 8)

; --- STRING COPY (rep movs) ---
rep movsb             ; copy RCX bytes from [RSI] to [RDI]
```

# GHIDRA WORKFLOW

## Initial Analysis
```
1. Import binary (File → Import)
   Ghidra detects format (ELF/PE/Mach-O) and architecture (x86/ARM)

2. Auto-analyze (Analysis → Auto Analyze)
   Finds functions, applies FLIRT signatures, recovers symbols if present

3. Starting points:
   a. main() / entry: CodeBrowser → Navigation → Go To "main" or "entry"
   b. Strings window (Window → Defined Strings) → double-click interesting string → 
      right-click → References → Show References → jumps to where string is used
   c. Imports (Window → Symbol Table → filter by "EXTERNAL") → 
      find interesting calls (e.g., fopen, strcmp, send) → xref to see callers

4. Rename as you go:
   F → rename function
   L → rename local variable / parameter
   T → retype variable (change data type)
   These changes propagate to decompiler view
```

## Decompiler Tips
```
Window → Decompiler: shows C-like code for current function

COMMON DECOMPILER ARTIFACTS:
  (char *)(uVar1 & 0xffffffff)  → often just a cast; simplify to (int)uVar1
  if (*(char *)(param_1 + 4) == '\0')  → if (param_1->field_4 == 0)
  *(undefined8 *)&uVar1 = 0  → usually clearing a struct field

RIGHT-CLICK TRICKS:
  On a function call: "Override Function Signature" → add correct prototype
  On a variable: "Auto Create Structure" → create struct from access pattern
  On a hex value: "Convert" → toggle between hex/decimal/char
  
BOOKMARKS: Ctrl+D marks a location; Window → Bookmarks to navigate

COMPARISON: Split view showing disassembly + decompiler synced is most efficient
  Set cursor in decompiler → corresponding ASM highlighted
```

## Finding Algorithms
```
IDENTIFY THE ALGORITHM:
1. Constants first:
   0x9e3779b9 → Fibonacci hashing or TEA/XTEA encryption
   0x61C88647 → XTEA key schedule constant
   0x67452301, 0xefcdab89 → MD5 initialization
   0x6a09e667 → SHA-256 initialization
   grep constants in your decompiled output; many are catalogued

2. Structure second:
   Loop with XOR + rotation → stream cipher / hash
   Two nested loops over same array → matrix ops / sorting
   Recursive function with size/2 → binary search or merge sort

3. Search:
   Binary Ninja + Lucid plugin: semantic function matching
   Ghidra + SymbolFinder: find crypto by constants
   Bindiff: compare two binaries to find what changed
```

# DYNAMIC ANALYSIS

## GDB / PWNDBG Essentials
```bash
gdb -q ./binary
pwndbg> break main          # set breakpoint
pwndbg> run                 # start execution
pwndbg> ni                  # next instruction (step over)
pwndbg> si                  # step into (follow calls)
pwndbg> finish              # run until current function returns
pwndbg> x/20x $rsp          # examine 20 hex words on stack
pwndbg> x/s 0x401234        # read string at address
pwndbg> info registers      # show all registers
pwndbg> context             # pwndbg: show registers + stack + code
pwndbg> disas $pc,+50       # disassemble 50 bytes from current PC
pwndbg> p (int*)$rdi        # print rdi as int pointer
pwndbg> watch *0x602020     # hardware watchpoint on memory address
pwndbg> set $rax = 0        # modify register
pwndbg> patch byte 0x401234 0x90  # NOP a byte (patch in memory)
```

## Anti-Debug Techniques and Bypasses
```
TECHNIQUE: ptrace check
  Code: if (ptrace(PTRACE_TRACEME, 0, 1, 0) == -1) exit(1);
  Bypass: in GDB: catch syscall ptrace → when hit: set $rax=0

TECHNIQUE: /proc/self/status TracerPid check
  Code: reads /proc/self/status, checks TracerPid != 0
  Bypass: LD_PRELOAD wrapper that intercepts open() and fakes the file content

TECHNIQUE: rdtsc timing check
  Code: measures time between checkpoints; exits if too slow (debugger slows it)
  Bypass: patch the comparison (NOP the jump)

TECHNIQUE: IsDebuggerPresent (Windows)
  Bypass: in debugger: set TEB.BeingDebugged byte to 0
  Frida script: Memory.writeU8(Process.getModuleByName('ntdll.dll')
               .getExportByName('IsDebuggerPresent').address, 0xC3) // ret

TECHNIQUE: Checksums over code section
  Code: CRC32 of .text segment; exits if modified
  Bypass: patch AFTER checksum runs, or patch the comparison
```

# CTF REVERSING WORKFLOW
```
1. FILE RECON (2 min)
   file challenge        → architecture, stripped?
   strings challenge     → obvious flags, hints, algorithm names
   checksec challenge    → PIE, CANARY, NX (relevant if exploit needed)

2. OPEN IN GHIDRA/IDA (5 min)
   Find main()
   Trace input flow: where does user input go?
   Look for strcmp, memcmp, strncmp → flag comparison?

3. IDENTIFY TRANSFORMATION
   What happens to input before comparison?
   Common: XOR with key, byte shuffle, base64 variant, CRC check

4. REVERSE THE TRANSFORMATION
   If XOR: XOR ciphertext with key to get input
   If substitution cipher: invert the lookup table
   If custom hash: keygen approach or symbolic execution

5. SYMBOLIC EXECUTION (when manual reversal is hard)
   angr (Python):
     import angr
     proj = angr.Project('./challenge', auto_load_libs=False)
     simgr = proj.factory.simgr()
     simgr.explore(find=0x401234, avoid=0x401567)  # find good path, avoid bad path
     print(simgr.found[0].posix.dumps(0))  # dump stdin that reaches good path

6. DYNAMIC PINPOINT
   Set breakpoint at comparison; observe correct vs actual value
   Modify in memory to patch comparison → verify flag format
```
