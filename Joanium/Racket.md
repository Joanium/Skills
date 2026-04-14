---
name: Racket
trigger: racket, racket-lang, .rkt, racket programming, racket language, drracket, racket scheme, plt scheme, raco
description: Write productive Racket code — a batteries-included Lisp for language-oriented programming. Covers syntax, macros, contracts, typed racket, web server, and the raco package manager.
---

# ROLE
You are a Racket language expert. Racket is a full-spectrum Lisp descendant designed for language-oriented programming. It ships with a complete IDE (DrRacket), a powerful macro system, a contract system, an optional type checker (Typed Racket), and a built-in web server.

# CORE PHILOSOPHY
```
LANGUAGE-ORIENTED — build DSLs as first-class languages with #lang
MACROS ARE THE LANGUAGE — syntax transformers, not text substitution
CONTRACTS — behavioral specifications enforced at runtime
BATTERIES INCLUDED — web server, GUI, image, math built in
PEDAGOGICAL — designed for teaching and professional use equally
```

# SYNTAX ESSENTIALS

## Values and Definitions
```racket
#lang racket

; Immutable binding
(define name "Joel")
(define age  22)
(define pi   3.14159)

; Multiple values
(define-values (a b c) (values 1 2 3))

; Let binding (local scope)
(let ([x 10]
      [y 20])
  (+ x y))   ; 30

; let* — sequential bindings
(let* ([x 5]
       [y (* x 2)])   ; x is available for y
  y)   ; 10

; letrec — recursive bindings
(letrec ([even? (lambda (n) (if (= n 0) #t (odd? (- n 1))))]
         [odd?  (lambda (n) (if (= n 0) #f (even? (- n 1))))])
  (even? 4))   ; #t
```

## Functions
```racket
; Basic function
(define (add a b) (+ a b))

; Lambda
(define double (lambda (x) (* x 2)))
(define triple (λ (x) (* x 3)))   ; λ is alias for lambda

; Optional and keyword args
(define (connect #:host [host "localhost"]
                 #:port [port 8080]
                 #:secure [secure #f])
  (string-append (if secure "https" "http") "://" host ":" (number->string port)))

(connect #:port 443 #:secure #t)

; Variable args (rest args)
(define (my-list . items) items)
(my-list 1 2 3)   ; '(1 2 3)

; Higher-order
(define (compose f g) (lambda (x) (f (g x))))
(define add1-then-double (compose double add1))
(add1-then-double 4)   ; 10
```

## Data Structures
```racket
; Lists — fundamental
(define nums '(1 2 3 4 5))
(car nums)          ; 1 (first)
(cdr nums)          ; '(2 3 4 5) (rest)
(cons 0 nums)       ; '(0 1 2 3 4 5)

; Vectors — mutable, random access O(1)
(define v (vector 1 2 3))
(vector-ref v 1)    ; 2
(vector-set! v 1 99)

; Hash tables
(define h (make-hash '((name . "Joel") (age . 22))))
(hash-ref h 'name)         ; "Joel"
(hash-set! h 'email "joeljollyhere@gmail.com")
(hash->list h)             ; all entries

; Structs
(struct point (x y) #:transparent)
(define p (point 3.0 4.0))
(point-x p)    ; 3.0
(point? p)     ; #t
```

# MACROS
```racket
; syntax-rules — pattern-based macros
(define-syntax my-when
  (syntax-rules ()
    [(_ cond body ...)
     (if cond (begin body ...) (void))]))

(my-when (> age 18) (display "adult") (newline))

; syntax-parse — industrial-strength macro system
(require syntax/parse)

(define-syntax (while stx)
  (syntax-parse stx
    [(_ condition:expr body:expr ...)
     #'(let loop ()
         (when condition
           body ...
           (loop)))]))

(let ([i 0])
  (while (< i 5)
    (display i)
    (set! i (add1 i))))

; define-syntax-rule — simple pattern alias
(define-syntax-rule (swap! a b)
  (let ([tmp a])
    (set! a b)
    (set! b tmp)))
```

# CONTRACTS
```racket
(require racket/contract)

; Function contracts — behavioral specifications
(define/contract (divide a b)
  (-> real? (and/c real? (not/c zero?)) real?)
  (/ a b))

(divide 10 2)     ; 5
(divide 10 0)     ; Contract violation: not/c zero?

; Custom predicates
(define positive-integer? (and/c integer? positive?))

(define/contract (make-user name age)
  (-> string? positive-integer? hash?)
  (make-hash `((name . ,name) (age . ,age))))

; Struct contracts
(struct/contract point
  ([x real?]
   [y real?]))
```

# PATTERN MATCHING
```racket
(require racket/match)

(define (describe-list lst)
  (match lst
    ['()          "empty"]
    [(list x)     (format "singleton: ~a" x)]
    [(list x y)   (format "pair: ~a, ~a" x y)]
    [(list x . r) (format "starts with ~a, ~a more" x (length r))]))

; Match structs
(define (area shape)
  (match shape
    [(point x y)          0]     ; point struct
    [(circle r)           (* pi r r)]
    [(rect w h)           (* w h)]))

; Guard conditions
(define (classify n)
  (match n
    [(? negative?)    "negative"]
    [0                "zero"]
    [(? even?)        "positive even"]
    [_                "positive odd"]))
```

# WEB SERVER
```racket
#lang web-server/insta

; Simple web app with the servlet system
(define (start request)
  (response/xexpr
    `(html
      (head (title "Hello"))
      (body (h1 "Hello from Racket!")
            (p ,(format "Path: ~a"
                  (url->string (request-uri request))))))))

; Or using the web-server library
(require web-server/servlet web-server/servlet-env)

(define (my-app req)
  (response/output
    (lambda (out)
      (display "Hello World" out))))

(serve/servlet my-app
  #:port 8080
  #:servlet-path "/")
```

# TYPED RACKET
```racket
#lang typed/racket

; Full static type checking
(: add (-> Integer Integer Integer))
(define (add a b) (+ a b))

(: greet (-> String String))
(define (greet name)
  (string-append "Hello, " name "!"))

; Polymorphic types
(: my-map (All (A B) (-> (-> A B) (Listof A) (Listof B))))
(define (my-map f lst)
  (if (null? lst) '()
      (cons (f (car lst)) (my-map f (cdr lst)))))

; Union types
(: safe-div (-> Real Real (U Real #f)))
(define (safe-div a b)
  (if (zero? b) #f (/ a b)))
```

# RACO (PACKAGE MANAGER)
```bash
raco pkg install pkg-name          # install package
raco pkg update                    # update all packages
raco pkg remove pkg-name           # remove
raco test file.rkt                 # run tests
raco exe file.rkt                  # compile to executable
raco doc                           # browse docs
raco make file.rkt                 # precompile
```

# QUICK WINS CHECKLIST
```
[ ] Start files with #lang racket (or typed/racket for type safety)
[ ] Use define/contract to specify behavioral guarantees on functions
[ ] Use syntax-parse for non-trivial macros — more error messages
[ ] Use match instead of nested cond for structural pattern matching
[ ] Use hash for mutable maps, hasheq for symbol-keyed maps
[ ] Use struct with #:transparent for printable, pattern-matchable structs
[ ] Use for/list, for/fold, for/hash instead of manual recursion
[ ] Use raco test for running test suites
[ ] Use with-handlers for structured exception handling
[ ] Use racket/trace for debugging function calls with (trace function-name)
```
