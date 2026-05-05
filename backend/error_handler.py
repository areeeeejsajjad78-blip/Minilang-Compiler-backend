# backend/error_handler.py
# Phase 7: Error Handling
# Collects errors from all compiler phases and formats them.
# Also implements panic-mode recovery for the parser so multiple
# errors can be reported in one compile run instead of stopping
# at the first one.

class CompilerError:
    """Represents one error from any compiler phase."""

    def __init__(self, phase, message, line=None):
        self.phase   = phase    # e.g. "Lexer", "Parser", "Semantic"
        self.message = message
        self.line    = line

    def __str__(self):
        location = f' Line {self.line}:' if self.line else ':'
        return f'[{self.phase} Error]{location} {self.message}'


class ErrorHandler:
    """
    Central error collector for all phases.
    Collects errors instead of crashing on the first one,
    allowing the compiler to report multiple problems at once.
    """

    MAX_ERRORS = 10   # stop collecting after this many errors

    def __init__(self):
        self.errors   = []
        self.warnings = []

    # ── Error Reporting ───────────────────────────────────────────────────
    def report(self, phase, message, line=None):
        """Add an error. Raises TooManyErrors if limit is reached."""
        err = CompilerError(phase, message, line)
        self.errors.append(err)
        if len(self.errors) >= self.MAX_ERRORS:
            self.errors.append(
                CompilerError('ErrorHandler',
                              f'Too many errors ({self.MAX_ERRORS}). Stopping compilation.')
            )
            raise TooManyErrors()

    def warn(self, phase, message, line=None):
        """Add a warning — does not stop compilation."""
        self.warnings.append(CompilerError(phase, message, line))

    def has_errors(self):
        return len(self.errors) > 0

    def all_messages(self):
        """Return all errors and warnings as a list of strings."""
        msgs = [str(e) for e in self.errors]
        msgs += [f'[WARNING] {str(w)}' for w in self.warnings]
        return msgs

    def clear(self):
        self.errors   = []
        self.warnings = []


class TooManyErrors(Exception):
    """Raised when error count hits the limit."""
    pass


# ── Panic Mode Recovery ───────────────────────────────────────────────────────
class PanicModeRecovery:
    """
    Panic mode is a classic error recovery technique for parsers.
    When an unexpected token is found, the parser PANICS — it discards
    tokens one by one until it finds a safe synchronization point,
    then resumes parsing from there.

    Safe synchronization tokens for MiniLang:
      - SEMICOLON ;  — end of a statement
      - RBRACE    }  — end of a block
      - EOF          — end of file
    """

    SYNC_TOKENS = ('SEMICOLON', 'RBRACE', 'EOF')

    def __init__(self, tokens, pos):
        self.tokens = tokens
        self.pos    = pos

    def recover(self):
        """
        Skip tokens until we find a sync token.
        Returns the new position after recovery.
        """
        while self.pos < len(self.tokens):
            if self.tokens[self.pos].type in self.SYNC_TOKENS:
                # Consume the sync token itself to move past it
                if self.tokens[self.pos].type == 'SEMICOLON':
                    self.pos += 1
                break
            self.pos += 1
        return self.pos


# ── Error Message Formatter ───────────────────────────────────────────────────
def format_errors(errors):
    """
    Takes a list of error strings and formats them into a structured
    report with phase grouping and line references.
    """
    if not errors:
        return ['No errors — compilation successful.']

    formatted = []
    formatted.append(f'Compilation failed with {len(errors)} error(s):')
    formatted.append('-' * 48)

    for i, err in enumerate(errors, 1):
        formatted.append(f'  {i}. {err}')

    formatted.append('-' * 48)
    return formatted