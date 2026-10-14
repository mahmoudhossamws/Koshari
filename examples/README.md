# Example programs

AI assistance was used to prepare the additional examples in this folder.
The original A1 samples and rejected strings were copied from `Part A1.tex`.

| Files | Source and purpose |
| --- | --- |
| `a1_sample1.ksh`, `a1_sample2.ksh`, `a1_sample3.ksh` | Copied from the existing A1 report to check acceptance by the parser. |
| `a1_rejected1.ksh`, `a1_rejected2.ksh` | Copied from the existing A1 report to check rejection by the parser. |
| `a1_features.ksh` | AI-generated example covering assignments, comparisons, and negation. |
| `a2_blocks.ksh` | AI-generated example covering nested blocks, shadowing, and assignment to an outer variable. |
| `a2_scope.ksh` | AI-generated demonstration of the difference between static and dynamic scoping. |
| `a2_assignment.ksh` | AI-generated example showing how the scoping rule affects assignment targets. |
| `a2_scope.static.out`, `a2_scope.dynamic.out` | Expected outputs checked against actual interpreter runs: `10` for static scoping and `20` for dynamic scoping. |

A2 requires one program whose output differs between static and dynamic
scoping. `a2_scope.ksh` supplies that demonstration. The other additional
examples are optional supporting checks.

The examples were checked with the interpreter and the automated test suite.
The third A1 sample is intentionally a syntax-only example: its variables
are undeclared, so parsing succeeds but execution raises a binding error.
