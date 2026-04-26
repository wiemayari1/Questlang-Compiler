# -*- coding: utf-8 -*-
from enum import Enum, auto

class NodeType(Enum):
    PROGRAM = auto(); WORLD = auto(); QUEST = auto(); ITEM = auto(); NPC = auto(); FUNCTION = auto()
    VAR_DECL = auto(); ASSIGN = auto(); COMPOUND_ASSIGN = auto(); IF = auto(); WHILE = auto()
    FOR = auto(); RETURN = auto(); GIVE_STMT = auto(); TAKE_STMT = auto(); CALL_STMT = auto()
    EXPR_STMT = auto(); BLOCK = auto(); BINARY_OP = auto(); UNARY_OP = auto(); LITERAL = auto()
    IDENTIFIER = auto(); INDEX = auto(); CALL = auto(); LIST_LITERAL = auto(); PROPERTY_ACCESS = auto()
    RESOURCE = auto(); REWARD_LIST = auto(); ID_LIST = auto()

class ASTNode:
    def __init__(self, node_type, line=0, column=0):
        self.node_type = node_type
        self.line = line
        self.column = column

class ProgramNode(ASTNode):
    def __init__(self, declarations, line=1, column=1):
        super().__init__(NodeType.PROGRAM, line, column)
        self.declarations = declarations
        self.world = None
        self.quests = {}
        self.items = {}
        self.npcs = {}
        self.functions = {}

    def add_declaration(self, decl):
        if isinstance(decl, WorldNode): self.world = decl
        elif isinstance(decl, QuestNode): self.quests[decl.name] = decl
        elif isinstance(decl, ItemNode): self.items[decl.name] = decl
        elif isinstance(decl, NPCNode): self.npcs[decl.name] = decl
        elif isinstance(decl, FunctionNode): self.functions[decl.name] = decl

class WorldNode(ASTNode):
    def __init__(self, name, properties, line=0, column=0):
        super().__init__(NodeType.WORLD, line, column)
        self.name = name
        self.properties = properties
        self.variables = []

class QuestNode(ASTNode):
    def __init__(self, name, properties, script=None, line=0, column=0):
        super().__init__(NodeType.QUEST, line, column)
        self.name = name
        self.properties = properties
        self.script = script
        self.is_start = False
        self.is_final = False

class ItemNode(ASTNode):
    def __init__(self, name, properties, line=0, column=0):
        super().__init__(NodeType.ITEM, line, column)
        self.name = name
        self.properties = properties

class NPCNode(ASTNode):
    def __init__(self, name, properties, line=0, column=0):
        super().__init__(NodeType.NPC, line, column)
        self.name = name
        self.properties = properties

class FunctionNode(ASTNode):
    def __init__(self, name, params, body, line=0, column=0):
        super().__init__(NodeType.FUNCTION, line, column)
        self.name = name
        self.params = params
        self.body = body

class VarDeclNode(ASTNode):
    def __init__(self, name, init_expr, var_type=None, line=0, column=0):
        super().__init__(NodeType.VAR_DECL, line, column)
        self.name = name
        self.init_expr = init_expr
        self.var_type = var_type

class AssignNode(ASTNode):
    def __init__(self, target, value, line=0, column=0):
        super().__init__(NodeType.ASSIGN, line, column)
        self.target = target
        self.value = value

class CompoundAssignNode(ASTNode):
    def __init__(self, target, op, value, line=0, column=0):
        super().__init__(NodeType.COMPOUND_ASSIGN, line, column)
        self.target = target
        self.op = op
        self.value = value

class IfNode(ASTNode):
    def __init__(self, condition, then_block, else_block=None, line=0, column=0):
        super().__init__(NodeType.IF, line, column)
        self.condition = condition
        self.then_block = then_block
        self.else_block = else_block

class WhileNode(ASTNode):
    def __init__(self, condition, body, line=0, column=0):
        super().__init__(NodeType.WHILE, line, column)
        self.condition = condition
        self.body = body

class ForNode(ASTNode):
    def __init__(self, var_name, iterable, body, line=0, column=0):
        super().__init__(NodeType.FOR, line, column)
        self.var_name = var_name
        self.iterable = iterable
        self.body = body

class ReturnNode(ASTNode):
    def __init__(self, value, line=0, column=0):
        super().__init__(NodeType.RETURN, line, column)
        self.value = value

class GiveStmtNode(ASTNode):
    def __init__(self, rewards, line=0, column=0):
        super().__init__(NodeType.GIVE_STMT, line, column)
        self.rewards = rewards

class TakeStmtNode(ASTNode):
    def __init__(self, rewards, line=0, column=0):
        super().__init__(NodeType.TAKE_STMT, line, column)
        self.rewards = rewards

class CallStmtNode(ASTNode):
    def __init__(self, call_expr, line=0, column=0):
        super().__init__(NodeType.CALL_STMT, line, column)
        self.call_expr = call_expr

class BlockNode(ASTNode):
    def __init__(self, statements, line=0, column=0):
        super().__init__(NodeType.BLOCK, line, column)
        self.statements = statements

class BinaryOpNode(ASTNode):
    def __init__(self, op, left, right, line=0, column=0):
        super().__init__(NodeType.BINARY_OP, line, column)
        self.op = op
        self.left = left
        self.right = right

class UnaryOpNode(ASTNode):
    def __init__(self, op, operand, line=0, column=0):
        super().__init__(NodeType.UNARY_OP, line, column)
        self.op = op
        self.operand = operand

class LiteralNode(ASTNode):
    def __init__(self, value, line=0, column=0):
        super().__init__(NodeType.LITERAL, line, column)
        self.value = value

class IdentifierNode(ASTNode):
    def __init__(self, name, line=0, column=0):
        super().__init__(NodeType.IDENTIFIER, line, column)
        self.name = name

class IndexNode(ASTNode):
    def __init__(self, target, index, line=0, column=0):
        super().__init__(NodeType.INDEX, line, column)
        self.target = target
        self.index = index

class CallExprNode(ASTNode):
    def __init__(self, name, args, line=0, column=0):
        super().__init__(NodeType.CALL, line, column)
        self.name = name
        self.args = args

class ListLiteralNode(ASTNode):
    def __init__(self, elements, line=0, column=0):
        super().__init__(NodeType.LIST_LITERAL, line, column)
        self.elements = elements

class PropertyAccessNode(ASTNode):
    def __init__(self, target, property_name, line=0, column=0):
        super().__init__(NodeType.PROPERTY_ACCESS, line, column)
        self.target = target
        self.property_name = property_name

class ResourceNode(ASTNode):
    def __init__(self, resource_type, name, amount=None, quantity=None, line=0, column=0):
        super().__init__(NodeType.RESOURCE, line, column)
        self.resource_type = resource_type
        self.name = name
        self.amount = amount
        self.quantity = quantity

class RewardListNode(ASTNode):
    def __init__(self, rewards, line=0, column=0):
        super().__init__(NodeType.REWARD_LIST, line, column)
        self.rewards = rewards

class IdListNode(ASTNode):
    def __init__(self, ids, line=0, column=0):
        super().__init__(NodeType.ID_LIST, line, column)
        self.ids = ids
