#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QuestLang Compiler v2.0
Compilateur pour un DSL de description de mondes RPG.
"""

import sys
import os
import argparse
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from lexer import Lexer, TokenType
from parser import Parser
from ast_nodes import ProgramNode
from semantic import SemanticAnalyzer
from codegen import CodeGenerator
from errors import LexicalError, SyntaxError, SemanticError

def print_colored(text, color="white", bold=False):
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "gray": "\033[90m",
    }
    reset = "\033[0m"
    bold_code = "\033[1m" if bold else ""
    color_code = colors.get(color, "")
    print(f"{bold_code}{color_code}{text}{reset}")

def format_time(seconds):
    if seconds < 0.001:
        return f"{seconds*1000:.2f} ms"
    elif seconds < 1:
        return f"{seconds*1000:.1f} ms"
    return f"{seconds:.3f} s"

def compile_file(filepath, options):
    import time

    if not os.path.exists(filepath):
        print_colored(f"Erreur: Le fichier '{filepath}' n'existe pas.", "red", True)
        return False, None, None

    filename = os.path.basename(filepath)
    print_colored(f"\n[1/5] Lecture du fichier: {filename}", "cyan")

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
    except Exception as e:
        print_colored(f"Erreur de lecture: {e}", "red", True)
        return False, None, None

    print_colored(f" {len(source)} caracteres, {source.count(chr(10))} lignes", "gray")

    # --- ETAPE 1: LEXER ---
    t0 = time.time()
    print_colored("\n[2/5] Analyse lexicale...", "cyan")

    try:
        lexer = Lexer(source, filename)
        tokens = lexer.tokenize()
    except LexicalError as e:
        print_colored(f" [ERREUR LEXICALE] {e}", "red", True)
        return False, None, None

    t1 = time.time()
    print_colored(f" {len(tokens)} tokens generes en {format_time(t1-t0)}", "green")

    if options.tokens:
        print_colored("\n --- Tokens ---", "gray")
        for tok in tokens[:50]:
            if tok.type not in [TokenType.NEWLINE, TokenType.EOF]:
                print_colored(f" {tok.type.name:15} {str(tok.value)!r:20} (ligne {tok.line})", "gray")
        if len(tokens) > 50:
            print_colored(f" ... et {len(tokens)-50} tokens supplementaires", "gray")

    # --- ETAPE 2: PARSER ---
    print_colored("\n[3/5] Analyse syntaxique...", "cyan")

    try:
        parser = Parser(tokens, filename)
        ast = parser.parse()
    except SyntaxError as e:
        print_colored(f" [ERREUR SYNTAXIQUE] {e}", "red", True)
        return False, None, None

    t2 = time.time()
    print_colored(f" AST construit en {format_time(t2-t1)}", "green")

    quest_count = len(ast.quests)
    item_count = len(ast.items)
    npc_count = len(ast.npcs)
    func_count = len(ast.functions)
    print_colored(f" Quetes: {quest_count} | Items: {item_count} | PNJ: {npc_count} | Fonctions: {func_count}", "gray")

    if options.ast:
        print_colored("\n --- AST (simplifie) ---", "gray")
        print_colored(f" Program({len(ast.declarations)} declarations)", "gray")
        for decl in ast.declarations:
            print_colored(f" - {type(decl).__name__}: {getattr(decl, 'name', 'N/A')}", "gray")

    # --- ETAPE 3: SEMANTIQUE ---
    print_colored("\n[4/5] Analyse semantique (5 passes)...", "cyan")

    try:
        analyzer = SemanticAnalyzer()
        success = analyzer.analyze(ast)
        diagnostics = analyzer.get_diagnostics()
    except SemanticError as e:
        print_colored(f" [ERREUR SEMANTIQUE] {e}", "red", True)
        return False, None, None

    t3 = time.time()
    print_colored(f" Analyse terminee en {format_time(t3-t2)}", "green")

    if diagnostics["errors"]:
        print_colored(f" {diagnostics['error_count']} ERREUR(S):", "red", True)
        for e in diagnostics["errors"]:
            loc = f" (ligne {e['line']})" if e.get('line') else ""
            print_colored(f" [ERREUR] {e['code']}: {e['message']}{loc}", "red")

    if diagnostics["warnings"]:
        print_colored(f" {diagnostics['warning_count']} AVERTISSEMENT(S):", "yellow")
        for w in diagnostics["warnings"]:
            loc = f" (ligne {w['line']})" if w.get('line') else ""
            print_colored(f" [AVERT.] {w['code']}: {w['message']}{loc}", "yellow")

    if diagnostics["infos"]:
        print_colored(f" {diagnostics['info_count']} INFO(S):", "blue")
        for i in diagnostics["infos"]:
            print_colored(f" [INFO] {i['code']}: {i['message']}", "blue")

    if not diagnostics["errors"] and not diagnostics["warnings"] and not diagnostics["infos"]:
        print_colored(" Aucun probleme detecte.", "green")

    # --- ETAPE 4: CODE GENERATION ---
    print_colored("\n[5/5] Generation de code...", "cyan")

    codegen = CodeGenerator(ast, diagnostics)
    ir_json = codegen.to_json()
    html_content = codegen.to_html()

    t4 = time.time()
    print_colored(f" Code genere en {format_time(t4-t3)}", "green")

    total_time = t4 - t0
    print_colored(f"\n{'='*50}", "gray")
    print_colored(f" Compilation terminee en {format_time(total_time)}", "cyan", True)

    if diagnostics["error_count"] == 0:
        print_colored(f" Statut: SUCCES", "green", True)
    else:
        print_colored(f" Statut: ECHEC ({diagnostics['error_count']} erreur(s))", "red", True)
    print_colored(f"{'='*50}\n", "gray")

    return diagnostics["error_count"] == 0, ir_json, html_content

def main():
    parser_args = argparse.ArgumentParser(
        description="QuestLang Compiler - Compilateur pour mondes RPG",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
 python questlang.py exemple.ql
 python questlang.py exemple.ql --html --out ./rapports/
 python questlang.py exemple.ql --ir --tokens
 """
    )
    parser_args.add_argument("fichier", help="Fichier source QuestLang (.ql)")
    parser_args.add_argument("--html", action="store_true", help="Generer un rapport HTML")
    parser_args.add_argument("--ir", action="store_true", help="Afficher l'IR JSON")
    parser_args.add_argument("--tokens", action="store_true", help="Afficher les tokens")
    parser_args.add_argument("--ast", action="store_true", help="Afficher l'AST")
    parser_args.add_argument("--out", default=".", help="Repertoire de sortie")
    parser_args.add_argument("-v", "--verbose", action="store_true", help="Mode verbeux")
    parser_args.add_argument("--no-banner", action="store_true", help="Desactiver la banniere")

    args = parser_args.parse_args()

    success, ir_json, html_content = compile_file(args.fichier, args)

    if not success:
        sys.exit(1)

    base_name = os.path.splitext(os.path.basename(args.fichier))[0]
    out_dir = args.out
    os.makedirs(out_dir, exist_ok=True)

    ir_path = os.path.join(out_dir, f"{base_name}.ir.json")
    with open(ir_path, "w", encoding="utf-8") as f:
        f.write(ir_json)
    print_colored(f"IR JSON ecrit: {ir_path}", "green")

    if args.ir:
        print_colored("\n--- IR JSON ---", "gray")
        print(ir_json)

    if args.html:
        html_path = os.path.join(out_dir, f"{base_name}.report.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        print_colored(f"Rapport HTML ecrit: {html_path}", "green")

    sys.exit(0)

if __name__ == "__main__":
    main()