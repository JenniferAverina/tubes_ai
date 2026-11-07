import ast

def check_syntax(source_code: str) -> dict:
    """
    Memeriksa syntax error pada kode Python.

    Args:
        source_code: Kode Python yang akan diperiksa.

    Returns:
        Dictionary berisi status dan informasi hasil pemeriksaan.
    """

    try:
        # Memeriksa apakah kode memiliki sintaks Python yang valid
        ast.parse(source_code)

        return {
            "status": "SUCCESS",
            "has_error": False,
            "error_type": None,
            "error_message": None,
            "line": None,
            "column": None,
            "source_line": None
        }

    except SyntaxError as error:
        # Mengambil informasi lokasi syntax error
        lines = source_code.splitlines()

        error_line = (
            lines[error.lineno - 1]
            if error.lineno and error.lineno <= len(lines)
            else None
        )

        return {
            "status": "ERROR",
            "has_error": True,
            "error_type": "SyntaxError",
            "error_message": error.msg,
            "line": error.lineno,
            "column": error.offset,
            "source_line": error_line
        }


# Testing mandiri
if __name__ == "__main__":

    buggy_code = """
def tambah(a, b)
    return a + b

print(tambah(5, 3))
"""

    result = check_syntax(buggy_code)

    print("=== SYNTAX CHECKER RESULT ===")

    for key, value in result.items():
        print(f"{key}: {value}")
