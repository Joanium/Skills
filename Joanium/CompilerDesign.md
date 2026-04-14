---
name: Compiler Design
trigger: compiler, lexer, tokenizer, parser, AST, abstract syntax tree, grammar, BNF, EBNF, recursive descent, Pratt parser, semantic analysis, type checking, IR, intermediate representation, code generation, LLVM, bytecode, interpreter, transpiler, DSL, language design
description: Design and implement programming languages, DSLs, transpilers, and compilers. Covers lexing, parsing (recursive descent, Pratt), AST construction, semantic analysis, type checking, IR design, and code generation/interpretation.
---

# ROLE
You are a language implementer. You build compilers, interpreters, transpilers, and DSLs from scratch. You understand every stage of the compilation pipeline and can implement robust parsers, type systems, and code generators.

# CORE PRINCIPLES
```
PIPELINE THINKING — lex → parse → analyze → transform → generate; each stage has clean input/output
RECURSIVE DESCENT IS READABLE — hand-written parsers are debuggable; use parser generators only when necessary
AST IS THE PIVOT — all analysis and transformation works on the AST
TYPE ERRORS ARE SEMANTIC, NOT SYNTAX — separate parsing from type checking
ERROR RECOVERY MATTERS — compilers should report multiple errors, not stop at the first
TEST EACH STAGE IN ISOLATION — snapshot tests for the lexer, parser, AST separately
```

# COMPILATION PIPELINE
```
Source code (string)
    ↓ [Lexer / Tokenizer]
Token stream
    ↓ [Parser]
Abstract Syntax Tree (AST)
    ↓ [Semantic Analyzer / Type Checker]
Annotated AST (with types, resolved symbols)
    ↓ [Optimizer / Transformer]
Optimized AST / IR (Intermediate Representation)
    ↓ [Code Generator]
Target (bytecode / native asm / JS / WASM / LLVM IR)
```

# LEXER

## Token Design
```python
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional

class TokenType(Enum):
    # Literals
    INT     = auto()
    FLOAT   = auto()
    STRING  = auto()
    IDENT   = auto()
    # Operators
    PLUS    = auto()
    MINUS   = auto()
    STAR    = auto()
    SLASH   = auto()
    EQ      = auto()
    EQEQ    = auto()
    BANG    = auto()
    BANGEQ  = auto()
    LT      = auto()
    GT      = auto()
    # Delimiters
    LPAREN  = auto()
    RPAREN  = auto()
    LBRACE  = auto()
    RBRACE  = auto()
    SEMI    = auto()
    COMMA   = auto()
    # Keywords
    LET     = auto()
    FN      = auto()
    IF      = auto()
    ELSE    = auto()
    WHILE   = auto()
    RETURN  = auto()
    TRUE    = auto()
    FALSE   = auto()
    # Control
    EOF     = auto()

KEYWORDS = {
    "let": TokenType.LET, "fn": TokenType.FN, "if": TokenType.IF,
    "else": TokenType.ELSE, "while": TokenType.WHILE, "return": TokenType.RETURN,
    "true": TokenType.TRUE, "false": TokenType.FALSE,
}

@dataclass
class Token:
    type:    TokenType
    lexeme:  str
    line:    int
    column:  int
```

## Lexer Implementation
```python
class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos    = 0
        self.line   = 1
        self.col    = 1
        self.tokens: list[Token] = []

    def peek(self) -> str:
        return self.source[self.pos] if self.pos < len(self.source) else '\0'

    def peek_next(self) -> str:
        return self.source[self.pos + 1] if self.pos + 1 < len(self.source) else '\0'

    def advance(self) -> str:
        ch = self.source[self.pos]
        self.pos += 1
        if ch == '\n': self.line += 1; self.col = 1
        else:          self.col  += 1
        return ch

    def match(self, expected: str) -> bool:
        if self.peek() == expected:
            self.advance(); return True
        return False

    def tokenize(self) -> list[Token]:
        while self.pos < len(self.source):
            self._scan_token()
        self.tokens.append(Token(TokenType.EOF, '', self.line, self.col))
        return self.tokens

    def _scan_token(self):
        start_col = self.col
        ch = self.advance()

        match ch:
            case ' ' | '\t' | '\r' | '\n': return  # skip whitespace
            case '+': self._emit(TokenType.PLUS,   '+',  start_col)
            case '-': self._emit(TokenType.MINUS,  '-',  start_col)
            case '*': self._emit(TokenType.STAR,   '*',  start_col)
            case '/':
                if self.match('/'):         # line comment
                    while self.peek() != '\n' and self.pos < len(self.source):
                        self.advance()
                else: self._emit(TokenType.SLASH, '/', start_col)
            case '=': 
                t = TokenType.EQEQ if self.match('=') else TokenType.EQ
                self._emit(t, '==' if t == TokenType.EQEQ else '=', start_col)
            case '!':
                t = TokenType.BANGEQ if self.match('=') else TokenType.BANG
                self._emit(t, '!=' if t == TokenType.BANGEQ else '!', start_col)
            case '"': self._string(start_col)
            case _:
                if ch.isdigit():  self._number(ch, start_col)
                elif ch.isalpha() or ch == '_': self._ident(ch, start_col)
                else: raise SyntaxError(f"Unexpected char '{ch}' at {self.line}:{start_col}")

    def _string(self, start_col):
        s = ''
        while self.peek() != '"' and self.pos < len(self.source):
            s += self.advance()
        self.advance()  # closing "
        self._emit(TokenType.STRING, s, start_col)

    def _number(self, first: str, start_col):
        n = first
        while self.peek().isdigit(): n += self.advance()
        if self.peek() == '.' and self.peek_next().isdigit():
            n += self.advance()
            while self.peek().isdigit(): n += self.advance()
            self._emit(TokenType.FLOAT, n, start_col)
        else:
            self._emit(TokenType.INT, n, start_col)

    def _ident(self, first: str, start_col):
        word = first
        while self.peek().isalnum() or self.peek() == '_': word += self.advance()
        ttype = KEYWORDS.get(word, TokenType.IDENT)
        self._emit(ttype, word, start_col)

    def _emit(self, ttype, lexeme, col):
        self.tokens.append(Token(ttype, lexeme, self.line, col))
```

# PARSER — RECURSIVE DESCENT WITH PRATT EXPRESSIONS

## AST Nodes
```python
from typing import Union
from dataclasses import dataclass, field

# Statement nodes
@dataclass class Program:    stmts: list["Stmt"]
@dataclass class LetStmt:    name: str; value: "Expr"
@dataclass class ReturnStmt: value: "Expr"
@dataclass class ExprStmt:   expr: "Expr"
@dataclass class BlockStmt:  stmts: list["Stmt"]
@dataclass class IfStmt:     cond: "Expr"; then: BlockStmt; else_: Optional["Stmt"]
@dataclass class WhileStmt:  cond: "Expr"; body: BlockStmt
@dataclass class FnDecl:     name: str; params: list[str]; body: BlockStmt

# Expression nodes
@dataclass class IntLit:     value: int
@dataclass class FloatLit:   value: float
@dataclass class BoolLit:    value: bool
@dataclass class StrLit:     value: str
@dataclass class Identifier: name: str
@dataclass class BinOp:      op: str; left: "Expr"; right: "Expr"
@dataclass class UnaryOp:    op: str; operand: "Expr"
@dataclass class Call:       callee: "Expr"; args: list["Expr"]
@dataclass class Assign:     target: str; value: "Expr"

Stmt = Union[LetStmt, ReturnStmt, ExprStmt, BlockStmt, IfStmt, WhileStmt, FnDecl]
Expr = Union[IntLit, FloatLit, BoolLit, StrLit, Identifier, BinOp, UnaryOp, Call, Assign]
```

## Pratt Parser (Top-Down Operator Precedence)
```python
# Pratt parsing: each token type has a binding power (precedence)
# and a parse function (null denotation + left denotation)

PRECEDENCES = {
    TokenType.EQ:     1,   # assignment (right-assoc)
    TokenType.EQEQ:   2,   # equality
    TokenType.BANGEQ: 2,
    TokenType.LT:     3,   # comparison
    TokenType.GT:     3,
    TokenType.PLUS:   4,   # addition
    TokenType.MINUS:  4,
    TokenType.STAR:   5,   # multiplication
    TokenType.SLASH:  5,
    TokenType.LPAREN: 6,   # call
}

class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos    = 0

    def current(self) -> Token: return self.tokens[self.pos]
    def peek_type(self) -> TokenType: return self.tokens[self.pos].type

    def advance(self) -> Token:
        t = self.tokens[self.pos]
        self.pos += 1
        return t

    def expect(self, ttype: TokenType) -> Token:
        t = self.advance()
        if t.type != ttype:
            raise SyntaxError(f"Expected {ttype}, got {t.type} at {t.line}:{t.column}")
        return t

    # --- Pratt expression parsing ---
    def parse_expr(self, min_bp: int = 0) -> Expr:
        # Null denotation (prefix)
        tok = self.advance()
        left = self._nud(tok)

        # Left denotation (infix) — while next token binds tighter
        while PRECEDENCES.get(self.peek_type(), 0) > min_bp:
            op_tok = self.advance()
            left = self._led(left, op_tok)

        return left

    def _nud(self, tok: Token) -> Expr:
        match tok.type:
            case TokenType.INT:    return IntLit(int(tok.lexeme))
            case TokenType.FLOAT:  return FloatLit(float(tok.lexeme))
            case TokenType.TRUE:   return BoolLit(True)
            case TokenType.FALSE:  return BoolLit(False)
            case TokenType.STRING: return StrLit(tok.lexeme)
            case TokenType.IDENT:  return Identifier(tok.lexeme)
            case TokenType.LPAREN:
                expr = self.parse_expr(0)
                self.expect(TokenType.RPAREN)
                return expr
            case TokenType.MINUS:  return UnaryOp('-', self.parse_expr(6))
            case TokenType.BANG:   return UnaryOp('!', self.parse_expr(6))
            case _: raise SyntaxError(f"Unexpected token {tok}")

    def _led(self, left: Expr, op_tok: Token) -> Expr:
        if op_tok.type == TokenType.LPAREN:  # function call
            args = []
            while self.peek_type() != TokenType.RPAREN:
                args.append(self.parse_expr(0))
                if self.peek_type() == TokenType.COMMA: self.advance()
            self.expect(TokenType.RPAREN)
            return Call(left, args)
        # Infix binary op
        bp = PRECEDENCES[op_tok.type]
        right = self.parse_expr(bp)  # right-assoc: bp-1 for =
        return BinOp(op_tok.lexeme, left, right)
```

# TYPE CHECKER

## Simple Type System
```python
from enum import Enum

class Type(Enum):
    INT = 'int'; FLOAT = 'float'; BOOL = 'bool'; STR = 'str'; VOID = 'void'

class TypeChecker:
    def __init__(self):
        self.env: list[dict[str, Type]] = [{}]   # scope stack

    def push_scope(self): self.env.append({})
    def pop_scope(self):  self.env.pop()

    def declare(self, name: str, t: Type):
        self.env[-1][name] = t

    def lookup(self, name: str) -> Type:
        for scope in reversed(self.env):
            if name in scope: return scope[name]
        raise NameError(f"Undefined variable: {name}")

    def check_expr(self, node: Expr) -> Type:
        match node:
            case IntLit():  return Type.INT
            case FloatLit(): return Type.FLOAT
            case BoolLit(): return Type.BOOL
            case StrLit():  return Type.STR
            case Identifier(name=n): return self.lookup(n)
            case BinOp(op=op, left=l, right=r):
                lt = self.check_expr(l)
                rt = self.check_expr(r)
                if op in ('+', '-', '*', '/'):
                    if lt != rt: raise TypeError(f"Type mismatch: {lt} {op} {rt}")
                    return lt
                if op in ('==', '!=', '<', '>'):
                    if lt != rt: raise TypeError(f"Comparison type mismatch")
                    return Type.BOOL
            case _: raise NotImplementedError(f"No type rule for {type(node)}")
```

# BYTECODE INTERPRETER

## Stack-Based VM
```python
from enum import Enum

class Op(Enum):
    PUSH = auto(); POP = auto(); ADD = auto(); SUB = auto()
    MUL = auto(); DIV = auto(); NEG = auto()
    EQ = auto(); LT = auto(); GT = auto()
    LOAD = auto(); STORE = auto()      # local variable slot
    JUMP = auto(); JUMP_IF_FALSE = auto()
    CALL = auto(); RETURN = auto()
    PRINT = auto(); HALT = auto()

@dataclass
class Instruction:
    op: Op
    operand: Optional[int | str | float] = None

class VM:
    def __init__(self, code: list[Instruction]):
        self.code   = code
        self.stack  = []
        self.locals = {}
        self.ip     = 0   # instruction pointer

    def run(self):
        while self.ip < len(self.code):
            instr = self.code[self.ip]; self.ip += 1
            match instr.op:
                case Op.PUSH:           self.stack.append(instr.operand)
                case Op.POP:            self.stack.pop()
                case Op.ADD:            b = self.stack.pop(); a = self.stack.pop(); self.stack.append(a + b)
                case Op.SUB:            b = self.stack.pop(); a = self.stack.pop(); self.stack.append(a - b)
                case Op.MUL:            b = self.stack.pop(); a = self.stack.pop(); self.stack.append(a * b)
                case Op.LOAD:           self.stack.append(self.locals[instr.operand])
                case Op.STORE:          self.locals[instr.operand] = self.stack.pop()
                case Op.JUMP:           self.ip = instr.operand
                case Op.JUMP_IF_FALSE:
                    if not self.stack.pop(): self.ip = instr.operand
                case Op.PRINT:          print(self.stack.pop())
                case Op.HALT:           return self.stack[-1] if self.stack else None
```

# QUICK TOOLCHAIN REFERENCE
```
PARSER GENERATORS (when manual parsing is overkill):
  Python: PLY, ANTLR4, Lark, PEG.js
  Rust:   Nom (combinator), Pest (PEG)
  Java:   ANTLR4 (gold standard)

LLVM BACKENDS (native code gen):
  Python: llvmlite (NumPy team)
  Rust:   inkwell (safe LLVM bindings)
  C/C++:  LLVM C API directly

TYPE THEORY RESOURCES:
  "Types and Programming Languages" — Benjamin Pierce (the textbook)
  "Crafting Interpreters" — Robert Nystrom (free online, practical)
  "Engineering a Compiler" — Cooper & Torczon
```
