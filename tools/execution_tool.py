import subprocess
import tempfile
import sys
import os
import re

def execute_code(source_code: str, timeout: int = 5) -> dict:
    """
    Menjalankan kode Python dan mendeteksi runtime error.

    Args:
        source_code: Kode Python yang akan dijalankan.
        timeout: Batas waktu eksekusi dalam detik.

    Returns:
        Dictionary berisi hasil eksekusi kode.
    """

    temp_file = None

    try:
        # Membuat file sementara untuk kode yang diuji
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".py",
            encoding="utf-8",
            delete=False
        ) as file:

            file.write(source_code)
            temp_file = file.name

        # Menjalankan kode menggunakan Python subprocess
        result = subprocess.run(
            [sys.executable, temp_file],
            capture_output=True,
            text=True,
            timeout=timeout
        )

        if result.returncode == 0:
            return {
                "status": "SUCCESS",
                "has_error": False,
                "error_type": None,
                "error_message": None,
                "line": None,
                "stdout": result.stdout,
                "stderr": None
            }

        # Mengambil informasi runtime error
        error_output = result.stderr.strip()

        error_type_match = re.search(
            r"(\w+Error|Exception):",
            error_output
        )

        error_type = (
            error_type_match.group(1)
            if error_type_match
            else "RuntimeError"
        )

        line_match = re.search(
            r"line (\d+)",
            error_output
        )

        error_line = (
            int(line_match.group(1))
            if line_match
            else None
        )

        return {
            "status": "ERROR",
            "has_error": True,
            "error_type": error_type,
            "error_message": error_output.splitlines()[-1],
            "line": error_line,
            "stdout": result.stdout,
            "stderr": error_output
        }

    except subprocess.TimeoutExpired:
        return {
            "status": "TIMEOUT",
            "has_error": True,
            "error_type": "TimeoutError",
            "error_message": f"Execution exceeded {timeout} seconds",
            "line": None,
            "stdout": None,
            "stderr": None
        }

    except Exception as error:
        return {
            "status": "ERROR",
            "has_error": True,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "line": None,
            "stdout": None,
            "stderr": None
        }

    finally:
        # Menghapus file sementara setelah eksekusi
        if temp_file and os.path.exists(temp_file):
            os.remove(temp_file)


# Testing mandiri
if __name__ == "__main__":

    buggy_code = """
angka = 10
hasil = angka / 0

print(hasil)
"""

    result = execute_code(buggy_code)

    print("=== EXECUTION TOOL RESULT ===")

    for key, value in result.items():
        print(f"{key}: {value}")
