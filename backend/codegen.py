from ast_nodes import *

class CodeGenerator:
    def __init__(self, ast):
        self.ast       = ast
        self.tac       = []       # three-address code lines
        self.temp_count = 0
        self.label_count = 0
        self.output    = []       # final Python lines
        self.indent    = 0

    def new_temp(self):
        self.temp_count += 1
        return f't{self.temp_count}'

    def new_label(self):
        self.label_count += 1
        return f'L{self.label_count}'

    def emit(self, line):
        self.tac.append(line)

    def emit_py(self, line):
        self.output.append('    ' * self.indent + line)

    def generate(self):
        self.visit(self.ast)
        return self.tac

    def visit(self, node):
        method = 'visit_' + node.__class__.__name__
        return getattr(self, method, lambda n: None)(node)

    def visit_ProgramNode(self, node):
        for stmt in node.statements:
            self.visit(stmt)

    def visit_AssignNode(self, node):
        val = self.visit(node.value)
        self.emit(f'{node.name} = {val}')
        self.emit_py(f'{node.name} = {val}')
        return node.name

    def visit_ReAssignNode(self, node):
        val = self.visit(node.value)
        self.emit(f'{node.name} = {val}')
        self.emit_py(f'{node.name} = {val}')
        return node.name

    def visit_NumberNode(self, node):  return str(node.value)
    def visit_FloatNode(self, node):   return str(node.value)
    def visit_BoolNode(self, node):    return 'True' if node.value else 'False'
    def visit_StringNode(self, node):  return f'"{node.value}"'
    def visit_IdentifierNode(self, node): return node.name

    def visit_BinOpNode(self, node):
        left  = self.visit(node.left)
        right = self.visit(node.right)
        # ── Constant Folding optimization ──────────────
        try:
            result = eval(f'{left} {node.op} {right}')
            self.emit(f'# [OPT] Folded: {left} {node.op} {right} => {result}')
            return str(result)
        except:
            pass
        # ──────────────────────────────────────────────
        t = self.new_temp()
        self.emit(f'{t} = {left} {node.op} {right}')
        return t

    def visit_PrintNode(self, node):
        val = self.visit(node.value)
        self.emit(f'print {val}')
        self.emit_py(f'print({val})')

    def visit_IfNode(self, node):
        cond  = self.visit(node.condition)
        l_else = self.new_label()
        l_end  = self.new_label()
        self.emit(f'if not ({cond}) goto {l_else}')
        self.emit_py(f'if {cond}:')
        self.indent += 1
        for stmt in node.body: self.visit(stmt)
        self.indent -= 1
        self.emit(f'goto {l_end}')
        self.emit(f'{l_else}:')
        if node.else_body:
            self.emit_py('else:')
            self.indent += 1
            for stmt in node.else_body: self.visit(stmt)
            self.indent -= 1
        self.emit(f'{l_end}:')

    def visit_WhileNode(self, node):
        l_start = self.new_label()
        l_end   = self.new_label()
        self.emit(f'{l_start}:')
        cond = self.visit(node.condition)
        self.emit(f'if not ({cond}) goto {l_end}')
        self.emit_py(f'while {cond}:')
        self.indent += 1
        for stmt in node.body: self.visit(stmt)
        self.indent -= 1
        self.emit(f'goto {l_start}')
        self.emit(f'{l_end}:')

    def visit_FuncDefNode(self, node):
        params = ', '.join(name for _, name in node.params)
        self.emit(f'func {node.name}({params}):')
        self.emit_py(f'def {node.name}({params}):')
        self.indent += 1
        for stmt in node.body: self.visit(stmt)
        self.indent -= 1
        self.emit('endfunc')

    def visit_ReturnNode(self, node):
        val = self.visit(node.value)
        self.emit(f'return {val}')
        self.emit_py(f'return {val}')

    def visit_FuncCallNode(self, node):
        args = [self.visit(a) for a in node.args]
        t = self.new_temp()
        self.emit(f'{t} = call {node.name}({', '.join(args)})')
        return t
