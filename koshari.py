#!/usr/bin/env python3
"""Koshari: the hand-written A1 parser and the A2 scope interpreter.

    python koshari.py demo.ksh
    python koshari.py --scope static examples/a2_scope.ksh
    python koshari.py --scope dynamic examples/a2_scope.ksh
    python koshari.py --stage a1 --parse-only examples/a1_sample3.ksh

A2 adds only `function name() { ... }` and `name();` to the A1 grammar.
"""

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import sys


# ---------------------------------------------------------------- 1. TOKENS
# A1's NUMBER and ID rules are deliberately narrower than the starter's.
TOKEN_SPEC = [
    ("NUMBER", r"[0-9]+"),
    ("ID", r"[A-Za-z][A-Za-z0-9_]*"),
    ("OP", r"==|!=|<=|>=|\+=|-=|\*=|/=|[+\-*/<>=!();{}]"),
    ("SKIP", r"[ \t\r\n]+"),
    ("COMMENT", r"#[^\r\n]*"),
]
MASTER = re.compile("|".join(f"(?P<{name}>{pattern})" for name, pattern in TOKEN_SPEC))


def tokenize(src, stage="a2"):
    if stage not in ("a1", "a2"):
        raise ValueError("stage must be 'a1' or 'a2'")
    reserved = {"let", "print"}
    if stage == "a2":
        reserved.add("function")
    pos, tokens = 0, []
    while pos < len(src):
        match = MASTER.match(src, pos)
        if not match:
            line = src.count("\n", 0, pos) + 1
            raise SyntaxError(f"unexpected character {src[pos]!r} on line {line}")
        kind, value = match.lastgroup, match.group()
        if kind == "ID" and value in reserved:
            kind = "KEYWORD"
        if kind not in ("SKIP", "COMMENT"):
            tokens.append((kind, value))
        pos = match.end()
    return tokens


# ---------------------------------------------------------------- 2. PARSER
# A1: recursive descent, with loops replacing the grammar's left recursion.
# A2: function definitions and statement calls, enabled only in stage a2.
class Parser:
    def __init__(self, toks, stage="a2"):
        if stage not in ("a1", "a2"):
            raise ValueError("stage must be 'a1' or 'a2'")
        self.t, self.i, self.stage = toks, 0, stage

    def peek(self):
        return self.t[self.i] if self.i < len(self.t) else (None, None)

    def eat(self, val=None):
        kind, value = self.peek()
        if kind is None:
            expected = repr(val) if val is not None else "a token"
            raise SyntaxError(f"expected {expected}, found end of input")
        if val is not None and value != val:
            raise SyntaxError(f"expected {val!r}, found {value!r}")
        self.i += 1
        return value

    def identifier(self):
        kind, value = self.peek()
        reserved = {"let", "print"}
        if self.stage == "a2":
            reserved.add("function")
        if kind != "ID" or value in reserved:
            raise SyntaxError(f"expected an identifier, found {value!r}")
        return self.eat()

    def program(self):
        statements = []
        while self.peek()[0] is not None:
            statements.append(self.stmt())
        # The program uses the global frame; only explicit braces create a block.
        return ("program", statements)

    def block(self):
        self.eat("{")
        statements = []
        while self.peek()[0] is not None and self.peek()[1] != "}":
            statements.append(self.stmt())
        self.eat("}")
        return ("block", statements)

    def stmt(self):
        kind, value = self.peek()
        if value == "let":
            self.eat("let")
            name = self.identifier()
            self.eat("=")
            expression = self.expr()
            self.eat(";")
            return ("let", name, expression)
        if value == "print":
            self.eat("print")
            expression = self.expr()
            self.eat(";")
            return ("print", expression)
        if value == "{":
            return self.block()
        if self.stage == "a2" and value == "function":
            self.eat("function")
            name = self.identifier()
            self.eat("(")
            self.eat(")")
            return ("function", name, self.block())
        if kind == "ID":
            name = self.identifier()
            if self.stage == "a2" and self.peek()[1] == "(":
                self.eat("(")
                self.eat(")")
                self.eat(";")
                return ("call", name)
            operator = self.peek()[1]
            if operator not in ("=", "+=", "-=", "*=", "/="):
                raise SyntaxError(f"expected an assignment operator, found {operator!r}")
            self.eat()
            expression = self.expr()
            self.eat(";")
            return ("assign", name, operator, expression)
        raise SyntaxError(f"no statement rule for {value!r}")

    def expr(self):
        node = self.math_expr()
        if self.peek()[1] in ("==", "!=", "<", "<=", ">", ">="):
            operator = self.eat()
            node = ("bin", operator, node, self.math_expr())
            if self.peek()[1] in ("==", "!=", "<", "<=", ">", ">="):
                raise SyntaxError("comparisons cannot chain; use parentheses")
        return node

    def math_expr(self):
        node = self.term()
        while self.peek()[1] in ("+", "-"):
            operator = self.eat()
            node = ("bin", operator, node, self.term())
        return node

    def term(self):
        node = self.atom()
        while self.peek()[1] in ("*", "/"):
            operator = self.eat()
            node = ("bin", operator, node, self.atom())
        return node

    def atom(self):
        kind, value = self.peek()
        if kind == "NUMBER":
            self.eat()
            return ("num", float(value))
        if kind == "ID":
            return ("var", self.identifier())
        if value == "(":
            self.eat("(")
            node = self.expr()
            self.eat(")")
            return node
        if value == "!":
            self.eat("!")
            return ("not", self.atom())
        raise SyntaxError(f"expected an atom, found {value!r}")


def parse(src, stage="a2"):
    return Parser(tokenize(src, stage), stage).program()


# ---------------------------------------------------------------- 3. ENVIRONMENT
# A2: one Env per global scope, explicit block, or function invocation.
class Env:
    def __init__(self, parent=None):
        self.vars = {}
        self.functions = {}  # Procedures have their own namespace, not values.
        self.parent = parent

    def variable_frame(self, name):
        frame = self
        while frame is not None:
            if name in frame.vars:
                return frame
            frame = frame.parent
        raise NameError(f"unbound: {name}")

    def get(self, name):
        return self.variable_frame(name).vars[name]

    def define(self, name, value):
        if name in self.vars:
            raise NameError(f"already declared in this scope: {name}")
        self.vars[name] = value

    def assign(self, name, value):
        self.variable_frame(name).vars[name] = value

    def define_function(self, name, function):
        if name in self.functions:
            raise NameError(f"function already declared in this scope: {name}")
        self.functions[name] = function

    def get_function(self, name):
        frame = self
        while frame is not None:
            if name in frame.functions:
                return frame.functions[name]
            frame = frame.parent
        raise NameError(f"unbound function: {name}")


@dataclass
class Function:
    body: tuple
    definition_env: Env


# ---------------------------------------------------------------- 4. EVALUATOR
# TODO(A3): design a type checker. Numbers are still Python floats. Comparisons
# and ! temporarily produce numeric 0/1; zero is false, nonzero is true.
# TODO(A4): design control flow and failure. Evaluation is currently left to
# right, and execution errors use Python exceptions, as in the starter.
# TODO(A5): add parameters, returned values, and a parameter-passing policy.
# TODO(A6): add first-class closures or another paradigm's feature.
def binary(operator, left, right):
    if operator == "+":
        return left + right
    if operator == "-":
        return left - right
    if operator == "*":
        return left * right
    if operator == "/":
        return left / right
    if operator == "==":
        return float(left == right)
    if operator == "!=":
        return float(left != right)
    if operator == "<":
        return float(left < right)
    if operator == "<=":
        return float(left <= right)
    if operator == ">":
        return float(left > right)
    if operator == ">=":
        return float(left >= right)
    raise SyntaxError(f"bad operator {operator}")


def execute_statements(statements, env, scope):
    for statement in statements:
        evaluate(statement, env, scope)


def evaluate(node, env, scope="static"):
    kind = node[0]
    if kind == "num":
        return node[1]
    if kind == "var":
        return env.get(node[1])
    if kind == "program":
        execute_statements(node[1], env, scope)
    elif kind == "block":
        execute_statements(node[1], Env(parent=env), scope)
    elif kind == "let":
        env.define(node[1], evaluate(node[2], env, scope))
    elif kind == "assign":
        _, name, operator, expression = node
        # Resolve first: assigning an undeclared variable never creates one.
        frame = env.variable_frame(name)
        old_value = frame.vars[name]
        value = evaluate(expression, env, scope)
        frame.vars[name] = value if operator == "=" else binary(operator[0], old_value, value)
    elif kind == "print":
        value = evaluate(node[1], env, scope)
        print(int(value) if value == int(value) else value)
    elif kind == "bin":
        _, operator, left, right = node
        return binary(operator, evaluate(left, env, scope), evaluate(right, env, scope))
    elif kind == "not":
        return float(evaluate(node[1], env, scope) == 0)
    elif kind == "function":
        env.define_function(node[1], Function(node[2], env))
    elif kind == "call":
        function = env.get_function(node[1])
        # This parent selection is the core distinction required by A2.
        parent = function.definition_env if scope == "static" else env
        call_env = Env(parent=parent)
        # The body's braces use the invocation frame, rather than an extra one.
        execute_statements(function.body[1], call_env, scope)
    else:
        raise SyntaxError(f"cannot evaluate {kind}")
    return None


# ---------------------------------------------------------------- 5. DRIVER
def run(src, scope="static", stage="a2"):
    if scope not in ("static", "dynamic"):
        raise ValueError("scope must be 'static' or 'dynamic'")
    env = Env()
    evaluate(parse(src, stage), env, scope)
    return env


def main(argv=None):
    arguments = argparse.ArgumentParser(description="Run the A1/A2 Koshari interpreter.")
    arguments.add_argument("file", nargs="?", type=Path, help="Koshari source file")
    arguments.add_argument("--scope", choices=("static", "dynamic"), default="static")
    arguments.add_argument("--stage", choices=("a1", "a2"), default="a2")
    arguments.add_argument("--parse-only", action="store_true", help="check syntax without execution")
    args = arguments.parse_args(argv)
    try:
        src = args.file.read_text(encoding="utf-8") if args.file else (
            "let x = 2; let y = x * 3 + 1; print y;"
        )
        if args.parse_only:
            parse(src, args.stage)
            print("Syntax OK")
        else:
            run(src, args.scope, args.stage)
    except (OSError, SyntaxError, NameError, ZeroDivisionError) as error:
        print(f"{type(error).__name__}: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
