# -*- coding: utf-8 -*-
"""
Suite de tests pour QuestLang Compiler v2.
Tests couvrant: lexer, parser, semantique, optimisation, integration.

Execution:
    python tests/test_compiler.py
    python -m pytest tests/test_compiler.py -v
"""

import sys
import os
import json
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from lexer import Lexer, TokenType
from parser import Parser
from ast_nodes import *
from semantic import SemanticAnalyzer
from codegen import CodeGenerator
from optimizer import Optimizer
from errors import LexicalError, SyntaxError


class TestLexer(unittest.TestCase):
    def test_basic_tokens(self):
        source = 'quest foo { title: "Hello"; }'
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        types = [t.type for t in tokens]
        self.assertIn(TokenType.QUEST, types)
        self.assertIn(TokenType.IDENTIFIER, types)
        self.assertIn(TokenType.LBRACE, types)
        self.assertIn(TokenType.TITLE, types)
        self.assertIn(TokenType.STRING, types)
        self.assertIn(TokenType.RBRACE, types)
        self.assertIn(TokenType.EOF, types)

    def test_numbers(self):
        source = "42 3.14 0 1000"
        lexer = Lexer(source)
        tokens = [t for t in lexer.tokenize() if t.type == TokenType.NUMBER]
        self.assertEqual(len(tokens), 4)
        self.assertEqual(tokens[0].value, 42)
        self.assertEqual(tokens[1].value, 3.14)
        self.assertEqual(tokens[2].value, 0)
        self.assertEqual(tokens[3].value, 1000)

    def test_operators(self):
        source = "== != >= <= += -= ->"
        lexer = Lexer(source)
        tokens = [t for t in lexer.tokenize() if t.type != TokenType.EOF]
        ops = [t.type for t in tokens]
        self.assertIn(TokenType.EQ, ops)
        self.assertIn(TokenType.NEQ, ops)
        self.assertIn(TokenType.GTE, ops)
        self.assertIn(TokenType.LTE, ops)
        self.assertIn(TokenType.PLUS_ASSIGN, ops)
        self.assertIn(TokenType.MINUS_ASSIGN, ops)
        self.assertIn(TokenType.ARROW, ops)

    def test_comments(self):
        source = """
        // Commentaire sur une ligne
        quest test { /* commentaire
        multi-ligne */ title: "T"; }
        """
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        types = [t.type for t in tokens]
        self.assertIn(TokenType.QUEST, types)
        self.assertIn(TokenType.IDENTIFIER, types)
        self.assertIn(TokenType.TITLE, types)

    def test_string_escapes(self):
        source = '"Ligne 1\\nLigne 2\\tTab"'
        lexer = Lexer(source)
        tokens = [t for t in lexer.tokenize() if t.type == TokenType.STRING]
        self.assertEqual(len(tokens), 1)
        self.assertIn("\n", tokens[0].value)
        self.assertIn("\t", tokens[0].value)

    def test_line_tracking(self):
        source = "quest a {\n}\nitem b {\n}"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        quest_tok = next(t for t in tokens if t.type == TokenType.QUEST)
        item_tok = next(t for t in tokens if t.type == TokenType.ITEM)
        self.assertEqual(quest_tok.line, 1)
        self.assertEqual(item_tok.line, 3)


class TestParser(unittest.TestCase):
    def test_parse_quest(self):
        source = 'quest quete1 { title: "Titre"; desc: "Desc"; }'
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        self.assertIn("quete1", ast.quests)
        quest = ast.quests["quete1"]
        self.assertIsInstance(quest.properties.get("title"), LiteralNode)

    def test_parse_world(self):
        source = 'world monde1 { start: quete1; start_gold: 50; win_condition: fin; }'
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        self.assertIsNotNone(ast.world)
        self.assertEqual(ast.world.name, "monde1")

    def test_parse_item(self):
        source = 'item epee { title: "Epee"; value: 100; type: weapon; stackable: false; }'
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        self.assertIn("epee", ast.items)
        item = ast.items["epee"]
        self.assertEqual(item.properties.get("type"), "weapon")

    def test_parse_npc(self):
        source = 'npc marchand { title: "Marchand"; location: village; gives_quest: q1, q2; }'
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        self.assertIn("marchand", ast.npcs)

    def test_parse_rewards(self):
        source = 'quest q1 { rewards: xp 100, gold 50, 3 potion; }'
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        quest = ast.quests["q1"]
        rewards = quest.properties.get("rewards")
        self.assertIsInstance(rewards, RewardListNode)
        self.assertEqual(len(rewards.rewards), 3)

    def test_parse_script(self):
        source = """
        quest q1 {
            title: "Test";
            script {
                var x = 10;
                if (x > 5) {
                    give xp 100;
                }
            }
        }
        """
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        quest = ast.quests["q1"]
        self.assertIsNotNone(quest.script)
        self.assertTrue(len(quest.script.statements) > 0)

    def test_parse_function(self):
        source = 'func calcul(a, b) { var c = a + b; return c; }'
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        self.assertIn("calcul", ast.functions)
        func = ast.functions["calcul"]
        self.assertEqual(func.params, ["a", "b"])


class TestSemanticPasses(unittest.TestCase):
    def test_duplicate_quest(self):
        source = """
        quest q1 { title: "A"; }
        quest q1 { title: "B"; }
        """
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)
        diag = analyzer.get_diagnostics()
        codes = [e["code"] for e in diag["errors"]]
        self.assertIn("DUPLICATE_QUEST", codes)

    def test_undef_unlock_ref(self):
        source = 'quest q1 { unlocks: q_inexistant; }'
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)
        diag = analyzer.get_diagnostics()
        codes = [e["code"] for e in diag["errors"]]
        self.assertIn("UNDEF_UNLOCK_REF", codes)

    def test_undef_item_ref(self):
        source = 'quest q1 { rewards: 1 item_inexistant; }'
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)
        diag = analyzer.get_diagnostics()
        codes = [e["code"] for e in diag["errors"]]
        self.assertIn("UNDEF_ITEM_REF", codes)

    def test_division_by_zero(self):
        expr = BinaryOpNode("/", LiteralNode(10), LiteralNode(0), 1, 1)
        analyzer = SemanticAnalyzer()
        analyzer.program = ProgramNode([])
        analyzer._infer_type(expr)
        diag = analyzer.get_diagnostics()
        codes = [e["code"] for e in diag["errors"]]
        self.assertIn("DIVISION_BY_ZERO", codes)


class TestOptimization(unittest.TestCase):
    def test_constant_folding_addition(self):
        expr = BinaryOpNode("+", LiteralNode(2), LiteralNode(3), 1, 1)
        opt = Optimizer()
        res = opt.optimize(expr)
        self.assertIsInstance(res, LiteralNode)
        self.assertEqual(res.value, 5)

    def test_constant_folding_multiplication(self):
        expr = BinaryOpNode("*", LiteralNode(4), LiteralNode(6), 1, 1)
        opt = Optimizer()
        res = opt.optimize(expr)
        self.assertIsInstance(res, LiteralNode)
        self.assertEqual(res.value, 24)

    def test_constant_folding_nested(self):
        expr = BinaryOpNode(
            "*",
            BinaryOpNode("+", LiteralNode(2), LiteralNode(3), 1, 1),
            LiteralNode(4),
            1, 1
        )
        opt = Optimizer()
        res = opt.optimize(expr)
        self.assertIsInstance(res, LiteralNode)
        self.assertEqual(res.value, 20)

    def test_division_by_zero_not_folded(self):
        expr = BinaryOpNode("/", LiteralNode(10), LiteralNode(0), 1, 1)
        opt = Optimizer()
        res = opt.optimize(expr)
        self.assertIsInstance(res, BinaryOpNode)
        self.assertEqual(res.op, "/")


class TestIntegration(unittest.TestCase):
    def test_full_pipeline_valid(self):
        source = """
        world valdris {
            start: prologue;
            start_gold: 50;
            win_condition: epilogue;
        }

        quest prologue {
            title: "L'appel aux armes";
            desc: "Le roi a besoin de vous.";
            rewards: xp 100, gold 20;
            unlocks: premiere_mission;
        }

        quest premiere_mission {
            title: "Premiere mission";
            desc: "Partez a l'aventure.";
            requires: prologue;
            rewards: xp 200, gold 50, 1 epee_magique;
            unlocks: epilogue;
        }

        quest epilogue {
            title: "Epilogue";
            desc: "Vous avez sauve le royaume.";
            requires: premiere_mission;
            rewards: xp 500, gold 100;
        }

        item epee_magique {
            title: "Epee Magique";
            value: 150;
            type: weapon;
            stackable: false;
        }

        npc roi {
            title: "Le Roi";
            location: chateau;
            gives_quest: prologue, premiere_mission;
        }
        """
        tokens = Lexer(source, "test.ql").tokenize()
        ast = Parser(tokens, "test.ql").parse()
        analyzer = SemanticAnalyzer()
        success = analyzer.analyze(ast)
        diag = analyzer.get_diagnostics()

        self.assertTrue(success)
        self.assertEqual(diag["error_count"], 0)

        codegen = CodeGenerator(ast, diag)
        ir = codegen.generate_ir()
        self.assertEqual(ir["compilation_status"], "OK")
        self.assertEqual(len(ir["quests"]), 3)
        self.assertEqual(len(ir["items"]), 1)
        self.assertEqual(len(ir["npcs"]), 1)
        self.assertTrue(ir["optimized"])

    def test_codegen_html(self):
        source = 'world w { start: q1; } quest q1 { title: "A"; }'
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)
        diag = analyzer.get_diagnostics()
        codegen = CodeGenerator(ast, diag)
        html = codegen.to_html()
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("QuestLang", html)

    def test_codegen_json(self):
        source = 'world w { start: q1; } quest q1 { title: "A"; rewards: xp 10; }'
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)
        diag = analyzer.get_diagnostics()
        codegen = CodeGenerator(ast, diag)
        json_str = codegen.to_json()
        data = json.loads(json_str)
        self.assertEqual(data["questlang_version"], "2.0")
        self.assertEqual(data["compilation_status"], "OK")
        self.assertTrue(data["optimized"])

    def test_broken_world(self):
        source = """
        world w { start: q1; win_condition: inexistant; }
        quest q1 { title: "A"; unlocks: q_inexistant; rewards: 1 item_inexistant; }
        quest q2 { title: "B"; }
        item epee { title: "E"; }
        npc pnj1 { title: "P"; }
        """
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)
        diag = analyzer.get_diagnostics()

        error_codes = [e["code"] for e in diag["errors"]]
        warning_codes = [w["code"] for w in diag["warnings"]]

        self.assertIn("UNDEF_WIN_COND", error_codes)
        self.assertIn("UNDEF_UNLOCK_REF", error_codes)
        self.assertIn("UNDEF_ITEM_REF", error_codes)
        self.assertIn("UNREACHABLE_QUEST", error_codes)
        self.assertIn("DEAD_ITEM", warning_codes)
        self.assertIn("IDLE_NPC", warning_codes)


if __name__ == "__main__":
    print("=" * 60)
    print("  QuestLang Compiler Test Suite v2.0")
    print("  Tests: Lexer + Parser + Semantic + Optimization + Integration")
    print("=" * 60)

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestLexer))
    suite.addTests(loader.loadTestsFromTestCase(TestParser))
    suite.addTests(loader.loadTestsFromTestCase(TestSemanticPasses))
    suite.addTests(loader.loadTestsFromTestCase(TestOptimization))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("  TOUS LES TESTS ONT REUSSI")
    else:
        print("  ECHECS: {}".format(len(result.failures) + len(result.errors)))
    print("=" * 60)

    sys.exit(0 if result.wasSuccessful() else 1)