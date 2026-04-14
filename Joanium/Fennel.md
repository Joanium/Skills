---
name: Fennel
trigger: fennel, fennel-lang, .fnl, fennel lisp, fennel lua, fennel programming, fennel language
description: Write expressive Fennel code — a Lisp that compiles to Lua. Covers syntax, macros, pattern matching, destructuring, modules, and embedding in Lua environments like LÖVE2D and Neovim.
---

# ROLE
You are a Fennel language expert. Fennel is a Lisp that compiles to Lua — you get Lua's performance, ecosystem, and embeddability with Lisp's macros, pattern matching, and expressive power. It's used in game development (LÖVE2D), Neovim configuration, and any Lua-embedded environment.

# CORE PHILOSOPHY
```
COMPILES TO LUA — runs anywhere Lua runs (games, editors, embedded)
ZERO RUNTIME OVERHEAD — macros expand at compile time
DESTRUCTURING EVERYWHERE — sequences, tables, multi-value
PATTERN MATCHING — match replaces nested if/elseif chains
LUA INTEROP — call any Lua library, use any Lua value
```

# SYNTAX ESSENTIALS

## Variables and Bindings
```fennel
;; let for local immutable bindings
(let [name "Joel"
      age  22
      pi   3.14159]
  (print name age))

;; var for mutable locals
(var counter 0)
(set counter (+ counter 1))

;; Global definition
(global MY-CONST 100)

;; Multiple return values
(let [(a b) (values 1 2)]
  (print a b))
```

## Functions
```fennel
;; fn — anonymous function
(fn [x] (* x x))

;; lambda shorthand (same as fn)
(lambda [x y] (+ x y))

;; Named function with global
(fn greet [name]
  (.. "Hello, " name "!"))

;; Local named function
(let [double (fn [x] (* x 2))]
  (double 5))    ; 10

;; Variadic
(fn sum [...]
  (let [nums [...]]
    (accumulate [total 0 _ n (ipairs nums)]
      (+ total n))))

;; Method call shorthand
(: obj :method arg1 arg2)   ; obj:method(arg1, arg2) in Lua
```

## Tables (Fennel's Everything)
```fennel
;; Sequential table (array)
(let [nums [1 2 3 4 5]]
  (. nums 1))    ; 1 (Lua is 1-indexed)

;; Hash table
(let [config {:host "localhost"
              :port 8080
              :debug false}]
  (. config :host))       ; "localhost"
  config.host)            ; alternative dot syntax

;; Nested
(let [app {:db {:host "db.local" :port 5432}}]
  (. (. app :db) :host))    ; "db.local"
  app.db.host)              ; or dot notation
```

# DESTRUCTURING
```fennel
;; Sequential destructuring
(let [[first second & rest] [1 2 3 4 5]]
  (print first)   ; 1
  (print second)  ; 2
  (print rest))   ; [3 4 5]

;; Table destructuring
(let [{:host host :port port} {:host "localhost" :port 8080}]
  (print host port))

;; Destructuring in function args
(fn print-point [{:x x :y y}]
  (print (.. "(" x ", " y ")")))

(print-point {:x 3 :y 4})   ; (3, 4)

;; Nested
(let [{:db {:host db-host}} {:db {:host "db.local"}}]
  (print db-host))   ; db.local
```

# PATTERN MATCHING
```fennel
(match shape
  {:type :circle :radius r}        (* math.pi r r)
  {:type :rect :w w :h h}          (* w h)
  {:type :point}                   0
  _                                (error "unknown shape"))

;; Guards
(match score
  (where s (>= s 90))   "A"
  (where s (>= s 80))   "B"
  (where s (>= s 70))   "C"
  _                      "F")

;; Matching sequences
(match nums
  []          "empty"
  [x]         (.. "one: " x)
  [x y & r]  (.. "many, starts with " x))
```

# MACROS
```fennel
;; defmacro — compile-time code transformation
(macro when [condition & body]
  `(if ,condition (do ,(table.unpack body))))

(when (> age 18)
  (print "adult")
  (set verified true))

;; Practical macro: assert
(macro assert! [cond msg]
  `(when (not ,cond)
     (error ,msg)))

;; With-open pattern
(macro with-file [bindings & body]
  (let [[name path mode] bindings]
    `(let [,name (io.open ,path ,mode)]
       (when ,name
         (let [result (do ,(table.unpack body))]
           (: ,name :close)
           result)))))

(with-file [f "data.txt" "r"]
  (: f :read "*all"))
```

# LUA INTEROP
```fennel
;; Require Lua modules
(local json (require :dkjson))
(local http (require :socket.http))

;; Call methods with : operator
(let [file (io.open "data.txt" "r")]
  (: file :read "*all")
  (: file :close))

;; Access Lua globals
lua-version   ; accesses _VERSION
(rawget _G :print)

;; Inline Lua when needed
(lua "local x = require('some.c.module')")

;; Use Lua standard library directly
(table.insert my-list item)
(string.format "%.2f" 3.14159)
(math.floor 4.9)
```

# LÖVE2D GAME EXAMPLE
```fennel
;; main.fnl — LÖVE2D game with Fennel
(local fennel (require :fennel))

;; game state
(var state {:x 100 :y 100 :speed 200})

(fn love.update [dt]
  (when (love.keyboard.isDown :right)
    (set state.x (+ state.x (* state.speed dt))))
  (when (love.keyboard.isDown :left)
    (set state.x (- state.x (* state.speed dt)))))

(fn love.draw []
  (love.graphics.setColor 1 0.4 0.4 1)
  (love.graphics.circle :fill state.x state.y 20))
```

# NEOVIM CONFIG EXAMPLE
```fennel
;; init.fnl — Neovim config in Fennel (with Aniseed or Hotpot)
(local nvim vim)

;; Set options
(set nvim.opt.number true)
(set nvim.opt.tabstop 4)

;; Keymaps
(nvim.keymap.set :n :<leader>ff
  (fn [] ((. (require :telescope.builtin) :find_files)))
  {:desc "Find files"})

;; Autocmds
(nvim.api.nvim_create_autocmd :BufWritePre
  {:pattern "*.fnl"
   :callback (fn [] (print "saving fennel file"))})
```

# MODULES
```fennel
;; mymodule.fnl
(local M {})

(fn M.greet [name]
  (.. "Hello, " name "!"))

(fn M.add [a b]
  (+ a b))

M   ; return the module table

;; main.fnl
(local mymod (require :mymodule))
(print (mymod.greet "Joel"))
```

# QUICK WINS CHECKLIST
```
[ ] Use let for all local bindings — never bare locals outside let
[ ] Use destructuring in function args instead of (. tbl :key) chains
[ ] Use match instead of nested if/elseif for multi-branch logic
[ ] Use macros for repetitive patterns — they compile to zero overhead
[ ] Use : method call syntax for Lua OOP objects
[ ] Use (.. str1 str2) for string concatenation (Lua's .. operator)
[ ] Use #list for table length (Lua's # operator)
[ ] Use ipairs for array-style tables, pairs for hash-style
[ ] Use (values ...) for multiple returns, destructure with let [(a b) ...]
[ ] Test with: fennel --eval "(require :mymodule)" from the shell
```
