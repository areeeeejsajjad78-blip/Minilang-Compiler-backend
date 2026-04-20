from lexer import *
from ast_nodes import *

class ParseError(Exception): pass

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos    = 0

    # ── Helpers ────────────────────────────────────────
    def current(self):
        return self.tokens[self.pos]

    def peek(self, offset=1):
        idx = self.pos + offset
        return self.tokens[idx] if idx < len(self.tokens) else None

    def eat(self, expected_type):
        tok = self.current()
        if tok.type != expected_type:
            raise ParseError(
                f'[Parser Error] Line {tok.line}: Expected {expected_type} but got {tok.type} ({tok.value!r})'
            )
        self.pos += 1
        return tok

    def advance(self):
        tok = self.current()
        self.pos += 1
        return tok

    # ── Entry point ────────────────────────────────────
    def parse(self):
        stmts = []
        while self.current().type != TT_EOF:
            stmts.append(self.statement())
        return ProgramNode(stmts)

    # ── Statements ─────────────────────────────────────
    def statement(self):
        tok = self.current()
        # Variable declaration: int x = 5;
        if tok.type in (TT_INT, TT_FLOAT, TT_BOOL, TT_STRING):
            return self.var_declaration()
        # If statement
        elif tok.type == TT_IF:
            return self.if_statement()
        # While loop
        elif tok.type == TT_WHILE:
            return self.while_statement()
        # Print
        elif tok.type == TT_PRINT:
            return self.print_statement()
        # Function definition
        elif tok.type == TT_FUNC:
            return self.func_def()
        # Return
        elif tok.type == TT_RETURN:
            return self.return_statement()
        # Reassignment: x = expr;
        elif tok.type == TT_IDENT:
            return self.reassignment()
        else:
            raise ParseError(f'[Parser Error] Line {tok.line}: Unexpected token {tok.value!r}')

    def var_declaration(self):
        type_tok = self.advance()           # int / float / bool / string
        name_tok = self.eat(TT_IDENT)       # variable name
        self.eat(TT_ASSIGN)                 # =
        value    = self.expression()
        self.eat(TT_SEMI)                   # ;
        return AssignNode(type_tok.value, name_tok.value, value, type_tok.line)

    def reassignment(self):
        name_tok = self.eat(TT_IDENT)
        self.eat(TT_ASSIGN)
        value = self.expression()
        self.eat(TT_SEMI)
        return ReAssignNode(name_tok.value, value, name_tok.line)

    def if_statement(self):
        line = self.current().line
        self.eat(TT_IF)
        self.eat(TT_LPAR)
        condition = self.expression()
        self.eat(TT_RPAR)
        body = self.block()
        else_body = None
        if self.current().type == TT_ELSE:
            self.advance()
            else_body = self.block()
        return IfNode(condition, body, else_body, line)

    def while_statement(self):
        line = self.current().line
        self.eat(TT_WHILE)
        self.eat(TT_LPAR)
        condition = self.expression()
        self.eat(TT_RPAR)
        body = self.block()
        return WhileNode(condition, body, line)

    def print_statement(self):
        line = self.current().line
        self.eat(TT_PRINT)
        self.eat(TT_LPAR)
        value = self.expression()
        self.eat(TT_RPAR)
        self.eat(TT_SEMI)
        return PrintNode(value, line)

    def func_def(self):
        line = self.current().line
        self.eat(TT_FUNC)
        name = self.eat(TT_IDENT).value
        self.eat(TT_LPAR)
        params = []
        while self.current().type != TT_RPAR:
            ptype = self.advance().value
            pname = self.eat(TT_IDENT).value
            params.append((ptype, pname))
            if self.current().type == TT_COMMA: self.advance()
        self.eat(TT_RPAR)
        # optional return type: -> int
        return_type = 'void'
        if self.current().type == TT_MINUS:
            self.advance()   # -
            self.eat(TT_GT)  # >
            return_type = self.advance().value
        body = self.block()
        return FuncDefNode(name, params, return_type, body, line)

    def return_statement(self):
        line = self.current().line
        self.eat(TT_RETURN)
        value = self.expression()
        self.eat(TT_SEMI)
        return ReturnNode(value, line)

    def block(self):
        self.eat(TT_LBRACE)
        stmts = []
        while self.current().type != TT_RBRACE:
            stmts.append(self.statement())
        self.eat(TT_RBRACE)
        return stmts

    # ── Expressions (operator precedence) ──────────────
    def expression(self):   # lowest precedence
        return self.comparison()

    def comparison(self):
        left = self.addition()
        while self.current().type in (TT_EQ, TT_NEQ, TT_LT, TT_GT):
            op  = self.advance().value
            right = self.addition()
            left  = BinOpNode(left, op, right, left.line)
        return left

    def addition(self):
        left = self.multiplication()
        while self.current().type in (TT_PLUS, TT_MINUS):
            op    = self.advance().value
            right = self.multiplication()
            left  = BinOpNode(left, op, right, left.line)
        return left

    def multiplication(self):
        left = self.primary()
        while self.current().type in (TT_MUL, TT_DIV):
            op    = self.advance().value
            right = self.primary()
            left  = BinOpNode(left, op, right, left.line)
        return left

    def primary(self):
        tok = self.current()
        if tok.type == TT_NUMBER:
            self.advance()
            return NumberNode(int(tok.value), tok.line)
        elif tok.type == TT_FNUM:
            self.advance()
            return FloatNode(float(tok.value), tok.line)
        elif tok.type in (TT_TRUE, TT_FALSE):
            self.advance()
            return BoolNode(tok.value == 'true', tok.line)
        elif tok.type == 'STRING_LIT':
            self.advance()
            return StringNode(tok.value[1:-1], tok.line)
        elif tok.type == TT_IDENT:
            # function call or identifier
            if self.peek() and self.peek().type == TT_LPAR:
                return self.func_call()
            self.advance()
            return IdentifierNode(tok.value, tok.line)
        elif tok.type == TT_LPAR:
            self.advance()
            expr = self.expression()
            self.eat(TT_RPAR)
            return expr
        else:
            raise ParseError(f'[Parser Error] Line {tok.line}: Unexpected {tok.value!r}')

    def func_call(self):
        name = self.eat(TT_IDENT).value
        line = self.current().line
        self.eat(TT_LPAR)
        args = []
        while self.current().type != TT_RPAR:
            args.append(self.expression())
            if self.current().type == TT_COMMA: self.advance()
        self.eat(TT_RPAR)
        return FuncCallNode(name, args, line)
