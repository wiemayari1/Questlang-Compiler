# -*- coding: utf-8 -*-
"""
Analyse lexicale pour QuestLang v2.
Convertit le code source en une sequence de tokens avec localisation precise.
"""

import re
from enum import Enum, auto

class TokenType(Enum):
    # Mots-cles - blocs
    WORLD = auto()
    QUEST = auto()
    ITEM = auto()
    NPC = auto()
    SCRIPT = auto()
    FUNC = auto()

    # Mots-cles - proprietes
    START = auto()
    START_GOLD = auto()
    WIN_CONDITION = auto()
    TITLE = auto()
    DESC = auto()
    REQUIRES = auto()
    UNLOCKS = auto()
    REWARDS = auto()
    COSTS = auto()
    CONDITION = auto()
    VALUE = auto()
    STACKABLE = auto()
    TYPE = auto()
    LOCATION = auto()
    GIVES_QUEST = auto()

    # Mots-cles - types
    VAR = auto()
    INT = auto()
    FLOAT = auto()
    BOOL = auto()
    STRING_KW = auto()
    LIST = auto()

    # Mots-cles - controle
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    FOR = auto()
    IN = auto()
    RETURN = auto()
    GIVE = auto()
    TAKE = auto()
    CALL = auto()

    # Mots-cles - logique
    AND = auto()
    OR = auto()
    NOT = auto()
    TRUE = auto()
    FALSE = auto()

    # Types d'items
    WEAPON = auto()
    ARMOR = auto()
    KEY = auto()
    REAGENT = auto()
    CONSUMABLE = auto()
    MISC = auto()

    # Litteraux
    IDENTIFIER = auto()
    NUMBER = auto()
    STRING = auto()

    # Operateurs arithmetiques
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()
    POWER = auto()

    # Operateurs de comparaison
    EQ = auto()
    NEQ = auto()
    GT = auto()
    LT = auto()
    GTE = auto()
    LTE = auto()

    # Operateurs d'affectation
    ASSIGN = auto()
    PLUS_ASSIGN = auto()
    MINUS_ASSIGN = auto()

    # Delimiteurs
    COLON = auto()
    SEMICOLON = auto()
    COMMA = auto()
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    DOT = auto()
    ARROW = auto()

    # Special
    NEWLINE = auto()
    COMMENT = auto()
    EOF = auto()
    INDENT = auto()
    DEDENT = auto()

class Token:
    """Represente un token avec son type, valeur et position."""
    def __init__(self, type_, value, line, column, filename=""):
        self.type = type_
        self.value = value
        self.line = line
        self.column = column
        self.filename = filename

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, ligne={self.line}, col={self.column})"

    def __eq__(self, other):
        if isinstance(other, TokenType):
            return self.type == other
        if isinstance(other, Token):
            return self.type == other.type and self.value == other.value
        return False

class Lexer:
    """
    Analyseur lexical pour QuestLang.
    Utilise une approche par automate a etats avec regex.
    """

    KEYWORDS = {
        'world': TokenType.WORLD,
        'quest': TokenType.QUEST,
        'item': TokenType.ITEM,
        'npc': TokenType.NPC,
        'script': TokenType.SCRIPT,
        'func': TokenType.FUNC,
        'start': TokenType.START,
        'start_gold': TokenType.START_GOLD,
        'win_condition': TokenType.WIN_CONDITION,
        'title': TokenType.TITLE,
        'desc': TokenType.DESC,
        'requires': TokenType.REQUIRES,
        'unlocks': TokenType.UNLOCKS,
        'rewards': TokenType.REWARDS,
        'costs': TokenType.COSTS,
        'condition': TokenType.CONDITION,
        'value': TokenType.VALUE,
        'stackable': TokenType.STACKABLE,
        'type': TokenType.TYPE,
        'location': TokenType.LOCATION,
        'gives_quest': TokenType.GIVES_QUEST,
        'var': TokenType.VAR,
        'int': TokenType.INT,
        'float': TokenType.FLOAT,
        'bool': TokenType.BOOL,
        'string': TokenType.STRING_KW,
        'list': TokenType.LIST,
        'if': TokenType.IF,
        'else': TokenType.ELSE,
        'while': TokenType.WHILE,
        'for': TokenType.FOR,
        'in': TokenType.IN,
        'return': TokenType.RETURN,
        'give': TokenType.GIVE,
        'take': TokenType.TAKE,
        'call': TokenType.CALL,
        'and': TokenType.AND,
        'or': TokenType.OR,
        'not': TokenType.NOT,
        'true': TokenType.TRUE,
        'false': TokenType.FALSE,
        'weapon': TokenType.WEAPON,
        'armor': TokenType.ARMOR,
        'key': TokenType.KEY,
        'reagent': TokenType.REAGENT,
        'consumable': TokenType.CONSUMABLE,
        'misc': TokenType.MISC,
        'xp': TokenType.IDENTIFIER,
        'gold': TokenType.IDENTIFIER,
    }

    def __init__(self, source, filename=""):
        self.source = source
        self.filename = filename
        self.tokens = []
        self.pos = 0
        self.line = 1
        self.column = 1
        self.indent_stack = [0]

    def error(self, message):
        from errors import LexicalError
        raise LexicalError(message, self.line, self.column, self.filename)

    def peek(self, offset=0):
        pos = self.pos + offset
        if pos >= len(self.source):
            return '\0'
        return self.source[pos]

    def advance(self):
        char = self.peek()
        self.pos += 1
        if char == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return char

    def skip_whitespace(self):
        while self.peek() in ' \t\r':
            self.advance()

    def skip_comment(self):
        if self.peek() == '/' and self.peek(1) == '/':
            while self.peek() not in '\n\0':
                self.advance()
        elif self.peek() == '/' and self.peek(1) == '*':
            self.advance()  # /
            self.advance()  # *
            while not (self.peek() == '*' and self.peek(1) == '/') and self.peek() != '\0':
                self.advance()
            if self.peek() == '*':
                self.advance()
            if self.peek() == '/':
                self.advance()

    def read_string(self):
        start_line = self.line
        start_col = self.column
        quote = self.advance()  # " ou '
        value = ""
        while self.peek() != quote and self.peek() != '\0':
            if self.peek() == '\\':
                self.advance()
                escape = self.advance()
                if escape == 'n':
                    value += '\n'
                elif escape == 't':
                    value += '\t'
                elif escape == '\\':
                    value += '\\'
                elif escape == '"':
                    value += '"'
                else:
                    value += escape
            else:
                value += self.advance()
        if self.peek() == quote:
            self.advance()
        else:
            self.error(f"Chaine non terminee commencee a la ligne {start_line}")
        return Token(TokenType.STRING, value, start_line, start_col, self.filename)

    def read_number(self):
        start_line = self.line
        start_col = self.column
        value = ""
        while self.peek().isdigit():
            value += self.advance()
        if self.peek() == '.' and self.peek(1).isdigit():
            value += self.advance()  # .
            while self.peek().isdigit():
                value += self.advance()
            return Token(TokenType.NUMBER, float(value), start_line, start_col, self.filename)
        return Token(TokenType.NUMBER, int(value), start_line, start_col, self.filename)

    def read_identifier(self):
        start_line = self.line
        start_col = self.column
        value = ""
        while self.peek().isalnum() or self.peek() == '_':
            value += self.advance()
        token_type = self.KEYWORDS.get(value, TokenType.IDENTIFIER)
        return Token(token_type, value, start_line, start_col, self.filename)

    def handle_indentation(self, line_start_col):
        """Gere l'indentation basee sur les accolades, pas les espaces."""
        pass  # On utilise des accolades, pas d'indentation significative

    def tokenize(self):
        """Tokenise l'ensemble du code source. Complexite O(n)."""
        self.tokens = []

        while self.peek() != '\0':
            self.skip_whitespace()

            if self.peek() == '/' and self.peek(1) in ('/', '*'):
                self.skip_comment()
                continue

            if self.peek() == '\n':
                self.tokens.append(Token(TokenType.NEWLINE, '\n', self.line, self.column, self.filename))
                self.advance()
                continue

            char = self.peek()
            line = self.line
            col = self.column

            # Chaines
            if char in ('"', "'"):
                self.tokens.append(self.read_string())
                continue

            # Nombres
            if char.isdigit():
                self.tokens.append(self.read_number())
                continue

            # Identifiants et mots-cles
            if char.isalpha() or char == '_':
                self.tokens.append(self.read_identifier())
                continue

            # Operateurs a deux caracteres
            two_char = char + self.peek(1)
            if two_char == '==':
                self.advance(); self.advance()
                self.tokens.append(Token(TokenType.EQ, '==', line, col, self.filename))
                continue
            if two_char == '!=':
                self.advance(); self.advance()
                self.tokens.append(Token(TokenType.NEQ, '!=', line, col, self.filename))
                continue
            if two_char == '>=':
                self.advance(); self.advance()
                self.tokens.append(Token(TokenType.GTE, '>=', line, col, self.filename))
                continue
            if two_char == '<=':
                self.advance(); self.advance()
                self.tokens.append(Token(TokenType.LTE, '<=', line, col, self.filename))
                continue
            if two_char == '+=':
                self.advance(); self.advance()
                self.tokens.append(Token(TokenType.PLUS_ASSIGN, '+=', line, col, self.filename))
                continue
            if two_char == '-=':
                self.advance(); self.advance()
                self.tokens.append(Token(TokenType.MINUS_ASSIGN, '-=', line, col, self.filename))
                continue
            if two_char == '->':
                self.advance(); self.advance()
                self.tokens.append(Token(TokenType.ARROW, '->', line, col, self.filename))
                continue

            # Operateurs et delimiteurs a un caractere
            single_tokens = {
                '+': TokenType.PLUS, '-': TokenType.MINUS, '*': TokenType.STAR,
                '/': TokenType.SLASH, '%': TokenType.PERCENT, '^': TokenType.POWER,
                '=': TokenType.ASSIGN, '>': TokenType.GT, '<': TokenType.LT,
                ':': TokenType.COLON, ';': TokenType.SEMICOLON, ',': TokenType.COMMA,
                '(': TokenType.LPAREN, ')': TokenType.RPAREN,
                '{': TokenType.LBRACE, '}': TokenType.RBRACE,
                '[': TokenType.LBRACKET, ']': TokenType.RBRACKET,
                '.': TokenType.DOT,
            }

            if char in single_tokens:
                self.advance()
                self.tokens.append(Token(single_tokens[char], char, line, col, self.filename))
                continue

            if char == '\0':
                break

            self.error(f"Caractere inattendu: '{char}'")

        self.tokens.append(Token(TokenType.EOF, None, self.line, self.column, self.filename))
        return self.tokens
