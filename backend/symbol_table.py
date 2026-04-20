class SymbolTableError(Exception): pass

class Symbol:
    def __init__(self, name, type_, scope_level):
        self.name        = name
        self.type_       = type_
        self.scope_level = scope_level

class SymbolTable:
    def __init__(self):
        # Stack of dicts: each dict = one scope
        self.scopes = [{}]   # global scope always exists

    def push_scope(self):
        self.scopes.append({})

    def pop_scope(self):
        if len(self.scopes) > 1:
            self.scopes.pop()

    @property
    def current_level(self):
        return len(self.scopes) - 1

    def declare(self, name, type_, line):
        if name in self.scopes[-1]:
            raise SymbolTableError(
                f'[Semantic Error] Line {line}: Variable "{name}" already declared in this scope'
            )
        self.scopes[-1][name] = Symbol(name, type_, self.current_level)

    def lookup(self, name, line=None):
        # Search from innermost scope outward
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        if line:
            raise SymbolTableError(
                f'[Semantic Error] Line {line}: Variable "{name}" used before declaration'
            )
        return None

    def declare_func(self, name, return_type, params):
        self.scopes[0][name] = Symbol(name, return_type, 0)
        self.scopes[0][name].params = params
