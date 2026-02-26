"""
AST Validator for user-created skill scripts.
Validates Python code for safety before saving.
"""

import ast
from typing import Dict, List, Set

BLOCKED_MODULES: Set[str] = {
    "os", "subprocess", "sys", "shutil",
    "socket", "http", "urllib", "ftplib", "smtplib",
    "importlib", "ctypes", "pickle", "shelve", "marshal",
    "multiprocessing", "threading", "signal",
    "code", "codeop", "compileall",
    "webbrowser", "antigravity",
}

BLOCKED_BUILTINS: Set[str] = {
    "eval", "exec", "compile", "__import__",
    "globals", "locals", "vars",
    "breakpoint", "exit", "quit",
}

BLOCKED_ATTRIBUTES: Set[str] = {
    "__builtins__", "__globals__", "__subclasses__",
    "__code__", "__class__", "__bases__", "__mro__",
}


def validate_code_ast(source: str, filename: str = "<user_skill>") -> Dict:
    """
    Valida codigo Python contra regras de seguranca.

    Returns:
        {"valid": bool, "errors": [str]}
    """
    errors = []

    try:
        tree = ast.parse(source, filename=filename)
    except SyntaxError as e:
        return {"valid": False, "errors": [f"Syntax error: {e}"]}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                module_root = alias.name.split(".")[0]
                if module_root in BLOCKED_MODULES:
                    errors.append(
                        f"Line {node.lineno}: Blocked import '{alias.name}'"
                    )

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                module_root = node.module.split(".")[0]
                if module_root in BLOCKED_MODULES:
                    errors.append(
                        f"Line {node.lineno}: Blocked import from '{node.module}'"
                    )

        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id in BLOCKED_BUILTINS:
                errors.append(
                    f"Line {node.lineno}: Blocked call '{func.id}()'"
                )
            elif isinstance(func, ast.Attribute) and func.attr in BLOCKED_BUILTINS:
                errors.append(
                    f"Line {node.lineno}: Blocked call '.{func.attr}()'"
                )

        elif isinstance(node, ast.Attribute):
            if node.attr in BLOCKED_ATTRIBUTES:
                errors.append(
                    f"Line {node.lineno}: Blocked attribute '.{node.attr}'"
                )

    return {"valid": len(errors) == 0, "errors": errors}
