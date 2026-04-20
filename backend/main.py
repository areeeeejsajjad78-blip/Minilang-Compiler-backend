from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import traceback

from lexer    import Lexer
from parser   import Parser
from semantic import SemanticAnalyzer, SemanticError
from codegen  import CodeGenerator
from symbol_table import SymbolTableError

app = FastAPI(title='MiniLang Compiler API')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*'],
)

class CodeInput(BaseModel):
    code: str

@app.get('/')
def root():
    return {'status': 'MiniLang Compiler API is running'}

@app.post('/compile')
def compile_code(input: CodeInput):
    result = {
        'tokens':  [],
        'ast':     {},
        'tac':     [],
        'output':  [],
        'errors':  [],
    }
    try:
        # Phase 1: Lex
        lexer  = Lexer(input.code)
        tokens = lexer.tokenize()
        result['tokens'] = [t.to_dict() for t in tokens]

        # Phase 2: Parse
        parser = Parser(tokens)
        ast    = parser.parse()
        result['ast'] = ast.to_dict()

        # Phase 3: Semantic Analysis
        analyzer = SemanticAnalyzer(ast)
        analyzer.analyze()

        # Phase 4: Code Generation (TAC + Python output)
        gen = CodeGenerator(ast)
        gen.generate()
        result['tac']    = gen.tac
        result['output'] = gen.output

    except Exception as e:
        result['errors'] = [str(e)]

    return result
