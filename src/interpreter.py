# -*- coding: utf-8 -*-
"""
Interpreteur QuestLang - Execute les scripts de quetes dynamiquement.
Bonus: evalue give/take/call dans les scripts avec portee des variables.
"""

from ast_nodes import *
from errors import QuestLangRuntimeError

class QuestLangInterpreter:
    """
    Interpreteur pour les scripts QuestLang.
    Evalue les expressions et execute les instructions give/take/call.
    """

    def __init__(self, symbol_table=None):
        self.global_vars = {}      # Variables globales (world)
        self.local_vars = {}       # Variables locales (script courant)
        self.functions = {}        # Definitions de fonctions
        self.symbol_table = symbol_table
        self.inventory = {
            "gold": 0,
            "xp": 0,
            "items": {}
        }
        self.output_log = []       # Log des operations effectuees

    def set_inventory(self, gold=0, xp=0, items=None):
        """Initialise l'inventaire du joueur."""
        self.inventory["gold"] = gold
        self.inventory["xp"] = xp
        self.inventory["items"] = items or {}

    def register_function(self, func_node: FunctionNode):
        """Enregistre une fonction utilisateur."""
        self.functions[func_node.name] = func_node

    def set_global_var(self, name, value):
        """Definit une variable globale."""
        self.global_vars[name] = value

    def execute_script(self, block: BlockNode, local_scope=None):
        """Execute un bloc de script et retourne l'inventaire modifie."""
        old_local = self.local_vars
        self.local_vars = local_scope or {}

        try:
            for stmt in block.statements:
                self._execute_stmt(stmt)
        finally:
            self.local_vars = old_local

        return dict(self.inventory)

    def _execute_stmt(self, stmt):
        """Execute une instruction."""
        if isinstance(stmt, VarDeclNode):
            value = self._eval_expr(stmt.init_expr)
            self.local_vars[stmt.name] = value
            self.output_log.append(f"var {stmt.name} = {value}")

        elif isinstance(stmt, AssignNode):
            value = self._eval_expr(stmt.value)
            target_name = self._get_target_name(stmt.target)
            if target_name in self.local_vars:
                self.local_vars[target_name] = value
            elif target_name in self.global_vars:
                self.global_vars[target_name] = value
            else:
                # Nouvelle variable locale
                self.local_vars[target_name] = value
            self.output_log.append(f"{target_name} = {value}")

        elif isinstance(stmt, CompoundAssignNode):
            value = self._eval_expr(stmt.value)
            target_name = self._get_target_name(stmt.target)
            current = self._get_var(target_name)
            if stmt.op == '+=':
                new_val = current + value
            elif stmt.op == '-=':
                new_val = current - value
            else:
                new_val = value

            if target_name in self.local_vars:
                self.local_vars[target_name] = new_val
            else:
                self.global_vars[target_name] = new_val
            self.output_log.append(f"{target_name} {stmt.op} {value} → {new_val}")

        elif isinstance(stmt, GiveStmtNode):
            rewards = stmt.rewards if isinstance(stmt.rewards, list) else [stmt.rewards]
            for r in rewards:
                if isinstance(r, ResourceNode):
                    self._apply_reward(r, "give")

        elif isinstance(stmt, TakeStmtNode):
            rewards = stmt.rewards if isinstance(stmt.rewards, list) else [stmt.rewards]
            for r in rewards:
                if isinstance(r, ResourceNode):
                    self._apply_reward(r, "take")

        elif isinstance(stmt, CallStmtNode):
            result = self._call_function(stmt.call_expr.name, stmt.call_expr.args)
            if result is not None:
                self.output_log.append(f"call {stmt.call_expr.name}() → {result}")

        elif isinstance(stmt, IfNode):
            condition = self._eval_expr(stmt.condition)
            if self._is_truthy(condition):
                self._execute_block(stmt.then_block)
            elif stmt.else_block:
                self._execute_block(stmt.else_block)

        elif isinstance(stmt, WhileNode):
            loop_count = 0
            max_loops = 1000  # Protection contre boucle infinie
            while self._is_truthy(self._eval_expr(stmt.condition)) and loop_count < max_loops:
                self._execute_block(stmt.body)
                loop_count += 1
            if loop_count >= max_loops:
                self.output_log.append("WARNING: Boucle while interrompue apres 1000 iterations")

        elif isinstance(stmt, ForNode):
            iterable = self._eval_expr(stmt.iterable)
            if isinstance(iterable, list):
                for item in iterable:
                    old_val = self.local_vars.get(stmt.var_name)
                    self.local_vars[stmt.var_name] = item
                    self._execute_block(stmt.body)
                    if old_val is not None:
                        self.local_vars[stmt.var_name] = old_val
                    elif stmt.var_name in self.local_vars:
                        del self.local_vars[stmt.var_name]

        elif isinstance(stmt, ReturnNode):
            value = self._eval_expr(stmt.value) if stmt.value else None
            raise _ReturnValue(value)

        elif isinstance(stmt, BlockNode):
            self._execute_block(stmt)

    def _execute_block(self, block: BlockNode):
        """Execute un bloc d'instructions."""
        if block and block.statements:
            for stmt in block.statements:
                self._execute_stmt(stmt)

    def _eval_expr(self, expr):
        """Evalue une expression et retourne sa valeur."""
        if expr is None:
            return None

        if isinstance(expr, LiteralNode):
            return expr.value

        if isinstance(expr, IdentifierNode):
            return self._get_var(expr.name)

        if isinstance(expr, BinaryOpNode):
            left = self._eval_expr(expr.left)
            right = self._eval_expr(expr.right)
            return self._apply_binary_op(expr.op, left, right)

        if isinstance(expr, UnaryOpNode):
            operand = self._eval_expr(expr.operand)
            if expr.op == '-':
                return -operand if operand is not None else 0
            elif expr.op == 'not':
                return not self._is_truthy(operand)
            return operand

        if isinstance(expr, CallExprNode):
            return self._call_function(expr.name, expr.args)

        if isinstance(expr, IndexNode):
            target = self._eval_expr(expr.target)
            index = self._eval_expr(expr.index)
            if isinstance(target, list) and isinstance(index, int):
                return target[index] if 0 <= index < len(target) else None
            return None

        if isinstance(expr, ListLiteralNode):
            return [self._eval_expr(e) for e in expr.elements]

        if isinstance(expr, PropertyAccessNode):
            target = self._eval_expr(expr.target)
            if isinstance(target, dict):
                return target.get(expr.property_name)
            return None

        if isinstance(expr, ResourceNode):
            if expr.resource_type in ["gold", "xp"]:
                return self._eval_expr(expr.amount)
            return self._eval_expr(expr.quantity)

        return None

    def _get_var(self, name):
        """Recupere la valeur d'une variable (locale d'abord, puis globale)."""
        if name in self.local_vars:
            return self.local_vars[name]
        if name in self.global_vars:
            return self.global_vars[name]
        # Variables speciales de l'inventaire
        if name == "gold":
            return self.inventory["gold"]
        if name == "xp":
            return self.inventory["xp"]
        return 0  # Valeur par defaut pour variable non declaree

    def _get_target_name(self, target):
        """Extrait le nom d'une cible d'affectation."""
        if isinstance(target, IdentifierNode):
            return target.name
        if isinstance(target, IndexNode):
            return self._get_target_name(target.target)
        return str(target)

    def _apply_binary_op(self, op, left, right):
        """Applique un operateur binaire."""
        if left is None:
            left = 0
        if right is None:
            right = 0

        if op == '+':
            return left + right
        elif op == '-':
            return left - right
        elif op == '*':
            return left * right
        elif op == '/':
            return left / right if right != 0 else 0
        elif op == '%':
            return left % right if right != 0 else 0
        elif op == '^':
            return left ** right
        elif op == '==':
            return left == right
        elif op == '!=':
            return left != right
        elif op == '<':
            return left < right
        elif op == '>':
            return left > right
        elif op == '<=':
            return left <= right
        elif op == '>=':
            return left >= right
        elif op == 'and':
            return self._is_truthy(left) and self._is_truthy(right)
        elif op == 'or':
            return self._is_truthy(left) or self._is_truthy(right)
        return None

    def _is_truthy(self, value):
        """Determine si une valeur est vraie."""
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            return len(value) > 0
        if isinstance(value, list):
            return len(value) > 0
        return True

    def _apply_reward(self, resource: ResourceNode, action: str):
        """Applique une recompense ou un cout a l'inventaire."""
        if resource.resource_type == "gold":
            amount = int(self._eval_expr(resource.amount))
            if action == "give":
                self.inventory["gold"] += amount
                self.output_log.append(f"give gold {amount} → or: {self.inventory['gold']}")
            else:
                self.inventory["gold"] = max(0, self.inventory["gold"] - amount)
                self.output_log.append(f"take gold {amount} → or: {self.inventory['gold']}")

        elif resource.resource_type == "xp":
            amount = int(self._eval_expr(resource.amount))
            if action == "give":
                self.inventory["xp"] += amount
                self.output_log.append(f"give xp {amount} → xp: {self.inventory['xp']}")
            else:
                self.inventory["xp"] = max(0, self.inventory["xp"] - amount)
                self.output_log.append(f"take xp {amount} → xp: {self.inventory['xp']}")

        elif resource.resource_type == "item":
            qty = int(self._eval_expr(resource.quantity))
            item_name = resource.name
            if action == "give":
                self.inventory["items"][item_name] = self.inventory["items"].get(item_name, 0) + qty
                self.output_log.append(f"give {qty}x {item_name}")
            else:
                current = self.inventory["items"].get(item_name, 0)
                self.inventory["items"][item_name] = max(0, current - qty)
                self.output_log.append(f"take {qty}x {item_name}")

    def _call_function(self, name, args):
        """Appelle une fonction utilisateur."""
        if name not in self.functions:
            self.output_log.append(f"ERREUR: Fonction '{name}' non definie")
            return None

        func = self.functions[name]

        # Evaluer les arguments
        arg_values = [self._eval_expr(a) for a in args]

        # Creer un nouveau scope local avec les parametres
        func_scope = {}
        for i, param in enumerate(func.params):
            func_scope[param] = arg_values[i] if i < len(arg_values) else None

        # Sauvegarder et restaurer le scope local
        old_local = self.local_vars
        self.local_vars = func_scope

        try:
            self._execute_block(func.body)
        except _ReturnValue as ret:
            self.local_vars = old_local
            return ret.value
        finally:
            self.local_vars = old_local

        return None


class _ReturnValue(Exception):
    """Exception interne pour gerer les return dans les fonctions."""
    def __init__(self, value):
        self.value = value
