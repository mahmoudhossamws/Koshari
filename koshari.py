#!/usr/bin/env python3
"""
KOSHARI STARTER KIT  -  CSCE 3104, Fall 2026
============================================
A deliberately INCOMPLETE interpreter. You will extend it across
A1-A6. Everything marked  # TODO(An)  is yours to design.

It runs as given. Try:   python3 koshari.py demo.ksh
"""
import sys, re

# ---------------------------------------------------------------- 1. TOKENS
TOKEN_SPEC = [
    ("NUMBER",  r"\d+(\.\d+)?"),
    ("ID",      r"[A-Za-z_][A-Za-z_0-9]*"),
    ("OP",      r"[+\-*/<>=!]=?|[();{},]"),
    ("SKIP",    r"[ \t\n]+"),
    ("COMMENT", r"#[^\n]*"),
]
MASTER = re.compile("|".join(f"(?P<{n}>{p})" for n, p in TOKEN_SPEC))

def tokenize(src):
    pos, out = 0, []
    while pos < len(src):
        m = MASTER.match(src, pos)
        if not m:
            raise SyntaxError(f"stuck at {src[pos:pos+12]!r}")
        kind = m.lastgroup
        if kind not in ("SKIP", "COMMENT"):
            out.append((kind, m.group()))
        pos = m.end()
    return out

# ---------------------------------------------------------------- 2. PARSER
# TODO(A1): this parser accepts ONLY  <program> ::= <stmt>*
#           and  <stmt> ::= let ID = <expr> ; | print <expr> ;
#           Extend it to match the grammar you wrote in A1.
class Parser:
    def __init__(self, toks): self.t, self.i = toks, 0
    def peek(self):  return self.t[self.i] if self.i < len(self.t) else (None, None)
    def eat(self, val=None):
        k, v = self.peek()
        if val is not None and v != val:
            raise SyntaxError(f"expected {val!r}, found {v!r}")
        self.i += 1
        return v
    def program(self):
        stmts = []
        while self.i < len(self.t):
            stmts.append(self.stmt())
        return ("block", stmts)
    def stmt(self):
        k, v = self.peek()
        if v == "let":
            self.eat("let"); name = self.eat(); self.eat("=")
            e = self.expr(); self.eat(";")
            return ("let", name, e)
        if v == "print":
            self.eat("print"); e = self.expr(); self.eat(";")
            return ("print", e)
        raise SyntaxError(f"no rule for {v!r}")
    def expr(self):                       # left-associative + and -
        node = self.term()
        while self.peek()[1] in ("+", "-"):
            op = self.eat(); node = ("bin", op, node, self.term())
        return node
    def term(self):
        node = self.atom()
        while self.peek()[1] in ("*", "/"):
            op = self.eat(); node = ("bin", op, node, self.atom())
        return node
    def atom(self):
        k, v = self.peek()
        if k == "NUMBER": self.eat(); return ("num", float(v))
        if k == "ID":     self.eat(); return ("var", v)
        if v == "(":      self.eat("("); e = self.expr(); self.eat(")"); return e
        raise SyntaxError(f"bad atom {v!r}")

# ---------------------------------------------------------------- 3. ENVIRONMENT
# TODO(A2): this is a SINGLE FLAT DICT. It has no nesting, so it cannot
#           express scope at all. Replace it with a chain of frames, and
#           make the lookup rule (static or dynamic) YOUR design decision.
class Env:
    def __init__(self, parent=None):
        self.vars, self.parent = {}, parent
    def get(self, name):
        if name in self.vars: return self.vars[name]
        if self.parent:       return self.parent.get(name)
        raise NameError(f"unbound: {name}")
    def set(self, name, val):
        self.vars[name] = val

# ---------------------------------------------------------------- 4. EVALUATOR
# TODO(A3): there are no TYPES here. Every value is a Python float.
#           Decide what types your language has and when they are checked.
# TODO(A4): decide the ORDER in which you evaluate operands, whether your
#           boolean operators short-circuit, and how failure is signalled.
# TODO(A5): add procedures, and choose a parameter-passing mode.
# TODO(A6): add a closure, or a rule that runs in more than one direction.
def evaluate(node, env):
    kind = node[0]
    if kind == "num":   return node[1]
    if kind == "var":   return env.get(node[1])
    if kind == "block":
        for s in node[1]: evaluate(s, env)
        return None
    if kind == "let":
        env.set(node[1], evaluate(node[2], env)); return None
    if kind == "print":
        v = evaluate(node[1], env)
        print(int(v) if v == int(v) else v)
        return None
    if kind == "bin":
        _, op, a, b = node
        x = evaluate(a, env)          # <- A4: is this order guaranteed?
        y = evaluate(b, env)
        if op == "+": return x + y
        if op == "-": return x - y
        if op == "*": return x * y
        if op == "/": return x / y    # <- A4: what happens when y is 0?
        raise SyntaxError(f"bad operator {op}")
    raise SyntaxError(f"cannot evaluate {kind}")

# ---------------------------------------------------------------- 5. DRIVER
def run(src):
    evaluate(Parser(tokenize(src)).program(), Env())

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run(open(sys.argv[1]).read())
    else:
        run("let x = 2; let y = x * 3 + 1; print y;")
