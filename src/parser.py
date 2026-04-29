# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from lexer import Token, TokenType
from ast_nodes import *
from errors import SyntaxError as QLSyntaxError

class Parser:
    def __init__(self, tokens, filename=""):
        self.tokens = tokens
        self.pos = 0
        self.filename = filename
        self.errors = []

    def error(self, message, token=None):
        if token is None:
            token = self.current()
        err = QLSyntaxError(message, token.line, token.column, self.filename)
        self.errors.append(err)
        raise err

    def current(self):
        if self.pos >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[self.pos]

    def peek(self, offset=1):
        idx = self.pos + offset
        if idx >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[idx]

    def match(self, *types):
        return self.current().type in types

    def consume(self, expected_type=None):
        token = self.current()
        if expected_type and token.type != expected_type:
            self.error(f"Attendu {expected_type.name}, trouve {token.type.name}")
        self.pos += 1
        return token

    def skip_newlines(self):
        while self.match(TokenType.NEWLINE):
            self.consume()

    def expect(self, token_type, message=None):
        if not self.match(token_type):
            msg = message or f"Attendu {token_type.name}"
            self.error(msg)
            return None
        return self.consume()

    def parse(self):
        declarations = []
        self.skip_newlines()
        while not self.match(TokenType.EOF):
            self.skip_newlines()
            if self.match(TokenType.EOF):
                break
            if self.match(TokenType.WORLD):
                decl = self.parse_world()
            elif self.match(TokenType.QUEST):
                decl = self.parse_quest()
            elif self.match(TokenType.ITEM):
                decl = self.parse_item()
            elif self.match(TokenType.NPC):
                decl = self.parse_npc()
            elif self.match(TokenType.FUNC):
                decl = self.parse_function()
            elif self.match(TokenType.VAR):
                decl = self.parse_var_decl()
            else:
                self.error(f"Declaration inattendue: {self.current().value!r}")
            if decl:
                declarations.append(decl)

        program = ProgramNode(declarations)
        for decl in declarations:
            program.add_declaration(decl)
        return program

    def parse_world(self):
        line, col = self.current().line, self.current().column
        self.consume(TokenType.WORLD)
        name_tok = self.expect(TokenType.IDENTIFIER, "Attendu le nom du monde")
        name = name_tok.value if name_tok else "monde"
        self.expect(TokenType.LBRACE)
        properties = {}
        variables = []
        self.skip_newlines()
        while not self.match(TokenType.RBRACE) and not self.match(TokenType.EOF):
            self.skip_newlines()
            if self.match(TokenType.RBRACE):
                break
            if self.match(TokenType.VAR):
                variables.append(self.parse_var_decl())
            else:
                prop = self.parse_world_property()
                if prop:
                    properties[prop[0]] = prop[1]
            self.skip_newlines()
        self.expect(TokenType.RBRACE)
        node = WorldNode(name, properties, line, col)
        node.variables = variables
        return node

    def parse_world_property(self):
        key_map = {
            TokenType.START: "start",
            TokenType.START_GOLD: "start_gold",
            TokenType.WIN_CONDITION: "win_condition"
        }
        if self.current().type in key_map:
            key = key_map[self.current().type]
            self.consume()
            self.expect(TokenType.COLON)
            value = self.parse_expression()
            self.expect(TokenType.SEMICOLON)
            return (key, value)
        self.error(f"Propriete world inattendue: {self.current().value!r}")
        self.consume()
        return None

    def parse_quest(self):
        line, col = self.current().line, self.current().column
        self.consume(TokenType.QUEST)
        name_tok = self.expect(TokenType.IDENTIFIER)
        name = name_tok.value if name_tok else "quete"
        self.expect(TokenType.LBRACE)
        properties = {}
        script = None
        self.skip_newlines()
        while not self.match(TokenType.RBRACE) and not self.match(TokenType.EOF):
            self.skip_newlines()
            if self.match(TokenType.RBRACE):
                break
            if self.match(TokenType.SCRIPT):
                script = self.parse_script()
            else:
                prop = self.parse_quest_property()
                if prop:
                    properties[prop[0]] = prop[1]
            self.skip_newlines()
        self.expect(TokenType.RBRACE)
        return QuestNode(name, properties, script, line, col)

    def parse_quest_property(self):
        prop_map = {
            TokenType.TITLE: "title", TokenType.DESC: "desc", TokenType.REQUIRES: "requires",
            TokenType.UNLOCKS: "unlocks", TokenType.REWARDS: "rewards", TokenType.COSTS: "costs",
            TokenType.CONDITION: "condition",
        }
        if self.current().type in prop_map:
            key = prop_map[self.current().type]
            self.consume()
            self.expect(TokenType.COLON)
            if key in ("title", "desc", "condition"):
                value = self.parse_expression()
            elif key in ("requires", "unlocks"):
                value = self.parse_id_list()
            elif key in ("rewards", "costs"):
                value = self.parse_reward_list()
            else:
                value = self.parse_expression()
            self.expect(TokenType.SEMICOLON)
            return (key, value)
        self.error(f"Propriete quete inattendue: {self.current().value!r}")
        self.consume()
        return None

    def parse_script(self):
        line, col = self.current().line, self.current().column
        self.consume(TokenType.SCRIPT)
        self.expect(TokenType.LBRACE)
        stmts = self.parse_statement_list()
        self.expect(TokenType.RBRACE)
        return BlockNode(stmts, line, col)

    def parse_item(self):
        line, col = self.current().line, self.current().column
        self.consume(TokenType.ITEM)
        name_tok = self.expect(TokenType.IDENTIFIER)
        name = name_tok.value if name_tok else "item"
        self.expect(TokenType.LBRACE)
        properties = {}
        self.skip_newlines()
        while not self.match(TokenType.RBRACE) and not self.match(TokenType.EOF):
            self.skip_newlines()
            if self.match(TokenType.RBRACE):
                break
            prop = self.parse_item_property()
            if prop:
                properties[prop[0]] = prop[1]
            self.skip_newlines()
        self.expect(TokenType.RBRACE)
        return ItemNode(name, properties, line, col)

    def parse_item_property(self):
        prop_map = {
            TokenType.TITLE: "title", TokenType.VALUE: "value",
            TokenType.STACKABLE: "stackable", TokenType.TYPE: "type"
        }
        type_kws = {
            TokenType.WEAPON, TokenType.ARMOR, TokenType.KEY, TokenType.REAGENT,
            TokenType.CONSUMABLE, TokenType.MISC, TokenType.ARTIFACT, TokenType.MATERIAL,
            TokenType.IDENTIFIER
        }
        if self.current().type in prop_map:
            key = prop_map[self.current().type]
            self.consume()
            self.expect(TokenType.COLON)
            if key == "type":
                if self.current().type in type_kws:
                    value = self.consume().value
                else:
                    value = "misc"
            elif key == "stackable":
                if self.match(TokenType.TRUE):
                    self.consume()
                    value = True
                elif self.match(TokenType.FALSE):
                    self.consume()
                    value = False
                else:
                    value = self.parse_expression()
            else:
                value = self.parse_expression()
            self.expect(TokenType.SEMICOLON)
            return (key, value)
        self.error(f"Propriete item inattendue: {self.current().value!r}")
        self.consume()
        return None

    def parse_npc(self):
        line, col = self.current().line, self.current().column
        self.consume(TokenType.NPC)
        name_tok = self.expect(TokenType.IDENTIFIER)
        name = name_tok.value if name_tok else "pnj"
        self.expect(TokenType.LBRACE)
        properties = {}
        self.skip_newlines()
        while not self.match(TokenType.RBRACE) and not self.match(TokenType.EOF):
            self.skip_newlines()
            if self.match(TokenType.RBRACE):
                break
            prop = self.parse_npc_property()
            if prop:
                properties[prop[0]] = prop[1]
            self.skip_newlines()
        self.expect(TokenType.RBRACE)
        return NPCNode(name, properties, line, col)

    def parse_npc_property(self):
        prop_map = {
            TokenType.TITLE: "title",
            TokenType.LOCATION: "location",
            TokenType.GIVES_QUEST: "gives_quest"
        }
        if self.current().type in prop_map:
            key = prop_map[self.current().type]
            self.consume()
            self.expect(TokenType.COLON)
            if key == "title":
                value = self.parse_expression()
            elif key == "location":
                tok = self.expect(TokenType.IDENTIFIER, "Attendu identifiant de lieu")
                value = tok.value if tok else ""
            elif key == "gives_quest":
                value = self.parse_id_list()
            else:
                value = self.parse_expression()
            self.expect(TokenType.SEMICOLON)
            return (key, value)
        self.error(f"Propriete NPC inattendue: {self.current().value!r}")
        self.consume()
        return None

    def parse_function(self):
        line, col = self.current().line, self.current().column
        self.consume(TokenType.FUNC)
        name_tok = self.expect(TokenType.IDENTIFIER)
        name = name_tok.value if name_tok else "fn"
        self.expect(TokenType.LPAREN)
        params = []
        if not self.match(TokenType.RPAREN):
            params.append(self.consume(TokenType.IDENTIFIER).value)
            while self.match(TokenType.COMMA):
                self.consume()
                params.append(self.consume(TokenType.IDENTIFIER).value)
        self.expect(TokenType.RPAREN)
        self.expect(TokenType.LBRACE)
        body = self.parse_statement_list()
        self.expect(TokenType.RBRACE)
        return FunctionNode(name, params, BlockNode(body, line, col), line, col)

    def parse_var_decl(self):
        line, col = self.current().line, self.current().column
        self.consume(TokenType.VAR)
        name_tok = self.expect(TokenType.IDENTIFIER)
        name = name_tok.value if name_tok else "v"
        self.expect(TokenType.ASSIGN)
        init = self.parse_expression()
        self.expect(TokenType.SEMICOLON)
        return VarDeclNode(name, init, None, line, col)

    def parse_statement_list(self):
        stmts = []
        self.skip_newlines()
        while not self.match(TokenType.RBRACE) and not self.match(TokenType.EOF):
            self.skip_newlines()
            if self.match(TokenType.RBRACE):
                break
            stmt = self.parse_statement()
            if stmt:
                stmts.append(stmt)
            self.skip_newlines()
        return stmts

    def parse_statement(self):
        if self.match(TokenType.VAR):
            return self.parse_var_decl()
        elif self.match(TokenType.IF):
            return self.parse_if()
        elif self.match(TokenType.WHILE):
            return self.parse_while()
        elif self.match(TokenType.FOR):
            return self.parse_for()
        elif self.match(TokenType.RETURN):
            return self.parse_return()
        elif self.match(TokenType.GIVE):
            return self.parse_give()
        elif self.match(TokenType.TAKE):
            return self.parse_take()
        elif self.match(TokenType.CALL):
            return self.parse_call_stmt()
        elif self.match(TokenType.IDENTIFIER):
            return self.parse_assignment_or_call()
        else:
            self.error(f"Instruction inattendue: {self.current().value!r}")
            self.consume()
            return None

    def parse_if(self):
        line, col = self.current().line, self.current().column
        self.consume(TokenType.IF)
        self.expect(TokenType.LPAREN)
        cond = self.parse_expression()
        self.expect(TokenType.RPAREN)
        self.expect(TokenType.LBRACE)
        then = BlockNode(self.parse_statement_list(), line, col)
        self.expect(TokenType.RBRACE)
        else_block = None
        if self.match(TokenType.ELSE):
            self.consume()
            self.expect(TokenType.LBRACE)
            else_block = BlockNode(self.parse_statement_list(), line, col)
            self.expect(TokenType.RBRACE)
        return IfNode(cond, then, else_block, line, col)

    def parse_while(self):
        line, col = self.current().line, self.current().column
        self.consume(TokenType.WHILE)
        self.expect(TokenType.LPAREN)
        cond = self.parse_expression()
        self.expect(TokenType.RPAREN)
        self.expect(TokenType.LBRACE)
        body = BlockNode(self.parse_statement_list(), line, col)
        self.expect(TokenType.RBRACE)
        return WhileNode(cond, body, line, col)

    def parse_for(self):
        line, col = self.current().line, self.current().column
        self.consume(TokenType.FOR)
        var_tok = self.expect(TokenType.IDENTIFIER)
        var_name = var_tok.value if var_tok else "i"
        self.expect(TokenType.IN)
        iterable = self.parse_expression()
        self.expect(TokenType.LBRACE)
        body = BlockNode(self.parse_statement_list(), line, col)
        self.expect(TokenType.RBRACE)
        return ForNode(var_name, iterable, body, line, col)

    def parse_return(self):
        line, col = self.current().line, self.current().column
        self.consume(TokenType.RETURN)
        value = self.parse_expression()
        self.expect(TokenType.SEMICOLON)
        return ReturnNode(value, line, col)

    def parse_give(self):
        line, col = self.current().line, self.current().column
        self.consume(TokenType.GIVE)
        rewards = self.parse_reward_list()
        self.expect(TokenType.SEMICOLON)
        r = rewards.rewards if isinstance(rewards, RewardListNode) else rewards
        return GiveStmtNode(r, line, col)

    def parse_take(self):
        line, col = self.current().line, self.current().column
        self.consume(TokenType.TAKE)
        rewards = self.parse_reward_list()
        self.expect(TokenType.SEMICOLON)
        r = rewards.rewards if isinstance(rewards, RewardListNode) else rewards
        return TakeStmtNode(r, line, col)

    def parse_call_stmt(self):
        line, col = self.current().line, self.current().column
        self.consume(TokenType.CALL)
        name_tok = self.expect(TokenType.IDENTIFIER)
        name = name_tok.value if name_tok else ""
        self.expect(TokenType.LPAREN)
        args = self.parse_arg_list()
        self.expect(TokenType.RPAREN)
        self.expect(TokenType.SEMICOLON)
        return CallStmtNode(CallExprNode(name, args, line, col), line, col)

    def parse_assignment_or_call(self):
        line, col = self.current().line, self.current().column
        name = self.consume(TokenType.IDENTIFIER).value
        if self.match(TokenType.LPAREN):
            self.consume()
            args = self.parse_arg_list()
            self.expect(TokenType.RPAREN)
            self.expect(TokenType.SEMICOLON)
            return CallStmtNode(CallExprNode(name, args, line, col), line, col)
        target = IdentifierNode(name, line, col)
        if self.match(TokenType.LBRACKET):
            self.consume()
            index = self.parse_expression()
            self.expect(TokenType.RBRACKET)
            target = IndexNode(target, index, line, col)
        if self.match(TokenType.ASSIGN):
            self.consume()
            value = self.parse_expression()
            self.expect(TokenType.SEMICOLON)
            return AssignNode(target, value, line, col)
        elif self.match(TokenType.PLUS_ASSIGN):
            self.consume()
            value = self.parse_expression()
            self.expect(TokenType.SEMICOLON)
            return CompoundAssignNode(target, '+=', value, line, col)
        elif self.match(TokenType.MINUS_ASSIGN):
            self.consume()
            value = self.parse_expression()
            self.expect(TokenType.SEMICOLON)
            return CompoundAssignNode(target, '-=', value, line, col)
        else:
            self.error("Attendu '=', '+=', '-=' ou '(' apres l'identifiant")
            while not self.match(TokenType.SEMICOLON, TokenType.RBRACE, TokenType.EOF, TokenType.NEWLINE):
                self.consume()
            if self.match(TokenType.SEMICOLON):
                self.consume()
            return None

    def parse_expression(self):
        return self.parse_or_expr()

    def parse_or_expr(self):
        left = self.parse_and_expr()
        while self.match(TokenType.OR):
            op = self.consume().value
            right = self.parse_and_expr()
            left = BinaryOpNode(op, left, right, left.line, left.column)
        return left

    def parse_and_expr(self):
        left = self.parse_equality_expr()
        while self.match(TokenType.AND):
            op = self.consume().value
            right = self.parse_equality_expr()
            left = BinaryOpNode(op, left, right, left.line, left.column)
        return left

    def parse_equality_expr(self):
        left = self.parse_comparison_expr()
        while self.match(TokenType.EQ, TokenType.NEQ):
            op = self.consume().value
            right = self.parse_comparison_expr()
            left = BinaryOpNode(op, left, right, left.line, left.column)
        return left

    def parse_comparison_expr(self):
        left = self.parse_additive_expr()
        while self.match(TokenType.LT, TokenType.GT, TokenType.LTE, TokenType.GTE):
            op = self.consume().value
            right = self.parse_additive_expr()
            left = BinaryOpNode(op, left, right, left.line, left.column)
        return left

    def parse_additive_expr(self):
        left = self.parse_multiplicative_expr()
        while self.match(TokenType.PLUS, TokenType.MINUS):
            op = self.consume().value
            right = self.parse_multiplicative_expr()
            left = BinaryOpNode(op, left, right, left.line, left.column)
        return left

    def parse_multiplicative_expr(self):
        left = self.parse_power_expr()
        while self.match(TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            op = self.consume().value
            right = self.parse_power_expr()
            left = BinaryOpNode(op, left, right, left.line, left.column)
        return left

    def parse_power_expr(self):
        left = self.parse_unary_expr()
        while self.match(TokenType.POWER):
            op = self.consume().value
            right = self.parse_unary_expr()
            left = BinaryOpNode(op, left, right, left.line, left.column)
        return left

    def parse_unary_expr(self):
        if self.match(TokenType.MINUS, TokenType.NOT):
            op = self.consume().value
            operand = self.parse_unary_expr()
            return UnaryOpNode(op, operand, self.current().line, self.current().column)
        return self.parse_primary()

    def parse_primary(self):
        line, col = self.current().line, self.current().column
        if self.match(TokenType.NUMBER):
            return LiteralNode(self.consume().value, line, col)
        if self.match(TokenType.STRING):
            return LiteralNode(self.consume().value, line, col)
        if self.match(TokenType.TRUE):
            self.consume()
            return LiteralNode(True, line, col)
        if self.match(TokenType.FALSE):
            self.consume()
            return LiteralNode(False, line, col)
        if self.match(TokenType.LPAREN):
            self.consume()
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN)
            return expr
        if self.match(TokenType.LBRACKET):
            return self.parse_list_literal()
        if self.match(TokenType.CALL):
            self.consume()
            name_tok = self.expect(TokenType.IDENTIFIER)
            name = name_tok.value if name_tok else ""
            self.expect(TokenType.LPAREN)
            args = self.parse_arg_list()
            self.expect(TokenType.RPAREN)
            return CallExprNode(name, args, line, col)
        if self.match(TokenType.IDENTIFIER):
            name = self.consume().value
            if self.match(TokenType.LPAREN):
                self.consume()
                args = self.parse_arg_list()
                self.expect(TokenType.RPAREN)
                return CallExprNode(name, args, line, col)
            if self.match(TokenType.LBRACKET):
                self.consume()
                index = self.parse_expression()
                self.expect(TokenType.RBRACKET)
                return IndexNode(IdentifierNode(name, line, col), index, line, col)
            if self.match(TokenType.DOT):
                self.consume()
                prop_tok = self.expect(TokenType.IDENTIFIER)
                prop = prop_tok.value if prop_tok else ""
                return PropertyAccessNode(IdentifierNode(name, line, col), prop, line, col)
            return IdentifierNode(name, line, col)
        self.error(f"Expression inattendue: {self.current().value!r}")
        self.consume()
        return LiteralNode(None, line, col)

    def parse_list_literal(self):
        line, col = self.current().line, self.current().column
        self.consume(TokenType.LBRACKET)
        elements = []
        if not self.match(TokenType.RBRACKET):
            elements.append(self.parse_expression())
            while self.match(TokenType.COMMA):
                self.consume()
                elements.append(self.parse_expression())
        self.expect(TokenType.RBRACKET)
        return ListLiteralNode(elements, line, col)

    def parse_arg_list(self):
        args = []
        if not self.match(TokenType.RPAREN):
            args.append(self.parse_expression())
            while self.match(TokenType.COMMA):
                self.consume()
                args.append(self.parse_expression())
        return args

    def parse_reward_list(self):
        line, col = self.current().line, self.current().column
        rewards = [self.parse_reward()]
        while self.match(TokenType.COMMA):
            self.consume()
            rewards.append(self.parse_reward())
        return RewardListNode(rewards, line, col)

    def parse_reward(self):
        line, col = self.current().line, self.current().column
        if self.match(TokenType.IDENTIFIER) and self.current().value in ('xp', 'gold'):
            rtype = self.consume().value
            amount = self.parse_expression()
            return ResourceNode(rtype, rtype, amount, None, line, col)
        amount = self.parse_expression()
        name_tok = self.expect(TokenType.IDENTIFIER, "Attendu nom item")
        name = name_tok.value if name_tok else "item"
        return ResourceNode("item", name, None, amount, line, col)

    def parse_id_list(self):
        line, col = self.current().line, self.current().column
        ids = [self.consume(TokenType.IDENTIFIER).value]
        while self.match(TokenType.COMMA):
            self.consume()
            ids.append(self.consume(TokenType.IDENTIFIER).value)
        return IdListNode(ids, line, col)