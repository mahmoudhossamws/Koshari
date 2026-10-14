Koshari - CSCE 3104
Assignments 1 and 2

Requires Python 3.7 or later. No extra packages are needed.
Run these commands from the project folder.

Basic examples:
    python koshari.py                                      -> 7
    python koshari.py demo.ksh                             -> 14

A2 scoping example:
    python koshari.py --scope static examples/a2_scope.ksh  -> 10
    python koshari.py --scope dynamic examples/a2_scope.ksh -> 20

Static scoping is the default. The --scope option changes the rule
used to find variables outside a function's local frame.

A1 syntax checks:
    python koshari.py --stage a1 --parse-only examples/a1_sample1.ksh
    python koshari.py --stage a1 --parse-only examples/a1_sample2.ksh
    python koshari.py --stage a1 --parse-only examples/a1_sample3.ksh

All three print "Syntax OK". Sample 3 uses undeclared variables,
so it is a syntax example rather than a complete executable program.
The two a1_rejected examples produce syntax errors.

Other examples:
    examples/a1_features.ksh   - assignments, comparisons, and negation
    examples/a2_blocks.ksh     - block scopes and shadowing
    examples/a2_assignment.ksh - assignment under both scoping rules

Tests:
    python -m unittest -v

Functions currently have no parameters or returned values.
Type checking and the remaining procedure features belong to later
assignments.
