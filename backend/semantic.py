from ast_nodes import *
from symbol_table import SymbolTable, SymbolTableError

TYPE_MAP = {
    'int':    {'NUMBER'},
    'float':  {'FLOAT_NUM', 'NUMBER'},
    'bool':   {'TRUE', 'FALSE'},
    'string': {'STRING_LIT'},
}

class SemanticError(Exception): pass

class SemanticAnalyzer:
    def __init__(self, ast):
        self.ast   = ast
        self.table = SymbolTable()

    def analyze(self):
        self.visit(self.ast)

    def visit(self, node):
        method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        pass

    def visit_ProgramNode(self, node):
        for stmt in node.statements:
            self.visit(stmt)

    def visit_AssignNode(self, node):
        # Declare in symbol table
        self.table.declare(node.name, node.type_, node.line)
        val_type = self.visit(node.value)
        return node.type_

    def visit_ReAssignNode(self, node):
        symbol = self.table.lookup(node.name, node.line)
        return symbol.type_

    def visit_IdentifierNode(self, node):
        symbol = self.table.lookup(node.name, node.line)
        return symbol.type_

    def visit_NumberNode(self, node):    return 'int'
    def visit_FloatNode(self, node):     return 'float'
    def visit_BoolNode(self, node):      return 'bool'
    def visit_StringNode(self, node):    return 'string'

    def visit_BinOpNode(self, node):
        left_type  = self.visit(node.left)
        right_type = self.visit(node.right)
        if left_type != right_type:
            raise SemanticError(
                f'[Semantic Error] Line {node.line}: Type mismatch: {left_type} vs {right_type}'
            )
        return left_type

    def visit_IfNode(self, node):
        self.visit(node.condition)
        self.table.push_scope()
        for stmt in node.body: self.visit(stmt)
        self.table.pop_scope()
        if node.else_body:
            self.table.push_scope()
            for stmt in node.else_body: self.visit(stmt)
            self.table.pop_scope()

    def visit_WhileNode(self, node):
        self.visit(node.condition)
        self.table.push_scope()
        for stmt in node.body: self.visit(stmt)
        self.table.pop_scope()

    def visit_PrintNode(self, node):
        self.visit(node.value)

    def visit_FuncDefNode(self, node):
        self.table.declare_func(node.name, node.return_type, node.params)
        self.table.push_scope()
        for ptype, pname in node.params:
            self.table.declare(pname, ptype, node.line)
        for stmt in node.body: self.visit(stmt)
        self.table.pop_scope()

    def visit_ReturnNode(self, node):
        return self.visit(node.value)

    def visit_FuncCallNode(self, node):
        sym = self.table.lookup(node.name, node.line)
        return sym.type_ if sym else 'void'
