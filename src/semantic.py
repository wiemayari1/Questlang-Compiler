# -*- coding: utf-8 -*-
"""
Analyse semantique pour QuestLang v2.
4 passes d'analyse :
 1. Table des symboles (symboles, doublons, references indefinies)
 2. Accessibilite (DFS depuis start_quest)
 3. Economie (analyse de flux d'items/or)
 4. Cycles (Tarjan SCC pour detecter les deadlocks narratifs)
"""

from collections import defaultdict, deque
from typing import List, Dict, Set, Tuple, Optional
from ast_nodes import *
from errors import SemanticError, ErrorReporter

class SymbolTable:
    """Table des symboles pour toutes les entites du monde."""
    def __init__(self):
        self.quests: Dict[str, QuestNode] = {}
        self.items: Dict[str, ItemNode] = {}
        self.npcs: Dict[str, NPCNode] = {}
        self.functions: Dict[str, FunctionNode] = {}
        self.variables: Dict[str, VarDeclNode] = {}
        self.world: Optional[WorldNode] = None

    def add_quest(self, quest: QuestNode):
        if quest.name in self.quests:
            existing = self.quests[quest.name]
            raise SemanticError(
                f"Quete '{quest.name}' deja definie",
                quest.line, quest.column
            )
        self.quests[quest.name] = quest

    def add_item(self, item: ItemNode):
        if item.name in self.items:
            existing = self.items[item.name]
            raise SemanticError(
                f"Item '{item.name}' deja defini",
                item.line, item.column
            )
        self.items[item.name] = item

    def add_npc(self, npc: NPCNode):
        if npc.name in self.npcs:
            existing = self.npcs[npc.name]
            raise SemanticError(
                f"PNJ '{npc.name}' deja defini",
                npc.line, npc.column
            )
        self.npcs[npc.name] = npc

    def add_function(self, func: FunctionNode):
        if func.name in self.functions:
            existing = self.functions[func.name]
            raise SemanticError(
                f"Fonction '{func.name}' deja definie",
                func.line, func.column
            )
        self.functions[func.name] = func

    def add_variable(self, var: VarDeclNode):
        """CORRECTION: Detection des variables dupliquees."""
        if var.name in self.variables:
            raise SemanticError(
                f"Variable '{var.name}' deja definie",
                var.line, var.column
            )
        self.variables[var.name] = var

    def has_quest(self, name: str) -> bool:
        return name in self.quests

    def has_item(self, name: str) -> bool:
        return name in self.items

    def has_npc(self, name: str) -> bool:
        return name in self.npcs

    def has_function(self, name: str) -> bool:
        return name in self.functions


class SemanticAnalyzer:
    """
    Analyseur semantique a 4 passes.
    Chaque passe detecte une categorie specifique d'erreurs.
    """

    def __init__(self):
        self.symbol_table = SymbolTable()
        self.reporter = ErrorReporter()
        self.program: Optional[ProgramNode] = None

    def analyze(self, program: ProgramNode) -> bool:
        """Execute les 4 passes d'analyse semantique."""
        self.program = program
        self.reporter = ErrorReporter()
        self.symbol_table = SymbolTable()

        # Passe 1: Table des symboles
        self.pass1_symbols()

        # Passe 2: Accessibilite (toujours executee pour collecter max d'erreurs)
        self.pass2_reachability()

        # Passe 3: Economie
        self.pass3_economy()

        # Passe 4: Cycles (Tarjan SCC)
        self.pass4_cycles()

        return not self.reporter.has_errors()

    # ============================================================
    # PASSE 1: TABLE DES SYMBOLES
    # ============================================================
    def pass1_symbols(self):
        """
        Passe 1: Construction de la table des symboles.
        Detecte: doublons, references indefinies, types manquants.
        """
        # Enregistrer les declarations
        for decl in self.program.declarations:
            if isinstance(decl, WorldNode):
                if self.symbol_table.world is not None:
                    self.reporter.add_error(
                        "DUPLICATE_WORLD",
                        "Le monde est defini plusieurs fois",
                        decl.line, decl.column
                    )
                else:
                    self.symbol_table.world = decl
                for var in decl.variables:
                    try:
                        self.symbol_table.add_variable(var)
                    except SemanticError as e:
                        self.reporter.add_error("DUPLICATE_VAR", e.message, e.line, e.column)

            elif isinstance(decl, QuestNode):
                try:
                    self.symbol_table.add_quest(decl)
                except SemanticError as e:
                    self.reporter.add_error("DUPLICATE_QUEST", e.message, e.line, e.column)

            elif isinstance(decl, ItemNode):
                try:
                    self.symbol_table.add_item(decl)
                except SemanticError as e:
                    self.reporter.add_error("DUPLICATE_ITEM", e.message, e.line, e.column)

            elif isinstance(decl, NPCNode):
                try:
                    self.symbol_table.add_npc(decl)
                except SemanticError as e:
                    self.reporter.add_error("DUPLICATE_NPC", e.message, e.line, e.column)

            elif isinstance(decl, FunctionNode):
                try:
                    self.symbol_table.add_function(decl)
                except SemanticError as e:
                    self.reporter.add_error("DUPLICATE_FUNC", e.message, e.line, e.column)

        # Verifier les references
        for decl in self.program.declarations:
            if isinstance(decl, WorldNode):
                self._check_world_refs(decl)
            elif isinstance(decl, QuestNode):
                self._check_quest_refs(decl)
            elif isinstance(decl, NPCNode):
                self._check_npc_refs(decl)
            elif isinstance(decl, FunctionNode):
                self._check_function_body(decl)

        # Verifier les items non declares dans les recompenses/couts
        for decl in self.program.declarations:
            if isinstance(decl, QuestNode):
                self._check_item_refs_in_quest(decl)

    def _check_world_refs(self, world: WorldNode):
        """Verifie que start_quest et win_condition existent."""
        if "start" in world.properties:
            start_val = self._extract_string(world.properties["start"])
            if start_val and not self.symbol_table.has_quest(start_val):
                self.reporter.add_error(
                    "UNDEF_START_QUEST",
                    f"La quete de depart '{start_val}' n'existe pas",
                    world.line, world.column
                )

        if "win_condition" in world.properties:
            win_val = self._extract_string(world.properties["win_condition"])
            if win_val and not self.symbol_table.has_quest(win_val):
                self.reporter.add_error(
                    "UNDEF_WIN_COND",
                    f"La condition de victoire '{win_val}' n'existe pas",
                    world.line, world.column
                )

    def _check_quest_refs(self, quest: QuestNode):
        """Verifie les references dans une quete."""
        props = quest.properties

        # requires -> quetes existantes
        if "requires" in props and isinstance(props["requires"], IdListNode):
            for qname in props["requires"].ids:
                if not self.symbol_table.has_quest(qname):
                    self.reporter.add_error(
                        "UNDEF_QUEST_REF",
                        f"La quete '{quest.name}' requiert une quete inexistante '{qname}'",
                        quest.line, quest.column
                    )

        # unlocks -> quetes existantes
        if "unlocks" in props and isinstance(props["unlocks"], IdListNode):
            for qname in props["unlocks"].ids:
                if not self.symbol_table.has_quest(qname):
                    self.reporter.add_error(
                        "UNDEF_UNLOCK_REF",
                        f"La quete '{quest.name}' debloque une quete inexistante '{qname}'",
                        quest.line, quest.column
                    )

        # Verifier le script
        if quest.script:
            self._check_script_refs(quest.script, quest.name)

    def _check_npc_refs(self, npc: NPCNode):
        """Verifie que les quetes donnees par le PNJ existent."""
        props = npc.properties
        if "gives_quest" in props and isinstance(props["gives_quest"], IdListNode):
            for qname in props["gives_quest"].ids:
                if not self.symbol_table.has_quest(qname):
                    self.reporter.add_error(
                        "UNDEF_QUEST_REF",
                        f"Le PNJ '{npc.name}' donne une quete inexistante '{qname}'",
                        npc.line, npc.column
                    )

    def _check_item_refs_in_quest(self, quest: QuestNode):
        """Verifie que les items dans rewards/couts existent."""
        for key in ["rewards", "costs"]:
            if key in quest.properties:
                rewards = quest.properties[key]
                if isinstance(rewards, RewardListNode):
                    for r in rewards.rewards:
                        if r.resource_type == "item" and not self.symbol_table.has_item(r.name):
                            self.reporter.add_error(
                                "UNDEF_ITEM_REF",
                                f"Item '{r.name}' utilise dans la quete '{quest.name}' n'existe pas",
                                quest.line, quest.column
                            )

    def _check_function_body(self, func: FunctionNode):
        """Verifie les references dans le corps d'une fonction."""
        if func.body:
            self._check_script_refs(func.body, func.name)

    def _check_script_refs(self, block: BlockNode, context: str):
        """Verifie les references dans un bloc d'instructions."""
        for stmt in block.statements:
            self._check_stmt_refs(stmt, context)

    def _check_stmt_refs(self, stmt, context: str):
        """Verifie les references dans une instruction."""
        if isinstance(stmt, CallStmtNode):
            call = stmt.call_expr
            if not self.symbol_table.has_function(call.name):
                self.reporter.add_error(
                    "UNDEF_FUNC_REF",
                    f"Appel a une fonction inexistante '{call.name}'",
                    call.line, call.column
                )
        elif isinstance(stmt, IfNode):
            self._check_script_refs(stmt.then_block, context)
            if stmt.else_block:
                self._check_script_refs(stmt.else_block, context)
        elif isinstance(stmt, WhileNode):
            self._check_script_refs(stmt.body, context)
        elif isinstance(stmt, ForNode):
            self._check_script_refs(stmt.body, context)
        elif isinstance(stmt, BlockNode):
            self._check_script_refs(stmt, context)

    def _extract_string(self, node):
        """Extrait une valeur string d'un noeud AST."""
        if isinstance(node, LiteralNode) and isinstance(node.value, str):
            return node.value
        if isinstance(node, IdentifierNode):
            return node.name
        return None

    # ============================================================
    # PASSE 2: ACCESSIBILITE (DFS)
    # ============================================================
    def pass2_reachability(self):
        """
        Passe 2: Accessibilite des quetes depuis start_quest.
        Algorithme: DFS iteratif. Complexite O(V + E).
        Detecte: quetes inaccessibles, fin inaccessible.
        """
        if not self.symbol_table.world:
            self.reporter.add_warning(
                "NO_WORLD",
                "Aucun bloc 'world' defini. Impossible de verifier l'accessibilite.",
                1, 1
            )
            return

        world = self.symbol_table.world
        start_quest = None
        win_condition = None

        if "start" in world.properties:
            start_quest = self._extract_string(world.properties["start"])

        if "win_condition" in world.properties:
            win_condition = self._extract_string(world.properties["win_condition"])

        if not start_quest:
            # Si pas de start explicite, prendre la premiere quete
            if self.symbol_table.quests:
                start_quest = list(self.symbol_table.quests.keys())[0]
                self.reporter.add_info(
                    "DEFAULT_START",
                    f"Aucune quete de depart specifiee. Utilisation de '{start_quest}' par defaut."
                )
            else:
                self.reporter.add_error(
                    "NO_START_QUEST",
                    "Aucune quete de depart definie",
                    world.line, world.column
                )
                return

        if not self.symbol_table.has_quest(start_quest):
            return  # Deja signale en passe 1

        # DFS iteratif
        visited = set()
        stack = [start_quest]

        while stack:
            qname = stack.pop()
            if qname in visited:
                continue
            visited.add(qname)

            quest = self.symbol_table.quests.get(qname)
            if not quest:
                continue

            # Ajouter les quetes debloquees
            if "unlocks" in quest.properties and isinstance(quest.properties["unlocks"], IdListNode):
                for next_q in quest.properties["unlocks"].ids:
                    if next_q not in visited:
                        stack.append(next_q)

        # Quetes inaccessibles
        for qname in self.symbol_table.quests:
            if qname not in visited:
                quest = self.symbol_table.quests[qname]
                self.reporter.add_error(
                    "UNREACHABLE_QUEST",
                    f"Quete '{qname}' inaccessible depuis la quete de depart",
                    quest.line, quest.column
                )

        # Verifier accessibilite de la condition de victoire
        if win_condition and win_condition not in visited:
            self.reporter.add_error(
                "WIN_UNREACHABLE",
                f"La condition de victoire '{win_condition}' est inaccessible",
                world.line, world.column
            )
        elif win_condition:
            self.reporter.add_info(
                "WIN_REACHABLE",
                f"La condition de victoire '{win_condition}' est atteignable"
            )

        # Quetes accessibles sans recompense
        for qname in visited:
            quest = self.symbol_table.quests.get(qname)
            if quest:
                has_reward = False
                if "rewards" in quest.properties:
                    rewards = quest.properties["rewards"]
                    if isinstance(rewards, RewardListNode) and rewards.rewards:
                        has_reward = True
                if not has_reward and not quest.properties.get("is_final", False):
                    self.reporter.add_warning(
                        "NO_REWARD",
                        f"Quete '{qname}' accessible sans recompense",
                        quest.line, quest.column
                    )

    # ============================================================
    # PASSE 3: ECONOMIE (ANALYSE DE FLUX)
    # ============================================================
    def pass3_economy(self):
        """
        Passe 3: Analyse economique du monde.
        Detecte: inflation/deflation d'or, deficit/surplus d'items.
        """
        item_production = defaultdict(float)  # item -> quantite produite
        item_consumption = defaultdict(float)  # item -> quantite consommee
        gold_injected = 0.0
        gold_consumed = 0.0

        for qname, quest in self.symbol_table.quests.items():
            # Recompenses (production)
            if "rewards" in quest.properties:
                rewards = quest.properties["rewards"]
                if isinstance(rewards, RewardListNode):
                    for r in rewards.rewards:
                        if r.resource_type == "gold":
                            gold_injected += self._eval_expr(r.amount)
                        elif r.resource_type == "item":
                            item_production[r.name] += self._eval_expr(r.quantity)

            # Couts (consommation)
            if "costs" in quest.properties:
                costs = quest.properties["costs"]
                if isinstance(costs, RewardListNode):
                    for c in costs.rewards:
                        if c.resource_type == "gold":
                            gold_consumed += self._eval_expr(c.amount)
                        elif c.resource_type == "item":
                            item_consumption[c.name] += self._eval_expr(c.quantity)

        # Analyse des items
        all_items = set(item_production.keys()) | set(item_consumption.keys())
        for item_name in all_items:
            produced = item_production[item_name]
            consumed = item_consumption[item_name]

            if consumed > produced:
                self.reporter.add_error(
                    "ITEM_DEFICIT",
                    f"Item '{item_name}' consomme ({consumed}) plus que produit ({produced})",
                    1, 1
                )
            elif produced > consumed and consumed == 0:
                self.reporter.add_warning(
                    "ITEM_SURPLUS",
                    f"Item '{item_name}' produit ({produced}) sans jamais etre consomme",
                    1, 1
                )

        # Analyse de l'or
        if gold_consumed > 0:
            ratio = gold_injected / gold_consumed
            if ratio > 10:
                self.reporter.add_warning(
                    "GOLD_INFLATION",
                    f"Inflation d'or detectee: ratio injecte/consomme = {ratio:.2f}",
                    1, 1
                )
            elif ratio < 0.5:
                self.reporter.add_warning(
                    "GOLD_DEFLATION",
                    f"Deflation d'or detectee: ratio injecte/consomme = {ratio:.2f}",
                    1, 1
                )

    def _eval_expr(self, node) -> float:
        """Evalue une expression constante."""
        if isinstance(node, LiteralNode):
            if isinstance(node.value, (int, float)):
                return float(node.value)
            return 0.0
        if isinstance(node, BinaryOpNode):
            left = self._eval_expr(node.left)
            right = self._eval_expr(node.right)
            if node.op == '+':
                return left + right
            elif node.op == '-':
                return left - right
            elif node.op == '*':
                return left * right
            elif node.op == '/':
                return left / right if right != 0 else 0
            elif node.op == '^':
                return left ** right
        return 0.0

    # ============================================================
    # PASSE 4: CYCLES (TARJAN SCC)
    # ============================================================
    def pass4_cycles(self):
        """
        Passe 4: Detection de cycles avec Tarjan SCC.
        Algorithme de Tarjan pour les composantes fortement connexes.
        Complexite O(V + E).
        Detecte: deadlocks narratifs, boucles d'unlock, items morts, PNJ inutiles.
        """
        # Construire le graphe de dependances entre quetes
        graph = defaultdict(list)
        for qname, quest in self.symbol_table.quests.items():
            if "requires" in quest.properties and isinstance(quest.properties["requires"], IdListNode):
                for req in quest.properties["requires"].ids:
                    graph[qname].append(req)
            if "unlocks" in quest.properties and isinstance(quest.properties["unlocks"], IdListNode):
                for unlocked in quest.properties["unlocks"].ids:
                    graph[unlocked].append(qname)  # unlocked depend de qname

        # Tarjan SCC
        index_counter = [0]
        stack = []
        lowlinks = {}
        index = {}
        on_stack = {}
        sccs = []

        def strongconnect(v):
            index[v] = index_counter[0]
            lowlinks[v] = index_counter[0]
            index_counter[0] += 1
            stack.append(v)
            on_stack[v] = True

            for w in graph.get(v, []):
                if w not in index:
                    strongconnect(w)
                    lowlinks[v] = min(lowlinks[v], lowlinks[w])
                elif on_stack.get(w, False):
                    lowlinks[v] = min(lowlinks[v], index[w])

            if lowlinks[v] == index[v]:
                scc = []
                while True:
                    w = stack.pop()
                    on_stack[w] = False
                    scc.append(w)
                    if w == v:
                        break
                sccs.append(scc)

        for v in list(self.symbol_table.quests.keys()):
            if v not in index:
                strongconnect(v)

        # Analyser les SCC
        for scc in sccs:
            if len(scc) > 1:
                # Cycle detecte
                cycle_str = " -> ".join(scc) + " -> " + scc[0]
                # Verifier si c'est un deadlock (toutes les quetes du cycle se requierent mutuellement)
                is_deadlock = True
                for qname in scc:
                    quest = self.symbol_table.quests.get(qname)
                    if quest and "requires" in quest.properties:
                        reqs = quest.properties["requires"]
                        if isinstance(reqs, IdListNode):
                            if not any(r in scc for r in reqs.ids):
                                is_deadlock = False
                                break

                if is_deadlock:
                    self.reporter.add_error(
                        "DEADLOCK_CYCLE",
                        f"Deadlock narratif detecte: {cycle_str}",
                        1, 1
                    )
                else:
                    self.reporter.add_warning(
                        "UNLOCK_LOOP",
                        f"Boucle d'unlock detectee: {cycle_str}",
                        1, 1
                    )

        # Items morts (declares mais jamais utilises)
        used_items = set()
        for qname, quest in self.symbol_table.quests.items():
            for key in ["rewards", "costs"]:
                if key in quest.properties:
                    rewards = quest.properties[key]
                    if isinstance(rewards, RewardListNode):
                        for r in rewards.rewards:
                            if r.resource_type == "item":
                                used_items.add(r.name)

        for item_name in self.symbol_table.items:
            if item_name not in used_items:
                item = self.symbol_table.items[item_name]
                self.reporter.add_warning(
                    "DEAD_ITEM",
                    f"Item '{item_name}' declare mais jamais utilise",
                    item.line, item.column
                )

        # PNJ inutiles (qui ne donnent aucune quete)
        for npc_name, npc in self.symbol_table.npcs.items():
            gives = npc.properties.get("gives_quest")
            if not gives or (isinstance(gives, IdListNode) and not gives.ids):
                self.reporter.add_warning(
                    "IDLE_NPC",
                    f"PNJ '{npc_name}' ne donne aucune quete",
                    npc.line, npc.column
                )

    def get_diagnostics(self):
        """Retourne les diagnostics collectes."""
        return self.reporter.get_diagnostics()
