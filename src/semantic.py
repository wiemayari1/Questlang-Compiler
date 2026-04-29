# -*- coding: utf-8 -*-
"""
Analyse semantique pour QuestLang v2.
5 passes d'analyse :
 0. Type checking
 1. Table des symboles
 2. Accessibilite
 3. Economie
 4. Cycles
"""

import sys
sys.setrecursionlimit(10000)

from collections import defaultdict
from typing import List, Dict, Optional
from ast_nodes import *
from errors import SemanticError, ErrorReporter


class SymbolTable:
    def __init__(self):
        self.quests: Dict[str, QuestNode] = {}
        self.items: Dict[str, ItemNode] = {}
        self.npcs: Dict[str, NPCNode] = {}
        self.functions: Dict[str, FunctionNode] = {}
        self.variables: Dict[str, VarDeclNode] = {}
        self.world: Optional[WorldNode] = None
        self.scope_stack: List[Dict[str, VarDeclNode]] = []

    def push_scope(self):
        self.scope_stack.append({})

    def pop_scope(self):
        if self.scope_stack:
            self.scope_stack.pop()

    def add_variable(self, var: VarDeclNode):
        if var.name in self.variables:
            raise SemanticError(f"Variable '{var.name}' deja definie", var.line, var.column)
        self.variables[var.name] = var

    def add_local_variable(self, var: VarDeclNode):
        if self.scope_stack:
            current_scope = self.scope_stack[-1]
            if var.name in current_scope:
                raise SemanticError(f"Variable locale '{var.name}' deja definie dans ce bloc", var.line, var.column)
            current_scope[var.name] = var
        else:
            self.add_variable(var)

    def has_variable(self, name: str) -> bool:
        for scope in reversed(self.scope_stack):
            if name in scope:
                return True
        return name in self.variables

    def get_variable(self, name: str) -> Optional[VarDeclNode]:
        for scope in reversed(self.scope_stack):
            if name in scope:
                return scope[name]
        return self.variables.get(name)

    def add_quest(self, quest: QuestNode):
        if quest.name in self.quests:
            raise SemanticError(f"Quete '{quest.name}' deja definie", quest.line, quest.column)
        self.quests[quest.name] = quest

    def add_item(self, item: ItemNode):
        if item.name in self.items:
            raise SemanticError(f"Item '{item.name}' deja defini", item.line, item.column)
        self.items[item.name] = item

    def add_npc(self, npc: NPCNode):
        if npc.name in self.npcs:
            raise SemanticError(f"PNJ '{npc.name}' deja defini", npc.line, npc.column)
        self.npcs[npc.name] = npc

    def add_function(self, func: FunctionNode):
        if func.name in self.functions:
            raise SemanticError(f"Fonction '{func.name}' deja definie", func.line, func.column)
        self.functions[func.name] = func

    def has_quest(self, name: str) -> bool:
        return name in self.quests

    def has_item(self, name: str) -> bool:
        return name in self.items

    def has_npc(self, name: str) -> bool:
        return name in self.npcs

    def has_function(self, name: str) -> bool:
        return name in self.functions


class SemanticAnalyzer:
    def __init__(self):
        self.symbol_table = SymbolTable()
        self.reporter = ErrorReporter()
        self.program: Optional[ProgramNode] = None

    def analyze(self, program: ProgramNode) -> bool:
        self.program = program
        self.reporter = ErrorReporter()
        self.symbol_table = SymbolTable()

        self.pass0_typecheck()
        self.pass1_symbols()
        self.pass2_reachability()
        self.pass3_economy()
        self.pass4_cycles()

        return not self.reporter.has_errors()

    def pass0_typecheck(self):
        if not self.program:
            return
        for decl in self.program.declarations:
            if isinstance(decl, WorldNode):
                for var in decl.variables:
                    self._check_var_types(var)
            elif isinstance(decl, QuestNode):
                if decl.script:
                    self._check_block_types(decl.script, decl.name)
            elif isinstance(decl, FunctionNode):
                if decl.body:
                    self.symbol_table.push_scope()
                    for param in decl.params:
                        param_node = VarDeclNode(param, LiteralNode(None, decl.line, decl.column), None, decl.line, decl.column)
                        try:
                            self.symbol_table.add_local_variable(param_node)
                        except SemanticError:
                            pass
                    self._check_block_types(decl.body, decl.name)
                    self.symbol_table.pop_scope()

    def _check_var_types(self, var: VarDeclNode):
        if var.init_expr:
            self._infer_type(var.init_expr)

    def _check_block_types(self, block: BlockNode, context: str):
        self.symbol_table.push_scope()
        for stmt in block.statements:
            self._check_stmt_types(stmt, context)
        self.symbol_table.pop_scope()

    def _check_stmt_types(self, stmt, context: str):
        if isinstance(stmt, VarDeclNode):
            if stmt.init_expr:
                init_type = self._infer_type(stmt.init_expr)
                stmt.var_type = init_type
            try:
                self.symbol_table.add_local_variable(stmt)
            except SemanticError as e:
                self.reporter.add_error("DUPLICATE_VAR", e.message, e.line, e.column)

        elif isinstance(stmt, AssignNode):
            target_type = self._infer_type(stmt.target)
            value_type = self._infer_type(stmt.value)
            if target_type != "unknown" and value_type != "unknown" and target_type != value_type:
                self.reporter.add_error("TYPE_MISMATCH", f"Affectation de type '{value_type}' a une cible de type '{target_type}'", stmt.line, stmt.column)

        elif isinstance(stmt, CompoundAssignNode):
            target_type = self._infer_type(stmt.target)
            value_type = self._infer_type(stmt.value)
            if stmt.op in ('+=', '-='):
                if target_type not in ('int', 'float', 'unknown'):
                    self.reporter.add_error("TYPE_MISMATCH", f"Operation '{stmt.op}' impossible sur le type '{target_type}'", stmt.line, stmt.column)
                if value_type not in ('int', 'float', 'unknown'):
                    self.reporter.add_error("TYPE_MISMATCH", f"Operation '{stmt.op}' avec une valeur de type '{value_type}'", stmt.line, stmt.column)

        elif isinstance(stmt, IfNode):
            cond_type = self._infer_type(stmt.condition)
            if cond_type != "bool" and cond_type != "unknown":
                self.reporter.add_error("TYPE_MISMATCH", f"Condition 'if' doit etre de type 'bool', trouve '{cond_type}'", stmt.line, stmt.column)
            self._check_block_types(stmt.then_block, context)
            if stmt.else_block:
                self._check_block_types(stmt.else_block, context)

        elif isinstance(stmt, WhileNode):
            cond_type = self._infer_type(stmt.condition)
            if cond_type != "bool" and cond_type != "unknown":
                self.reporter.add_error("TYPE_MISMATCH", f"Condition 'while' doit etre de type 'bool', trouve '{cond_type}'", stmt.line, stmt.column)
            self._check_block_types(stmt.body, context)

        elif isinstance(stmt, ForNode):
            iterable_type = self._infer_type(stmt.iterable)
            if iterable_type != "list" and iterable_type != "unknown":
                self.reporter.add_error("TYPE_MISMATCH", f"Iteration 'for' requiert une liste, trouve '{iterable_type}'", stmt.line, stmt.column)
            self.symbol_table.push_scope()
            loop_var = VarDeclNode(stmt.var_name, LiteralNode(None, stmt.line, stmt.column), None, stmt.line, stmt.column)
            try:
                self.symbol_table.add_local_variable(loop_var)
            except SemanticError:
                pass
            self._check_block_types(stmt.body, context)
            self.symbol_table.pop_scope()

        elif isinstance(stmt, ReturnNode):
            if stmt.value:
                self._infer_type(stmt.value)

        elif isinstance(stmt, GiveStmtNode):
            for r in stmt.rewards if isinstance(stmt.rewards, list) else []:
                self._infer_type(r)

        elif isinstance(stmt, TakeStmtNode):
            for r in stmt.rewards if isinstance(stmt.rewards, list) else []:
                self._infer_type(r)

        elif isinstance(stmt, CallStmtNode):
            call = stmt.call_expr
            for arg in call.args:
                self._infer_type(arg)

        elif isinstance(stmt, BlockNode):
            self._check_block_types(stmt, context)

    def _infer_type(self, expr) -> str:
        if isinstance(expr, LiteralNode):
            if isinstance(expr.value, bool):
                return "bool"
            if isinstance(expr.value, int):
                return "int"
            if isinstance(expr.value, float):
                return "float"
            if isinstance(expr.value, str):
                return "string"
            return "unknown"

        elif isinstance(expr, IdentifierNode):
            var = self.symbol_table.get_variable(expr.name)
            if var and var.var_type:
                return var.var_type
            if expr.name in ('true', 'false'):
                return "bool"
            if expr.name in ('xp', 'gold'):
                return "int"
            return "unknown"

        elif isinstance(expr, BinaryOpNode):
            left_type = self._infer_type(expr.left)
            right_type = self._infer_type(expr.right)

            if expr.op == '/' and self._is_zero(expr.right):
                self.reporter.add_error(
                    "DIVISION_BY_ZERO",
                    "Division par zero detectee.",
                    getattr(expr, "line", 1),
                    getattr(expr, "column", 1)
                )
                return "unknown"

            if expr.op in ('and', 'or'):
                if left_type != "bool" and left_type != "unknown":
                    self.reporter.add_error("TYPE_MISMATCH", f"Operateur '{expr.op}' requiert 'bool', trouve '{left_type}'", expr.left.line, expr.left.column)
                if right_type != "bool" and right_type != "unknown":
                    self.reporter.add_error("TYPE_MISMATCH", f"Operateur '{expr.op}' requiert 'bool', trouve '{right_type}'", expr.right.line, expr.right.column)
                return "bool"
            if expr.op in ('==', '!=', '<', '>', '<=', '>='):
                return "bool"
            if expr.op in ('+', '-', '*', '/', '%', '^'):
                if left_type not in ('int', 'float', 'unknown'):
                    self.reporter.add_error("TYPE_MISMATCH", f"Operateur '{expr.op}' impossible sur le type '{left_type}'", expr.left.line, expr.left.column)
                if right_type not in ('int', 'float', 'unknown'):
                    self.reporter.add_error("TYPE_MISMATCH", f"Operateur '{expr.op}' impossible sur le type '{right_type}'", expr.right.line, expr.right.column)
                if left_type == "float" or right_type == "float":
                    return "float"
                return "int"

        elif isinstance(expr, UnaryOpNode):
            operand_type = self._infer_type(expr.operand)
            if expr.op == 'not':
                if operand_type != "bool" and operand_type != "unknown":
                    self.reporter.add_error("TYPE_MISMATCH", f"Operateur 'not' requiert 'bool', trouve '{operand_type}'", expr.operand.line, expr.operand.column)
                return "bool"
            elif expr.op == '-':
                if operand_type not in ('int', 'float', 'unknown'):
                    self.reporter.add_error("TYPE_MISMATCH", f"Operateur '-' unaire requiert un nombre, trouve '{operand_type}'", expr.operand.line, expr.operand.column)
                return operand_type

        elif isinstance(expr, ListLiteralNode):
            return "list"

        elif isinstance(expr, IndexNode):
            target_type = self._infer_type(expr.target)
            index_type = self._infer_type(expr.index)
            if target_type != "list" and target_type != "unknown":
                self.reporter.add_error("TYPE_MISMATCH", f"Indexation impossible sur le type '{target_type}'", expr.target.line, expr.target.column)
            if index_type not in ('int', 'unknown'):
                self.reporter.add_error("TYPE_MISMATCH", f"Index doit etre 'int', trouve '{index_type}'", expr.index.line, expr.index.column)
            return "unknown"

        elif isinstance(expr, CallExprNode):
            for arg in expr.args:
                self._infer_type(arg)
            return "unknown"

        elif isinstance(expr, ResourceNode):
            if expr.amount:
                self._infer_type(expr.amount)
            if expr.quantity:
                self._infer_type(expr.quantity)
            return "int" if expr.resource_type in ('xp', 'gold') else "unknown"

        return "unknown"

    def _is_zero(self, expr) -> bool:
        if isinstance(expr, LiteralNode):
            return isinstance(expr.value, (int, float)) and expr.value == 0
        return False

    def pass1_symbols(self):
        if not self.program:
            return
        for decl in self.program.declarations:
            if isinstance(decl, WorldNode):
                if self.symbol_table.world is not None:
                    self.reporter.add_error("DUPLICATE_WORLD", "Le monde est defini plusieurs fois", decl.line, decl.column)
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

        for decl in self.program.declarations:
            if isinstance(decl, WorldNode):
                self._check_world_refs(decl)
            elif isinstance(decl, QuestNode):
                self._check_quest_refs(decl)
            elif isinstance(decl, NPCNode):
                self._check_npc_refs(decl)
            elif isinstance(decl, FunctionNode):
                self._check_function_body(decl)

        for decl in self.program.declarations:
            if isinstance(decl, QuestNode):
                self._check_item_refs_in_quest(decl)

    def _check_world_refs(self, world: WorldNode):
        if "start" in world.properties:
            start_val = self._extract_string(world.properties["start"])
            if start_val and not self.symbol_table.has_quest(start_val):
                self.reporter.add_error("UNDEF_START_QUEST", f"La quete de depart '{start_val}' n'existe pas", world.line, world.column)

        if "win_condition" in world.properties:
            win_val = self._extract_string(world.properties["win_condition"])
            if win_val and not self.symbol_table.has_quest(win_val):
                self.reporter.add_error("UNDEF_WIN_COND", f"La condition de victoire '{win_val}' n'existe pas", world.line, world.column)

    def _check_quest_refs(self, quest: QuestNode):
        props = quest.properties
        if "requires" in props and isinstance(props["requires"], IdListNode):
            for qname in props["requires"].ids:
                if not self.symbol_table.has_quest(qname):
                    self.reporter.add_error("UNDEF_QUEST_REF", f"La quete '{quest.name}' requiert une quete inexistante '{qname}'", quest.line, quest.column)

        if "unlocks" in props and isinstance(props["unlocks"], IdListNode):
            for qname in props["unlocks"].ids:
                if not self.symbol_table.has_quest(qname):
                    self.reporter.add_error("UNDEF_UNLOCK_REF", f"La quete '{quest.name}' debloque une quete inexistante '{qname}'", quest.line, quest.column)

        if quest.script:
            self.symbol_table.push_scope()
            self._check_script_refs(quest.script, quest.name)
            self.symbol_table.pop_scope()

    def _check_npc_refs(self, npc: NPCNode):
        props = npc.properties
        if "gives_quest" in props and isinstance(props["gives_quest"], IdListNode):
            for qname in props["gives_quest"].ids:
                if not self.symbol_table.has_quest(qname):
                    self.reporter.add_error("UNDEF_QUEST_REF", f"Le PNJ '{npc.name}' donne une quete inexistante '{qname}'", npc.line, npc.column)

    def _check_item_refs_in_quest(self, quest: QuestNode):
        for key in ["rewards", "costs"]:
            if key in quest.properties:
                rewards = quest.properties[key]
                if isinstance(rewards, RewardListNode):
                    for r in rewards.rewards:
                        if r.resource_type == "item" and not self.symbol_table.has_item(r.name):
                            self.reporter.add_error("UNDEF_ITEM_REF", f"Item '{r.name}' utilise dans la quete '{quest.name}' n'existe pas", quest.line, quest.column)

    def _check_function_body(self, func: FunctionNode):
        if func.body:
            self.symbol_table.push_scope()
            for param in func.params:
                param_node = VarDeclNode(param, LiteralNode(None, func.line, func.column), None, func.line, func.column)
                try:
                    self.symbol_table.add_local_variable(param_node)
                except SemanticError:
                    pass
            self._check_script_refs(func.body, func.name)
            self.symbol_table.pop_scope()

    def _check_script_refs(self, block: BlockNode, context: str):
        for stmt in block.statements:
            self._check_stmt_refs(stmt, context)

    def _check_stmt_refs(self, stmt, context: str):
        if isinstance(stmt, VarDeclNode):
            try:
                self.symbol_table.add_local_variable(stmt)
            except SemanticError as e:
                self.reporter.add_error("DUPLICATE_VAR", e.message, e.line, e.column)
            if stmt.init_expr:
                self._check_expr_refs(stmt.init_expr, context)

        elif isinstance(stmt, AssignNode):
            self._check_expr_refs(stmt.target, context)
            self._check_expr_refs(stmt.value, context)

        elif isinstance(stmt, CompoundAssignNode):
            self._check_expr_refs(stmt.target, context)
            self._check_expr_refs(stmt.value, context)

        elif isinstance(stmt, CallStmtNode):
            call = stmt.call_expr
            if not self.symbol_table.has_function(call.name):
                self.reporter.add_error("UNDEF_FUNC_REF", f"Appel a une fonction inexistante '{call.name}'", call.line, call.column)
            for arg in call.args:
                self._check_expr_refs(arg, context)

        elif isinstance(stmt, IfNode):
            self._check_expr_refs(stmt.condition, context)
            self.symbol_table.push_scope()
            self._check_script_refs(stmt.then_block, context)
            self.symbol_table.pop_scope()
            if stmt.else_block:
                self.symbol_table.push_scope()
                self._check_script_refs(stmt.else_block, context)
                self.symbol_table.pop_scope()

        elif isinstance(stmt, WhileNode):
            self._check_expr_refs(stmt.condition, context)
            self.symbol_table.push_scope()
            self._check_script_refs(stmt.body, context)
            self.symbol_table.pop_scope()

        elif isinstance(stmt, ForNode):
            self._check_expr_refs(stmt.iterable, context)
            self.symbol_table.push_scope()
            loop_var = VarDeclNode(stmt.var_name, LiteralNode(None, stmt.line, stmt.column), None, stmt.line, stmt.column)
            try:
                self.symbol_table.add_local_variable(loop_var)
            except SemanticError:
                pass
            self._check_script_refs(stmt.body, context)
            self.symbol_table.pop_scope()

        elif isinstance(stmt, ReturnNode):
            if stmt.value:
                self._check_expr_refs(stmt.value, context)

        elif isinstance(stmt, GiveStmtNode):
            for r in stmt.rewards if isinstance(stmt.rewards, list) else []:
                self._check_expr_refs(r, context)

        elif isinstance(stmt, TakeStmtNode):
            for r in stmt.rewards if isinstance(stmt.rewards, list) else []:
                self._check_expr_refs(r, context)

        elif isinstance(stmt, BlockNode):
            self.symbol_table.push_scope()
            self._check_script_refs(stmt, context)
            self.symbol_table.pop_scope()

    def _check_expr_refs(self, expr, context: str):
        if isinstance(expr, IdentifierNode):
            reserved_names = {'xp', 'gold', 'true', 'false'}
            if (not self.symbol_table.has_variable(expr.name) and
                expr.name not in reserved_names and
                not self.symbol_table.has_quest(expr.name) and
                not self.symbol_table.has_item(expr.name) and
                not self.symbol_table.has_npc(expr.name) and
                not self.symbol_table.has_function(expr.name)):
                self.reporter.add_error("UNDECLARED_VAR", f"Variable '{expr.name}' utilisee mais non declaree dans '{context}'", expr.line, expr.column)

        elif isinstance(expr, BinaryOpNode):
            self._check_expr_refs(expr.left, context)
            self._check_expr_refs(expr.right, context)
        elif isinstance(expr, UnaryOpNode):
            self._check_expr_refs(expr.operand, context)
        elif isinstance(expr, CallExprNode):
            if not self.symbol_table.has_function(expr.name):
                self.reporter.add_error("UNDEF_FUNC_REF", f"Appel a une fonction inexistante '{expr.name}'", expr.line, expr.column)
            for arg in expr.args:
                self._check_expr_refs(arg, context)
        elif isinstance(expr, IndexNode):
            self._check_expr_refs(expr.target, context)
            self._check_expr_refs(expr.index, context)
        elif isinstance(expr, PropertyAccessNode):
            self._check_expr_refs(expr.target, context)
        elif isinstance(expr, ListLiteralNode):
            for elem in expr.elements:
                self._check_expr_refs(elem, context)
        elif isinstance(expr, ResourceNode):
            if expr.amount:
                self._check_expr_refs(expr.amount, context)
            if expr.quantity:
                self._check_expr_refs(expr.quantity, context)

    def _extract_string(self, node):
        if isinstance(node, LiteralNode) and isinstance(node.value, str):
            return node.value
        if isinstance(node, IdentifierNode):
            return node.name
        return None

    def pass2_reachability(self):
        if not self.symbol_table.world:
            self.reporter.add_warning("NO_WORLD", "Aucun bloc 'world' defini. Impossible de verifier l'accessibilite.", 1, 1)
            return

        world = self.symbol_table.world
        start_quest = None
        win_condition = None

        if "start" in world.properties:
            start_quest = self._extract_string(world.properties["start"])

        if "win_condition" in world.properties:
            win_condition = self._extract_string(world.properties["win_condition"])

        if not start_quest:
            if self.symbol_table.quests:
                start_quest = list(self.symbol_table.quests.keys())[0]
                self.reporter.add_info("DEFAULT_START", f"Aucune quete de depart specifiee. Utilisation de '{start_quest}' par defaut.")
            else:
                self.reporter.add_error("NO_START_QUEST", "Aucune quete de depart definie", world.line, world.column)
                return

        if not self.symbol_table.has_quest(start_quest):
            return

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
            if "unlocks" in quest.properties and isinstance(quest.properties["unlocks"], IdListNode):
                for next_q in quest.properties["unlocks"].ids:
                    if next_q not in visited:
                        stack.append(next_q)

        for qname in self.symbol_table.quests:
            if qname not in visited:
                quest = self.symbol_table.quests[qname]
                self.reporter.add_error("UNREACHABLE_QUEST", f"Quete '{qname}' inaccessible depuis la quete de depart", quest.line, quest.column)

        if win_condition and win_condition not in visited:
            self.reporter.add_error("WIN_UNREACHABLE", f"La condition de victoire '{win_condition}' est inaccessible", world.line, world.column)
        elif win_condition:
            self.reporter.add_info("WIN_REACHABLE", f"La condition de victoire '{win_condition}' est atteignable")

        for qname in visited:
            quest = self.symbol_table.quests.get(qname)
            if quest:
                has_reward = False
                if "rewards" in quest.properties:
                    rewards = quest.properties["rewards"]
                    if isinstance(rewards, RewardListNode) and rewards.rewards:
                        has_reward = True
                if not has_reward and not quest.properties.get("is_final", False):
                    self.reporter.add_warning("NO_REWARD", f"Quete '{qname}' accessible sans recompense", quest.line, quest.column)

    def pass3_economy(self):
        item_production = defaultdict(float)
        item_consumption = defaultdict(float)
        gold_injected = 0.0
        gold_consumed = 0.0

        for qname, quest in self.symbol_table.quests.items():
            if "rewards" in quest.properties:
                rewards = quest.properties["rewards"]
                if isinstance(rewards, RewardListNode):
                    for r in rewards.rewards:
                        if r.resource_type == "gold":
                            gold_injected += self._eval_expr(r.amount)
                        elif r.resource_type == "item":
                            item_production[r.name] += self._eval_expr(r.quantity)

            if "costs" in quest.properties:
                costs = quest.properties["costs"]
                if isinstance(costs, RewardListNode):
                    for c in costs.rewards:
                        if c.resource_type == "gold":
                            gold_consumed += self._eval_expr(c.amount)
                        elif c.resource_type == "item":
                            item_consumption[c.name] += self._eval_expr(c.quantity)

        all_items = set(item_production.keys()) | set(item_consumption.keys())
        for item_name in all_items:
            produced = item_production[item_name]
            consumed = item_consumption[item_name]

            if consumed > produced:
                self.reporter.add_error("ITEM_DEFICIT", f"Item '{item_name}' consomme ({consumed}) plus que produit ({produced})", 1, 1)
            elif produced > consumed and consumed == 0:
                self.reporter.add_warning("ITEM_SURPLUS", f"Item '{item_name}' produit ({produced}) sans jamais etre consomme", 1, 1)

        if gold_consumed > 0:
            ratio = gold_injected / gold_consumed
            if ratio > 10:
                self.reporter.add_warning("GOLD_INFLATION", f"Inflation d'or detectee: ratio injecte/consomme = {ratio:.2f}", 1, 1)
            elif ratio < 0.5:
                self.reporter.add_warning("GOLD_DEFLATION", f"Deflation d'or detectee: ratio injecte/consomme = {ratio:.2f}", 1, 1)

    def _eval_expr(self, node, _visited=None) -> float:
        if _visited is None:
            _visited = set()

        if node is None:
            return 0.0
        if isinstance(node, LiteralNode):
            if isinstance(node.value, (int, float)):
                return float(node.value)
            return 0.0
        if isinstance(node, BinaryOpNode):
            left = self._eval_expr(node.left, _visited)
            right = self._eval_expr(node.right, _visited)
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
        if isinstance(node, IdentifierNode):
            var = self.symbol_table.get_variable(node.name)
            if var and var.init_expr:
                var_id = id(var.init_expr)
                if var_id in _visited:
                    return 0.0
                _visited.add(var_id)
                return self._eval_expr(var.init_expr, _visited)
            return 0.0
        return 0.0

    def pass4_cycles(self):
        graph = defaultdict(list)
        for qname, quest in self.symbol_table.quests.items():
            if "requires" in quest.properties and isinstance(quest.properties["requires"], IdListNode):
                for req in quest.properties["requires"].ids:
                    graph[qname].append(req)
            if "unlocks" in quest.properties and isinstance(quest.properties["unlocks"], IdListNode):
                for unlocked in quest.properties["unlocks"].ids:
                    graph[unlocked].append(qname)

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

        for scc in sccs:
            if len(scc) > 1:
                cycle_str = " -> ".join(scc) + " -> " + scc[0]
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
                    self.reporter.add_error("DEADLOCK_CYCLE", f"Deadlock narratif detecte: {cycle_str}", 1, 1)
                else:
                    self.reporter.add_warning("UNLOCK_LOOP", f"Boucle d'unlock detectee: {cycle_str}", 1, 1)

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
                self.reporter.add_warning("DEAD_ITEM", f"Item '{item_name}' declare mais jamais utilise", item.line, item.column)

        for npc_name, npc in self.symbol_table.npcs.items():
            gives = npc.properties.get("gives_quest")
            if not gives or (isinstance(gives, IdListNode) and not gives.ids):
                self.reporter.add_warning("IDLE_NPC", f"PNJ '{npc_name}' ne donne aucune quete", npc.line, npc.column)

    def get_diagnostics(self):
        return self.reporter.get_diagnostics()