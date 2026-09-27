KOSHARI STARTER KIT - CSCE 3104, Fall 2026
==========================================
Give koshari.py and demo.ksh to students at S4, with A1.

IT RUNS AS GIVEN - verified:
    $ python3 koshari.py            ->  7
    $ python3 koshari.py demo.ksh   ->  14

It is deliberately incomplete. Every decision point is marked:
    # TODO(A1)  parser accepts two statement forms. Extend it.
    # TODO(A2)  Env is a flat dict - cannot express scope at all.
    # TODO(A3)  no types. Every value is a Python float.
    # TODO(A4)  is operand order guaranteed? what does 1/0 do?
    # TODO(A5)  no procedures.
    # TODO(A6)  no closures; nothing runs in two directions.

IT FAILS WHERE THE ASSIGNMENTS ASK - verified:
    unbound name  ->  NameError: unbound: nope
    1/0           ->  ZeroDivisionError: float division by zero
A4 asks students to REPLACE both with a designed mechanism. Leaving
the Python exception in place is a legitimate answer ONLY if
defended - it means "my language inherits its host's failure model",
which has a real cost worth naming.

STUDENTS MAY REPLACE IT ENTIRELY, in any language. The one
prohibition is a PARSER GENERATOR for A1 - writing the parser by
hand is the point of A1.

WHY PYTHON: everyone in the room can read it, so the starter kit
does not become a second subject. It is not an endorsement of
Python as an implementation language, and students who rewrite it
in C, Haskell or Java should be encouraged.
