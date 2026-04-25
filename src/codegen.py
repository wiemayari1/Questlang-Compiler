# -*- coding: utf-8 -*-
"""
Generateur de code pour QuestLang v2.
Produit une representation intermediaire JSON et un rapport HTML.
"""

import json
import html as html_module
from ast_nodes import *

class CodeGenerator:
    """
    Generateur de code intermediaire et de rapports.
    Produit un fichier .ir.json et un fichier .report.html.
    """

    def __init__(self, program: ProgramNode, diagnostics=None):
        self.program = program
        self.diagnostics = diagnostics or {"errors": [], "warnings": [], "infos": [],
                                           "error_count": 0, "warning_count": 0, "info_count": 0}

    def generate_ir(self) -> dict:
        """Genere la representation intermediaire JSON."""
        ir = {
            "questlang_version": "2.0",
            "compilation_status": "OK" if self.diagnostics["error_count"] == 0 else "ERROR",
            "world": self._gen_world(),
            "quests": self._gen_quests(),
            "items": self._gen_items(),
            "npcs": self._gen_npcs(),
            "functions": self._gen_functions(),
            "diagnostics": self.diagnostics
        }
        return ir

    def to_json(self, indent=2) -> str:
        """Convertit l'IR en chaine JSON formatee."""
        ir = self.generate_ir()
        return json.dumps(ir, indent=indent, ensure_ascii=False, default=str)

    def to_html(self) -> str:
        """Genere un rapport HTML complet avec graphe de dependances."""
        ir = self.generate_ir()

        # Construire le graphe de dependances en DOT
        dot_graph = self._build_dot_graph()

        # Statistiques
        stats = self._build_stats()

        # Diagnostics HTML
        diagnostics_html = self._build_diagnostics_html()

        # Quetes HTML
        quests_html = self._build_quests_html()

        # Items HTML
        items_html = self._build_items_html()

        # NPCs HTML
        npcs_html = self._build_npcs_html()

        return f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>QuestLang - Rapport de Compilation</title>
    <style>
        :root {{
            --bg-primary: #1a1a2e;
            --bg-secondary: #16213e;
            --bg-card: #0f3460;
            --accent: #e94560;
            --accent-green: #16c79a;
            --accent-gold: #f4a261;
            --text-primary: #eaeaea;
            --text-secondary: #a0a0a0;
            --border: #2a2a4a;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        header {{
            background: var(--bg-secondary);
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
            border-left: 5px solid var(--accent);
        }}
        header h1 {{ font-size: 2.2em; margin-bottom: 10px; }}
        header .subtitle {{ color: var(--text-secondary); font-size: 1.1em; }}
        .status {{
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
            margin-top: 15px;
        }}
        .status.ok {{ background: var(--accent-green); color: #000; }}
        .status.error {{ background: var(--accent); color: #fff; }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: var(--bg-card);
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            border: 1px solid var(--border);
        }}
        .stat-card .number {{
            font-size: 2.5em;
            font-weight: bold;
            color: var(--accent);
        }}
        .stat-card .label {{ color: var(--text-secondary); font-size: 0.9em; }}

        .section {{
            background: var(--bg-secondary);
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 25px;
            border: 1px solid var(--border);
        }}
        .section h2 {{
            color: var(--accent-gold);
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid var(--border);
        }}

        .diagnostic {{
            padding: 12px 15px;
            margin: 8px 0;
            border-radius: 8px;
            border-left: 4px solid;
        }}
        .diagnostic.error {{ background: rgba(233, 69, 96, 0.1); border-color: var(--accent); }}
        .diagnostic.warning {{ background: rgba(244, 162, 97, 0.1); border-color: var(--accent-gold); }}
        .diagnostic.info {{ background: rgba(22, 199, 154, 0.1); border-color: var(--accent-green); }}
        .diagnostic .code {{ font-weight: bold; font-family: monospace; }}
        .diagnostic .msg {{ margin-left: 10px; }}
        .diagnostic .loc {{ color: var(--text-secondary); font-size: 0.85em; margin-left: 10px; }}

        .quest-card {{
            background: var(--bg-card);
            border-radius: 10px;
            padding: 20px;
            margin: 15px 0;
            border-left: 4px solid var(--accent);
        }}
        .quest-card.start {{ border-left-color: var(--accent-green); }}
        .quest-card.final {{ border-left-color: var(--accent-gold); }}
        .quest-card h3 {{ color: var(--text-primary); margin-bottom: 10px; }}
        .quest-card .badge {{
            display: inline-block;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.75em;
            margin-right: 5px;
        }}
        .badge.start {{ background: var(--accent-green); color: #000; }}
        .badge.final {{ background: var(--accent-gold); color: #000; }}
        .badge.normal {{ background: var(--border); color: var(--text-secondary); }}

        .resource-tag {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 0.85em;
            margin: 3px;
        }}
        .resource-tag.gold {{ background: #d4a017; color: #000; }}
        .resource-tag.xp {{ background: #4a90d9; color: #fff; }}
        .resource-tag.item {{ background: #8e44ad; color: #fff; }}
        .resource-tag.cost {{ background: #c0392b; color: #fff; }}

        .item-card, .npc-card {{
            background: var(--bg-card);
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
        }}

        .graph-container {{
            background: #fff;
            border-radius: 10px;
            padding: 20px;
            overflow-x: auto;
        }}
        .graph-container svg {{ max-width: 100%; }}

        .code-block {{
            background: #0d1117;
            border-radius: 8px;
            padding: 15px;
            overflow-x: auto;
            font-family: 'Consolas', monospace;
            font-size: 0.9em;
            color: #c9d1d9;
        }}

        footer {{
            text-align: center;
            padding: 20px;
            color: var(--text-secondary);
            font-size: 0.85em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>QuestLang</h1>
            <p class="subtitle">Rapport de compilation - Analyse complete du monde RPG</p>
            <span class="status {'ok' if ir['compilation_status'] == 'OK' else 'error'}">
                {'Compilation reussie' if ir['compilation_status'] == 'OK' else 'Erreurs detectees'}
            </span>
        </header>

        <div class="stats-grid">
            {stats}
        </div>

        <div class="section">
            <h2>Diagnostics</h2>
            {diagnostics_html}
        </div>

        <div class="section">
            <h2>Graphe de dependances</h2>
            <div class="graph-container">
                {dot_graph}
            </div>
        </div>

        <div class="section">
            <h2>Quetes</h2>
            {quests_html}
        </div>

        <div class="section">
            <h2>Items</h2>
            {items_html}
        </div>

        <div class="section">
            <h2>Personnages non-joueurs</h2>
            {npcs_html}
        </div>

        <div class="section">
            <h2>Representation intermediaire (IR)</h2>
            <pre class="code-block">{html_module.escape(json.dumps(ir, indent=2, ensure_ascii=False, default=str))}</pre>
        </div>

        <footer>
            QuestLang Compiler v2.0 - Projet de Techniques de Compilation 2024-2025
        </footer>
    </div>
</body>
</html>"""

    def _gen_world(self):
        """Genere la partie world de l'IR."""
        if not self.program.world:
            return None
        w = self.program.world
        result = {"name": w.name}
        for key, val in w.properties.items():
            result[key] = self._expr_to_ir(val)
        result["variables"] = [v.name for v in w.variables]
        return result

    def _gen_quests(self):
        """Genere la liste des quetes pour l'IR."""
        quests = []
        for name, quest in self.program.quests.items():
            q = {
                "id": name,
                "is_start": quest.is_start,
                "is_final": quest.is_final,
                "line": quest.line,
                "column": quest.column
            }
            for key, val in quest.properties.items():
                q[key] = self._expr_to_ir(val)
            if quest.script:
                q["has_script"] = True
            quests.append(q)
        return quests

    def _gen_items(self):
        """Genere la liste des items pour l'IR."""
        items = []
        for name, item in self.program.items.items():
            i = {"id": name, "line": item.line, "column": item.column}
            for key, val in item.properties.items():
                i[key] = self._expr_to_ir(val)
            items.append(i)
        return items

    def _gen_npcs(self):
        """Genere la liste des PNJ pour l'IR."""
        npcs = []
        for name, npc in self.program.npcs.items():
            n = {"id": name, "line": npc.line, "column": npc.column}
            for key, val in npc.properties.items():
                n[key] = self._expr_to_ir(val)
            npcs.append(n)
        return npcs

    def _gen_functions(self):
        """Genere la liste des fonctions pour l'IR."""
        funcs = []
        for name, func in self.program.functions.items():
            funcs.append({
                "id": name,
                "params": func.params,
                "line": func.line,
                "column": func.column
            })
        return funcs

    def _expr_to_ir(self, node):
        """Convertit un noeud d'expression en valeur IR."""
        if node is None:
            return None
        if isinstance(node, LiteralNode):
            return node.value
        if isinstance(node, IdentifierNode):
            return node.name
        if isinstance(node, BinaryOpNode):
            return {
                "op": node.op,
                "left": self._expr_to_ir(node.left),
                "right": self._expr_to_ir(node.right)
            }
        if isinstance(node, UnaryOpNode):
            return {"op": node.op, "operand": self._expr_to_ir(node.operand)}
        if isinstance(node, ListLiteralNode):
            return [self._expr_to_ir(e) for e in node.elements]
        if isinstance(node, RewardListNode):
            return [self._resource_to_ir(r) for r in node.rewards]
        if isinstance(node, IdListNode):
            return node.ids
        if isinstance(node, ResourceNode):
            return self._resource_to_ir(node)
        if isinstance(node, CallExprNode):
            return {"call": node.name, "args": [self._expr_to_ir(a) for a in node.args]}
        if isinstance(node, IndexNode):
            return {"index": self._expr_to_ir(node.target), "of": self._expr_to_ir(node.index)}
        if isinstance(node, PropertyAccessNode):
            return {"access": self._expr_to_ir(node.target), "prop": node.property_name}
        return str(node)

    def _resource_to_ir(self, res: ResourceNode):
        """Convertit une ressource en dict IR."""
        result = {"type": res.resource_type, "name": res.name}
        if res.amount is not None:
            result["amount"] = self._expr_to_ir(res.amount)
        if res.quantity is not None:
            result["quantity"] = self._expr_to_ir(res.quantity)
        return result

    def _build_stats(self):
        """Construit les cartes de statistiques."""
        world_name = self.program.world.name if self.program.world else "N/A"
        quest_count = len(self.program.quests)
        item_count = len(self.program.items)
        npc_count = len(self.program.npcs)
        func_count = len(self.program.functions)
        err_count = self.diagnostics["error_count"]
        warn_count = self.diagnostics["warning_count"]

        cards = [
            ("Monde", world_name),
            ("Quetes", quest_count),
            ("Items", item_count),
            ("PNJ", npc_count),
            ("Fonctions", func_count),
            ("Erreurs", err_count),
            ("Avertissements", warn_count),
        ]

        html = ""
        for label, value in cards:
            html += f"""
            <div class="stat-card">
                <div class="number">{value}</div>
                <div class="label">{label}</div>
            </div>"""
        return html

    def _build_diagnostics_html(self):
        """Construit la section diagnostics en HTML."""
        if not any([self.diagnostics["errors"], self.diagnostics["warnings"], self.diagnostics["infos"]]):
            return '<p style="color: var(--text-secondary);">Aucun diagnostic a afficher.</p>'

        html = ""
        for d in self.diagnostics["errors"]:
            html += self._diag_to_html(d, "error")
        for d in self.diagnostics["warnings"]:
            html += self._diag_to_html(d, "warning")
        for d in self.diagnostics["infos"]:
            html += self._diag_to_html(d, "info")
        return html

    def _diag_to_html(self, d, severity):
        loc = f"ligne {d.get('line', '?')}, col {d.get('column', '?')}" if d.get('line') else ""
        return f"""
        <div class="diagnostic {severity}">
            <span class="code">[{d['code']}]</span>
            <span class="msg">{html_module.escape(d['message'])}</span>
            <span class="loc">{loc}</span>
        </div>"""

    def _build_quests_html(self):
        """Construit la section quetes en HTML."""
        if not self.program.quests:
            return '<p style="color: var(--text-secondary);">Aucune quete definie.</p>'

        html = ""
        for name, quest in self.program.quests.items():
            classes = "quest-card"
            badges = '<span class="badge normal">Quete</span>'
            if quest.is_start:
                classes += " start"
                badges = '<span class="badge start">DEPART</span>' + badges
            if quest.is_final:
                classes += " final"
                badges = '<span class="badge final">FINALE</span>' + badges

            title = quest.properties.get("title")
            title_str = self._expr_to_string(title) if title else name
            desc = quest.properties.get("desc")
            desc_str = self._expr_to_string(desc) if desc else ""

            rewards_html = self._rewards_to_html(quest.properties.get("rewards"), "Recompenses")
            costs_html = self._rewards_to_html(quest.properties.get("costs"), "Couts")
            unlocks = quest.properties.get("unlocks")
            unlocks_html = ""
            if unlocks and isinstance(unlocks, IdListNode) and unlocks.ids:
                unlocks_html = f'<p><strong>Debloque:</strong> {", ".join(unlocks.ids)}</p>'

            requires = quest.properties.get("requires")
            requires_html = ""
            if requires and isinstance(requires, IdListNode) and requires.ids:
                requires_html = f'<p><strong>Requiert:</strong> {", ".join(requires.ids)}</p>'

            html += f"""
            <div class="{classes}">
                <h3>{html_module.escape(title_str)} <span style="font-size:0.7em;color:var(--text-secondary)">({name})</span></h3>
                {badges}
                <p style="color:var(--text-secondary);margin:10px 0;">{html_module.escape(desc_str)}</p>
                {requires_html}
                {rewards_html}
                {costs_html}
                {unlocks_html}
                <p style="font-size:0.8em;color:var(--text-secondary);margin-top:10px;">Ligne {quest.line}</p>
            </div>"""
        return html

    def _build_items_html(self):
        """Construit la section items en HTML."""
        if not self.program.items:
            return '<p style="color: var(--text-secondary);">Aucun item defini.</p>'

        html = ""
        for name, item in self.program.items.items():
            title = item.properties.get("title")
            title_str = self._expr_to_string(title) if title else name
            value = item.properties.get("value")
            value_str = f"Valeur: {self._expr_to_string(value)}" if value else ""
            itype = item.properties.get("type", "misc")
            stackable = item.properties.get("stackable", False)

            html += f"""
            <div class="item-card">
                <strong>{html_module.escape(title_str)}</strong> <span style="color:var(--text-secondary)">({name})</span>
                <p style="font-size:0.9em;color:var(--text-secondary);">
                    Type: {itype} | {value_str} | Empilable: {'Oui' if stackable else 'Non'}
                </p>
            </div>"""
        return html

    def _build_npcs_html(self):
        """Construit la section PNJ en HTML."""
        if not self.program.npcs:
            return '<p style="color: var(--text-secondary);">Aucun PNJ defini.</p>'

        html = ""
        for name, npc in self.program.npcs.items():
            title = npc.properties.get("title")
            title_str = self._expr_to_string(title) if title else name
            location = npc.properties.get("location", "Inconnu")
            gives = npc.properties.get("gives_quest")
            gives_str = ""
            if gives and isinstance(gives, IdListNode) and gives.ids:
                gives_str = f"Donne les quetes: {', '.join(gives.ids)}"

            html += f"""
            <div class="npc-card">
                <strong>{html_module.escape(title_str)}</strong> <span style="color:var(--text-secondary)">({name})</span>
                <p style="font-size:0.9em;color:var(--text-secondary);">
                    Lieu: {location} | {gives_str}
                </p>
            </div>"""
        return html

    def _build_dot_graph(self):
        """Construit un graphe SVG de dependances entre quetes."""
        # Generer un graphe simple en SVG
        quests = list(self.program.quests.keys())
        if not quests:
            return "<p>Aucune quete a afficher.</p>"

        # Positionner les noeuds en cercle
        import math
        n = len(quests)
        radius = 150
        center_x, center_y = 200, 200
        positions = {}

        for i, q in enumerate(quests):
            angle = 2 * math.pi * i / n - math.pi / 2
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            positions[q] = (x, y)

        svg_elements = []

        # Fleches (edges)
        for qname, quest in self.program.quests.items():
            unlocks = quest.properties.get("unlocks")
            if unlocks and isinstance(unlocks, IdListNode):
                for target in unlocks.ids:
                    if target in positions:
                        x1, y1 = positions[qname]
                        x2, y2 = positions[target]
                        svg_elements.append(
                            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                            f'stroke="#e94560" stroke-width="2" marker-end="url(#arrowhead)" />'
                        )

        # Noeuds
        for qname, (x, y) in positions.items():
            quest = self.program.quests[qname]
            color = "#16c79a" if quest.is_start else ("#f4a261" if quest.is_final else "#0f3460")
            svg_elements.append(
                f'<circle cx="{x}" cy="{y}" r="30" fill="{color}" stroke="#eaeaea" stroke-width="2" />'
            )
            svg_elements.append(
                f'<text x="{x}" y="{y+5}" text-anchor="middle" fill="#fff" font-size="11" font-family="sans-serif">{qname[:8]}</text>'
            )

        svg_content = "\n".join(svg_elements)

        return f"""<svg width="400" height="400" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="28" refY="3.5" orient="auto">
                    <polygon points="0 0, 10 3.5, 0 7" fill="#e94560" />
                </marker>
            </defs>
            {svg_content}
        </svg>"""

    def _rewards_to_html(self, rewards, label):
        """Convertit une liste de recompenses en HTML."""
        if not rewards or not isinstance(rewards, RewardListNode) or not rewards.rewards:
            return ""

        tags = ""
        for r in rewards.rewards:
            if r.resource_type == "gold":
                amount = self._expr_to_string(r.amount) if r.amount else "?"
                tags += f'<span class="resource-tag gold">{amount} or</span>'
            elif r.resource_type == "xp":
                amount = self._expr_to_string(r.amount) if r.amount else "?"
                tags += f'<span class="resource-tag xp">{amount} XP</span>'
            elif r.resource_type == "item":
                qty = self._expr_to_string(r.quantity) if r.quantity else "1"
                tags += f'<span class="resource-tag item">{qty}x {r.name}</span>'

        return f'<p><strong>{label}:</strong> {tags}</p>'

    def _expr_to_string(self, node):
        """Convertit une expression en chaine lisible."""
        if node is None:
            return ""
        if isinstance(node, LiteralNode):
            return str(node.value)
        if isinstance(node, IdentifierNode):
            return node.name
        if isinstance(node, BinaryOpNode):
            return f"{self._expr_to_string(node.left)} {node.op} {self._expr_to_string(node.right)}"
        if isinstance(node, ResourceNode):
            if node.resource_type in ["gold", "xp"]:
                return f"{self._expr_to_string(node.amount)} {node.resource_type}"
            return f"{self._expr_to_string(node.quantity)}x {node.name}"
        return str(node)
