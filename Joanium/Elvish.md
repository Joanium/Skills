---
name: Elvish Shell
trigger: elvish, elvish shell, elvish-shell, .elv, elvish scripting, elvish programming, elv language
description: Write powerful Elvish shell scripts. Covers syntax, structured data pipelines, exceptions, modules, interactive features, and the key ways Elvish differs from bash.
---

# ROLE
You are an Elvish shell expert. Elvish is a modern, expressive shell language that treats structured data (lists, maps) as first-class pipeline citizens — not just text streams. It has proper exceptions, lexical scoping, modules, and a built-in readline with programmable completions.

# CORE PHILOSOPHY
```
STRUCTURED DATA PIPELINES — pipe lists/maps, not just text
REAL EXCEPTIONS — try/catch, not exit codes everywhere
LEXICAL SCOPE — variables don't bleed between scopes
FUNCTIONAL FLAVOUR — higher-order functions, closures
INTERACTIVE + SCRIPTING — same language in both modes
```

# SYNTAX ESSENTIALS

## Variables
```elvish
# var — declares a variable
var name = "Joel"
var age  = 22
var pi   = 3.14159

# Multiple assignment
var a b = 1 2

# Reassignment (no var)
set name = "Joel Jolly"

# Environment variables via E:
set E:PATH = $E:PATH":""/home/joel/bin"

# Capture command output
var files = [(ls)]

# List
var nums = [1 2 3 4 5]

# Map
var config = [&host=localhost &port=8080]
```

## Functions
```elvish
# fn — function definition
fn greet {|name|
    echo "Hello, "$name"!"
}

greet Joel

# Multiple params
fn add {|a b|
    + $a $b
}

# Rest args
fn sum {|@nums|
    var total = 0
    for n $nums {
        set total = (+ $total $n)
    }
    put $total
}

# Return value — use put (outputs to pipeline)
fn double {|x|
    put (* $x 2)
}

var result = (double 5)   # 10

# Closures
fn make-adder {|n|
    put {|x| put (+ $x $n)}
}

var add5 = (make-adder 5)
$add5 3   # 8
```

# PIPELINES — STRUCTURED DATA
```elvish
# Traditional text pipeline still works
ls | grep ".go"

# But Elvish can pipe structured values
# each — iterate over pipeline values
echo &sep="" one two three | each {|word|
    echo "word: "$word
}

# Pipe a list into each
put 1 2 3 4 5 | each {|n| put (* $n $n)}

# where — filter
put 1 2 3 4 5 6 | where {|n| == (% $n 2) 0}   # 2 4 6

# All on a list
var nums = [1 2 3 4 5]
each {|n| echo $n} $nums

# Collect results
var squares = [(put 1 2 3 4 5 | each {|n| put (* $n $n)})]
```

# CONTROL FLOW
```elvish
# if/elif/else
if (> $age 18) {
    echo "adult"
} elif (> $age 12) {
    echo "teen"
} else {
    echo "child"
}

# for loop
for item [a b c d] {
    echo $item
}

# while
var i = 0
while (< $i 5) {
    echo $i
    set i = (+ $i 1)
}

# break/continue
for n [1 2 3 4 5] {
    if (== $n 3) { break }
    echo $n
}
```

# EXCEPTIONS
```elvish
# try/catch — real exception handling, not exit code checking
try {
    cat /nonexistent-file
} catch e {
    echo "Error: "$e[message]
}

# fail — raise an exception
fn divide {|a b|
    if (== $b 0) {
        fail "division by zero"
    }
    put (/ $a $b)
}

# except in pipeline
try {
    divide 10 0
} catch e {
    echo "caught: "$e[message]
}

# Checking exit codes the Elvish way
if ?(test -f myfile.txt) {
    echo "file exists"
}
```

# MAPS AND LISTS
```elvish
# Map (associative array)
var config = [&host=localhost &port=8080 &debug=$false]

# Access
echo $config[host]          # localhost

# Modify (creates new map — maps are immutable by default)
set config[debug] = $true

# Check key
has-key $config host   # true

# List
var items = [alpha beta gamma]

# Index
echo $items[0]    # alpha
echo $items[-1]   # gamma (last)

# Slice
echo $items[1..3]   # [beta gamma]

# Concatenate
var more = (conj $items delta epsilon)
```

# STRING OPERATIONS
```elvish
var s = "Hello, World!"

# Length
count $s

# Split
var parts = [(str:split , "a,b,c")]

# Join
str:join - [a b c]    # a-b-c

# Contains, has-prefix, has-suffix
str:has-prefix $s "Hello"     # true
str:has-suffix $s "World!"    # true
str:contains   $s "lo, W"     # true

# Replace
str:replace "World" "Elvish" $s

# Upper/lower
str:to-upper $s
str:to-lower $s
```

# MODULES
```elvish
# mylib.elv
fn public-fn {|x|
    put (* $x 2)
}

# main.elv
use ./mylib

echo (mylib:public-fn 5)    # 10

# Built-in modules
use str
use path
use math
use re

str:split / "a/b/c"
path:join /usr local bin
math:sqrt 16.0
re:match '\d+' "abc123"
```

# INTERACTIVE FEATURES
```elvish
# ~/.config/elvish/rc.elv — shell config

# Prompt customization
set edit:prompt = {
    if (has-env "VIRTUAL_ENV") {
        styled "[venv] " green
    }
    styled (tilde-abbr $pwd) blue
    styled " $ " bold
}

# Completions
set edit:completion:arg-completer[myapp] = {|@args|
    put deploy build test
}

# Aliases (just functions)
fn ll { ls -la $@args }
fn gs { git status }
fn gc { git commit -m $@args }
```

# QUICK WINS CHECKLIST
```
[ ] Use put to output values to pipeline (not echo for data)
[ ] Use each/where for structured pipeline processing
[ ] Use try/catch for error handling — not exit code checking
[ ] Use $() — NO! Use (cmd) for command substitution in Elvish
[ ] Use ? prefix to convert exceptions to booleans: ?(cmd)
[ ] Use var for declaration, set for mutation
[ ] Access map keys with $map[key], list items with $list[index]
[ ] Use the str: module for all string operations
[ ] Use path: module for file path manipulation
[ ] Source rc.elv for interactive config; use modules for shared code
```
