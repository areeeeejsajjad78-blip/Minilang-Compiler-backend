class NumberNode:
    def __init__(self, value, line): self.value = value; self.line = line
    def to_dict(self): return {'node':'Number','value':self.value}

class FloatNode:
    def __init__(self, value, line): self.value = value; self.line = line
    def to_dict(self): return {'node':'Float','value':self.value}

class BoolNode:
    def __init__(self, value, line): self.value = value; self.line = line
    def to_dict(self): return {'node':'Bool','value':self.value}

class StringNode:
    def __init__(self, value, line): self.value = value; self.line = line
    def to_dict(self): return {'node':'String','value':self.value}

class IdentifierNode:
    def __init__(self, name, line): self.name = name; self.line = line
    def to_dict(self): return {'node':'Identifier','name':self.name}

class BinOpNode:
    def __init__(self, left, op, right, line):
        self.left=left; self.op=op; self.right=right; self.line=line
    def to_dict(self):
        return {'node':'BinOp','op':self.op,
                'left':self.left.to_dict(),'right':self.right.to_dict()}

class AssignNode:
    def __init__(self, type_, name, value, line):
        self.type_=type_; self.name=name; self.value=value; self.line=line
    def to_dict(self):
        return {'node':'Assign','type':self.type_,'name':self.name,
                'value':self.value.to_dict() if self.value else None}

class ReAssignNode:
    def __init__(self, name, value, line):
        self.name=name; self.value=value; self.line=line
    def to_dict(self):
        return {'node':'ReAssign','name':self.name,'value':self.value.to_dict()}

class IfNode:
    def __init__(self, condition, body, else_body, line):
        self.condition=condition; self.body=body
        self.else_body=else_body; self.line=line
    def to_dict(self):
        return {'node':'If','condition':self.condition.to_dict(),
                'body':[s.to_dict() for s in self.body],
                'else_body':[s.to_dict() for s in (self.else_body or [])]}

class WhileNode:
    def __init__(self, condition, body, line):
        self.condition=condition; self.body=body; self.line=line
    def to_dict(self):
        return {'node':'While','condition':self.condition.to_dict(),
                'body':[s.to_dict() for s in self.body]}

class PrintNode:
    def __init__(self, value, line): self.value=value; self.line=line
    def to_dict(self): return {'node':'Print','value':self.value.to_dict()}

class FuncDefNode:
    def __init__(self, name, params, return_type, body, line):
        self.name=name; self.params=params
        self.return_type=return_type; self.body=body; self.line=line
    def to_dict(self):
        return {'node':'FuncDef','name':self.name,
                'params':self.params,'return_type':self.return_type,
                'body':[s.to_dict() for s in self.body]}

class FuncCallNode:
    def __init__(self, name, args, line):
        self.name=name; self.args=args; self.line=line
    def to_dict(self):
        return {'node':'FuncCall','name':self.name,
                'args':[a.to_dict() for a in self.args]}

class ReturnNode:
    def __init__(self, value, line): self.value=value; self.line=line
    def to_dict(self): return {'node':'Return','value':self.value.to_dict()}

class ProgramNode:
    def __init__(self, statements): self.statements=statements
    def to_dict(self):
        return {'node':'Program','statements':[s.to_dict() for s in self.statements]}
