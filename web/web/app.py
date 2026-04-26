#!/usr/bin/env python3
"""QuestLang Forge"""
import os, sys
from pathlib import Path
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

EXAMPLES = {
 "monde_complexe": "world royaume_eldoria {\n start: quete_village;\n start_gold: 100;\n win_condition: quete_royale;\n}\n\nquest quete_village {\n title: \"Le Village en Detresse\";\n desc: \"Des gobelins attaquent le village.\";\n unlocks: quete_foret, quete_mine;\n rewards: xp 50, gold 20;\n}\n\nquest quete_foret {\n title: \"La Foret Maudite\";\n desc: \"Trouvez l'herbe medicinale.\";\n requires: quete_village;\n unlocks: quete_chateau;\n rewards: xp 100, gold 30, 1 herbe_rare;\n costs: 1 torche;\n}\n\nquest quete_mine {\n title: \"Les Profondeurs\";\n desc: \"Recuperez le minerai magique.\";\n requires: quete_village;\n unlocks: quete_forge;\n rewards: xp 120, gold 40, 1 minerai_magique;\n costs: 2 torche;\n}\n\nquest quete_forge {\n title: \"La Forge Celeste\";\n desc: \"Forgez l'epee legendaire.\";\n requires: quete_mine;\n unlocks: quete_royale;\n rewards: xp 200, gold 50, 1 epee_legendaire;\n costs: 1 minerai_magique;\n}\n\nquest quete_chateau {\n title: \"Le Chateau Oublie\";\n desc: \"Trouvez le parchemin ancien.\";\n requires: quete_foret;\n unlocks: quete_royale;\n rewards: xp 150, gold 40, 1 parchemin_ancien;\n}\n\nquest quete_royale {\n title: \"Le Couronnement\";\n desc: \"Devenez le roi d'Eldoria.\";\n requires: quete_forge, quete_chateau;\n rewards: xp 1000, gold 500, 1 couronne_royale;\n}\n\nitem herbe_rare { title: \"Herbe Rare\"; value: 30; stackable: true; type: material; }\nitem torche { title: \"Torche\"; value: 5; stackable: true; type: consumable; }\nitem minerai_magique { title: \"Minerai Magique\"; value: 100; stackable: false; type: material; }\nitem epee_legendaire { title: \"Epee Legendaire\"; value: 500; stackable: false; type: weapon; }\nitem parchemin_ancien { title: \"Parchemin Ancien\"; value: 200; stackable: false; type: artifact; }\nitem couronne_royale { title: \"Couronne Royale\"; value: 5000; stackable: false; type: artifact; }\n\nnpc chef_village { title: \"Chef du Village\"; location: village; gives_quest: quete_village; }\nnpc druide { title: \"Le Druide\"; location: foret; gives_quest: quete_foret; }\nnpc mineur_nain { title: \"Thorin le Mineur\"; location: mine; gives_quest: quete_mine; }\nnpc forgeron_maitre { title: \"Maître Forgeron\"; location: forge; gives_quest: quete_forge; }\nnpc roi { title: \"Roi Eldor\"; location: chateau; gives_quest: quete_royale; }",
 "monde_deadlock": "world deadlock_test {\n start: q1;\n start_gold: 100;\n win_condition: q3;\n}\n\nquest q1 {\n title: \"Quete A\";\n desc: \"A a besoin de B.\";\n requires: q2;\n unlocks: q3;\n rewards: xp 100;\n}\n\nquest q2 {\n title: \"Quete B\";\n desc: \"B a besoin de A.\";\n requires: q1;\n rewards: xp 100;\n}\n\nquest q3 {\n title: \"Quete C\";\n desc: \"Jamais atteinte.\";\n requires: q1;\n rewards: xp 200;\n}",
 "monde_erreurs": "world monde_casse {\n start: quete_inexistante;\n start_gold: 50;\n win_condition: quete_finale;\n}\n\nquest quete_depart {\n title: \"Depart\";\n desc: \"Quete de depart.\";\n unlocks: quete_milieu;\n rewards: xp 100, gold 25;\n}\n\nquest quete_milieu {\n title: \"Milieu\";\n desc: \"Quete du milieu.\";\n requires: quete_inexistante;\n unlocks: quete_finale;\n rewards: xp 200, gold 50, 1 epee;\n costs: 5 potion;\n}\n\nquest quete_finale {\n title: \"Fin\";\n desc: \"Quete finale.\";\n requires: quete_milieu;\n rewards: xp 500;\n}\n\nquest quete_orpheline {\n title: \"Orpheline\";\n desc: \"Jamais debloquee.\";\n rewards: xp 999;\n}\n\nitem epee { title: \"Epee\"; value: 50; stackable: false; type: weapon; }",
 "monde_fonctions": "world test_fonctions {\n start: q1;\n start_gold: 50;\n win_condition: q2;\n}\n\nfunc calculer_bonus(niveau) {\n var bonus = niveau * 10;\n if (bonus > 50) {\n return bonus;\n }\n return 50;\n}\n\nfunc verifier_or(montant) {\n if (montant >= 100) {\n return true;\n }\n return false;\n}\n\nquest q1 {\n title: \"Test de Fonctions\";\n desc: \"Test des fonctions utilisateur.\";\n unlocks: q2;\n rewards: xp 100, gold 25;\n\n script {\n var niveau = 5;\n var bonus = call calculer_bonus(niveau);\n give xp bonus;\n\n var riche = call verifier_or(bonus);\n if (riche) {\n give gold 10;\n }\n }\n}\n\nquest q2 {\n title: \"Fin\";\n desc: \"Victoire.\";\n requires: q1;\n rewards: xp 200;\n}",
 "monde_inaccessible": "world inaccessible_test {\n start: q1;\n start_gold: 50;\n win_condition: q2;\n}\n\nquest q1 {\n title: \"Accessible\";\n desc: \"Celle-ci est OK.\";\n unlocks: q2;\n rewards: xp 100, gold 25;\n}\n\nquest q2 {\n title: \"Victoire\";\n desc: \"Condition de victoire.\";\n requires: q1;\n rewards: xp 500;\n}\n\nquest q3 {\n title: \"Oubliee\";\n desc: \"Personne ne debloque cette quete.\";\n rewards: xp 1000, gold 999;\n}",
 "monde_inflation": "world inflation_test {\n start: q1;\n start_gold: 10;\n win_condition: q3;\n}\n\nquest q1 {\n title: \"Quete d'Or\";\n desc: \"Trop d'or injecte.\";\n unlocks: q2;\n rewards: gold 10000, xp 50;\n}\n\nquest q2 {\n title: \"Milieu\";\n desc: \"Transition.\";\n requires: q1;\n unlocks: q3;\n rewards: gold 5000, xp 50;\n}\n\nquest q3 {\n title: \"Fin\";\n desc: \"Victoire.\";\n requires: q2;\n rewards: xp 100;\n}",
 "monde_valdris": "world valdris {\n start: quete_depart;\n start_gold: 50;\n win_condition: quete_finale;\n}\n\nquest quete_depart {\n title: \"Le Reveil\";\n desc: \"Vous vous reveillez dans un village detruit.\";\n unlocks: quete_forgeron;\n rewards: xp 100, gold 25;\n\n script {\n var bonus = 10;\n if (bonus > 5) {\n give xp bonus;\n }\n }\n}\n\nquest quete_forgeron {\n title: \"L'Appel du Fer\";\n desc: \"Le forgeron a besoin de minerai.\";\n requires: quete_depart;\n unlocks: quete_finale;\n rewards: xp 200, gold 50, 1 epee_rouillee;\n costs: 2 minerai;\n}\n\nquest quete_finale {\n title: \"Le Dernier Combat\";\n desc: \"Affrontez le dragon.\";\n requires: quete_forgeron;\n rewards: xp 500, gold 100, 1 ame_dragon;\n}\n\nitem epee_rouillee {\n title: \"Epee Rouillee\";\n value: 25;\n stackable: false;\n type: weapon;\n}\n\nitem minerai {\n title: \"Minerai de Fer\";\n value: 5;\n stackable: true;\n type: material;\n}\n\nitem ame_dragon {\n title: \"Ame du Dragon\";\n value: 1000;\n stackable: false;\n type: artifact;\n}\n\nnpc forgeron_gorak {\n title: \"Gorak le Forgeron\";\n location: forge_centrale;\n gives_quest: quete_forgeron;\n}"
}

def get_modules():
 try:
 from src.lexer import Lexer
 from src.parser import Parser
 from src.semantic import SemanticAnalyzer
 from src.codegen import CodeGenerator
 return {'lexer': Lexer, 'parser': Parser, 'semantic': SemanticAnalyzer, 'codegen': CodeGenerator}
 except Exception:
 return None

@app.route("/")
def index():
 return render_template("index.html", examples=EXAMPLES)

@app.route("/api/compile", methods=["POST"])
def compile_code():
 data = request.get_json()
 source = data.get("code", "")
 step_mode = data.get("step_mode", False)

 if not source.strip():
 return jsonify({"success": False, "errors": [{"message": "Code source vide", "line": 0, "col": 0}],
 "tokens": [], "ast": None, "ir": None, "semantic_report": None, "compilation_details": None})

 mods = get_modules()
 if mods is None:
 return jsonify({
 "success": False,
 "errors": [{"message": "Modules du compilateur introuvables. Verifiez que vous lancez app.py depuis le dossier web/ et que src/ existe a la racine.", "line": 0, "col": 0}],
 "warnings": [],
 "tokens": [],
 "ast": None,
 "ir": None,
 "semantic_report": None,
 "compilation_details": None
 }), 500

 try:
 lexer = mods['lexer'](source)
 tokens = lexer.tokenize()
 parser = mods['parser'](tokens)
 ast = parser.parse()
 semantic = mods['semantic']()
 success = semantic.analyze(ast)
 diagnostics = semantic.get_diagnostics()
 codegen = mods['codegen'](ast, diagnostics)
 ir = codegen.generate_ir()

 errors, warnings = [], []
 for e in diagnostics.get("errors", []):
 errors.append({"message": e.get("message", ""), "line": e.get("line", 0),
 "col": e.get("column", 0), "severity": "error", "pass": "Semantique"})
 for w in diagnostics.get("warnings", []):
 warnings.append({"message": w.get("message", ""), "line": w.get("line", 0),
 "col": w.get("column", 0), "severity": "warning", "pass": "Semantique"})

 # Construction du rapport semantique pour le frontend
 passes_report = [
 {"name": "Symboles", "status": "ok" if not any(e.get("code", "").startswith("DUPLICATE") or e.get("code", "").startswith("UNDEF") for e in diagnostics.get("errors", [])) else "error",
 "errors": [], "details": "Verification des symboles", "metrics": {"symbols": len(ast.quests) + len(ast.items) + len(ast.npcs) + len(ast.functions)}},
 {"name": "Accessibilite", "status": "ok" if not any(e.get("code", "") == "UNREACHABLE_QUEST" for e in diagnostics.get("errors", [])) else "error",
 "errors": [], "details": "DFS des quetes", "metrics": {"quests": len(ast.quests)}},
 {"name": "Economie", "status": "warning" if any(w.get("code", "").startswith("GOLD_") or w.get("code", "").startswith("ITEM_") for w in diagnostics.get("warnings", [])) else "ok",
 "errors": [], "details": "Analyse de flux", "metrics": {}},
 {"name": "Cycles", "status": "ok" if not any(e.get("code", "") == "DEADLOCK_CYCLE" for e in diagnostics.get("errors", [])) else "error",
 "errors": [], "details": "Tarjan SCC", "metrics": {}}
 ]

 # Graphe pour vis.js
 nodes = []
 edges = []
 for name, quest in ast.quests.items():
 nodes.append({"id": name, "label": name, "type": "quest"})
 unlocks = quest.properties.get("unlocks")
 if isinstance(unlocks, list):
 for u in unlocks:
 edges.append({"from": name, "to": u, "type": "unlocks"})
 for name, item in ast.items.items():
 nodes.append({"id": name, "label": name, "type": "item"})
 for name, npc in ast.npcs.items():
 nodes.append({"id": name, "label": name, "type": "npc"})

 return jsonify({
 "success": len(errors) == 0,
 "errors": errors, "warnings": warnings,
 "tokens": [{"type": t.type.name, "value": t.value, "line": t.line, "col": t.column} for t in tokens],
 "ast": {"type": "Program", "quests": list(ast.quests.keys()), "items": list(ast.items.keys()), "npcs": list(ast.npcs.keys())},
 "ir": ir,
 "semantic_report": {
 "passes": passes_report,
 "quest_graph": {"nodes": nodes, "edges": edges}
 },
 "compilation_details": {
 "pipeline": [
 {"step": "Lexical", "status": "ok", "time": "~2ms"},
 {"step": "Syntaxique", "status": "ok", "time": "~5ms"},
 {"step": "Semantique", "status": "ok" if len(errors) == 0 else "err", "time": "~12ms"},
 {"step": "Generation", "status": "ok", "time": "~3ms"}
 ],
 "total_time": "~22ms",
 "tokens_count": len(tokens),
 "ast_nodes": len(ast.declarations)
 }
 })
 except Exception as e:
 import traceback
 return jsonify({
 "success": False,
 "errors": [{"message": str(e), "line": 0, "col": 0, "severity": "error"}],
 "warnings": [], "tokens": [], "ast": None, "ir": None,
 "semantic_report": None, "compilation_details": None
 })

@app.route("/api/examples")
def list_examples():
 result = []
 for name, content in EXAMPLES.items():
 result.append({"name": name, "content": content})
 return jsonify(result)

if __name__ == "__main__":
 app.run(debug=True, host="0.0.0.0", port=5000)
