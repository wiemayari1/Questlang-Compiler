# -*- coding: utf-8 -*-
"""
Module de gestion des erreurs pour QuestLang.
Fournit une hierarchie d'exceptions et un systeme de reporting.
"""

class QuestLangError(Exception):
    """Classe de base pour toutes les erreurs QuestLang."""
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
    """Erreur detectee pendant l'analyse lexicale."""
    pass

class SyntaxError(QuestLangError):
    """Erreur detectee pendant l'analyse syntaxique."""
    pass

class SemanticError(QuestLangError):
    """Erreur detectee pendant l'analyse semantique."""
    pass

class RuntimeError(QuestLangError):
    """Erreur detectee pendant l'execution."""
    pass

class ErrorReporter:
    """Collecte et formate les diagnostics de compilation."""
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.infos = []

    def add_error(self, code, message, line=0, column=0, severity="ERROR"):
        self.errors.append({
            "code": code,
            "message": message,
            "line": line,
            "column": column,
            "severity": severity
        })

    def add_warning(self, code, message, line=0, column=0):
        self.warnings.append({
            "code": code,
            "message": message,
            "line": line,
            "column": column,
            "severity": "WARNING"
        })

    def add_info(self, code, message, line=0, column=0):
        self.infos.append({
            "code": code,
            "message": message,
            "line": line,
            "column": column,
            "severity": "INFO"
        })

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

    def format_console(self):
        lines = []
        for e in self.errors:
            lines.append(f"  [ERREUR] {e['code']}: {e['message']} (ligne {e['line']})")
        for w in self.warnings:
            lines.append(f"  [AVERTISSEMENT] {w['code']}: {w['message']} (ligne {w['line']})")
        for i in self.infos:
            lines.append(f"  [INFO] {i['code']}: {i['message']}")
        return "\n".join(lines)
