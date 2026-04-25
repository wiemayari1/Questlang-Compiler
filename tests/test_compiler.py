# -*- coding: utf-8 -*-
"""
Suite de tests pour QuestLang Compiler v2.
27 tests couvrant: lexer, parser, semantique (4 passes), integration.

Execution:
    python tests/test_compiler.py
    python -m pytest tests/test_compiler.py -v
"""

import sys
import os
import json
import unittest

# Ajouter src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from lexer import Lexer, TokenType
from parser import Parser
from ast_nodes import *
from semantic import SemanticAnalyzer
from codegen import CodeGenerator
from errors import LexicalError, SyntaxError


class TestLexer(unittest.TestCase):
    """Tests de l'analyse lexicale (6 tests)."""

    def test_basic_tokens(self):
        """Test 1: Tokenisation des mots-cles et operateurs de base."""
        source = "quest foo { title: \"Hello\"; }"
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
        """Test 2: Tokenisation des nombres entiers et flottants."""
        source = "42 3.14 0 1000"
        lexer = Lexer(source)
        tokens = [t for t in lexer.tokenize() if t.type == TokenType.NUMBER]
        self.assertEqual(len(tokens), 4)
        self.assertEqual(tokens[0].value, 42)
        self.assertEqual(tokens[1].value, 3.14)
        self.assertEqual(tokens[2].value, 0)
        self.assertEqual(tokens[3].value, 1000)

    def test_operators(self):
        """Test 3: Tokenisation des operateurs complexes."""
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
        """Test 4: Les commentaires sont ignores."""
        source = """
        // Commentaire sur une ligne
        quest test { /* commentaire
        multi-ligne */ title: \"T\"; }
        """
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        # Verifier que les tokens significatifs sont presents
        types = [t.type for t in tokens]
        self.assertIn(TokenType.QUEST, types)
        self.assertIn(TokenType.IDENTIFIER, types)
        self.assertIn(TokenType.TITLE, types)

    def test_string_escapes(self):
        """Test 5: Sequences d'echappement dans les chaines."""
        source = '\"Ligne 1\nLigne 2\tTab\"'
        lexer = Lexer(source)
        tokens = [t for t in lexer.tokenize() if t.type == TokenType.STRING]
        self.assertEqual(len(tokens), 1)
        self.assertIn("\n", tokens[0].value)
        self.assertIn("\t", tokens[0].value)

    def test_line_tracking(self):
        """Test 6: Suivi correct des numeros de ligne."""
        source = "quest a {\n}\nitem b {\n}"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        quest_tok = next(t for t in tokens if t.type == TokenType.QUEST)
        item_tok = next(t for t in tokens if t.type == TokenType.ITEM)
        self.assertEqual(quest_tok.line, 1)
        self.assertEqual(item_tok.line, 3)


class TestParser(unittest.TestCase):
    """Tests de l'analyse syntaxique (7 tests)."""

    def test_parse_quest(self):
        """Test 7: Parsing d'une quete simple."""
        source = 'quest quete1 { title: \"Titre\"; desc: \"Desc\"; }'
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        self.assertIn("quete1", ast.quests)
        quest = ast.quests["quete1"]
        self.assertIsInstance(quest.properties.get("title"), LiteralNode)

    def test_parse_world(self):
        """Test 8: Parsing du bloc world."""
        source = 'world monde1 { start: quete1; start_gold: 50; win_condition: fin; }'
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        self.assertIsNotNone(ast.world)
        self.assertEqual(ast.world.name, "monde1")

    def test_parse_item(self):
        """Test 9: Parsing d'un item."""
        source = 'item epee { title: \"Epee\"; value: 100; type: weapon; stackable: false; }'
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        self.assertIn("epee", ast.items)
        item = ast.items["epee"]
        self.assertEqual(item.properties.get("type"), "weapon")

    def test_parse_npc(self):
        """Test 10: Parsing d'un PNJ."""
        source = 'npc marchand { title: \"Marchand\"; location: village; gives_quest: q1, q2; }'
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        self.assertIn("marchand", ast.npcs)

    def test_parse_rewards(self):
        """Test 11: Parsing des recompenses avec quantites."""
        source = 'quest q1 { rewards: xp 100, gold 50, 3 potion; }'
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        quest = ast.quests["q1"]
        rewards = quest.properties.get("rewards")
        self.assertIsInstance(rewards, RewardListNode)
        self.assertEqual(len(rewards.rewards), 3)

    def test_parse_script(self):
        """Test 12: Parsing d'un script avec variables et controle."""
        source = """
        quest q1 {
            title: \"Test\";
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
        """Test 13: Parsing d'une fonction utilisateur."""
        source = 'func calcul(a, b) { var c = a + b; return c; }'
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        self.assertIn("calcul", ast.functions)
        func = ast.functions["calcul"]
        self.assertEqual(func.params, ["a", "b"])


class TestSemanticPass1(unittest.TestCase):
    """Tests de la Passe 1: Table des symboles (3 tests)."""

    def test_duplicate_quest(self):
        """Test 14: Detection des quetes dupliquees."""
        source = """
        quest q1 { title: \"A\"; }
        quest q1 { title: \"B\"; }
        """
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)
        diag = analyzer.get_diagnostics()
        codes = [e["code"] for e in diag["errors"]]
        self.assertIn("DUPLICATE_QUEST", codes)

    def test_undef_quest_ref(self):
        """Test 15: Detection des references a des quetes inexistantes."""
        source = 'quest q1 { unlocks: q_inexistant; }'
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)
        diag = analyzer.get_diagnostics()
        codes = [e["code"] for e in diag["errors"]]
        self.assertIn("UNDEF_UNLOCK_REF", codes)

    def test_undef_item_ref(self):
        """Test 16: Detection des references a des items inexistantes."""
        source = 'quest q1 { rewards: 1 item_inexistant; }'
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)
        diag = analyzer.get_diagnostics()
        codes = [e["code"] for e in diag["errors"]]
        self.assertIn("UNDEF_ITEM_REF", codes)


class TestSemanticPass2(unittest.TestCase):
    """Tests de la Passe 2: Accessibilite (3 tests)."""

    def test_unreachable_quest(self):
        """Test 17: Detection des quetes inaccessibles."""
        source = """
        world w { start: q1; }
        quest q1 { title: \"A\"; unlocks: q2; }
        quest q2 { title: \"B\"; }
        quest q3 { title: \"C\"; }
        """
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)
        diag = analyzer.get_diagnostics()
        codes = [e["code"] for e in diag["errors"]]
        self.assertIn("UNREACHABLE_QUEST", codes)

    def test_win_unreachable(self):
        """Test 18: Detection de la victoire inaccessible."""
        source = """
        world w { start: q1; win_condition: q_fin; }
        quest q1 { title: \"A\"; }
        quest q_fin { title: \"Fin\"; }
        """
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)
        diag = analyzer.get_diagnostics()
        codes = [e["code"] for e in diag["errors"]]
        self.assertIn("WIN_UNREACHABLE", codes)

    def test_no_reward_warning(self):
        """Test 19: Avertissement pour quete sans recompense."""
        source = """
        world w { start: q1; }
        quest q1 { title: \"A\"; unlocks: q2; }
        quest q2 { title: \"B\"; }
        """
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)
        diag = analyzer.get_diagnostics()
        codes = [w["code"] for w in diag["warnings"]]
        self.assertIn("NO_REWARD", codes)


class TestSemanticPass3(unittest.TestCase):
    """Tests de la Passe 3: Economie (2 tests)."""

    def test_item_deficit(self):
        """Test 20: Detection du deficit d'items."""
        source = """
        world w { start: q1; }
        quest q1 { title: \"A\"; costs: 5 potion; rewards: xp 100; }
        item potion { title: \"Potion\"; value: 10; type: consumable; stackable: true; }
        """
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)
        diag = analyzer.get_diagnostics()
        codes = [e["code"] for e in diag["errors"]]
        self.assertIn("ITEM_DEFICIT", codes)

    def test_gold_inflation(self):
        """Test 21: Detection de l'inflation d'or."""
        source = """
        world w { start: q1; }
        quest q1 { title: \"A\"; rewards: gold 1000; costs: gold 10; }
        """
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)
        diag = analyzer.get_diagnostics()
        codes = [w["code"] for w in diag["warnings"]]
        self.assertIn("GOLD_INFLATION", codes)


class TestSemanticPass4(unittest.TestCase):
    """Tests de la Passe 4: Cycles (2 tests)."""

    def test_deadlock_cycle(self):
        """Test 22: Detection des deadlocks narratifs."""
        source = """
        world w { start: q1; }
        quest q1 { title: \"A\"; requires: q2; unlocks: q2; }
        quest q2 { title: \"B\"; requires: q1; unlocks: q1; }
        """
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)
        diag = analyzer.get_diagnostics()
        codes = [e["code"] for e in diag["errors"]]
        self.assertIn("DEADLOCK_CYCLE", codes)

    def test_dead_item(self):
        """Test 23: Detection des items jamais utilises."""
        source = """
        world w { start: q1; }
        quest q1 { title: \"A\"; }
        item epee { title: \"Epee\"; value: 100; type: weapon; }
        """
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)
        diag = analyzer.get_diagnostics()
        codes = [w["code"] for w in diag["warnings"]]
        self.assertIn("DEAD_ITEM", codes)


class TestIntegration(unittest.TestCase):
    """Tests d'integration (4 tests)."""

    def test_full_pipeline_valid(self):
        """Test 24: Pipeline complet sur un monde valide."""
        source = """
        world valdris {
            start: prologue;
            start_gold: 50;
            win_condition: epilogue;
        }

        quest prologue {
            title: \"L'appel aux armes\";
            desc: \"Le roi a besoin de vous.\";
            rewards: xp 100, gold 20;
            unlocks: premiere_mission;
        }

        quest premiere_mission {
            title: \"Premiere mission\";
            desc: \"Partez a l'aventure.\";
            requires: prologue;
            rewards: xp 200, gold 50, 1 epee_magique;
            unlocks: epilogue;
        }

        quest epilogue {
            title: \"Epilogue\";
            desc: \"Vous avez sauve le royaume.\";
            requires: premiere_mission;
            rewards: xp 500, gold 100;
        }

        item epee_magique {
            title: \"Epee Magique\";
            value: 150;
            type: weapon;
            stackable: false;
        }

        npc roi {
            title: \"Le Roi\";
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

        # Generation de code
        codegen = CodeGenerator(ast, diag)
        ir = codegen.generate_ir()
        self.assertEqual(ir["compilation_status"], "OK")
        self.assertEqual(len(ir["quests"]), 3)
        self.assertEqual(len(ir["items"]), 1)
        self.assertEqual(len(ir["npcs"]), 1)

    def test_codegen_html(self):
        """Test 25: Generation du rapport HTML."""
        source = 'world w { start: q1; } quest q1 { title: \"A\"; }'
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)
        diag = analyzer.get_diagnostics()
        codegen = CodeGenerator(ast, diag)
        html = codegen.to_html()
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("QuestLang", html)
        self.assertIn("q1", html)

    def test_codegen_json(self):
        """Test 26: Generation de l'IR JSON."""
        source = 'world w { start: q1; } quest q1 { title: \"A\"; rewards: xp 10; }'
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

    def test_broken_world(self):
        """Test 27: Monde avec erreurs intentionnelles."""
        source = """
        world w { start: q1; win_condition: inexistant; }
        quest q1 { title: \"A\"; unlocks: q_inexistant; rewards: 1 item_inexistant; }
        quest q2 { title: \"B\"; }
        item epee { title: \"E\"; }
        npc pnj1 { title: \"P\"; }
        """
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)
        diag = analyzer.get_diagnostics()

        # Doit detecter plusieurs erreurs
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
    print("  27 tests: Lexer(6) + Parser(7) + Semantic(7) + Integration(4)")
    print("=" * 60)

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestLexer))
    suite.addTests(loader.loadTestsFromTestCase(TestParser))
    suite.addTests(loader.loadTestsFromTestCase(TestSemanticPass1))
    suite.addTests(loader.loadTestsFromTestCase(TestSemanticPass2))
    suite.addTests(loader.loadTestsFromTestCase(TestSemanticPass3))
    suite.addTests(loader.loadTestsFromTestCase(TestSemanticPass4))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("  TOUS LES TESTS ONT REUSSI")
    else:
        print(f"  ECHECS: {len(result.failures) + len(result.errors)}")
    print("=" * 60)

    sys.exit(0 if result.wasSuccessful() else 1)
