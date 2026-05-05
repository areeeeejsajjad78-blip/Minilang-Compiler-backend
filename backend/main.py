# backend/main.py
# FastAPI server — ties all 7 compiler phases together

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from lexer          import Lexer, LexerError
from parser         import Parser, ParseError
from semantic       import SemanticAnalyzer, SemanticError
from symbol_table   import SymbolTableError
from codegen        import CodeGenerator
from optimizer      import Optimizer
from machine_codegen import StackMachineCodegen
from bottom_up_parser import BottomUpExprParser
from error_handler  import ErrorHandler, format_errors, TooManyErrors

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
    return {'status': 'MiniLang Compiler API is running — all 7 phases active'}


@app.post('/compile')
def compile_code(input: CodeInput):

    handler = ErrorHandler()

    result = {
        'tokens':        [],
        'ast':           {},
        'tac':           [],
        'optimized_tac': [],
        'machine_code':  [],
        'output':        [],
        'errors':        [],
        'warnings':      [],
        'phases_completed': [],
    }

    try:
        # ── Phase 1: Lexical Analysis ─────────────────────────────
        try:
            lexer  = Lexer(input.code)
            tokens = lexer.tokenize()
            result['tokens'] = [t.to_dict() for t in tokens]
            result['phases_completed'].append('Phase 1: Lexical Analysis')
        except LexerError as e:
            handler.report('Lexer', str(e))
            result['errors'] = handler.all_messages()
            return result

        # ── Phase 2: Syntax Analysis (Top-Down) ───────────────────
        try:
            parser = Parser(tokens)
            ast    = parser.parse()
            result['ast'] = ast.to_dict()
            result['phases_completed'].append('Phase 2: Syntax Analysis (Recursive Descent)')
        except ParseError as e:
            handler.report('Parser', str(e))
            result['errors'] = handler.all_messages()
            return result

        # ── Phase 2b: Bottom-Up Parser (expression demo) ──────────
        # We re-parse the first expression token sequence to demonstrate
        # bottom-up shift-reduce parsing alongside the top-down parser.
        try:
            expr_tokens = _extract_first_expression(tokens)
            if expr_tokens:
                bu_parser  = BottomUpExprParser(expr_tokens)
                bu_result  = bu_parser.parse()
                result['bottom_up_ast'] = bu_result.to_dict()
                result['phases_completed'].append(
                    'Phase 2b: Syntax Analysis (Bottom-Up Shift-Reduce)'
                )
        except Exception as e:
            handler.warn('BottomUpParser', str(e))

        # ── Phase 3: Semantic Analysis ────────────────────────────
        try:
            analyzer = SemanticAnalyzer(ast)
            analyzer.analyze()
            result['phases_completed'].append('Phase 3: Semantic Analysis')
        except (SemanticError, SymbolTableError) as e:
            handler.report('Semantic', str(e))
            result['errors'] = handler.all_messages()
            return result

        # ── Phase 4: Intermediate Code Generation (TAC) ───────────
        try:
            gen = CodeGenerator(ast)
            gen.generate()
            result['tac']    = gen.tac
            result['output'] = gen.output
            result['phases_completed'].append('Phase 4: Intermediate Code Generation (TAC)')
        except Exception as e:
            handler.report('CodeGen', str(e))
            result['errors'] = handler.all_messages()
            return result

        # ── Phase 5: Code Optimization ────────────────────────────
        try:
            optimizer = Optimizer(gen.tac)
            optimized = optimizer.optimize()
            result['optimized_tac'] = optimized
            result['phases_completed'].append(
                'Phase 5: Code Optimization (Folding + Propagation + DCE)'
            )
        except Exception as e:
            handler.warn('Optimizer', str(e))
            result['optimized_tac'] = gen.tac  # fallback to unoptimized

        # ── Phase 6: Final Code Generation (Stack Machine) ────────
        try:
            machine = StackMachineCodegen(result['optimized_tac'])
            result['machine_code'] = machine.generate()
            result['phases_completed'].append('Phase 6: Code Generation (Stack Machine)')
        except Exception as e:
            handler.warn('MachineCodegen', str(e))

        # ── Phase 7: Error Summary ─────────────────────────────────
        result['errors']   = handler.all_messages()
        result['warnings'] = [str(w) for w in handler.warnings]
        result['phases_completed'].append('Phase 7: Error Handling')

    except TooManyErrors:
        result['errors'] = handler.all_messages()

    except Exception as e:
        result['errors'] = [f'[Internal Error] {str(e)}']

    return result


# ── Helper ────────────────────────────────────────────────────────────────────
def _extract_first_expression(tokens):
    """
    Extract the tokens for the first expression in the program.
    Used to feed into the bottom-up parser for demonstration.
    Stops at the first SEMICOLON, LBRACE, or EOF.
    """
    from lexer import TT_EOF, Token

    expr_tokens = []
    recording   = False

    for tok in tokens:
        # Start after the first ASSIGN token
        if tok.type == 'ASSIGN':
            recording = True
            continue
        if recording:
            if tok.type in ('SEMICOLON', 'LBRACE', 'EOF'):
                break
            expr_tokens.append(tok)

    if not expr_tokens:
        return None

    expr_tokens.append(Token(TT_EOF, '', expr_tokens[-1].line))
    return expr_tokens
