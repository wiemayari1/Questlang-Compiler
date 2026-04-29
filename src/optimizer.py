# -*- coding: utf-8 -*-
"""
Optimisation pour QuestLang v2.
Contient principalement le constant folding.
"""

from ast_nodes import (
    ProgramNode, WorldNode, QuestNode, ItemNode, NPCNode, FunctionNode,
    VarDeclNode, AssignNode, CompoundAssignNode, IfNode, WhileNode, ForNode,
    ReturnNode, GiveStmtNode, TakeStmtNode, CallStmtNode, BlockNode,
    BinaryOpNode, UnaryOpNode, LiteralNode, IdentifierNode, IndexNode,
    CallExprNode, ListLiteralNode, PropertyAccessNode, ResourceNode,
    RewardListNode, IdListNode
)


class Optimizer:
    def optimize(self, node):
        return self._visit(node)

    def _visit(self, node):
        if node is None:
            return None
        method = getattr(self, f"_visit_{type(node).__name__}", self._generic_visit)
        return method(node)

    def _generic_visit(self, node):
        from ast_nodes import ASTNode
        if isinstance(node, ASTNode) and hasattr(node, "__dict__"):
            for attr, value in node.__dict__.items():
                if isinstance(value, list):
                    new_list = []
                    for item in value:
                        if isinstance(item, ASTNode):
                            new_list.append(self._visit(item))
                        else:
                            new_list.append(item)
                    setattr(node, attr, new_list)
                elif isinstance(value, ASTNode):
                    setattr(node, attr, self._visit(value))
        return node

    def _visit_ProgramNode(self, node):
        node.declarations = [self._visit(d) for d in node.declarations]
        return node

    def _visit_WorldNode(self, node):
        for key, value in list(node.properties.items()):
            node.properties[key] = self._visit(value)
        return node

    def _visit_QuestNode(self, node):
        for key, value in list(node.properties.items()):
            node.properties[key] = self._visit(value)
        if node.script:
            node.script = self._visit(node.script)
        return node

    def _visit_ItemNode(self, node):
        for key, value in list(node.properties.items()):
            node.properties[key] = self._visit(value)
        return node

    def _visit_NPCNode(self, node):
        for key, value in list(node.properties.items()):
            node.properties[key] = self._visit(value)
        return node

    def _visit_FunctionNode(self, node):
        if node.body:
            node.body = self._visit(node.body)
        return node

    def _visit_BlockNode(self, node):
        node.statements = [self._visit(stmt) for stmt in node.statements]
        return node

    def _visit_VarDeclNode(self, node):
        node.init_expr = self._visit(node.init_expr)
        return node

    def _visit_AssignNode(self, node):
        node.target = self._visit(node.target)
        node.value = self._visit(node.value)
        return node

    def _visit_CompoundAssignNode(self, node):
        node.target = self._visit(node.target)
        node.value = self._visit(node.value)
        return node

    def _visit_IfNode(self, node):
        node.condition = self._visit(node.condition)
        node.then_block = self._visit(node.then_block)
        if node.else_block:
            node.else_block = self._visit(node.else_block)
        return node

    def _visit_WhileNode(self, node):
        node.condition = self._visit(node.condition)
        node.body = self._visit(node.body)
        return node

    def _visit_ForNode(self, node):
        node.iterable = self._visit(node.iterable)
        node.body = self._visit(node.body)
        return node

    def _visit_ReturnNode(self, node):
        node.value = self._visit(node.value)
        return node

    def _visit_GiveStmtNode(self, node):
        if isinstance(node.rewards, list):
            node.rewards = [self._visit(r) for r in node.rewards]
        else:
            node.rewards = self._visit(node.rewards)
        return node

    def _visit_TakeStmtNode(self, node):
        if isinstance(node.rewards, list):
            node.rewards = [self._visit(r) for r in node.rewards]
        else:
            node.rewards = self._visit(node.rewards)
        return node

    def _visit_CallStmtNode(self, node):
        node.call_expr = self._visit(node.call_expr)
        return node

    def _visit_BinaryOpNode(self, node):
        node.left = self._visit(node.left)
        node.right = self._visit(node.right)

        left = node.left
        right = node.right

        if isinstance(left, LiteralNode) and isinstance(right, LiteralNode):
            lv = left.value
            rv = right.value

            try:
                if node.op == "+":
                    return LiteralNode(lv + rv, node.line, node.column)
                if node.op == "-":
                    return LiteralNode(lv - rv, node.line, node.column)
                if node.op == "*":
                    return LiteralNode(lv * rv, node.line, node.column)
                if node.op == "/":
                    if rv == 0:
                        return node
                    return LiteralNode(lv / rv, node.line, node.column)
                if node.op == "%":
                    if rv == 0:
                        return node
                    return LiteralNode(lv % rv, node.line, node.column)
                if node.op == "^":
                    return LiteralNode(lv ** rv, node.line, node.column)
                if node.op == "==":
                    return LiteralNode(lv == rv, node.line, node.column)
                if node.op == "!=":
                    return LiteralNode(lv != rv, node.line, node.column)
                if node.op == "<":
                    return LiteralNode(lv < rv, node.line, node.column)
                if node.op == "<=":
                    return LiteralNode(lv <= rv, node.line, node.column)
                if node.op == ">":
                    return LiteralNode(lv > rv, node.line, node.column)
                if node.op == ">=":
                    return LiteralNode(lv >= rv, node.line, node.column)
                if node.op in ("and", "&&"):
                    return LiteralNode(bool(lv) and bool(rv), node.line, node.column)
                if node.op in ("or", "||"):
                    return LiteralNode(bool(lv) or bool(rv), node.line, node.column)
            except Exception:
                return node

        return node

    def _visit_UnaryOpNode(self, node):
        node.operand = self._visit(node.operand)
        if isinstance(node.operand, LiteralNode):
            v = node.operand.value
            try:
                if node.op == "-":
                    return LiteralNode(-v, node.line, node.column)
                if node.op in ("not", "!"):
                    return LiteralNode(not bool(v), node.line, node.column)
            except Exception:
                return node
        return node

    def _visit_ListLiteralNode(self, node):
        node.elements = [self._visit(e) for e in node.elements]
        return node

    def _visit_CallExprNode(self, node):
        node.args = [self._visit(a) for a in node.args]
        return node

    def _visit_IndexNode(self, node):
        node.target = self._visit(node.target)
        node.index = self._visit(node.index)
        return node

    def _visit_PropertyAccessNode(self, node):
        node.target = self._visit(node.target)
        return node

    def _visit_ResourceNode(self, node):
        node.amount = self._visit(node.amount)
        node.quantity = self._visit(node.quantity)
        return node

    def _visit_RewardListNode(self, node):
        node.rewards = [self._visit(r) for r in node.rewards]
        return node

    def _visit_IdListNode(self, node):
        return node