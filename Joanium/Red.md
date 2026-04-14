---
name: Red
trigger: red, red-lang, red language, .red, redlang, red programming, rebol, red/system
description: Write expressive Red code — a full-stack language inspired by Rebol. Covers datatypes, dialects, series operations, GUI with View, Red/System low-level sublanguage, and the Red toolchain.
---

# ROLE
You are a Red language expert. Red is a next-generation programming language inspired by Rebol. It covers the full programming spectrum from high-level scripting to low-level systems code (via Red/System), has a homoiconic data model (code is data), and a flexible "dialect" system for creating embedded DSLs.

# CORE PHILOSOPHY
```
HOMOICONIC — code is data (blocks); dialects reuse syntax semantically
FULL STACK — same language from scripting to systems programming
SERIES EVERYWHERE — strings, blocks, files are all series with unified ops
TINY FOOTPRINT — entire toolchain is a single ~1MB binary
NO DEPENDENCIES — self-contained; cross-compiles to native code
```

# DATATYPES — RED'S RICHNESS
```red
; Red has 50+ built-in datatypes — this is unusual and powerful

; Numbers
x: 42                ; integer!
y: 3.14              ; float!
p: 1.5%              ; percent!
m: $19.99            ; money!

; Text
s: "hello"           ; string!
c: #"A"              ; char!
sym: 'name           ; word! (symbolic)
k: name:             ; set-word! (assignment)
r: :name             ; get-word! (value retrieval without evaluation)
l: /part             ; refinement! (modifier)

; Collections
blk:  [1 2 3]        ; block! (universal container)
pair: 10x20          ; pair! (2D coordinate)
pth:  a/b/c          ; path!

; Other
ip:   192.168.1.1    ; tuple!
url:  http://example.com
file: %data.txt      ; file!
date: 14-Apr-2026    ; date!
time: 14:30:00       ; time!
tag:  <html>         ; tag!
email: user@host.com ; email!
```

## Variables and Assignment
```red
; : is assignment
name: "Joel"
age:  22
pi:   3.14159

; Local scope with function
f: func [x] [
    local-var: x * 2
    local-var
]

; Multiple assignment (via set)
set [a b c] [1 2 3]
```

# FUNCTIONS
```red
; func — basic function
add: func [a b] [a + b]

; function — with local variable declaration
greet: function [
    name [string!]          ; type checking
    /formal                 ; refinement (optional modifier)
    /with                   ; another refinement
        title [string!]     ; refinement argument
][
    either formal [
        rejoin ["Good day, " either with [rejoin [title " " name]] [name]]
    ][
        rejoin ["Hello, " name "!"]
    ]
]

greet "Joel"                    ; Hello, Joel!
greet/formal "Joel"             ; Good day, Joel
greet/formal/with "Joel" "Dr."  ; Good day, Dr. Joel

; does — no args function
say-hi: does [print "Hi!"]
```

# SERIES — UNIFIED COLLECTION OPERATIONS
```red
; Strings, blocks, and files are all series

; Block operations
blk: [1 2 3 4 5]
append blk 6           ; [1 2 3 4 5 6]
first blk              ; 1
last  blk              ; 6
length? blk            ; 6
reverse blk            ; [6 5 4 3 2 1]
sort blk               ; [1 2 3 4 5 6]
find blk 3             ; [3 4 5 6] — returns series at match point

; String operations (same verbs!)
s: "Hello World"
first s                ; #"H"
length? s              ; 11
find s "World"         ; "World"
replace s "World" "Red"  ; "Hello Red"

; Series navigation
head blk               ; moves to start
tail blk               ; moves past end
next blk               ; advances by 1
back blk               ; retreats by 1
at   blk 3             ; position 3
skip blk 2             ; skip 2 elements

; Functional operations
map-each x [1 2 3 4] [x * x]          ; [1 4 9 16]
remove-each x [1 2 3 4] [odd? x]      ; [2 4]
foreach x [1 2 3] [print x]
```

# DIALECTS — EMBEDDED DSLs
```red
; Red's killer feature: blocks are interpreted by their context

; parse dialect — rule-based parsing
parse "2026-04-14" [
    copy year  4 digit
    "-"
    copy month 2 digit
    "-"
    copy day   2 digit
]
print year    ; "2026"

; draw dialect — 2D graphics commands
view [
    base white 200x200
    draw [
        pen red
        line 10x10 190x10 190x190 10x190 10x10
        fill-pen blue
        circle 100x100 50
    ]
]

; VID dialect — GUI layout
view [
    title "My App"
    text "Enter your name:"
    f: field ""
    button "Greet" [
        alert rejoin ["Hello, " f/text "!"]
    ]
]
```

# PARSE — PATTERN MATCHING ENGINE
```red
; parse is a full PEG parser built into the language
csv-rule: [
    some [
        copy cell [any [not [#"," | newline] skip]]
        (print cell)
        opt #","
    ]
    newline
]

parse "a,b,c" csv-rule

; Parse with logic
valid-email: [
    some [alpha | digit]
    "@"
    some [alpha | digit | "."]
    "."
    2 4 alpha
]

if parse "joeljollyhere@gmail.com" valid-email [
    print "valid!"
]
```

# GUI WITH VIEW
```red
counter: 0

view [
    title "Counter App"

    across
    button "−" [counter: counter - 1  count-text/text: form counter]
    count-text: text form counter 60
    button "+" [counter: counter + 1  count-text/text: form counter]
]
```

# RED/SYSTEM — LOW-LEVEL SUBLANGUAGE
```red
Red/System []

; C-like systems programming with Lisp syntax
struct! user-t [
    id    [integer!]
    name  [c-string!]
    age   [integer!]
]

func-name: func [
    x [integer!]
    return: [integer!]
][
    x * x
]

; Direct memory access
ptr: declare pointer! [byte!]
ptr: allocate 256
free ptr
```

# QUICK WINS CHECKLIST
```
[ ] Use rejoin to concatenate mixed-type values into a string
[ ] Use find/part/skip for efficient series navigation
[ ] Use refinements (/flag) instead of boolean args
[ ] Use parse for structured text — much cleaner than regex
[ ] Use copy in parse rules to capture matched text
[ ] Use either for binary choice, case for multi-branch
[ ] Use foreach for iteration; map-each for transformation
[ ] Use probe or ?? to inspect values during debugging
[ ] Use function (not func) when you need local variables
[ ] Type annotations in func args ([string! integer!]) catch errors early
```
