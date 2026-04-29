# -*- coding: utf-8 -*-
from enum import Enum, auto

class TokenType(Enum):
    WORLD=auto(); QUEST=auto(); ITEM=auto(); NPC=auto(); SCRIPT=auto(); FUNC=auto()
    START=auto(); START_GOLD=auto(); WIN_CONDITION=auto(); TITLE=auto(); DESC=auto()
    REQUIRES=auto(); UNLOCKS=auto(); REWARDS=auto(); COSTS=auto(); CONDITION=auto()
    VALUE=auto(); STACKABLE=auto(); TYPE=auto(); LOCATION=auto(); GIVES_QUEST=auto()
    VAR=auto(); INT=auto(); FLOAT=auto(); BOOL=auto(); STRING_KW=auto(); LIST=auto()
    IF=auto(); ELSE=auto(); WHILE=auto(); FOR=auto(); IN=auto(); RETURN=auto()
    GIVE=auto(); TAKE=auto(); CALL=auto()
    AND=auto(); OR=auto(); NOT=auto(); TRUE=auto(); FALSE=auto()
    WEAPON=auto(); ARMOR=auto(); KEY=auto(); REAGENT=auto(); CONSUMABLE=auto(); MISC=auto()
    ARTIFACT=auto(); MATERIAL=auto()
    IDENTIFIER=auto(); NUMBER=auto(); STRING=auto()
    PLUS=auto(); MINUS=auto(); STAR=auto(); SLASH=auto(); PERCENT=auto(); POWER=auto()
    EQ=auto(); NEQ=auto(); GT=auto(); LT=auto(); GTE=auto(); LTE=auto()
    ASSIGN=auto(); PLUS_ASSIGN=auto(); MINUS_ASSIGN=auto()
    COLON=auto(); SEMICOLON=auto(); COMMA=auto(); LPAREN=auto(); RPAREN=auto()
    LBRACE=auto(); RBRACE=auto(); LBRACKET=auto(); RBRACKET=auto(); DOT=auto(); ARROW=auto()
    NEWLINE=auto(); COMMENT=auto(); EOF=auto()

class Token:
    def __init__(self, type_, value, line, column, filename=""):
        self.type = type_
        self.value = value
        self.line = line
        self.column = column
        self.filename = filename

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, L{self.line})"

    def __eq__(self, other):
        if isinstance(other, TokenType):
            return self.type == other
        if isinstance(other, Token):
            return self.type == other.type and self.value == other.value
        return False

class Lexer:
    KEYWORDS = {
        'world': TokenType.WORLD, 'quest': TokenType.QUEST, 'item': TokenType.ITEM,
        'npc': TokenType.NPC, 'script': TokenType.SCRIPT, 'func': TokenType.FUNC,
        'start': TokenType.START, 'start_gold': TokenType.START_GOLD,
        'win_condition': TokenType.WIN_CONDITION, 'title': TokenType.TITLE,
        'desc': TokenType.DESC, 'requires': TokenType.REQUIRES, 'unlocks': TokenType.UNLOCKS,
        'rewards': TokenType.REWARDS, 'costs': TokenType.COSTS, 'condition': TokenType.CONDITION,
        'value': TokenType.VALUE, 'stackable': TokenType.STACKABLE, 'type': TokenType.TYPE,
        'location': TokenType.LOCATION, 'gives_quest': TokenType.GIVES_QUEST,
        'var': TokenType.VAR, 'int': TokenType.INT, 'float': TokenType.FLOAT,
        'bool': TokenType.BOOL, 'string': TokenType.STRING_KW, 'list': TokenType.LIST,
        'if': TokenType.IF, 'else': TokenType.ELSE, 'while': TokenType.WHILE,
        'for': TokenType.FOR, 'in': TokenType.IN, 'return': TokenType.RETURN,
        'give': TokenType.GIVE, 'take': TokenType.TAKE, 'call': TokenType.CALL,
        'and': TokenType.AND, 'or': TokenType.OR, 'not': TokenType.NOT,
        'true': TokenType.TRUE, 'false': TokenType.FALSE,
        'weapon': TokenType.WEAPON, 'armor': TokenType.ARMOR, 'key': TokenType.KEY,
        'reagent': TokenType.REAGENT, 'consumable': TokenType.CONSUMABLE, 'misc': TokenType.MISC,
        'artifact': TokenType.ARTIFACT, 'material': TokenType.MATERIAL,
        'xp': TokenType.IDENTIFIER, 'gold': TokenType.IDENTIFIER,
    }

    def __init__(self, source, filename=""):
        self.source = source
        self.filename = filename
        self.tokens = []
        self.pos = 0
        self.line = 1
        self.column = 1

    def peek(self, offset=0):
        pos = self.pos + offset
        return self.source[pos] if pos < len(self.source) else '\0'

    def advance(self):
        char = self.peek()
        if char != '\0':
            self.pos += 1
            if char == '\n':
                self.line += 1
                self.column = 1
            else:
                self.column += 1
        return char

    def skip_whitespace(self):
        while self.peek() in ' \t\r' and self.peek() != '\0':
            self.advance()

    def skip_comment(self):
        if self.peek() == '/' and self.peek(1) == '/':
            while self.peek() not in '\n\0':
                self.advance()
        elif self.peek() == '/' and self.peek(1) == '*':
            self.advance(); self.advance()
            while not (self.peek() == '*' and self.peek(1) == '/') and self.peek() != '\0':
                self.advance()
            if self.peek() == '*':
                self.advance()
            if self.peek() == '/':
                self.advance()

    def read_string(self):
        sl, sc = self.line, self.column
        quote = self.advance()
        value = ""
        while self.peek() != quote and self.peek() != '\0':
            if self.peek() == '\\':
                self.advance()
                e = self.advance()
                escapes = {'n': '\n', 't': '\t', '\\': '\\', '"': '"', "'": "'"}
                value += escapes.get(e, e)
            else:
                value += self.advance()
        if self.peek() == quote:
            self.advance()
        else:
            from errors import LexicalError
            raise LexicalError("Chaine non terminee", sl, sc, self.filename)
        return Token(TokenType.STRING, value, sl, sc, self.filename)

    def read_number(self):
        sl, sc = self.line, self.column
        value = ""
        while self.peek().isdigit() and self.peek() != '\0':
            value += self.advance()
        if self.peek() == '.' and self.peek(1).isdigit():
            value += self.advance()
            while self.peek().isdigit() and self.peek() != '\0':
                value += self.advance()
            return Token(TokenType.NUMBER, float(value), sl, sc, self.filename)
        return Token(TokenType.NUMBER, int(value), sl, sc, self.filename)

    def read_identifier(self):
        sl, sc = self.line, self.column
        value = ""
        while (self.peek().isalnum() or self.peek() == '_') and self.peek() != '\0':
            value += self.advance()
        ttype = self.KEYWORDS.get(value, TokenType.IDENTIFIER)
        return Token(ttype, value, sl, sc, self.filename)

    def tokenize(self):
        from errors import LexicalError
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
            if self.peek() == '\0':
                break
            char = self.peek()
            line, col = self.line, self.column
            if char in ('"', "'"):
                self.tokens.append(self.read_string())
                continue
            if char.isdigit():
                self.tokens.append(self.read_number())
                continue
            if char.isalpha() or char == '_':
                self.tokens.append(self.read_identifier())
                continue
            two = char + self.peek(1)
            two_map = {
                '==': TokenType.EQ, '!=': TokenType.NEQ, '>=': TokenType.GTE, '<=': TokenType.LTE,
                '+=': TokenType.PLUS_ASSIGN, '-=': TokenType.MINUS_ASSIGN, '->': TokenType.ARROW
            }
            if two in two_map:
                self.advance(); self.advance()
                self.tokens.append(Token(two_map[two], two, line, col, self.filename))
                continue
            single = {
                '+': TokenType.PLUS, '-': TokenType.MINUS, '*': TokenType.STAR, '/': TokenType.SLASH,
                '%': TokenType.PERCENT, '^': TokenType.POWER, '=': TokenType.ASSIGN,
                '>': TokenType.GT, '<': TokenType.LT, ':': TokenType.COLON, ';': TokenType.SEMICOLON,
                ',': TokenType.COMMA, '(': TokenType.LPAREN, ')': TokenType.RPAREN,
                '{': TokenType.LBRACE, '}': TokenType.RBRACE, '[': TokenType.LBRACKET,
                ']': TokenType.RBRACKET, '.': TokenType.DOT
            }
            if char in single:
                self.advance()
                self.tokens.append(Token(single[char], char, line, col, self.filename))
                continue
            raise LexicalError(
                f"Caractere inconnu '{char}' (code ASCII {ord(char)})",
                self.line, self.column, self.filename
            )
        self.tokens.append(Token(TokenType.EOF, None, self.line, self.column, self.filename))
        return self.tokens