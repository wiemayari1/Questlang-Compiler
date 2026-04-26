# -*- coding: utf-8 -*-
"""
Constant Folding pour QuestLang.
Evalue les expressions constantes a la compilation.
Ex: var x = 5 * 10;  →  var x = 50;
"""

from ast_nodes import *

class ConstantFolder:
    """
    Passe d'optimisation: remplace les expressions constantes
    par leur valeur evaluee dans l'AST.
    """

    def fold(self, program: ProgramNode) -> ProgramNode:
        """Applique le constant folding sur tout le programme."""
        for decl in program.declarations:
            self._fold_declaration(decl)
        return program

    def _fold_declaration(self, decl):
        """Applique le folding sur une declaration."""
        if isinstance(decl, WorldNode):
            for key, val in decl.properties.items():
                decl.properties[key] = self._fold_expr(val)
            for var in decl.variables:
                var.init_expr = self._fold_expr(var.init_expr)

        elif isinstance(decl, QuestNode):
            for key, val in decl.properties.items():
                decl.properties[key] = self._fold_expr(val)
            if decl.script:
                self._fold_block(decl.script)

        elif isinstance(decl, ItemNode):
            for key, val in decl.properties.items():
                decl.properties[key] = self._fold_expr(val)

        elif isinstance(decl, NPCNode):
            for key, val in decl.properties.items():
                decl.properties[key] = self._fold_expr(val)

        elif isinstance(decl, FunctionNode):
            if decl.body:
                self._fold_block(decl.body)

    def _fold_block(self, block: BlockNode):
        """Applique le folding sur un bloc d'instructions."""
        if not block or not block.statements:
            return
        for stmt in block.statements:
            self._fold_statement(stmt)

    def _fold_statement(self, stmt):
        """Applique le folding sur une instruction."""
        if isinstance(stmt, VarDeclNode):
            stmt.init_expr = self._fold_expr(stmt.init_expr)

        elif isinstance(stmt, AssignNode):
            stmt.value = self._fold_expr(stmt.value)

        elif isinstance(stmt, CompoundAssignNode):
            stmt.value = self._fold_expr(stmt.value)

        elif isinstance(stmt, IfNode):
            stmt.condition = self._fold_expr(stmt.condition)
            self._fold_block(stmt.then_block)
            if stmt.else_block:
                self._fold_block(stmt.else_block)

        elif isinstance(stmt, WhileNode):
            stmt.condition = self._fold_expr(stmt.condition)
            self._fold_block(stmt.body)

        elif isinstance(stmt, ForNode):
            stmt.iterable = self._fold_expr(stmt.iterable)
            self._fold_block(stmt.body)

        elif isinstance(stmt, ReturnNode):
            if stmt.value:
                stmt.value = self._fold_expr(stmt.value)

        elif isinstance(stmt, GiveStmtNode):
            if isinstance(stmt.rewards, list):
                stmt.rewards = [self._fold_reward(r) for r in stmt.rewards]

        elif isinstance(stmt, TakeStmtNode):
            if isinstance(stmt.rewards, list):
                stmt.rewards = [self._fold_reward(r) for r in stmt.rewards]

        elif isinstance(stmt, CallStmtNode):
            stmt.call_expr = self._fold_expr(stmt.call_expr)

        elif isinstance(stmt, BlockNode):
            self._fold_block(stmt)

    def _fold_reward(self, reward):
        """Applique le folding sur une recompense."""
        if isinstance(reward, ResourceNode):
            if reward.amount:
                reward.amount = self._fold_expr(reward.amount)
            if reward.quantity:
                reward.quantity = self._fold_expr(reward.quantity)
        return reward

    def _fold_expr(self, expr):
        """
        Applique le folding sur une expression.
        Retourne un LiteralNode si l'expression est constante,
        sinon retourne l'expression partiellement pliee.
        """
        if expr is None:
            return None

        if isinstance(expr, LiteralNode):
            return expr

        if isinstance(expr, IdentifierNode):
            # Les identifiants ne sont pas constants (sauf si c'est une constante connue)
            return expr

        if isinstance(expr, BinaryOpNode):
            left = self._fold_expr(expr.left)
            right = self._fold_expr(expr.right)

            # Si les deux operandes sont des litteraux, evaluer
            if isinstance(left, LiteralNode) and isinstance(right, LiteralNode):
                result = self._eval_binary(expr.op, left.value, right.value)
                if result is not None:
                    return LiteralNode(result, expr.line, expr.column)

            # Sinon, remplacer les sous-expressions pliees
            expr.left = left
            expr.right = right
            return expr

        if isinstance(expr, UnaryOpNode):
            operand = self._fold_expr(expr.operand)
            if isinstance(operand, LiteralNode):
                result = self._eval_unary(expr.op, operand.value)
                if result is not None:
                    return LiteralNode(result, expr.line, expr.column)
            expr.operand = operand
            return expr

        if isinstance(expr, CallExprNode):
            # Les appels de fonction ne sont generalement pas constants
            # Mais on peut plier les arguments
            expr.args = [self._fold_expr(a) for a in expr.args]
            return expr

        if isinstance(expr, IndexNode):
            expr.target = self._fold_expr(expr.target)
            expr.index = self._fold_expr(expr.index)
            # Si target est une liste litterale et index un entier
            if (isinstance(expr.target, ListLiteralNode) and 
                isinstance(expr.index, LiteralNode) and 
                isinstance(expr.index.value, int)):
                idx = expr.index.value
                elements = expr.target.elements
                if 0 <= idx < len(elements):
                    return elements[idx]
            return expr

        if isinstance(expr, ListLiteralNode):
            expr.elements = [self._fold_expr(e) for e in expr.elements]
            return expr

        if isinstance(expr, PropertyAccessNode):
            expr.target = self._fold_expr(expr.target)
            return expr

        if isinstance(expr, ResourceNode):
            if expr.amount:
                expr.amount = self._fold_expr(expr.amount)
            if expr.quantity:
                expr.quantity = self._fold_expr(expr.quantity)
            return expr

        if isinstance(expr, RewardListNode):
            expr.rewards = [self._fold_reward(r) for r in expr.rewards]
            return expr

        if isinstance(expr, IdListNode):
            return expr

        return expr

    def _eval_binary(self, op, left, right):
        """Evalue une operation binaire sur des valeurs constantes."""
        try:
            if op == '+':
                return left + right
            elif op == '-':
                return left - right
            elif op == '*':
                return left * right
            elif op == '/':
                return left / right if right != 0 else None
            elif op == '%':
                return left % right if right != 0 else None
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
                return bool(left) and bool(right)
            elif op == 'or':
                return bool(left) or bool(right)
        except (TypeError, ValueError):
            return None
        return None

    def _eval_unary(self, op, operand):
        """Evalue une operation unaire sur une valeur constante."""
        try:
            if op == '-':
                return -operand
            elif op == 'not':
                return not operand
        except (TypeError, ValueError):
            return None
        return None
