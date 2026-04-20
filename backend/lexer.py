import re

# ── Token type constants ──────────────────────────────
TT_INT      = 'INT'
TT_FLOAT    = 'FLOAT'
TT_BOOL     = 'BOOL'
TT_STRING   = 'STRING'
TT_IDENT    = 'IDENTIFIER'
TT_NUMBER   = 'NUMBER'
TT_FNUM     = 'FLOAT_NUM'
TT_PLUS     = 'PLUS'
TT_MINUS    = 'MINUS'
TT_MUL      = 'MUL'
TT_DIV      = 'DIV'
TT_ASSIGN   = 'ASSIGN'
TT_EQ       = 'EQ'
TT_NEQ      = 'NEQ'
TT_LT       = 'LT'
TT_GT       = 'GT'
TT_LPAR     = 'LPAREN'
TT_RPAR     = 'RPAREN'
TT_LBRACE   = 'LBRACE'
TT_RBRACE   = 'RBRACE'
TT_SEMI     = 'SEMICOLON'
TT_COMMA    = 'COMMA'
TT_IF       = 'IF'
TT_ELSE     = 'ELSE'
TT_WHILE    = 'WHILE'
TT_FUNC     = 'FUNC'
TT_RETURN   = 'RETURN'
TT_PRINT    = 'PRINT'
TT_TRUE     = 'TRUE'
TT_FALSE    = 'FALSE'
TT_EOF      = 'EOF'

# ── Keyword map ───────────────────────────────────────
KEYWORDS = {
    'int': TT_INT, 'float': TT_FLOAT, 'bool': TT_BOOL,
    'string': TT_STRING, 'if': TT_IF, 'else': TT_ELSE,
    'while': TT_WHILE, 'func': TT_FUNC, 'return': TT_RETURN,
    'print': TT_PRINT, 'true': TT_TRUE, 'false': TT_FALSE,
}

# ── Token specification (order matters!) ──────────────
TOKEN_SPEC = [
    ('FLOAT_NUM',  r'\d+\.\d+'),
    ('NUMBER',     r'\d+'),
    ('STRING_LIT', r'"[^"]*"'),
    ('IDENTIFIER', r'[A-Za-z_][A-Za-z0-9_]*'),
    ('EQ',         r'=='),
    ('NEQ',        r'!='),
    ('ASSIGN',     r'='),
    ('PLUS',       r'\+'),
    ('MINUS',      r'-'),
    ('MUL',        r'\*'),
    ('DIV',        r'/'),
    ('LT',         r'<'),
    ('GT',         r'>'),
    ('LPAREN',     r'\('),
    ('RPAREN',     r'\)'),
    ('LBRACE',     r'\{'),
    ('RBRACE',     r'\}'),
    ('SEMICOLON',  r';'),
    ('COMMA',      r','),
    ('NEWLINE',    r'\n'),
    ('SKIP',       r'[ \t]+'),
    ('COMMENT',    r'//[^\n]*'),
    ('MISMATCH',   r'.'),
]

MASTER_PATTERN = re.compile(
    '|'.join(f'(?P<{name}>{pattern})' for name, pattern in TOKEN_SPEC)
)

class LexerError(Exception): pass

class Token:
    def __init__(self, type_, value, line):
        self.type  = type_
        self.value = value
        self.line  = line
    def to_dict(self):
        return {'type': self.type, 'value': self.value, 'line': self.line}
    def __repr__(self):
        return f'Token({self.type}, {self.value!r}, line={self.line})'

class Lexer:
    def __init__(self, source: str):
        self.source = source

    def tokenize(self):
        tokens = []
        line_num = 1
        for mo in MASTER_PATTERN.finditer(self.source):
            kind  = mo.lastgroup
            value = mo.group()
            if kind == 'NEWLINE':
                line_num += 1
                continue
            elif kind in ('SKIP', 'COMMENT'):
                continue
            elif kind == 'MISMATCH':
                raise LexerError(
                    f'[Lexer Error] Line {line_num}: Unknown character {value!r}'
                )
            # Keyword check
            if kind == 'IDENTIFIER' and value in KEYWORDS:
                kind = KEYWORDS[value]
            tokens.append(Token(kind, value, line_num))
        tokens.append(Token(TT_EOF, '', line_num))
        return tokens
