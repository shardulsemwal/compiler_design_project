from flask import Flask, render_template, request
import re
import subprocess
import tempfile

app = Flask(__name__)

# ================= COMPILER MODULES =================

def tokenize(code):
    return re.findall(r'[a-zA-Z_]\w*|\d+|[=+*/()-;]', code)

def syntax_check(code):
    lines = code.strip().split('\n')
    for i, line in enumerate(lines, start=1):
        if '=' in line and not re.match(r'[a-zA-Z_]\w*\s*=\s*.+;', line.strip()):
            return f"Syntax Error at line {i}: {line}"
    return "Syntax is correct"

def constant_folding(code):
    result = []
    for line in code.split('\n'):
        match = re.search(r'(\d+)\s*\+\s*(\d+)', line)
        if match:
            value = str(int(match.group(1)) + int(match.group(2)))
            line = re.sub(r'\d+\s*\+\s*\d+', value, line)
        result.append(line)
    return "\n".join(result)

def dead_code_detector(code):
    lines = [l.strip() for l in code.split('\n') if l.strip()]
    assigns = {}
    dead = []

    for i, line in enumerate(lines):
        if '=' in line:
            var = line.split('=')[0].strip()
            assigns.setdefault(var, []).append(i+1)

    for var, occ in assigns.items():
        if len(occ) > 1:
            dead.append(f"Dead code at line {occ[0]}")

    return "\n".join(dead) if dead else "No dead code found"

def undefined_variable(code):
    lines = [l.strip() for l in code.split('\n') if l.strip()]
    defined = set()

    for i, line in enumerate(lines, start=1):
        if '=' in line:
            left, right = line.split('=')
            vars_in_expr = re.findall(r'[a-zA-Z_]\w*', right)
            for v in vars_in_expr:
                if v not in defined:
                    return f"Undefined variable '{v}' at line {i}"
            defined.add(left.strip())

    return "No undefined variables"

def symbol_table(code):
    tokens = re.findall(r'[a-zA-Z_]\w*', code)
    return "\n".join(sorted(set(tokens)))

def redundant_expression(code):
    expr_map = {}
    warnings = []

    for i, line in enumerate(code.split('\n'), start=1):
        if '=' in line:
            expr = line.split('=')[1].strip()
            if expr in expr_map:
                warnings.append(f"Redundant expression at line {i}")
            else:
                expr_map[expr] = i

    return "\n".join(warnings) if warnings else "No redundant expressions"

def division_by_zero(code):
    for i, line in enumerate(code.split('\n'), start=1):
        if re.search(r'/\s*0', line):
            return f"Division by zero at line {i}"
    return "No division by zero detected"

def compile_c_code(code):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".c") as f:
            f.write(code.encode())
            file_name = f.name

        exe_file = file_name.replace(".c", ".exe")

        result = subprocess.run(
            ["gcc", file_name, "-o", exe_file],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            return "Compilation Error:\n\n" + result.stderr
        else:
            run = subprocess.run([exe_file], capture_output=True, text=True)
            return "Compilation Successful!\n\nProgram Output:\n" + run.stdout

    except Exception as e:
        return str(e)

# ================= ROUTE =================

@app.route("/", methods=["GET", "POST"])
def index():
    output = ""
    code = ""

    if request.method == "POST":
        code = request.form["code"]
        action = request.form["action"]

        if action == "token":
            output = str(tokenize(code))
        elif action == "syntax":
            output = syntax_check(code)
        elif action == "opt":
            output = constant_folding(code)
        elif action == "dead":
            output = dead_code_detector(code)
        elif action == "undefined":
            output = undefined_variable(code)
        elif action == "symbol":
            output = symbol_table(code)
        elif action == "redundant":
            output = redundant_expression(code)
        elif action == "divide":
            output = division_by_zero(code)
        elif action == "compile":
            output = compile_c_code(code)

    return render_template("index.html", output=output, code=code)

if __name__ == "__main__":
    app.run(debug=True)

