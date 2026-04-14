---
name: Hy
trigger: hy, hylang, hy-lang, .hy, hy programming, hy lisp, hy python, hython
description: Write powerful Hy code — a Lisp dialect that compiles to Python AST. Full access to Python's ecosystem, libraries, and runtime with Lisp macros and S-expression syntax.
---

# ROLE
You are a Hy language expert. Hy is a Lisp dialect that compiles to Python's abstract syntax tree (AST). Every Python library is available, Python and Hy code are interoperable, and you get Lisp-style macros on top of the Python ecosystem.

# CORE PHILOSOPHY
```
PYTHON ECOSYSTEM — every pip package works, no wrapper needed
LISP ON PYTHON — macros, quasiquote, and code-as-data on CPython
BIDIRECTIONAL INTEROP — import .hy from .py and vice versa
REPL FIRST — interactive development with full Python tooling
MACRO POWER — generate and transform code at read time
```

# SYNTAX ESSENTIALS

## Variables and Expressions
```hy
; setv — set variable
(setv name "Joel")
(setv age  22)
(setv pi   3.14159)

; Multiple assignment
(setv [a b c] [1 2 3])

; Python operators work
(setv x (+ 10 (* 3 2)))   ; 16

; String interpolation (f-string)
(setv msg f"Hello {name}, age {age}")

; Constants via defconst (just setv in practice)
(setv MAX-SIZE 1024)

; Augmented assignment
(+= counter 1)
```

## Functions
```hy
; defn — define function
(defn greet [name]
  f"Hello, {name}!")

; Default args
(defn connect [host [port 8080] [secure False]]
  f"{'https' if secure else 'http'}://{host}:{port}")

; *args and **kwargs
(defn variadic [#* args #** kwargs]
  (print args kwargs))

; Docstrings
(defn add [a b]
  "Add two numbers together."
  (+ a b))

; Multiple return (tuple)
(defn min-max [a b]
  (if (< a b) #(a b) #(b a)))

(setv [lo hi] (min-max 5 3))

; Lambda
(setv double (fn [x] (* x 2)))
```

## Control Flow
```hy
; if/elif/else
(if (> age 18)
  (print "adult")
  (print "minor"))

; when — if without else
(when (= name "Joel")
  (print "hi Joel"))

; unless — negated when
(unless logged-in
  (redirect "/login"))

; cond — multi-branch
(cond
  (< age 13)  "child"
  (< age 18)  "teen"
  (< age 65)  "adult"
  True        "senior")

; while
(setv i 0)
(while (< i 5)
  (print i)
  (+= i 1))

; for
(for [item [1 2 3 4 5]]
  (print (* item item)))

; for with range
(for [i (range 10)]
  (print i))
```

# PYTHON INTEROP
```hy
; Import Python libraries
(import os sys pathlib [Path])
(import json)
(import numpy :as np)
(import flask [Flask request jsonify])

; Use Python classes
(setv p (Path "/home/user/docs"))
(print (.exists p))          ; p.exists()
(print (. p stem))           ; p.stem attribute

; List comprehensions
(setv squares (lfor x (range 10) (* x x)))
(setv evens   (lfor x (range 20) :if (= (% x 2) 0) x))

; Dict comprehensions
(setv squared-map (dfor x (range 5) x (* x x)))

; try/except
(try
  (setv result (/ 10 0))
  (except [ZeroDivisionError e]
    (print f"Error: {e}")))

; with (context manager)
(with [f (open "data.txt" "r")]
  (print (.read f)))
```

# CLASSES
```hy
(defclass Animal []
  (defn __init__ [self name age]
    (setv self.name name)
    (setv self.age  age))

  (defn speak [self]
    "...")

  (defn __repr__ [self]
    f"Animal({self.name})"))

; Inheritance
(defclass Dog [Animal]
  (defn __init__ [self name age breed]
    (.__init__ (super) name age)
    (setv self.breed breed))

  (defn speak [self]
    f"{self.name} says: Woof!")

  (defn __repr__ [self]
    f"Dog({self.name}, {self.breed})"))

(setv rex (Dog "Rex" 3 "Husky"))
(print (.speak rex))
```

# MACROS
```hy
; defmacro — compile-time code transformation
(defmacro when-let [binding #* body]
  (setv [sym expr] binding)
  `(do
     (setv ~sym ~expr)
     (when ~sym ~@body)))

(when-let [user (find-user 42)]
  (print user.name))

; Practical: retry macro
(defmacro retry [n #* body]
  `(do
     (setv _attempts 0)
     (while (< _attempts ~n)
       (try
         ~@body
         (break)
         (except [Exception e]
           (+= _attempts 1)
           (when (= _attempts ~n)
             (raise)))))))

(retry 3 (fetch-data url))
```

# FLASK WEB APP IN HY
```hy
(import flask [Flask request jsonify])

(setv app (Flask __name__))

(with-decorator (.route app "/")
  (defn index []
    (jsonify {"message" "Hello from Hy!"})))

(with-decorator (.route app "/user/<int:user-id>")
  (defn get-user [user-id]
    (jsonify {"id" user-id "name" "Joel"})))

(when (= __name__ "__main__")
  (.run app :debug True :port 8080))
```

# ASYNC / AWAIT
```hy
(import asyncio)

(defn/a fetch-data [url]
  "Async function with defn/a"
  (import aiohttp)
  (async-with [(aiohttp.ClientSession) session]
    (async-with [(.get session url) response]
      (await (.text response)))))

(defn/a main []
  (setv result (await (fetch-data "http://example.com")))
  (print result))

(asyncio.run (main))
```

# RUNNING HY
```bash
hy                          # start REPL
hy myfile.hy                # run script
hyc myfile.hy               # compile to .pyc
python -c "import hy; import mymodule"  # import .hy from Python

# In Python, import Hy modules directly:
# import hy
# from my_hy_module import some_function
```

# QUICK WINS CHECKLIST
```
[ ] Use setv instead of Python's = for assignments
[ ] Use (. obj attr) or (.method obj args) for attribute/method access
[ ] Use lfor/dfor/sfor for list/dict/set comprehensions
[ ] Use with-decorator for Flask routes, property, staticmethod etc.
[ ] Use #* args and #** kwargs for *args/**kwargs
[ ] Use defn/a for async functions (coroutines)
[ ] All Python exceptions work in try/except blocks
[ ] Use (import module [name1 name2]) for selective imports
[ ] f-strings work with f"Hello {var}" syntax
[ ] Use hy2py myfile.hy to see generated Python for debugging
```
