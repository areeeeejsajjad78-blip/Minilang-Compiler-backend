# backend/optimizer.py
# Phase 5: Code Optimization
# Runs on the TAC list produced by codegen.py
# Implements three classic optimizations:
#   1. Constant Folding      — evaluate constant expressions at compile time
#   2. Constant Propagation  — replace variable uses with known constant values
#   3. Dead Code Elimination — remove assignments to temps never used again

import re


class Optimizer:
    def __init__(self, tac):
        self.tac = tac[:]   # work on a copy

    def optimize(self):
        tac = self.tac
        tac = self.constant_folding(tac)
        tac = self.constant_propagation(tac)
        tac = self.dead_code_elimination(tac)
        return tac

    # ── Optimization 1: Constant Folding ──────────────────────────────────
    def constant_folding(self, tac):
        """
        If RHS of an assignment is a binary op on two numeric constants,
        evaluate it at compile time.
        Example:  t1 = 3 + 5   →   t1 = 8
        """
        result = []
        pattern = re.compile(
            r'^(\w+)\s*=\s*(-?[\d.]+)\s*([+\-*/])\s*(-?[\d.]+)$'
        )
        for line in tac:
            m = pattern.match(line.strip())
            if m:
                lhs  = m.group(1)
                left = m.group(2)
                op   = m.group(3)
                right= m.group(4)
                try:
                    folded = eval(f'{left} {op} {right}')
                    # Convert to int if result is whole number
                    if isinstance(folded, float) and folded.is_integer():
                        folded = int(folded)
                    result.append(f'# [FOLD] {left} {op} {right} => {folded}')
                    result.append(f'{lhs} = {folded}')
                    continue
                except Exception:
                    pass
            result.append(line)
        return result

    # ── Optimization 2: Constant Propagation ──────────────────────────────
    def constant_propagation(self, tac):
        """
        If a variable is assigned a constant, replace all later uses
        of that variable with the constant value.
        Example:
            x = 5
            t1 = x + 3   →   t1 = 5 + 3
        """
        constants = {}
        result    = []

        for line in tac:
            # Do not touch comment lines, labels, gotos, if-jumps
            stripped = line.strip()
            if (stripped.startswith('#') or
                stripped.endswith(':')   or
                stripped.startswith('goto') or
                stripped.startswith('if') or
                stripped.startswith('print') or
                stripped.startswith('return') or
                stripped.startswith('func') or
                stripped == 'endfunc'):
                result.append(line)
                continue

            parts = stripped.split(' = ', 1)
            if len(parts) == 2:
                lhs = parts[0].strip()
                rhs = parts[1].strip()

                # Replace known constants in RHS
                propagated_rhs = rhs
                for var, val in constants.items():
                    propagated_rhs = re.sub(
                        r'\b' + re.escape(var) + r'\b',
                        str(val),
                        propagated_rhs
                    )

                # If RHS is now a plain constant, record it for future propagation
                if self._is_numeric(propagated_rhs):
                    constants[lhs] = propagated_rhs

                if propagated_rhs != rhs:
                    result.append(f'# [PROP] {lhs}: replaced {rhs} → {propagated_rhs}')
                result.append(f'{lhs} = {propagated_rhs}')
            else:
                result.append(line)

        return result

    # ── Optimization 3: Dead Code Elimination ─────────────────────────────
    def dead_code_elimination(self, tac):
        """
        Remove assignments to temporary variables (t1, t2, ...) that are
        never read after being assigned.
        Example:
            t1 = x + y    ← if t1 never appears later, this is dead code
        """
        temp_pattern = re.compile(r'^t\d+$')

        def uses_after(var, from_index):
            """Count how many lines after from_index reference var."""
            count = 0
            for i in range(from_index + 1, len(tac)):
                line = tac[i]
                parts = line.split(' = ', 1)
                rhs   = parts[1] if len(parts) == 2 else line
                if re.search(r'\b' + re.escape(var) + r'\b', rhs):
                    count += 1
                # Also check in print / return / if lines
                if var in line and '=' not in line:
                    count += 1
            return count

        result = []
        for i, line in enumerate(tac):
            stripped = line.strip()
            if stripped.startswith('#'):
                result.append(line)
                continue
            parts = stripped.split(' = ', 1)
            if len(parts) == 2:
                lhs = parts[0].strip()
                if temp_pattern.match(lhs):
                    if uses_after(lhs, i) == 0:
                        result.append(
                            f'# [DCE] Eliminated dead temp: {stripped}'
                        )
                        continue
            result.append(line)
        return result

    # ── Helper ────────────────────────────────────────────────────────────
    def _is_numeric(self, s):
        try:
            float(s)
            return True
        except ValueError:
            return False