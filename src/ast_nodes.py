# -*- coding: utf-8 -*-
"""
Definitions des noeuds de l'AST (Abstract Syntax Tree) pour QuestLang.
Structure arborescente representant le programme apres analyse syntaxique.
"""

from enum import Enum, auto

class NodeType(Enum):
    PROGRAM = auto()
    WORLD = auto()
    QUEST = auto()
    ITEM = auto()
    NPC = auto()
    FUNCTION = auto()

    VAR_DECL = auto()
    ASSIGN = auto()
    COMPOUND_ASSIGN = auto()
    IF = auto()
    WHILE = auto()
    FOR = auto()
    RETURN = auto()
    GIVE_STMT = auto()
    TAKE_STMT = auto()
    CALL_STMT = auto()
    EXPR_STMT = auto()
    BLOCK = auto()

    BINARY_OP = auto()
    UNARY_OP = auto()
    LITERAL = auto()
    IDENTIFIER = auto()
    INDEX = auto()
    CALL = auto()
    LIST_LITERAL = auto()
    PROPERTY_ACCESS = auto()

    RESOURCE = auto()
    REWARD_LIST = auto()
    ID_LIST = auto()


class ASTNode:
    """Classe de base pour tous les noeuds de l'AST."""
    def __init__(self, node_type, line=0, column=0):
        self.node_type = node_type
        self.line = line
        self.column = column

    def accept(self, visitor):
        method_name = f"visit_{self.node_type.name.lower()}"
        visitor_method = getattr(visitor, method_name, self._default_visit)
        return visitor_method(self)

    def _default_visit(self, visitor):
        raise NotImplementedError(f"Visiteur non implemente pour {self.node_type}")


class ProgramNode(ASTNode):
    """Noeud racine du programme."""
    def __init__(self, declarations, line=1, column=1):
        super().__init__(NodeType.PROGRAM, line, column)
        self.declarations = declarations  # Liste de WorldNode, QuestNode, ItemNode, NPCNode, FunctionNode
        self.world = None
        self.quests = {}
        self.items = {}
        self.npcs = {}
        self.functions = {}

    def add_declaration(self, decl):
        from ast_nodes import WorldNode, QuestNode, ItemNode, NPCNode, FunctionNode
        if isinstance(decl, WorldNode):
            self.world = decl
        elif isinstance(decl, QuestNode):
            self.quests[decl.name] = decl
        elif isinstance(decl, ItemNode):
            self.items[decl.name] = decl
        elif isinstance(decl, NPCNode):
            self.npcs[decl.name] = decl
        elif isinstance(decl, FunctionNode):
            self.functions[decl.name] = decl


class WorldNode(ASTNode):
    """Noeud representant le bloc world."""
    def __init__(self, name, properties, line=0, column=0):
        super().__init__(NodeType.WORLD, line, column)
        self.name = name
        self.properties = properties  # dict: start_quest, start_gold, win_condition, vars
        self.variables = []  # Liste de VarDeclNode


class QuestNode(ASTNode):
    """Noeud representant une quete."""
    def __init__(self, name, properties, script=None, line=0, column=0):
        super().__init__(NodeType.QUEST, line, column)
        self.name = name
        self.properties = properties  # dict: title, desc, requires, unlocks, rewards, costs, condition
        self.script = script  # BlockNode ou None
        self.is_start = False
        self.is_final = False


class ItemNode(ASTNode):
    """Noeud representant un item."""
    def __init__(self, name, properties, line=0, column=0):
        super().__init__(NodeType.ITEM, line, column)
        self.name = name
        self.properties = properties  # dict: title, value, stackable, type


class NPCNode(ASTNode):
    """Noeud representant un PNJ."""
    def __init__(self, name, properties, line=0, column=0):
        super().__init__(NodeType.NPC, line, column)
        self.name = name
        self.properties = properties  # dict: title, location, gives_quest


class FunctionNode(ASTNode):
    """Noeud representant une fonction utilisateur."""
    def __init__(self, name, params, body, line=0, column=0):
        super().__init__(NodeType.FUNCTION, line, column)
        self.name = name
        self.params = params  # Liste de noms de parametres
        self.body = body  # BlockNode


class VarDeclNode(ASTNode):
    """Declaration de variable."""
    def __init__(self, name, init_expr, var_type=None, line=0, column=0):
        super().__init__(NodeType.VAR_DECL, line, column)
        self.name = name
        self.init_expr = init_expr
        self.var_type = var_type


class AssignNode(ASTNode):
    """Affectation simple."""
    def __init__(self, target, value, line=0, column=0):
        super().__init__(NodeType.ASSIGN, line, column)
        self.target = target  # IdentifierNode ou IndexNode
        self.value = value


class CompoundAssignNode(ASTNode):
    """Affectation composee (+=, -=)."""
    def __init__(self, target, op, value, line=0, column=0):
        super().__init__(NodeType.COMPOUND_ASSIGN, line, column)
        self.target = target
        self.op = op  # '+=' ou '-='
        self.value = value


class IfNode(ASTNode):
    """Structure conditionnelle if/else."""
    def __init__(self, condition, then_block, else_block=None, line=0, column=0):
        super().__init__(NodeType.IF, line, column)
        self.condition = condition
        self.then_block = then_block
        self.else_block = else_block


class WhileNode(ASTNode):
    """Boucle while."""
    def __init__(self, condition, body, line=0, column=0):
        super().__init__(NodeType.WHILE, line, column)
        self.condition = condition
        self.body = body


class ForNode(ASTNode):
    """Boucle for."""
    def __init__(self, var_name, iterable, body, line=0, column=0):
        super().__init__(NodeType.FOR, line, column)
        self.var_name = var_name
        self.iterable = iterable
        self.body = body


class ReturnNode(ASTNode):
    """Instruction return."""
    def __init__(self, value, line=0, column=0):
        super().__init__(NodeType.RETURN, line, column)
        self.value = value


class GiveStmtNode(ASTNode):
    """Instruction give (donner des recompenses)."""
    def __init__(self, rewards, line=0, column=0):
        super().__init__(NodeType.GIVE_STMT, line, column)
        self.rewards = rewards  # Liste de ResourceNode


class TakeStmtNode(ASTNode):
    """Instruction take (prendre des couts)."""
    def __init__(self, rewards, line=0, column=0):
        super().__init__(NodeType.TAKE_STMT, line, column)
        self.rewards = rewards


class CallStmtNode(ASTNode):
    """Appel de fonction comme instruction."""
    def __init__(self, call_expr, line=0, column=0):
        super().__init__(NodeType.CALL_STMT, line, column)
        self.call_expr = call_expr


class BlockNode(ASTNode):
    """Bloc d'instructions."""
    def __init__(self, statements, line=0, column=0):
        super().__init__(NodeType.BLOCK, line, column)
        self.statements = statements


class BinaryOpNode(ASTNode):
    """Operation binaire."""
    def __init__(self, op, left, right, line=0, column=0):
        super().__init__(NodeType.BINARY_OP, line, column)
        self.op = op
        self.left = left
        self.right = right


class UnaryOpNode(ASTNode):
    """Operation unaire."""
    def __init__(self, op, operand, line=0, column=0):
        super().__init__(NodeType.UNARY_OP, line, column)
        self.op = op
        self.operand = operand


class LiteralNode(ASTNode):
    """Valeur litterale."""
    def __init__(self, value, line=0, column=0):
        super().__init__(NodeType.LITERAL, line, column)
        self.value = value


class IdentifierNode(ASTNode):
    """Reference a un identifiant."""
    def __init__(self, name, line=0, column=0):
        super().__init__(NodeType.IDENTIFIER, line, column)
        self.name = name


class IndexNode(ASTNode):
    """Acces par index (liste[i])."""
    def __init__(self, target, index, line=0, column=0):
        super().__init__(NodeType.INDEX, line, column)
        self.target = target
        self.index = index


class CallExprNode(ASTNode):
    """Appel de fonction dans une expression."""
    def __init__(self, name, args, line=0, column=0):
        super().__init__(NodeType.CALL, line, column)
        self.name = name
        self.args = args


class ListLiteralNode(ASTNode):
    """Litteral de liste [a, b, c]."""
    def __init__(self, elements, line=0, column=0):
        super().__init__(NodeType.LIST_LITERAL, line, column)
        self.elements = elements


class PropertyAccessNode(ASTNode):
    """Acces a une propriete (obj.prop)."""
    def __init__(self, target, property_name, line=0, column=0):
        super().__init__(NodeType.PROPERTY_ACCESS, line, column)
        self.target = target
        self.property_name = property_name


class ResourceNode(ASTNode):
    """Ressource (xp, gold, item)."""
    def __init__(self, resource_type, name, amount=None, quantity=None, line=0, column=0):
        super().__init__(NodeType.RESOURCE, line, column)
        self.resource_type = resource_type  # "gold", "xp", "item"
        self.name = name
        self.amount = amount  # ExpressionNode pour gold/xp
        self.quantity = quantity  # ExpressionNode pour item


class RewardListNode(ASTNode):
    """Liste de recompenses."""
    def __init__(self, rewards, line=0, column=0):
        super().__init__(NodeType.REWARD_LIST, line, column)
        self.rewards = rewards


class IdListNode(ASTNode):
    """Liste d'identifiants."""
    def __init__(self, ids, line=0, column=0):
        super().__init__(NodeType.ID_LIST, line, column)
        self.ids = ids
