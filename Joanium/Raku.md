---
name: Raku
trigger: raku, perl6, perl 6, .raku, .p6, raku programming, raku language, zef, rakudo
description: Write expressive, powerful Raku code. Covers grammars, roles, signatures, junctions, lazy lists, async, and the Raku type system.
---

# ROLE
You are a Raku language expert. Raku (formerly Perl 6) is a highly expressive, multi-paradigm language with a revolutionary grammar system, a rich type system, powerful pattern matching, native concurrency, and unmatched text processing capabilities.

# CORE PHILOSOPHY
```
TIMTOWTDI — There Is More Than One Way To Do It
GRAMMARS FIRST — parsing is a first-class language feature
GRADUAL TYPING — optional but powerful type constraints
LAZY BY DEFAULT — infinite lists are idiomatic
CONCURRENCY BUILT IN — async/await, channels, and parallel maps
```

# SYNTAX ESSENTIALS

## Variables — Sigils Have Meaning
```raku
# $ — scalar (single value)
my $name = "Joel";
my Int $age = 22;

# @ — array (ordered list)
my @nums = (1, 2, 3, 4, 5);

# % — hash (key-value)
my %config = host => "localhost", port => 8080;

# & — code (callable)
my &greet = sub ($name) { "Hello, $name!" };

# Constants
my constant PI = 3.14159;
my constant MAX = 100;

say "$name is $age years old";   # string interpolation
```

## Subroutines and Signatures
```raku
# Rich signature system
sub greet(Str $name, Int $age = 0) returns Str {
    "Hello $name" ~ ($age ?? ", age $age" !! "")
}

# Named parameters
sub connect(:$host = "localhost", :$port = 8080, :$secure = False) {
    ($secure ?? "https" !! "http") ~ "://$host:$port"
}

connect(port => 443, secure => True);   # named call

# Slurpy params
sub sum(*@nums) { [+] @nums }   # [+] reduces with addition

# Multiple dispatch
multi sub describe(Int $n)  { "An integer: $n" }
multi sub describe(Str $s)  { "A string: $s"   }
multi sub describe(Any $x)  { "Something else" }

say describe(42);       # An integer: 42
say describe("hi");     # A string: hi
```

## Classes and Roles
```raku
class Animal {
    has Str $.name  is required;
    has Int $.age   = 0;

    method speak() returns Str { "..." }
    method describe() {
        say "$.name is $.age years old"
    }
}

class Dog is Animal {
    has Str $.breed;

    method speak() { "Woof!" }
    method full-desc() {
        "$.name ($.breed), age $.age"
    }
}

# Roles — composable behavior (like traits/mixins)
role Serializable {
    method to-json() {
        my %data = self.^attributes.map: { .name.substr(2) => .get_value(self) };
        to-json(%data);
    }
}

class Config does Serializable {
    has Str $.host = "localhost";
    has Int $.port = 8080;
}

my $cfg = Config.new;
say $cfg.to-json;
```

# GRAMMARS — THE KILLER FEATURE
```raku
# Define a grammar — a PEG parser as a first-class type
grammar CSVParser {
    rule  TOP   { <row>+ }
    rule  row   { <cell>+ % ',' }
    token cell  { <-[,\n]>* }
}

# Action class — transform parse tree to data
class CSVActions {
    method TOP($/) {
        make $<row>».made
    }
    method row($/) {
        make $<cell>».made
    }
    method cell($/) {
        make ~$/
    }
}

my $csv = "a,b,c\n1,2,3\n";
my $match = CSVParser.parse($csv, actions => CSVActions.new);
say $match.made;   # [["a","b","c"],["1","2","3"]]

# Grammars work for full programming language parsers too
grammar JSON {
    rule  TOP    { <value> }
    rule  value  { <string> | <number> | <object> | <array> | <bool> | <null> }
    token string { '"' <-["]>* '"' }
    token number { '-'? \d+ ['.' \d+]? }
    # ... and so on
}
```

# JUNCTIONS — SET LOGIC IN EXPRESSIONS
```raku
my $x = 5;

# any — true if any operand makes expression true
if $x == any(1, 3, 5, 7, 9) { say "odd" }

# all — true if all operands satisfy
my @nums = (2, 4, 6, 8);
if all(@nums) %% 2 { say "all even" }

# none
if $x != none(0, -1) { say "not zero or negative" }

# one — exactly one
if $x == one(3, 5) { say "exactly one match" }

# Junctions in grep
my @items = (1..10).grep: * == any(2, 4, 6);   # [2, 4, 6]
```

# LAZY LISTS AND SEQUENCES
```raku
# Infinite sequences are lazy — evaluated on demand
my @naturals = 1, 2, 3 ... *;            # 1,2,3,4,...
my @evens    = 0, 2, 4 ... *;
my @fibs     = 1, 1, * + * ... *;        # Fibonacci!

say @fibs[0..9];    # first 10 Fibonacci numbers

# Take from lazy sequence
my @first-100-primes = (2 .. *).grep(*.is-prime)[^100];

# gather/take — custom lazy generator
my @squares = gather {
    my $n = 1;
    loop { take $n * $n; $n++ }
};
say @squares[^10];   # [1,4,9,16,25,36,49,64,81,100]
```

# ASYNC AND CONCURRENCY
```raku
use v6;

# Promises
my $p = Promise.in(2).then({ say "2 seconds later" });
await $p;

# start block — concurrent task
my $result = start { expensive-computation() };
say await $result;

# Parallel map
my @results = @urls.race.map({ fetch($_) });

# Channels
my $chan = Channel.new;

start {
    for 1..5 -> $n {
        $chan.send($n);
        sleep 0.1;
    }
    $chan.close;
}

react {
    whenever $chan -> $val { say "Got: $val" }
    LAST { say "Channel closed" }
}
```

# TEXT PROCESSING
```raku
# Powerful regex with named captures
my $date = "2026-04-14";
if $date ~~ / (\d{4}) '-' (\d{2}) '-' (\d{2}) / {
    say "Year: $0, Month: $1, Day: $2";
}

# Named captures
if $date ~~ / $<year>=\d{4} '-' $<month>=\d{2} '-' $<day>=\d{2} / {
    say $<year>;
}

# Substitution
my $text = "Hello world";
$text ~~ s/world/Raku/;

# Global substitution
$text ~~ s:g/o/0/;

# Split with regex
my @parts = "a1b2c3".split(/\d/);   # ["a","b","c",""]
```

# ZEF (PACKAGE MANAGER)
```bash
zef install HTTP::UserAgent    # install module
zef upgrade                    # upgrade all
zef search json                # search packages
raku -e 'use HTTP::UserAgent'  # test import
```

# QUICK WINS CHECKLIST
```
[ ] Use multi sub/method for type-based dispatch instead of if/elsif chains
[ ] Prefix params with : for named arguments in signatures
[ ] Use ... (sequence operator) for arithmetic/geometric/custom sequences
[ ] Use gather/take for lazy custom generators
[ ] Write grammars instead of regex soup for structured text parsing
[ ] Use junctions (any/all/none) to replace verbose condition chains
[ ] Use .race or .hyper for parallel collection operations
[ ] Use CATCH block inside a sub for structured error handling
[ ] Use .raku method for object introspection/debugging
[ ] Use .grep(*.method) shorthand over verbose closures
```
