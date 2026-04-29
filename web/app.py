#!/usr/bin/env python3

import os, sys, threading, traceback
from pathlib import Path
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from collections import defaultdict, deque

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

app = Flask(__name__, template_folder='templates', static_folder='static')

CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5000", "http://127.0.0.1:5000"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

def load_examples():
    examples_dir = PROJECT_ROOT / 'examples'
    examples = {}
    if examples_dir.exists():
        for f in examples_dir.glob('*.ql'):
            try:
                examples[f.stem] = f.read_text(encoding='utf-8')
            except Exception:
                pass
    return examples

EXAMPLES = load_examples()

def get_modules():
    try:
        from lexer import Lexer
        from parser import Parser
        from semantic import SemanticAnalyzer
        from codegen import CodeGenerator
        return {
            'lexer': Lexer,
            'parser': Parser,
            'semantic': SemanticAnalyzer,
            'codegen': CodeGenerator,
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
    return jsonify({"status": "ok", "modules": ["lexer", "parser", "semantic", "codegen"]})

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
    if hasattr(report, 'get_diagnostics'):
        diagnostics = report.get_diagnostics()
        if isinstance(diagnostics, dict):
            all_entries.extend([(e, "error") for e in diagnostics.get("errors", [])])
            all_entries.extend([(w, "warning") for w in diagnostics.get("warnings", [])])
    elif hasattr(report, 'errors') and isinstance(report.errors, list):
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
            report = semantic
            codegen = mods['codegen'](ast, None)
            ir = codegen.generate_ir()
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
                "traceback": traceback.format_exc(),
                "line": getattr(e, 'line', 0),
                "column": getattr(e, 'column', 0),
                "code": getattr(e, 'code', type(e).__name__)
            }
            result["done"] = True

    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()
    thread.join(timeout=timeout_sec)

    if thread.is_alive():
        raise CompilationTimeout(f"La compilation a depasse le delai de {timeout_sec} secondes.")

    if result["error"]:
        err = result["error"]
        exc = type(err["type"], (Exception,), {})(err["msg"])
        exc.traceback = err.get("traceback", "")
        exc.error_type = err["type"]
        exc.line = err.get("line", 0)
        exc.column = err.get("column", 0)
        exc.code = err.get("code", err["type"])
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
            "warnings": [],
            "tokens": [],
            "ast": None,
            "ir": None,
            "semantic_report": None,
            "compilation_details": None
        })
    try:
        comp_result = compile_with_timeout(source, step_mode, timeout_sec=8)
        tokens = comp_result["tokens"]
        ast = comp_result["ast"]
        ir = comp_result["ir"]
        report = comp_result["report"]
        parser_errors = comp_result.get("parser_errors", [])
        errors, warnings = [], []

        if report and hasattr(report, 'get_diagnostics'):
            diagnostics = report.get_diagnostics()
            if isinstance(diagnostics, dict):
                for e in diagnostics.get("errors", []):
                    entry = _error_to_dict(e, "error")
                    entry["pass"] = ""
                    errors.append(entry)
                for w in diagnostics.get("warnings", []):
                    entry = _error_to_dict(w, "warning")
                    entry["pass"] = ""
                    warnings.append(entry)
        elif report:
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
            }
        })
    except CompilationTimeout as te:
        return jsonify({
            "success": False,
            "errors": [{"message": str(te), "line": 0, "col": 0, "severity": "error", "code": "CompilationTimeout"}],
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
        err_line = getattr(e, 'line', 0)
        err_col = getattr(e, 'column', 0)
        err_code = getattr(e, 'code', err_type)
        
        status_code = 200 if err_type in ('LexicalError', 'SyntaxError', 'SemanticError', 'GenerationError', 'QLSyntaxError', 'QuestLangError') else 500
        
        pipeline = [
            {"step": "Lexical", "status": "ok", "time": "-"},
            {"step": "Syntaxique", "status": "ok", "time": "-"},
            {"step": "Semantique", "status": "ok", "time": "-"},
            {"step": "Generation", "status": "ok", "time": "-"}
        ]
        
        if err_type == 'LexicalError':
            pipeline[0]["status"] = "error"
            pipeline[1]["status"] = "pending"
            pipeline[2]["status"] = "pending"
            pipeline[3]["status"] = "pending"
        elif err_type in ('SyntaxError', 'QLSyntaxError'):
            pipeline[1]["status"] = "error"
            pipeline[2]["status"] = "pending"
            pipeline[3]["status"] = "pending"
        elif err_type == 'SemanticError':
            pipeline[2]["status"] = "error"
            pipeline[3]["status"] = "pending"
        elif err_type == 'GenerationError':
            pipeline[3]["status"] = "error"
        else:
            for p in pipeline:
                p["status"] = "error"
                
        compilation_details = {
            "pipeline": pipeline,
            "total_time": "-",
            "tokens_count": 0,
            "ast_nodes": 0
        }
        
        return jsonify({
            "success": False,
            "errors": [{"message": str(e), "line": err_line, "col": err_col, "severity": "error", "code": err_code}],
            "warnings": [],
            "tokens": [],
            "ast": None,
            "ir": None,
            "semantic_report": None,
            "compilation_details": compilation_details,
            "_debug": {"traceback": tb}
        }), status_code

@app.route("/api/report/html", methods=["POST"])
def report_html():
    data = request.get_json() or {}
    source = data.get("code", "")
    if not source or not source.strip():
        return jsonify({"success": False, "error": "Code source vide"}), 400
    try:
        mods = get_modules()
        if isinstance(mods, dict) and "error" in mods:
            return jsonify({"success": False, "error": mods['error']}), 500
        
        lexer = mods['lexer'](source)
        tokens = lexer.tokenize()
        parser = mods['parser'](tokens)
        ast = parser.parse()
        semantic = mods['semantic']()
        semantic.analyze(ast)
        
        diagnostics = semantic.get_diagnostics() if hasattr(semantic, 'get_diagnostics') else None
        codegen = mods['codegen'](ast, diagnostics)
        html_content = codegen.to_html()
        
        return jsonify({"success": True, "html": html_content})
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "traceback": traceback.format_exc()}), 500

@app.route("/api/examples")
def list_examples():
    return jsonify([{"name": name, "content": content} for name, content in EXAMPLES.items()])

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)