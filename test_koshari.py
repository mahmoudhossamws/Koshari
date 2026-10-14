"""Run with: python -m unittest -v

Checks the written A1 grammar, scope behavior, and the A2 submission example.
"""

from contextlib import redirect_stderr, redirect_stdout
import io
from pathlib import Path
import unittest

from koshari import Env, main, parse, run, tokenize


ROOT = Path(__file__).resolve().parent


def output_of(source, scope="static", stage="a2"):
    output = io.StringIO()
    with redirect_stdout(output):
        run(source, scope=scope, stage=stage)
    return output.getvalue()


class A1ParserTests(unittest.TestCase):
    def test_three_submitted_samples_are_accepted(self):
        for number in range(1, 4):
            with self.subTest(sample=number):
                parse((ROOT / f"examples/a1_sample{number}.ksh").read_text(), stage="a1")

    def test_two_submitted_rejections(self):
        for number in (1, 2):
            with self.subTest(sample=number):
                source = (ROOT / f"examples/a1_rejected{number}.ksh").read_text()
                with self.assertRaises(SyntaxError):
                    parse(source, stage="a1")

    def test_additional_invalid_syntax(self):
        sources = [
            "let x = 1", "let 12 = 1;", "let print = 1;", "let let = 1;",
            "print let;", "let x = -1;", "print 3 * -2;", "print 1.5;",
            "let _x = 1;", "let x = 1 < 2 == 1;", "print ();", "{ print 1;",
            "print (1 + 2;", "}", "{ } ;", "print 1; garbage", "let x = 1,2;",
            "function show() {}", "show();",
        ]
        for source in sources:
            with self.subTest(source=source), self.assertRaises(SyntaxError):
                parse(source, stage="a1")

    def test_empty_program_and_nested_empty_blocks(self):
        self.assertEqual(output_of("", stage="a1"), "")
        self.assertEqual(output_of("{ { } }", stage="a1"), "")

    def test_keyword_prefixes_and_identifier_rules(self):
        self.assertEqual(
            output_of("let letter_2 = 3; let printer = 4; print letter_2 + printer;", stage="a1"),
            "7\n",
        )

    def test_function_is_a_valid_identifier_only_in_a1(self):
        self.assertEqual(output_of("let function = 3; print function;", stage="a1"), "3\n")
        with self.assertRaises(SyntaxError):
            parse("let function = 3;")

    def test_longest_operator_matches(self):
        operators = "<= >= == != += -= *= /= < > = ! + - * /"
        self.assertEqual([value for _, value in tokenize(operators)], operators.split())

    def test_comments_and_windows_newlines(self):
        source = "# comment\r\nlet x = 2; # another\r\n\tprint x;\r\n"
        self.assertEqual(output_of(source, stage="a1"), "2\n")

    def test_precedence_and_left_associativity(self):
        source = "print 2 + 3 * 4; print (2 + 3) * 4; print 1 - 2 - 3; print 8 / 4 / 2;"
        self.assertEqual(output_of(source, stage="a1"), "14\n20\n-4\n1\n")

    def test_comparison_precedence_and_parentheses(self):
        source = "print 2 + 3 * 4 == 14; print (1 < 2) < 3; print 3 < (1 < 2);"
        self.assertEqual(output_of(source, stage="a1"), "1\n1\n0\n")

    def test_negation_binds_to_one_atom(self):
        source = "print !0; print !5; print !!5; print !0 * 2; print !(0 * 2);"
        self.assertEqual(output_of(source, stage="a1"), "1\n0\n1\n2\n1\n")

    def test_all_a1_operators_execute(self):
        source = (ROOT / "examples/a1_features.ksh").read_text()
        self.assertEqual(output_of(source, stage="a1"), "6\n1\n0\n1\n1\n1\n1\n0\n1\n")

    def test_syntax_acceptance_does_not_require_bound_variables(self):
        source = (ROOT / "examples/a1_sample3.ksh").read_text()
        parse(source, stage="a1")
        with self.assertRaisesRegex(NameError, "unbound: a"):
            output_of(source, stage="a1")


class A2ScopeTests(unittest.TestCase):
    def test_real_chain_can_lookup_and_assign_across_multiple_frames(self):
        outer = Env()
        outer.define("x", 10.0)
        middle = Env(outer)
        inner = Env(middle)
        self.assertIs(inner.parent, middle)
        self.assertIs(middle.parent, outer)
        self.assertEqual(inner.get("x"), 10.0)
        inner.assign("x", 11.0)
        self.assertEqual(outer.get("x"), 11.0)
        middle.define("x", 20.0)
        self.assertEqual(inner.get("x"), 20.0)
        self.assertEqual(outer.get("x"), 11.0)

    def test_nested_blocks_shadow_and_restore_outer_binding(self):
        source = (ROOT / "examples/a2_blocks.ksh").read_text()
        for scope in ("static", "dynamic"):
            with self.subTest(scope=scope):
                self.assertEqual(output_of(source, scope), "30\n20\n10\n11\n")

    def test_block_local_does_not_leak(self):
        with self.assertRaisesRegex(NameError, "unbound: hidden"):
            output_of("{ let hidden = 1; } print hidden;")

    def test_assignment_updates_nearest_existing_variable(self):
        source = "let x = 1; { let x = 2; { x += 3; } print x; } print x;"
        self.assertEqual(output_of(source), "5\n1\n")

    def test_unbound_assignment_is_rejected(self):
        for operator in ("=", "+=", "-=", "*=", "/="):
            with self.subTest(operator=operator), self.assertRaisesRegex(NameError, "unbound: x"):
                output_of(f"x {operator} 1;")

    def test_duplicate_local_declaration_is_rejected(self):
        with self.assertRaisesRegex(NameError, "already declared in this scope: x"):
            output_of("let x = 1; let x = 2;")

    def test_initializer_can_read_outer_binding_before_shadowing(self):
        self.assertEqual(output_of("let x = 10; { let x = x + 1; print x; } print x;"), "11\n10\n")

    def test_same_program_has_both_required_outputs(self):
        source = (ROOT / "examples/a2_scope.ksh").read_text()
        for scope in ("static", "dynamic"):
            with self.subTest(scope=scope):
                expected = (ROOT / f"examples/a2_scope.{scope}.out").read_text()
                self.assertEqual(output_of(source, scope), expected)

    def test_static_is_the_default(self):
        source = (ROOT / "examples/a2_scope.ksh").read_text()
        self.assertEqual(output_of(source), "10\n")

    def test_function_local_binding_has_priority_in_both_modes(self):
        source = "let x = 10; function show() { let x = 30; print x; } { let x = 20; show(); }"
        for scope in ("static", "dynamic"):
            with self.subTest(scope=scope):
                self.assertEqual(output_of(source, scope), "30\n")

    def test_static_captures_nested_definition_scope_not_just_global(self):
        source = "let x = 10; { let x = 30; function show() { print x; } { let x = 20; show(); } }"
        self.assertEqual(output_of(source, "static"), "30\n")
        self.assertEqual(output_of(source, "dynamic"), "20\n")

    def test_dynamic_searches_multiple_active_callers(self):
        source = "let x = 10; function show() { print x; } function middle() { show(); } function caller() { let x = 20; middle(); } caller();"
        self.assertEqual(output_of(source, "static"), "10\n")
        self.assertEqual(output_of(source, "dynamic"), "20\n")

    def test_only_dynamic_can_find_a_caller_only_variable(self):
        source = "function show() { print callerLocal; } function caller() { let callerLocal = 7; show(); } caller();"
        with self.assertRaisesRegex(NameError, "unbound: callerLocal"):
            output_of(source, "static")
        self.assertEqual(output_of(source, "dynamic"), "7\n")

    def test_function_assignment_follows_selected_scope_chain(self):
        source = (ROOT / "examples/a2_assignment.ksh").read_text()
        self.assertEqual(output_of(source, "static"), "20\n11\n")
        self.assertEqual(output_of(source, "dynamic"), "21\n10\n")

    def test_definition_environment_is_a_live_frame(self):
        source = "let x = 1; function show() { print x; } x = 2; show();"
        self.assertEqual(output_of(source), "2\n")

    def test_each_invocation_has_fresh_locals(self):
        source = "function show() { let local = 1; local += 1; print local; } show(); show();"
        self.assertEqual(output_of(source), "2\n2\n")

    def test_empty_function(self):
        self.assertEqual(output_of("function empty() {} empty();"), "")

    def test_functions_are_scoped_and_can_shadow(self):
        source = "function show() { print 1; } { function show() { print 2; } show(); } show();"
        self.assertEqual(output_of(source), "2\n1\n")
        with self.assertRaisesRegex(NameError, "unbound function: hidden"):
            output_of("{ function hidden() {} } hidden();")

    def test_variable_and_function_namespaces_are_separate(self):
        self.assertEqual(output_of("let show = 4; function show() { print show; } show();"), "4\n")

    def test_unknown_and_duplicate_functions_are_rejected(self):
        with self.assertRaisesRegex(NameError, "unbound function: missing"):
            output_of("missing();")
        with self.assertRaisesRegex(NameError, "function already declared"):
            output_of("function show() {} function show() {}")

    def test_minimal_function_syntax_rejects_later_stage_features(self):
        for source in ("function show(x) {}", "function show() {} show(1);", "let x = show();", "function print() {}", "function show() { return 1; }"):
            with self.subTest(source=source), self.assertRaises(SyntaxError):
                parse(source)

    def test_program_environment_keeps_globals_only(self):
        with redirect_stdout(io.StringIO()):
            env = run("let global = 1; { let local = 2; } function show() {}")
        self.assertEqual(env.vars, {"global": 1.0})
        self.assertIn("show", env.functions)


class DriverTests(unittest.TestCase):
    def test_original_starter_demo(self):
        self.assertEqual(output_of((ROOT / "demo.ksh").read_text()), "14\n")

    def test_cli_default_and_scope_flags(self):
        source = str(ROOT / "examples/a2_scope.ksh")
        for arguments, expected in (([], "7\n"), ([source], "10\n"), (["--scope", "dynamic", source], "20\n")):
            with self.subTest(arguments=arguments), redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main(arguments), 0)
                self.assertEqual(output.getvalue(), expected)

    def test_cli_parse_only_does_not_execute_unbound_sample(self):
        with redirect_stdout(io.StringIO()) as output:
            result = main(["--stage", "a1", "--parse-only", str(ROOT / "examples/a1_sample3.ksh")])
        self.assertEqual(result, 0)
        self.assertEqual(output.getvalue(), "Syntax OK\n")

    def test_cli_syntax_failure_has_nonzero_status_and_message(self):
        with redirect_stderr(io.StringIO()) as error:
            result = main(["--stage", "a1", "--parse-only", str(ROOT / "examples/a1_rejected1.ksh")])
        self.assertEqual(result, 1)
        self.assertIn("SyntaxError: comparisons cannot chain", error.getvalue())

    def test_unknown_scope_or_stage_is_rejected(self):
        with self.assertRaises(ValueError):
            run("", scope="other")
        with self.assertRaises(ValueError):
            parse("", stage="other")


if __name__ == "__main__":
    unittest.main()
