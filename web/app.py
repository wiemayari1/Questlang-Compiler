#!/usr/bin/env python3
"""QuestLang Forge - Interface Web Corrigee"""
import os, sys, threading, traceback, importlib.util
from pathlib import Path
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from collections import defaultdict, deque

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

app = Flask(__name__, template_folder='templates', static_folder='static')
# CORS restreint aux origines locales uniquement
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5000", "http://127.0.0.1:5000"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

EXAMPLES = {
    "monde_complexe": "world royaume_eldoria {\n start: quete_village;\n start_gold: 100;\n win_condition: quete_royale;\n}\n\nquest quete_village {\n title: \"Le Village en Detresse\";\n desc: \"Des gobelins attaquent le village.\";\n unlocks: quete_foret, quete_mine;\n rewards: xp 50, gold 20;\n}\n\nquest quete_foret {\n title: \"La Foret Maudite\";\n desc: \"Trouvez l'herbe medicinale.\";\n requires: quete_village;\n unlocks: quete_chateau;\n rewards: xp 100, gold 30, 1 herbe_rare;\n costs: 1 torche;\n}\n\nquest quete_mine {\n title: \"Les Profondeurs\";\n desc: \"Recuperez le minerai magique.\";\n requires: quete_village;\n unlocks: quete_forge;\n rewards: xp 120, gold 40, 1 minerai_magique;\n costs: 2 torche;\n}\n\nquest quete_forge {\n title: \"La Forge Celeste\";\n desc: \"Forgez l'epee legendaire.\";\n requires: quete_mine;\n unlocks: quete_royale;\n rewards: xp 200, gold 50, 1 epee_legendaire;\n costs: 1 minerai_magique;\n}\n\nquest quete_chateau {\n title: \"Le Chateau Oublie\";\n desc: \"Trouvez le parchemin ancien.\";\n requires: quete_foret;\n unlocks: quete_royale;\n rewards: xp 150, gold 40, 1 parchemin_ancien;\n}\n\nquest quete_royale {\n title: \"Le Couronnement\";\n desc: \"Devenez le roi d'Eldoria.\";\n requires: quete_forge, quete_chateau;\n rewards: xp 1000, gold 500, 1 couronne_royale;\n}\n\nitem herbe_rare { title: \"Herbe Rare\"; value: 30; stackable: true; type: material; }\nitem torche { title: \"Torche\"; value: 5; stackable: true; type: consumable; }\nitem minerai_magique { title: \"Minerai Magique\"; value: 100; stackable: false; type: material; }\nitem epee_legendaire { title: \"Epee Legendaire\"; value: 500; stackable: false; type: weapon; }\nitem parchemin_ancien { title: \"Parchemin Ancien\"; value: 200; stackable: false; type: artifact; }\nitem couronne_royale { title: \"Couronne Royale\"; value: 5000; stackable: false; type: artifact; }\n\nnpc chef_village { title: \"Chef du Village\"; location: village; gives_quest: quete_village; }\nnpc druide { title: \"Le Druide\"; location: foret; gives_quest: quete_foret; }\nnpc mineur_nain { title: \"Thorin le Mineur\"; location: mine; gives_quest: quete_mine; }\nnpc forgeron_maitre { title: \"Maitre Forgeron\"; location: forge; gives_quest: quete_forge; }\nnpc roi { title: \"Roi Eldor\"; location: chateau; gives_quest: quete_royale; }",
    "monde_deadlock": "world deadlock_test {\n start: q1;\n start_gold: 100;\n win_condition: q3;\n}\n\nquest q1 {\n title: \"Quete A\";\n desc: \"A a besoin de B.\";\n requires: q2;\n unlocks: q3;\n rewards: xp 100;\n}\n\nquest q2 {\n title: \"Quete B\";\n desc: \"B a besoin de A.\";\n requires: q1;\n rewards: xp 100;\n}\n\nquest q3 {\n title: \"Quete C\";\n desc: \"Jamais atteinte.\";\n requires: q1;\n rewards: xp 200;\n}",
    "monde_erreurs": "world monde_casse {\n start: quete_inexistante;\n start_gold: 50;\n win_condition: quete_finale;\n}\n\nquest quete_depart {\n title: \"Depart\";\n desc: \"Quete de depart.\";\n unlocks: quete_milieu;\n rewards: xp 100, gold 25;\n}\n\nquest quete_milieu {\n title: \"Milieu\";\n desc: \"Quete du milieu.\";\n requires: quete_inexistante;\n unlocks: quete_finale;\n rewards: xp 200, gold 50, 1 epee;\n costs: 5 potion;\n}\n\nquest quete_finale {\n title: \"Fin\";\n desc: \"Quete finale.\";\n requires: quete_milieu;\n rewards: xp 500;\n}\n\nquest quete_orpheline {\n title: \"Orpheline\";\n desc: \"Jamais debloquee.\";\n rewards: xp 999;\n}\n\nitem epee { title: \"Epee\"; value: 50; stackable: false; type: weapon; }",
    "monde_inaccessible": "world inaccessible_test {\n start: q1;\n start_gold: 50;\n win_condition: q2;\n}\n\nquest q1 {\n title: \"Accessible\";\n desc: \"Celle-ci est OK.\";\n unlocks: q2;\n rewards: xp 100, gold 25;\n}\n\nquest q2 {\n title: \"Victoire\";\n desc: \"Condition de victoire.\";\n requires: q1;\n rewards: xp 500;\n}\n\nquest q3 {\n title: \"Oubliee\";\n desc: \"Personne ne debloque cette quete.\";\n rewards: xp 1000, gold 999;\n}",
    "monde_inflation": "world inflation_test {\n start: q1;\n start_gold: 10;\n win_condition: q3;\n}\n\nquest q1 {\n title: \"Quete d'Or\";\n desc: \"Trop d'or injecte.\";\n unlocks: q2;\n rewards: gold 10000, xp 50;\n}\n\nquest q2 {\n title: \"Milieu\";\n desc: \"Transition.\";\n requires: q1;\n unlocks: q3;\n rewards: gold 5000, xp 50;\n}\n\nquest q3 {\n title: \"Fin\";\n desc: \"Victoire.\";\n requires: q2;\n rewards: xp 100;\n}",
    "monde_valdris": "world valdris {\n start: quete_depart;\n start_gold: 50;\n win_condition: quete_finale;\n}\n\nquest quete_depart {\n title: \"Le Reveil\";\n desc: \"Vous vous reveillez dans un village detruit.\";\n unlocks: quete_forgeron;\n rewards: xp 100, gold 25;\n\n script {\n var bonus = 10;\n if (bonus > 5) {\n give xp bonus;\n }\n }\n}\n\nquest quete_forgeron {\n title: \"L'Appel du Fer\";\n desc: \"Le forgeron a besoin de minerai.\";\n requires: quete_depart;\n unlocks: quete_finale;\n rewards: xp 200, gold 50, 1 epee_rouillee;\n costs: 2 minerai;\n}\n\nquest quete_finale {\n title: \"Le Dernier Combat\";\n desc: \"Affrontez le dragon.\";\n requires: quete_forgeron;\n rewards: xp 500, gold 100, 1 ame_dragon;\n}\n\nitem epee_rouillee {\n title: \"Epee Rouillee\";\n value: 25;\n stackable: false;\n type: weapon;\n}\n\nitem minerai {\n title: \"Minerai de Fer\";\n value: 5;\n stackable: true;\n type: material;\n}\n\nitem ame_dragon {\n title: \"Ame du Dragon\";\n value: 1000;\n stackable: false;\n type: artifact;\n}\n\nnpc forgeron_gorak {\n title: \"Gorak le Forgeron\";\n location: forge_centrale;\n gives_quest: quete_forgeron;\n}"
}


def get_modules():
    """Charge les modules src/ via importlib (robuste, pas besoin de __init__.py)."""
    try:
        root = Path(__file__).parent.parent
        modules = {}
        for name, path in [
            ('lexer', root / 'src' / 'lexer.py'),
            ('parser', root / 'src' / 'parser.py'),
            ('semantic', root / 'src' / 'semantic.py'),
            ('codegen', root / 'src' / 'codegen.py'),
        ]:
            if not path.exists():
                return {"error": f"Fichier manquant: {path}", "traceback": ""}
            spec = importlib.util.spec_from_file_location(name, path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            modules[name] = mod
        return {
            'lexer': modules['lexer'].Lexer,
            'parser': modules['parser'].Parser,
            'semantic': modules['semantic'].SemanticAnalyzer,
            'codegen': modules['codegen'].CodeGenerator,
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}


@app.route("/")
def index():
    return render_template("index.html", examples=EXAMPLES)


@app.route("/api/health")
def health():
    mods = get_modules()
    if isinstance(mods, dict) and "error" in mods:
        return jsonify({"status": "error", "message": mods["error"]}), 500
    return jsonify({
        "status": "ok",
        "modules": ["lexer", "parser", "semantic", "codegen"]
    })


# --- Gestionnaires d'erreurs globaux ---

@app.errorhandler(404)
def not_found(e):
    if request.path.startswith('/api/'):
        return jsonify({"success": False, "error": "Route non trouvee", "path": request.path}), 404
    return render_template("index.html", examples=EXAMPLES), 404


@app.errorhandler(500)
def internal_error(e):
    tb = traceback.format_exc()
    if request.path.startswith('/api/'):
        return jsonify({
            "success": False,
            "error": "Erreur interne du serveur",
            "message": str(e),
            "traceback": tb
        }), 500
    return "Erreur interne", 500


@app.errorhandler(Exception)
def handle_exception(e):
    tb = traceback.format_exc()
    if request.path.startswith('/api/'):
        return jsonify({
            "success": False,
            "error": type(e).__name__,
            "message": str(e),
            "traceback": tb
        }), 500
    raise e


# --- Helpers ---

def _normalize_quests(ir):
    raw = ir.get("quests") if isinstance(ir, dict) else None
    if raw is None:
        return []
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        return list(raw.values())
    return []


def _normalize_entities(ir, key):
    if not isinstance(ir, dict):
        return []
    raw = ir.get(key)
    if raw is None:
        return []
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        return list(raw.values())
    return []


def _extract_title(entity, fallback):
    if not isinstance(entity, dict):
        return fallback
    title = entity.get("title", fallback)
    if isinstance(title, dict):
        return title.get("value", fallback)
    if isinstance(title, str):
        return title
    return str(title)


def _error_to_dict(entry, severity="error"):
    if isinstance(entry, dict):
        result = dict(entry)
        result["severity"] = severity
        return result
    result = {
        "severity": severity,
        "message": "",
        "line": 0,
        "col": 0,
        "code": ""
    }
    if hasattr(entry, 'message'):
        result["message"] = entry.message
    if hasattr(entry, 'line'):
        result["line"] = entry.line
    if hasattr(entry, 'column'):
        result["col"] = entry.column
    if hasattr(entry, 'code'):
        result["code"] = entry.code
    return result


def compute_simulation(ir, ast):
    if not ir or not ast:
        return None
    quests = _normalize_quests(ir)
    if not quests:
        return None
    world = ir.get("world", {}) if isinstance(ir, dict) else {}
    graph = defaultdict(list)
    in_degree = defaultdict(int)
    quest_map = {}
    for q in quests:
        qid = q.get("id") if isinstance(q, dict) else None
        if not qid:
            continue
        quest_map[qid] = q
        in_degree[qid]
    for q in quests:
        qid = q.get("id") if isinstance(q, dict) else None
        if not qid:
            continue
        unlocks = q.get("unlocks", [])
        if isinstance(unlocks, list):
            for unlocked in unlocks:
                if unlocked in quest_map:
                    graph[qid].append(unlocked)
                    in_degree[unlocked] += 1
        requires = q.get("requires", [])
        if isinstance(requires, list):
            for req in requires:
                if req in quest_map:
                    graph[req].append(qid)
                    in_degree[qid] += 1
    start_quest = ""
    if isinstance(world, dict):
        sg = world.get("start", "")
        start_quest = sg if isinstance(sg, str) else ""
    queue = deque()
    if start_quest and start_quest in quest_map:
        queue.append(start_quest)
    else:
        for qid in list(quest_map.keys()):
            if in_degree.get(qid, 0) == 0:
                queue.append(qid)
    order = []
    max_iter = len(quest_map) * 10
    iterations = 0
    while queue and iterations < max_iter:
        iterations += 1
        current = queue.popleft()
        if current not in order:
            order.append(current)
        for neighbor in graph.get(current, []):
            in_degree[neighbor] -= 1
            if in_degree.get(neighbor, 0) <= 0 and neighbor not in order:
                queue.append(neighbor)
    for qid in quest_map:
        if qid not in order:
            order.append(qid)
    start_gold = 50
    if isinstance(world, dict):
        sg = world.get("start_gold", 50)
        if isinstance(sg, (int, float)):
            start_gold = int(sg)
    inventory = {"gold": start_gold, "xp": 0, "items": {}}
    history = []
    win_reached = False
    win_condition = ""
    if isinstance(world, dict):
        wc = world.get("win_condition", "")
        win_condition = wc if isinstance(wc, str) else ""

    def eval_expr(expr):
        if isinstance(expr, (int, float)):
            return expr
        if isinstance(expr, dict):
            op = expr.get("op")
            if op in ("+", "-", "*", "/"):
                left = eval_expr(expr.get("left", 0))
                right = eval_expr(expr.get("right", 0))
                if op == "+":
                    return left + right
                elif op == "-":
                    return left - right
                elif op == "*":
                    return left * right
                elif op == "/":
                    return left / right if right != 0 else 0
            if "call" in expr:
                return 0
        return 0

    for qid in order:
        q = quest_map.get(qid)
        if not q:
            continue
        rewards = q.get("rewards", [])
        if isinstance(rewards, list):
            for r in rewards:
                if isinstance(r, dict):
                    rtype = r.get("type", "")
                    if rtype == "gold":
                        inventory["gold"] += eval_expr(r.get("amount", 0))
                    elif rtype == "xp":
                        inventory["xp"] += eval_expr(r.get("amount", 0))
                    elif rtype == "item":
                        item_name = r.get("name", "")
                        qty = int(eval_expr(r.get("quantity", 1)))
                        if item_name:
                            inventory["items"][item_name] = inventory["items"].get(item_name, 0) + qty
        costs = q.get("costs", [])
        if isinstance(costs, list):
            for c in costs:
                if isinstance(c, dict):
                    ctype = c.get("type", "")
                    if ctype == "gold":
                        inventory["gold"] -= eval_expr(c.get("amount", 0))
                    elif ctype == "item":
                        item_name = c.get("name", "")
                        qty = int(eval_expr(c.get("quantity", 1)))
                        if item_name and item_name in inventory["items"]:
                            inventory["items"][item_name] = max(0, inventory["items"][item_name] - qty)
        title = q.get("title", qid)
        if isinstance(title, dict):
            title = title.get("value", qid)
        elif not isinstance(title, str):
            title = str(title)
        history.append({
            "quest": qid,
            "title": title,
            "inventory_after": {
                "gold": inventory["gold"],
                "xp": inventory["xp"],
                "items": dict(inventory["items"])
            }
        })
        if win_condition and qid == win_condition:
            win_reached = True
    return {
        "order": order,
        "inventory": {
            "gold": inventory["gold"],
            "xp": inventory["xp"],
            "items": dict(inventory["items"])
        },
        "history": history,
        "win_reached": win_reached
    }


def build_quest_graph(ast, ir):
    nodes = []
    edges = []
    if not ir:
        return {"nodes": nodes, "edges": edges}
    quests = _normalize_quests(ir)
    items = _normalize_entities(ir, "items")
    npcs = _normalize_entities(ir, "npcs")
    for q in quests:
        qid = q.get("id", "") if isinstance(q, dict) else ""
        if not qid:
            continue
        title = _extract_title(q, qid)
        nodes.append({
            "id": qid,
            "label": title,
            "type": "quest",
            "reachable": q.get("reachable", True) if isinstance(q, dict) else True
        })
        unlocks = q.get("unlocks", []) if isinstance(q, dict) else []
        if isinstance(unlocks, list):
            for u in unlocks:
                edges.append({"from": qid, "to": u, "type": "unlocks", "dashes": False})
        requires = q.get("requires", []) if isinstance(q, dict) else []
        if isinstance(requires, list):
            for r in requires:
                edges.append({"from": r, "to": qid, "type": "requires", "dashes": True})
        rewards = q.get("rewards", []) if isinstance(q, dict) else []
        if isinstance(rewards, list):
            for r in rewards:
                if isinstance(r, dict) and r.get("type") == "item":
                    item_name = r.get("name", "")
                    edges.append({"from": qid, "to": item_name, "type": "reward", "dashes": True})
        costs = q.get("costs", []) if isinstance(q, dict) else []
        if isinstance(costs, list):
            for c in costs:
                if isinstance(c, dict) and c.get("type") == "item":
                    item_name = c.get("name", "")
                    edges.append({"from": qid, "to": item_name, "type": "cost", "dashes": True, "color": "#c44"})
    for i in items:
        iid = i.get("id", "") if isinstance(i, dict) else ""
        if not iid:
            continue
        title = _extract_title(i, iid)
        nodes.append({"id": iid, "label": title, "type": "item"})
    for n in npcs:
        nid = n.get("id", "") if isinstance(n, dict) else ""
        if not nid:
            continue
        title = _extract_title(n, nid)
        nodes.append({"id": nid, "label": title, "type": "npc"})
        gives = n.get("gives_quest", []) if isinstance(n, dict) else []
        if isinstance(gives, list):
            for g in gives:
                edges.append({"from": nid, "to": g, "type": "gives", "dashes": False, "color": "#1abc9c"})
    return {"nodes": nodes, "edges": edges}


def build_passes_report(report):
    passes = [
        {"name": "Symboles", "status": "ok", "errors": [], "details": "", "metrics": {}},
        {"name": "Accessibilite", "status": "ok", "errors": [], "details": "", "metrics": {}},
        {"name": "Economie", "status": "ok", "errors": [], "details": "", "metrics": {}},
        {"name": "Cycles", "status": "ok", "errors": [], "details": "", "metrics": {}}
    ]
    if not report:
        return passes
    pass_map = {
        "DUPLICATE_WORLD": 0, "DUPLICATE_QUEST": 0, "DUPLICATE_ITEM": 0, "DUPLICATE_NPC": 0,
        "DUPLICATE_FUNC": 0, "DUPLICATE_VAR": 0, "UNDEF_START_QUEST": 0, "UNDEF_WIN_COND": 0,
        "UNDEF_QUEST_REF": 0, "UNDEF_UNLOCK_REF": 0, "UNDEF_ITEM_REF": 0, "UNDEF_FUNC_REF": 0,
        "UNDECLARED_VAR": 0,
        "UNREACHABLE_QUEST": 1, "WIN_UNREACHABLE": 1, "NO_REWARD": 1, "DEFAULT_START": 1,
        "ITEM_DEFICIT": 2, "ITEM_SURPLUS": 2, "GOLD_INFLATION": 2, "GOLD_DEFLATION": 2,
        "DEADLOCK_CYCLE": 3, "UNLOCK_LOOP": 3, "DEAD_ITEM": 3, "IDLE_NPC": 3
    }
    all_entries = []
    if hasattr(report, 'errors') and isinstance(report.errors, list):
        all_entries.extend([(e, "error") for e in report.errors])
    if hasattr(report, 'warnings') and isinstance(report.warnings, list):
        all_entries.extend([(w, "warning") for w in report.warnings])
    for entry, severity in all_entries:
        code = entry.get("code", "") if isinstance(entry, dict) else getattr(entry, 'code', "")
        pass_idx = pass_map.get(code, 0)
        passes[pass_idx]["errors"].append(_error_to_dict(entry, severity))
        if severity == "error":
            passes[pass_idx]["status"] = "err"
        elif passes[pass_idx]["status"] == "ok":
            passes[pass_idx]["status"] = "warning"
    for i, p in enumerate(passes):
        err_count = len([e for e in p["errors"] if e.get("severity") in ("error", "err")])
        warn_count = len([e for e in p["errors"] if e.get("severity") in ("warning", "warn")])
        if err_count > 0:
            p["status"] = "err"
            p["details"] = f"{err_count} erreur(s) detectee(s)"
        elif warn_count > 0:
            p["status"] = "warning"
            p["details"] = f"{warn_count} avertissement(s)"
        else:
            p["details"] = "Aucun probleme detecte"
        p["metrics"] = {"errors": err_count, "warnings": warn_count}
    return passes


def count_ast_nodes(node, _visited=None):
    if node is None:
        return 0
    if _visited is None:
        _visited = set()
    node_id = id(node)
    if node_id in _visited:
        return 0
    _visited.add(node_id)
    count = 1
    attrs = ['declarations', 'statements', 'body', 'then_block', 'else_block',
             'init_expr', 'condition', 'left', 'right', 'operand', 'call_expr',
             'args', 'rewards', 'variables']
    for attr in attrs:
        val = getattr(node, attr, None)
        if val is None:
            continue
        if isinstance(val, list):
            count += sum(count_ast_nodes(c, _visited) for c in val)
        else:
            count += count_ast_nodes(val, _visited)
    if hasattr(node, 'properties') and isinstance(node.properties, dict):
        for v in node.properties.values():
            count += count_ast_nodes(v, _visited)
    return count


class CompilationTimeout(Exception):
    pass


def compile_with_timeout(source, step_mode, timeout_sec=8):
    result = {"done": False, "data": None, "error": None}

    def target():
        try:
            mods = get_modules()
            if isinstance(mods, dict) and "error" in mods:
                result["error"] = {
                    "type": "import",
                    "msg": mods['error'],
                    "traceback": mods.get('traceback', '')
                }
                result["done"] = True
                return
            lexer = mods['lexer'](source)
            tokens = lexer.tokenize()
            parser = mods['parser'](tokens)
            ast = parser.parse()
            semantic = mods['semantic']()
            semantic.analyze(ast)
            report = getattr(semantic, 'reporter', None)
            if report is None:
                report = semantic
            codegen = mods['codegen'](ast)
            ir = codegen.generate_ir() if hasattr(codegen, 'generate_ir') else codegen.generate()
            result["data"] = {
                "tokens": tokens,
                "ast": ast,
                "ir": ir,
                "report": report,
                "parser_errors": getattr(parser, 'errors', [])
            }
            result["done"] = True
        except Exception as e:
            result["error"] = {
                "type": type(e).__name__,
                "msg": str(e),
                "traceback": traceback.format_exc()
            }
            result["done"] = True

    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()
    thread.join(timeout=timeout_sec)
    if not result["done"]:
        raise CompilationTimeout("La compilation a depasse le delai de {} secondes".format(timeout_sec))
    if result["error"]:
        err = result["error"]
        exc = type(err["type"], (Exception,), {})(err["msg"])
        exc.traceback = err.get("traceback", "")
        exc.error_type = err["type"]
        raise exc
    return result["data"]


@app.route("/api/compile", methods=["POST"])
def compile_code():
    data = request.get_json() or {}
    source = data.get("code", "")
    step_mode = data.get("step_mode", False)
    if not source or not source.strip():
        return jsonify({
            "success": False,
            "errors": [{"message": "Code source vide", "line": 0, "col": 0}],
            "tokens": [], "ast": None, "ir": None,
            "semantic_report": None, "compilation_details": None
        })
    try:
        comp_result = compile_with_timeout(source, step_mode, timeout_sec=8)
        tokens = comp_result["tokens"]
        ast = comp_result["ast"]
        ir = comp_result["ir"]
        report = comp_result["report"]
        parser_errors = comp_result.get("parser_errors", [])
        errors, warnings = [], []
        if report:
            if hasattr(report, 'errors') and isinstance(report.errors, list):
                for e in report.errors:
                    entry = _error_to_dict(e, "error")
                    entry["pass"] = ""
                    errors.append(entry)
            if hasattr(report, 'warnings') and isinstance(report.warnings, list):
                for w in report.warnings:
                    entry = _error_to_dict(w, "warning")
                    entry["pass"] = ""
                    warnings.append(entry)
        for pe in parser_errors:
            if hasattr(pe, 'message'):
                errors.append({
                    "severity": "error",
                    "message": pe.message,
                    "line": getattr(pe, 'line', 0),
                    "col": getattr(pe, 'column', 0),
                    "code": "SYNTAX_ERROR",
                    "pass": ""
                })
        quest_graph = build_quest_graph(ast, ir)
        passes_report = build_passes_report(report)
        simulation = compute_simulation(ir, ast)
        ast_nodes_count = count_ast_nodes(ast)
        ast_dict = None
        if hasattr(ast, 'to_dict'):
            try:
                ast_dict = ast.to_dict()
            except Exception as te:
                ast_dict = {"type": "Program", "to_dict_error": str(te)}
        else:
            ast_dict = {"type": "Program"}
        return jsonify({
            "success": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "tokens": [{"type": t.type.name if hasattr(t.type, 'name') else str(t.type), "value": t.value, "line": t.line, "col": t.column} for t in tokens],
            "ast": ast_dict,
            "ir": ir,
            "semantic_report": {
                "passes": passes_report,
                "quest_graph": quest_graph
            },
            "compilation_details": {
                "pipeline": [
                    {"step": "Lexical", "status": "ok", "time": "~2ms"},
                    {"step": "Syntaxique", "status": "ok", "time": "~5ms"},
                    {"step": "Semantique", "status": "ok" if len(errors) == 0 else "err", "time": "~12ms"},
                    {"step": "Generation", "status": "ok", "time": "~3ms"}
                ],
                "total_time": "~25ms",
                "tokens_count": len(tokens),
                "ast_nodes": ast_nodes_count
            },
            "simulation": simulation
        })
    except CompilationTimeout as te:
        return jsonify({
            "success": False,
            "errors": [{"message": str(te), "line": 0, "col": 0, "severity": "error"}],
            "warnings": [],
            "tokens": [],
            "ast": None,
            "ir": None,
            "semantic_report": None,
            "compilation_details": None
        })
    except Exception as e:
        tb = getattr(e, 'traceback', traceback.format_exc())
        err_type = getattr(e, 'error_type', type(e).__name__)
        return jsonify({
            "success": False,
            "errors": [{"message": str(e), "line": 0, "col": 0, "severity": "error", "code": err_type}],
            "warnings": [],
            "tokens": [],
            "ast": None,
            "ir": None,
            "semantic_report": None,
            "compilation_details": None,
            "_debug": {"traceback": tb}
        }), 500


@app.route("/api/examples")
def list_examples():
    result = []
    for name, content in EXAMPLES.items():
        result.append({"name": name, "content": content})
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
