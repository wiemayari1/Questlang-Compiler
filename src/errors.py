# -*- coding: utf-8 -*-
class QuestLangError(Exception):
    def __init__(self, message, line=0, column=0, filename=""):
        self.message = message
        self.line = line
        self.column = column
        self.filename = filename
        super().__init__(self.format_message())

    def format_message(self):
        loc = ""
        if self.filename:
            loc += f"{self.filename}:"
        if self.line > 0:
            loc += f"{self.line}"
            if self.column > 0:
                loc += f":{self.column}"
        if loc:
            return f"[{loc}] {self.message}"
        return self.message

class LexicalError(QuestLangError):
    pass

class SyntaxError(QuestLangError):
    pass

class SemanticError(QuestLangError):
    pass

class QuestLangRuntimeError(QuestLangError):
    pass

class ErrorReporter:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.infos = []

    def add_error(self, code, message, line=0, column=0, severity="ERROR"):
        self.errors.append({"code": code, "message": message, "line": line, "column": column, "severity": severity})

    def add_warning(self, code, message, line=0, column=0):
        self.warnings.append({"code": code, "message": message, "line": line, "column": column, "severity": "WARNING"})

    def add_info(self, code, message, line=0, column=0):
        self.infos.append({"code": code, "message": message, "line": line, "column": column, "severity": "INFO"})

    def has_errors(self):
        return len(self.errors) > 0

    def get_diagnostics(self):
        return {
            "errors": self.errors,
            "warnings": self.warnings,
            "infos": self.infos,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "info_count": len(self.infos)
        }
