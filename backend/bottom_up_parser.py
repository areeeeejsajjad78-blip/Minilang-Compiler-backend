# backend/bottom_up_parser.py
# Phase 2 (Part 2): Bottom-Up Shift-Reduce Expression Parser

from ast_nodes import NumberNode, FloatNode, IdentifierNode, BinOpNode, FuncCallNode
from lexer import (TT_NUMBER, TT_FNUM, TT_IDENT, TT_PLUS, TT_MINUS,
                   TT_MUL, TT_DIV, TT_LPAR, TT_RPAR, TT_EOF,
                   TT_EQ, TT_NEQ, TT_LT, TT_GT, Token)

# Operator precedence — higher number = evaluated first
PRECEDENCE = {
    '==': 0, '!=': 0,
    '<':  1, '>':  1,
    '+':  2, '-':  2,
    '*':  3, '/':  3,
}

OP_TOKENS = (TT_PLUS, TT_MINUS, TT_MUL, TT_DIV, TT_EQ, TT_NEQ, TT_LT, TT_GT)


class BottomUpExprParser:
    """
    Shift-Reduce expression parser.

    SHIFT  = push current token onto operand or operator stack
    REDUCE = pop two operands + one operator → create BinOpNode → push back

    We reduce when the operator on top of the stack has
    >= precedence than the incoming operator (enforces left-associativity).
    """

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.operand_stack  = []
        self.operator_stack = []

    def current(self):
        return self.tokens[self.pos]

    def advance(self):
        tok = self.tokens[self.pos]
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return tok

    def _reduce(self):
        """Pop two operands and one operator, push a BinOpNode."""
        right = self.operand_stack.pop()
        left  = self.operand_stack.pop()
        op    = self.operator_stack.pop()
        node  = BinOpNode(left, op, right, left.line)
        self.operand_stack.append(node)

    def parse(self):
        self._parse_expr()
        # Reduce everything remaining on the stacks
        while self.operator_stack:
            self._reduce()
        if not self.operand_stack:
            raise Exception('[BottomUp] Empty expression')
        return self.operand_stack[0]

    def _parse_expr(self):
        # SHIFT first operand
        self._parse_primary()

        # Shift-Reduce loop
        while True:
            tok = self.current()
            if tok.type not in OP_TOKENS:
                break

            incoming_op   = tok.value
            incoming_prec = PRECEDENCE.get(incoming_op, -1)

            # REDUCE: while top operator has >= precedence, reduce first
            while (self.operator_stack and
                   self.operator_stack[-1] in PRECEDENCE and
                   PRECEDENCE[self.operator_stack[-1]] >= incoming_prec):
                self._reduce()

            # SHIFT operator
            self.operator_stack.append(incoming_op)
            self.advance()

            # SHIFT next operand
            self._parse_primary()

    def _parse_primary(self):
        tok = self.current()

        if tok.type == TT_NUMBER:
            self.advance()
            self.operand_stack.append(NumberNode(int(tok.value), tok.line))

        elif tok.type == TT_FNUM:
            self.advance()
            self.operand_stack.append(FloatNode(float(tok.value), tok.line))

        elif tok.type == TT_IDENT:
            # Check if it's a function call: name(args)
            next_tok = self.tokens[self.pos + 1] if self.pos + 1 < len(self.tokens) else None
            if next_tok and next_tok.type == TT_LPAR:
                self._parse_func_call()
            else:
                self.advance()
                self.operand_stack.append(IdentifierNode(tok.value, tok.line))

        elif tok.type == TT_LPAR:
            self.advance()  # consume (
            self._parse_expr()
            if self.current().type == TT_RPAR:
                self.advance()  # consume )

        else:
            raise Exception(
                f'[BottomUp Parser Error] Line {tok.line}: Unexpected token {tok.value!r}'
            )

    def _parse_func_call(self):
        name_tok = self.advance()  # function name
        self.advance()             # consume (
        args = []
        while self.current().type != TT_RPAR and self.current().type != TT_EOF:
            # Collect tokens for each argument
            arg_tokens = []
            depth = 0
            while True:
                t = self.current()
                if t.type == TT_LPAR:
                    depth += 1
                if t.type == TT_RPAR:
                    if depth == 0:
                        break
                    depth -= 1
                if t.type == TT_EOF:
                    break
                if t.value == ',' and depth == 0:
                    self.advance()
                    break
                arg_tokens.append(t)
                self.advance()
            if arg_tokens:
                arg_tokens.append(Token(TT_EOF, '', arg_tokens[-1].line))
                arg_node = BottomUpExprParser(arg_tokens).parse()
                args.append(arg_node)
        if self.current().type == TT_RPAR:
            self.advance()  # consume )
        self.operand_stack.append(FuncCallNode(name_tok.value, args, name_tok.line))