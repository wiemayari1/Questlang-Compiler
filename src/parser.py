# -*- coding: utf-8 -*-
"""
Analyse syntaxique pour QuestLang v2.
Parser recursif descendant LL(1) avec recuperation d'erreurs.
"""

from lexer import Lexer, Token, TokenType
from ast_nodes import *
from errors import SyntaxError

class Parser:
    """
    Parser recursif descendant pour QuestLang.
    Grammaire LL(1) avec gestion des erreurs et recuperation.
    """

    def __init__(self, tokens, filename=""):
        self.tokens = tokens
        self.pos = 0
        self.filename = filename
        self.errors = []

    def error(self, message, token=None):
        if token is None:
            token = self.current()
        err = SyntaxError(message, token.line, token.column, self.filename)
        self.errors.append(err)
        return err

    def current(self):
        if self.pos >= len(self.tokens):
            return self.tokens[-1] if self.tokens else Token(TokenType.EOF, None, 0, 0)
        return self.tokens[self.pos]

    def peek(self, offset=1):
        idx = self.pos + offset
        if idx >= len(self.tokens):
            return self.tokens[-1] if self.tokens else Token(TokenType.EOF, None, 0, 0)
        return self.tokens[idx]

    def match(self, *types):
        return self.current().type in types

    def consume(self, expected_type=None):
        token = self.current()
        if expected_type and token.type != expected_type:
            self.error(f"Attendu {expected_type.name}, trouve {token.type.name}")
            return token
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
        """Point d'entree: parse un programme complet."""
        declarations = []
        self.skip_newlines()

        while not self.match(TokenType.EOF):
            self.skip_newlines()
            if self.match(TokenType.EOF):
                break

            try:
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
                    self.error(f"Declaration inattendue: {self.current().value}")
                    self.consume()
                    continue

                if decl:
                    declarations.append(decl)
            except Exception as e:
                self.error(f"Erreur de parsing: {str(e)}")
                self.synchronize()

        program = ProgramNode(declarations)
        for decl in declarations:
            program.add_declaration(decl)

        return program

    def synchronize(self):
        """Recuperation d'erreurs: avance jusqu'au prochain point de synchronisation."""
        self.consume()
        while not self.match(TokenType.EOF):
            if self.current().type in [TokenType.WORLD, TokenType.QUEST,
                                       TokenType.ITEM, TokenType.NPC,
                                       TokenType.FUNC, TokenType.VAR]:
                return
            self.consume()

    def parse_world(self):
        """world ID { worldStmt* }"""
        line = self.current().line
        col = self.current().column
        self.consume(TokenType.WORLD)
        name_tok = self.expect(TokenType.IDENTIFIER, "Attendu le nom du monde")
        name = name_tok.value if name_tok else "monde"
        self.expect(TokenType.LBRACE, "Attendu '{' apres le nom du monde")

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

        self.expect(TokenType.RBRACE, "Attendu '}' a la fin du bloc world")

        node = WorldNode(name, properties, line, col)
        node.variables = variables
        return node

    def parse_world_property(self):
        """start | start_gold | win_condition : expr ;"""
        if self.match(TokenType.START):
            key = "start"
            self.consume()
        elif self.match(TokenType.START_GOLD):
            key = "start_gold"
            self.consume()
        elif self.match(TokenType.WIN_CONDITION):
            key = "win_condition"
            self.consume()
        else:
            self.error(f"Propriete world inattendue: {self.current().value}")
            self.consume()
            return None

        self.expect(TokenType.COLON, "Attendu ':' apres la propriete")
        value = self.parse_expression()
        self.expect(TokenType.SEMICOLON, "Attendu ';' apres la valeur")
        return (key, value)

    def parse_quest(self):
        """quest ID { questStmt* }"""
        line = self.current().line
        col = self.current().column
        self.consume(TokenType.QUEST)
        name_tok = self.expect(TokenType.IDENTIFIER, "Attendu le nom de la quete")
        name = name_tok.value if name_tok else "quete"
        self.expect(TokenType.LBRACE, "Attendu '{' apres le nom de la quete")

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

        self.expect(TokenType.RBRACE, "Attendu '}' a la fin du bloc quest")

        node = QuestNode(name, properties, script, line, col)
        return node

    def parse_quest_property(self):
        """title | desc | requires | unlocks | rewards | costs | condition : value ;"""
        prop_map = {
            TokenType.TITLE: "title",
            TokenType.DESC: "desc",
            TokenType.REQUIRES: "requires",
            TokenType.UNLOCKS: "unlocks",
            TokenType.REWARDS: "rewards",
            TokenType.COSTS: "costs",
            TokenType.CONDITION: "condition",
        }

        if self.current().type in prop_map:
            key = prop_map[self.current().type]
            self.consume()
            self.expect(TokenType.COLON, "Attendu ':' apres la propriete")

            if key in ["title", "desc", "condition"]:
                value = self.parse_expression()
            elif key in ["requires", "unlocks"]:
                value = self.parse_id_list()
            elif key in ["rewards", "costs"]:
                value = self.parse_reward_list()
            else:
                value = self.parse_expression()

            self.expect(TokenType.SEMICOLON, "Attendu ';' apres la valeur")
            return (key, value)
        else:
            self.error(f"Propriete de quete inattendue: {self.current().value}")
            self.consume()
            return None

    def parse_script(self):
        """script { stmt* }"""
        line = self.current().line
        col = self.current().column
        self.consume(TokenType.SCRIPT)
        self.expect(TokenType.LBRACE, "Attendu '{' apres 'script'")
        stmts = self.parse_statement_list()
        self.expect(TokenType.RBRACE, "Attendu '}' a la fin du script")
        return BlockNode(stmts, line, col)

    def parse_item(self):
        """item ID { itemStmt* }"""
        line = self.current().line
        col = self.current().column
        self.consume(TokenType.ITEM)
        name_tok = self.expect(TokenType.IDENTIFIER, "Attendu le nom de l'item")
        name = name_tok.value if name_tok else "item"
        self.expect(TokenType.LBRACE, "Attendu '{' apres le nom de l'item")

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

        self.expect(TokenType.RBRACE, "Attendu '}' a la fin du bloc item")
        return ItemNode(name, properties, line, col)

    def parse_item_property(self):
        """title | value | stackable | type : value ;"""
        prop_map = {
            TokenType.TITLE: "title",
            TokenType.VALUE: "value",
            TokenType.STACKABLE: "stackable",
            TokenType.TYPE: "type",
        }

        if self.current().type in prop_map:
            key = prop_map[self.current().type]
            self.consume()
            self.expect(TokenType.COLON, "Attendu ':' apres la propriete")

            if key == "title":
                value = self.parse_expression()
            elif key == "type":
                type_keywords = [TokenType.WEAPON, TokenType.ARMOR, TokenType.KEY,
                                 TokenType.REAGENT, TokenType.CONSUMABLE, TokenType.MISC,
                                 TokenType.IDENTIFIER]
                if self.match(*type_keywords):
                    type_tok = self.consume()
                    value = type_tok.value
                else:
                    self.error("Attendu un type d'item (weapon, armor, key, reagent, consumable, misc)")
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

            self.expect(TokenType.SEMICOLON, "Attendu ';' apres la valeur")
            return (key, value)
        else:
            self.error(f"Propriete d'item inattendue: {self.current().value}")
            self.consume()
            return None

    def parse_npc(self):
        """npc ID { npcStmt* }"""
        line = self.current().line
        col = self.current().column
        self.consume(TokenType.NPC)
        name_tok = self.expect(TokenType.IDENTIFIER, "Attendu le nom du PNJ")
        name = name_tok.value if name_tok else "pnj"
        self.expect(TokenType.LBRACE, "Attendu '{' apres le nom du PNJ")

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

        self.expect(TokenType.RBRACE, "Attendu '}' a la fin du bloc npc")
        return NPCNode(name, properties, line, col)

    def parse_npc_property(self):
        """title | location | gives_quest : value ;"""
        prop_map = {
            TokenType.TITLE: "title",
            TokenType.LOCATION: "location",
            TokenType.GIVES_QUEST: "gives_quest",
        }

        if self.current().type in prop_map:
            key = prop_map[self.current().type]
            self.consume()
            self.expect(TokenType.COLON, "Attendu ':' apres la propriete")

            if key == "title":
                value = self.parse_expression()
            elif key == "location":
                loc_tok = self.expect(TokenType.IDENTIFIER, "Attendu un identifiant de lieu")
                value = loc_tok.value if loc_tok else ""
            elif key == "gives_quest":
                value = self.parse_id_list()
            else:
                value = self.parse_expression()

            self.expect(TokenType.SEMICOLON, "Attendu ';' apres la valeur")
            return (key, value)
        else:
            self.error(f"Propriete de PNJ inattendue: {self.current().value}")
            self.consume()
            return None

    def parse_function(self):
        """func ID ( params ) { stmt* }"""
        line = self.current().line
        col = self.current().column
        self.consume(TokenType.FUNC)
        name_tok = self.expect(TokenType.IDENTIFIER, "Attendu le nom de la fonction")
        name = name_tok.value if name_tok else "fonction"

        self.expect(TokenType.LPAREN, "Attendu '(' apres le nom de la fonction")
        params = []
        if not self.match(TokenType.RPAREN):
            params.append(self.consume(TokenType.IDENTIFIER).value)
            while self.match(TokenType.COMMA):
                self.consume()
                params.append(self.consume(TokenType.IDENTIFIER).value)
        self.expect(TokenType.RPAREN, "Attendu ')' apres les parametres")

        self.expect(TokenType.LBRACE, "Attendu '{' pour le corps de la fonction")
        body = self.parse_statement_list()
        self.expect(TokenType.RBRACE, "Attendu '}' a la fin de la fonction")

        return FunctionNode(name, params, BlockNode(body, line, col), line, col)

    def parse_var_decl(self):
        """var ID = expr ;"""
        line = self.current().line
        col = self.current().column
        self.consume(TokenType.VAR)
        name_tok = self.expect(TokenType.IDENTIFIER, "Attendu le nom de la variable")
        name = name_tok.value if name_tok else "var"
        self.expect(TokenType.ASSIGN, "Attendu '=' apres le nom de la variable")
        init = self.parse_expression()
        self.expect(TokenType.SEMICOLON, "Attendu ';' apres l'initialisation")
        return VarDeclNode(name, init, None, line, col)

    def parse_statement_list(self):
        """Parse une liste d'instructions jusqu'a '}'."""
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
        """Parse une instruction."""
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
            self.error(f"Instruction inattendue: {self.current().value}")
            self.consume()
            return None

    def parse_if(self):
        """if ( expr ) { stmt* } [ else { stmt* } ]"""
        line = self.current().line
        col = self.current().column
        self.consume(TokenType.IF)
        self.expect(TokenType.LPAREN, "Attendu '(' apres 'if'")
        condition = self.parse_expression()
        self.expect(TokenType.RPAREN, "Attendu ')' apres la condition")
        self.expect(TokenType.LBRACE, "Attendu '{' apres la condition")
        then_block = BlockNode(self.parse_statement_list(), line, col)
        self.expect(TokenType.RBRACE, "Attendu '}' a la fin du bloc then")

        else_block = None
        if self.match(TokenType.ELSE):
            self.consume()
            self.expect(TokenType.LBRACE, "Attendu '{' apres 'else'")
            else_block = BlockNode(self.parse_statement_list(), line, col)
            self.expect(TokenType.RBRACE, "Attendu '}' a la fin du bloc else")

        return IfNode(condition, then_block, else_block, line, col)

    def parse_while(self):
        """while ( expr ) { stmt* }"""
        line = self.current().line
        col = self.current().column
        self.consume(TokenType.WHILE)
        self.expect(TokenType.LPAREN, "Attendu '(' apres 'while'")
        condition = self.parse_expression()
        self.expect(TokenType.RPAREN, "Attendu ')' apres la condition")
        self.expect(TokenType.LBRACE, "Attendu '{' apres la condition")
        body = BlockNode(self.parse_statement_list(), line, col)
        self.expect(TokenType.RBRACE, "Attendu '}' a la fin du bloc while")
        return WhileNode(condition, body, line, col)

    def parse_for(self):
        """for ID in expr { stmt* }"""
        line = self.current().line
        col = self.current().column
        self.consume(TokenType.FOR)
        var_tok = self.expect(TokenType.IDENTIFIER, "Attendu le nom de la variable de boucle")
        var_name = var_tok.value if var_tok else "i"
        self.expect(TokenType.IN, "Attendu 'in' apres la variable")
        iterable = self.parse_expression()
        self.expect(TokenType.LBRACE, "Attendu '{' apres l'iterable")
        body = BlockNode(self.parse_statement_list(), line, col)
        self.expect(TokenType.RBRACE, "Attendu '}' a la fin du bloc for")
        return ForNode(var_name, iterable, body, line, col)

    def parse_return(self):
        """return expr ;"""
        line = self.current().line
        col = self.current().column
        self.consume(TokenType.RETURN)
        value = self.parse_expression()
        self.expect(TokenType.SEMICOLON, "Attendu ';' apres return")
        return ReturnNode(value, line, col)

    def parse_give(self):
        """give rewardList ;"""
        line = self.current().line
        col = self.current().column
        self.consume(TokenType.GIVE)
        rewards = self.parse_reward_list()
        self.expect(TokenType.SEMICOLON, "Attendu ';' apres give")
        return GiveStmtNode(rewards.rewards if isinstance(rewards, RewardListNode) else rewards, line, col)

    def parse_take(self):
        """take rewardList ;"""
        line = self.current().line
        col = self.current().column
        self.consume(TokenType.TAKE)
        rewards = self.parse_reward_list()
        self.expect(TokenType.SEMICOLON, "Attendu ';' apres take")
        return TakeStmtNode(rewards.rewards if isinstance(rewards, RewardListNode) else rewards, line, col)

    def parse_call_stmt(self):
        """call ID ( args ) ;"""
        line = self.current().line
        col = self.current().column
        self.consume(TokenType.CALL)
        name_tok = self.expect(TokenType.IDENTIFIER, "Attendu le nom de la fonction")
        name = name_tok.value if name_tok else ""
        self.expect(TokenType.LPAREN, "Attendu '(' apres le nom")
        args = self.parse_arg_list()
        self.expect(TokenType.RPAREN, "Attendu ')' apres les arguments")
        self.expect(TokenType.SEMICOLON, "Attendu ';' apres l'appel")
        return CallStmtNode(CallExprNode(name, args, line, col), line, col)

    def parse_assignment_or_call(self):
    """ID = expr ; | ID += expr ; | ID -= expr ; | ID ( args ) ; | ID [ expr ] = expr ;"""
    line = self.current().line
    col = self.current().column
    name_tok = self.consume(TokenType.IDENTIFIER)
    name = name_tok.value

    if self.match(TokenType.LPAREN):
        self.consume()
        args = self.parse_arg_list()
        self.expect(TokenType.RPAREN, "Attendu ')' apres les arguments")
        self.expect(TokenType.SEMICOLON, "Attendu ';' apres l'appel")
        return CallStmtNode(CallExprNode(name, args, line, col), line, col)

    target = IdentifierNode(name, line, col)

    if self.match(TokenType.LBRACKET):
        self.consume()
        index = self.parse_expression()
        self.expect(TokenType.RBRACKET, "Attendu ']' apres l'index")
        target = IndexNode(target, index, line, col)

    if self.match(TokenType.ASSIGN):
        self.consume()
        value = self.parse_expression()
        self.expect(TokenType.SEMICOLON, "Attendu ';' apres l'affectation")
        return AssignNode(target, value, line, col)
    elif self.match(TokenType.PLUS_ASSIGN):
        self.consume()
        value = self.parse_expression()
        self.expect(TokenType.SEMICOLON, "Attendu ';' apres +=")
        return CompoundAssignNode(target, '+=', value, line, col)
    elif self.match(TokenType.MINUS_ASSIGN):
        self.consume()
        value = self.parse_expression()
        self.expect(TokenType.SEMICOLON, "Attendu ';' apres -=")
        return CompoundAssignNode(target, '-=', value, line, col)
    else:
        # CORRECTION ANTI-BOUCLE INFINIE
        self.error("Attendu '=', '+=', '-=' ou '(' apres l'identifiant")
        # On avance jusqu'au prochain point de synchronisation
        while not self.match(TokenType.SEMICOLON, TokenType.RBRACE, TokenType.EOF, TokenType.NEWLINE):
            self.consume()
        if self.match(TokenType.SEMICOLON):
            self.consume()
        return None

    def parse_expression(self):
        """expr ::= or_expr"""
        return self.parse_or_expr()

    def parse_or_expr(self):
        """or_expr ::= and_expr ( 'or' and_expr )*"""
        left = self.parse_and_expr()
        while self.match(TokenType.OR):
            op = self.consume().value
            right = self.parse_and_expr()
            left = BinaryOpNode(op, left, right, left.line, left.column)
        return left

    def parse_and_expr(self):
        """and_expr ::= equality_expr ( 'and' equality_expr )*"""
        left = self.parse_equality_expr()
        while self.match(TokenType.AND):
            op = self.consume().value
            right = self.parse_equality_expr()
            left = BinaryOpNode(op, left, right, left.line, left.column)
        return left

    def parse_equality_expr(self):
        """equality_expr ::= comparison_expr ( ( '==' | '!=' ) comparison_expr )*"""
        left = self.parse_comparison_expr()
        while self.match(TokenType.EQ, TokenType.NEQ):
            op = self.consume().value
            right = self.parse_comparison_expr()
            left = BinaryOpNode(op, left, right, left.line, left.column)
        return left

    def parse_comparison_expr(self):
        """comparison_expr ::= additive_expr ( ( '<' | '>' | '<=' | '>=' ) additive_expr )*"""
        left = self.parse_additive_expr()
        while self.match(TokenType.LT, TokenType.GT, TokenType.LTE, TokenType.GTE):
            op = self.consume().value
            right = self.parse_additive_expr()
            left = BinaryOpNode(op, left, right, left.line, left.column)
        return left

    def parse_additive_expr(self):
        """additive_expr ::= multiplicative_expr ( ( '+' | '-' ) multiplicative_expr )*"""
        left = self.parse_multiplicative_expr()
        while self.match(TokenType.PLUS, TokenType.MINUS):
            op = self.consume().value
            right = self.parse_multiplicative_expr()
            left = BinaryOpNode(op, left, right, left.line, left.column)
        return left

    def parse_multiplicative_expr(self):
        """multiplicative_expr ::= power_expr ( ( '*' | '/' | '%' ) power_expr )*"""
        left = self.parse_power_expr()
        while self.match(TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            op = self.consume().value
            right = self.parse_power_expr()
            left = BinaryOpNode(op, left, right, left.line, left.column)
        return left

    def parse_power_expr(self):
        """power_expr ::= unary_expr ( '^' unary_expr )*"""
        left = self.parse_unary_expr()
        while self.match(TokenType.POWER):
            op = self.consume().value
            right = self.parse_unary_expr()
            left = BinaryOpNode(op, left, right, left.line, left.column)
        return left

    def parse_unary_expr(self):
        """unary_expr ::= ( '-' | 'not' )? primary"""
        if self.match(TokenType.MINUS, TokenType.NOT):
            op = self.consume().value
            operand = self.parse_unary_expr()
            return UnaryOpNode(op, operand, self.current().line, self.current().column)
        return self.parse_primary()

    def parse_primary(self):
        """primary ::= NUMBER | STRING | BOOL | ID | '(' expr ')' | ID '(' args ')' | '[' elements ']' | ID '[' expr ']' | ID '.' ID | CALL ID '(' args ')'"""
        line = self.current().line
        col = self.current().column

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
            self.expect(TokenType.RPAREN, "Attendu ')' apres l'expression")
            return expr

        if self.match(TokenType.LBRACKET):
            return self.parse_list_literal()

        # FIX #3: Ajouter le support de CALL dans les expressions
        if self.match(TokenType.CALL):
            self.consume(TokenType.CALL)
            name_tok = self.expect(TokenType.IDENTIFIER, "Attendu le nom de la fonction apres 'call'")
            name = name_tok.value if name_tok else ""
            self.expect(TokenType.LPAREN, "Attendu '(' apres le nom de la fonction")
            args = self.parse_arg_list()
            self.expect(TokenType.RPAREN, "Attendu ')' apres les arguments")
            return CallExprNode(name, args, line, col)

        if self.match(TokenType.IDENTIFIER):
            name = self.consume().value

            if self.match(TokenType.LPAREN):
                self.consume()
                args = self.parse_arg_list()
                self.expect(TokenType.RPAREN, "Attendu ')' apres les arguments")
                return CallExprNode(name, args, line, col)

            if self.match(TokenType.LBRACKET):
                self.consume()
                index = self.parse_expression()
                self.expect(TokenType.RBRACKET, "Attendu ']' apres l'index")
                return IndexNode(IdentifierNode(name, line, col), index, line, col)

            if self.match(TokenType.DOT):
                self.consume()
                prop_tok = self.expect(TokenType.IDENTIFIER, "Attendu un nom de propriete")
                prop = prop_tok.value if prop_tok else ""
                return PropertyAccessNode(IdentifierNode(name, line, col), prop, line, col)

            return IdentifierNode(name, line, col)

        self.error(f"Expression inattendue: {self.current().value}")
        self.consume()
        return LiteralNode(None, line, col)

    def parse_list_literal(self):
        """[ expr ( , expr )* ]"""
        line = self.current().line
        col = self.current().column
        self.consume(TokenType.LBRACKET)
        elements = []
        if not self.match(TokenType.RBRACKET):
            elements.append(self.parse_expression())
            while self.match(TokenType.COMMA):
                self.consume()
                elements.append(self.parse_expression())
        self.expect(TokenType.RBRACKET, "Attendu ']' a la fin de la liste")
        return ListLiteralNode(elements, line, col)

    def parse_arg_list(self):
        """expr ( , expr )*"""
        args = []
        if not self.match(TokenType.RPAREN):
            args.append(self.parse_expression())
            while self.match(TokenType.COMMA):
                self.consume()
                args.append(self.parse_expression())
        return args

    def parse_reward_list(self):
        """reward ( , reward )*"""
        line = self.current().line
        col = self.current().column
        rewards = []
        rewards.append(self.parse_reward())
        while self.match(TokenType.COMMA):
            self.consume()
            rewards.append(self.parse_reward())
        return RewardListNode(rewards, line, col)

    def parse_reward(self):
        """xp expr | gold expr | expr ID"""
        line = self.current().line
        col = self.current().column

        if self.match(TokenType.IDENTIFIER) and self.current().value in ['xp', 'gold']:
            rtype = self.consume().value
            amount = self.parse_expression()
            return ResourceNode(rtype, rtype, amount, None, line, col)

        amount = self.parse_expression()
        name_tok = self.expect(TokenType.IDENTIFIER, "Attendu le nom de l'item")
        name = name_tok.value if name_tok else "item"
        return ResourceNode("item", name, None, amount, line, col)

    def parse_id_list(self):
        """ID ( , ID )*"""
        line = self.current().line
        col = self.current().column
        ids = []
        ids.append(self.consume(TokenType.IDENTIFIER).value)
        while self.match(TokenType.COMMA):
            self.consume()
            ids.append(self.consume(TokenType.IDENTIFIER).value)
        return IdListNode(ids, line, col)
