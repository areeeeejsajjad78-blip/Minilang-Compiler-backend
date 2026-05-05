# backend/machine_codegen.py
# Phase 6: Final Code Generation
# Converts optimized TAC into Stack Machine instructions.
#
# Stack Machine instruction set:
#   PUSH <val>     — push a constant onto the stack
#   LOAD <var>     — push a variable's value onto the stack
#   STORE <var>    — pop top of stack and store into variable
#   ADD            — pop two values, push their sum
#   SUB            — pop two values, push their difference
#   MUL            — pop two values, push their product
#   DIV            — pop two values, push their quotient
#   CMP_EQ         — pop two values, push 1 if equal else 0
#   CMP_NEQ        — pop two values, push 1 if not equal else 0
#   CMP_LT         — pop two values, push 1 if left < right else 0
#   CMP_GT         — pop two values, push 1 if left > right else 0
#   JUMP <label>   — unconditional jump to label
#   JUMPF <label>  — pop top, jump to label if it is falsy (0)
#   LABEL <name>   — declares a jump target
#   PRINT          — pop top of stack and output it
#   RETURN         — pop top of stack and return it
#   FUNC_START <n> — marks beginning of function n
#   FUNC_END       — marks end of function

import re


class StackMachineCodegen:

    OP_MAP = {
        '+': 'ADD', '-': 'SUB',
        '*': 'MUL', '/': 'DIV',
        '==': 'CMP_EQ', '!=': 'CMP_NEQ',
        '<':  'CMP_LT', '>':  'CMP_GT',
    }

    def __init__(self, tac):
        self.tac          = tac
        self.instructions = []

    def generate(self):
        for line in self.tac:
            self._process(line.strip())
        return self.instructions

    def emit(self, instr):
        self.instructions.append(instr)

    # ── Line Dispatcher ───────────────────────────────────────────────────
    def _process(self, line):
        if not line:
            return

        # Comment — keep as remark
        if line.startswith('#'):
            self.emit(f'; {line}')
            return

        # Label:   e.g.  L1:
        if re.match(r'^L\d+:$', line):
            self.emit(f'LABEL {line[:-1]}')
            return

        # goto L1
        if line.startswith('goto '):
            self.emit(f'JUMP {line.split()[1]}')
            return

        # if not (cond) goto L1
        m = re.match(r'if not \((.+)\) goto (\w+)', line)
        if m:
            self._push_expr(m.group(1).strip())
            self.emit(f'JUMPF {m.group(2)}')
            return

        # print <val>
        if line.startswith('print '):
            self._push_operand(line[6:].strip())
            self.emit('PRINT')
            return

        # return <val>
        if line.startswith('return '):
            self._push_operand(line[7:].strip())
            self.emit('RETURN')
            return

        # func name(params):
        if line.startswith('func '):
            self.emit(f'FUNC_START {line[5:]}')
            return

        # endfunc
        if line == 'endfunc':
            self.emit('FUNC_END')
            return

        # var = expr
        if ' = ' in line:
            parts = line.split(' = ', 1)
            lhs   = parts[0].strip()
            rhs   = parts[1].strip()
            self._push_expr(rhs)
            self.emit(f'STORE {lhs}')
            return

    # ── Expression Emitter ────────────────────────────────────────────────
    def _push_expr(self, expr):
        """
        Detect if expr is a binary operation and emit the right instructions,
        otherwise treat as a single operand.
        """
        # Try to match:  left OP right   (e.g.  x + y  or  t1 * 3)
        m = re.match(
            r'^(.+?)\s*([+\-*/]|==|!=|<=|>=|<|>)\s*(.+)$', expr
        )
        if m:
            left  = m.group(1).strip()
            op    = m.group(2).strip()
            right = m.group(3).strip()
            self._push_operand(left)
            self._push_operand(right)
            instr = self.OP_MAP.get(op, f'OP_{op}')
            self.emit(instr)
        else:
            self._push_operand(expr)

    def _push_operand(self, operand):
        """
        If operand is a numeric constant → PUSH <val>
        Otherwise it is a variable name  → LOAD <var>
        """
        operand = operand.strip()
        # Handle string literals
        if operand.startswith('"') and operand.endswith('"'):
            self.emit(f'PUSH {operand}')
            return
        # Handle booleans
        if operand in ('True', 'False'):
            self.emit(f'PUSH {operand}')
            return
        # Numeric constant
        try:
            float(operand)
            self.emit(f'PUSH {operand}')
        except ValueError:
            # Variable or temp — load from memory
            self.emit(f'LOAD {operand}')