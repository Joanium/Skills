---
name: Janet
trigger: janet, janet-lang, .janet, janet programming, janet language, janet lisp, jpm, janet scripting
description: Write expressive Janet code — a Lisp/Clojure-inspired scripting language with C interop. Covers syntax, macros, fibers, PEG parsing, modules, and the JPM package manager.
---

# ROLE
You are a Janet language expert. Janet is a dynamic, functional, Lisp-inspired scripting and systems language that embeds cleanly into C projects. It has first-class fibers (coroutines), a powerful PEG parser, and a small footprint (~1MB). Think Lua meets Clojure.

# CORE PHILOSOPHY
```
EMBEDDABLE — designed to live inside C/C++ applications
FIBERS FIRST — coroutines are the concurrency primitive
PEG PARSING — built-in parsing expression grammars
MINIMAL CORE — small, learnable, no magic
LISP HERITAGE — code is data, macros transform code
```

# SYNTAX ESSENTIALS

## Basic Values and Binding
```janet
# Immutable binding
(def name "Joel")
(def age 22)
(def pi 3.14159)

# Mutable variable
(var counter 0)
(set counter (+ counter 1))
(++ counter)   # shorthand

# Data structures
(def arr   @[1 2 3 4 5])      # mutable array
(def tup   [1 2 3])           # immutable tuple
(def tab   @{"key" "val"})    # mutable table
(def struct {:x 1 :y 2})      # immutable struct

# Nil and booleans
(def nothing nil)
(def yes true)
(def no  false)
```

## Functions
```janet
# Basic function
(defn add [a b]
  (+ a b))

# Optional/default via destructuring
(defn greet [name &opt age]
  (default age 0)
  (if (> age 0)
    (string "Hello " name ", age " age)
    (string "Hello " name)))

# Variadic
(defn sum [& nums]
  (reduce + 0 nums))

(sum 1 2 3 4 5)   # 15

# Anonymous functions
(def double (fn [x] (* x 2)))
(def triple |(* $ 3))          # shorthand: $ is the argument
```

## Control Flow
```janet
# if/when/unless
(if (> age 18)
  (print "adult")
  (print "minor"))

(when (= name "Joel") (print "hi Joel"))

# cond — multi-branch
(cond
  (< age 13)  "child"
  (< age 18)  "teen"
  (< age 65)  "adult"
  "senior")

# case
(case direction
  :north "going north"
  :south "going south"
  "unknown")

# for loop
(for i 0 10 (print i))

# each over collection
(each item [1 2 3]
  (print (* item item)))
```

# TABLES AND STRUCTS
```janet
# Table — mutable dict
(def config @{:host "localhost" :port 8080})
(put config :debug true)
(get config :host)   # "localhost"
(config :host)       # shorthand keyword access

# Struct — immutable dict
(def point {:x 3 :y 4})
(def updated (merge point {:z 0}))   # creates new struct

# Nested access
(def app {:db {:host "db.local" :port 5432}})
(get-in app [:db :host])   # "db.local"
```

# MACROS
```janet
# Macros transform code at compile time
(defmacro when-let [[binding expr] & body]
  ~(let [,binding ,expr]
     (when ,binding ,;body)))

(when-let [user (find-user 42)]
  (print "Found: " (user :name)))

# defmacro with quasiquote ~ and unquote ,
(defmacro swap! [a b]
  ~(do
     (def tmp ,a)
     (set ,a ,b)
     (set ,b tmp)))

(var x 1) (var y 2)
(swap! x y)
(print x y)   # 2 1

# assert macro
(defmacro assert [cond msg]
  ~(when (not ,cond)
     (error ,msg)))
```

# FIBERS (COROUTINES)
```janet
# Fiber — cooperative coroutine
(def gen
  (fiber/new
    (fn []
      (yield 1)
      (yield 2)
      (yield 3)
      "done")))

(print (resume gen))   # 1
(print (resume gen))   # 2
(print (resume gen))   # 3
(print (resume gen))   # "done" (fiber returned)

# Generator pattern
(defn range-gen [start end]
  (fiber/new
    (fn []
      (var i start)
      (while (< i end)
        (yield i)
        (++ i)))))

(def gen (range-gen 0 5))
(each-fiber gen (fn [v] (print v)))

# Fibers for error handling
(def result
  (fiber/new
    (fn []
      (error "something went wrong"))))

(case (fiber/status result)
  :error (print "caught: " (fiber/last-value result))
  :dead  (print "done"))
```

# PEG PARSING
```janet
# Built-in Parsing Expression Grammars
(def date-peg
  (peg/compile
    '{:year  (capture (repeat 4 :d))
      :month (capture (repeat 2 :d))
      :day   (capture (repeat 2 :d))
      :main  (* :year "-" :month "-" :day)}))

(peg/match date-peg "2026-04-14")
# => @["2026" "04" "14"]

# More patterns
(def csv-peg
  (peg/compile
    '{:cell  (capture (any (if-not (set ",\n") 1)))
      :row   (any (* :cell (? ",")))
      :main  (any (* :row "\n"))}))
```

# C INTEROP
```janet
# Call C functions via janet's C API (in embedding context)
# Or use native modules

# Import a Janet native module (.so/.dll)
(import path/to/native-module :as mod)
(mod/some-function arg1 arg2)

# Janet C embedding (in C code)
# janet_init();
# JanetTable *env = janet_core_env(NULL);
# janet_dostring(env, "(print \"hello\")", "main", NULL);
# janet_deinit();
```

# MODULES AND IMPORTS
```janet
# mymodule.janet
(defn public-fn [x] (* x 2))
(def- private-val 42)   # def- is module-private

# main.janet
(import ./mymodule :as m)
(print (m/public-fn 5))   # 10

# Import with prefix
(import spork/path)
(path/join "usr" "local" "bin")
```

# JPM (JANET PACKAGE MANAGER)
```bash
jpm install                 # install declared deps
jpm add https://github.com/user/pkg   # add package
jpm build                   # build project
jpm test                    # run tests
jpm run script-name         # run project.janet script
```

```janet
# project.janet
(declare-project
  :name "myapp"
  :description "My Janet application"
  :dependencies ["https://github.com/janet-lang/spork"])

(declare-executable
  :name "myapp"
  :entry "src/main.janet")
```

# QUICK WINS CHECKLIST
```
[ ] Use def for immutable, var only when mutation is needed
[ ] Use | shorthand for single-argument closures: |(* $ 2)
[ ] Use get-in for nested table/struct access
[ ] Use fiber/new + yield for generators and lazy sequences
[ ] Use peg/compile for parsing — avoid string regex for structured data
[ ] Use merge for "updating" immutable structs
[ ] Use defmacro with quasiquote ~ and unquote , for code generation
[ ] Use spork library for HTTP, JSON, and common utilities
[ ] Use (pp value) to pretty-print data structures during debugging
[ ] Embed Janet in C apps with ~5 lines of init code
```
