import requests
import select
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import subprocess
import os
import threading
import time
import signal
import re
from typing import List, Dict
from collections import defaultdict

app = Flask(__name__)
CORS(app)



HUGGINGFACE_API_KEY = "your api here"   #tempemail

#HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/codellama/CodeLlama-34b-Instruct-hf"

#HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/Qwen/QwQ-32B-Preview"                #working good
HUGGINGFACE_API_URL =    "https://api-inference.huggingface.co/models/Qwen/Qwen2.5-Coder-32B-Instruct"



class CodeExecutionError(Exception):
    pass

def cleanup_files(*files):
    """Remove temporary files if they exist."""
    for file in files:
        try:
            os.remove(file)
        except (FileNotFoundError, PermissionError):
            pass

def run_with_timeout(process, timeout=10):
    """Terminate the process after a timeout period."""
    def kill_process():
        time.sleep(timeout)
        try:
            process.kill()
        except ProcessLookupError:
            pass

    thread = threading.Thread(target=kill_process)
    thread.daemon = True
    thread.start()
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/run_code', methods=['POST'])
def run_code():
    data = request.get_json()
    language = data.get('language', '').strip().lower()
    code = data.get('code', '').strip()
    user_inputs = data.get('inputs', [])

    if not code:
        return jsonify({'error': 'No code provided', 'input_required': False})

    try:
        if language == 'python':
            return handle_python_execution(code, user_inputs)
        elif language in ['c', 'cpp', 'java']:
            return handle_compiled_language_execution(language, code, user_inputs)
        else:
            return jsonify({'error': 'Unsupported language', 'input_required': False})
    except Exception as e:
        return jsonify({'error': str(e), 'input_required': False})


def handle_python_execution(code, user_inputs):
    try:
        temp_file = 'temp_script.py'
        with open(temp_file, 'w') as f:
            f.write(code)

        process = subprocess.Popen(
            ['python3', temp_file],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        output_buffer = []
        input_index = 0

        def read_output():
            """Read output until input is needed"""
            try:
                line = process.stdout.readline()
                if line:
                    return line.rstrip()
            except:
                pass
            return None

        # Process line by line
        while True:
            # Read output until input prompt
            while True:
                line = read_output()
                if not line:
                    break
                output_buffer.append(line)
                if 'input' in code and not line.endswith('input'):
                    break

            # Check if process has ended
            if process.poll() is not None:
                break

            # Check if input is needed
            if input_index < len(user_inputs):
                process.stdin.write(f"{user_inputs[input_index]}\n")
                process.stdin.flush()
                input_index += 1
            else:
                # Need more input
                if code.count('input(') > input_index:
                    cleanup_files(temp_file)
                    return jsonify({
                        'output': '\n'.join(output_buffer),
                        'error': '',
                        'input_required': True
                    })
                break

        # Get remaining output
        remaining_output, error = process.communicate()
        if remaining_output:
            output_buffer.extend(line.rstrip() for line in remaining_output.splitlines() if line.strip())

        cleanup_files(temp_file)
        return jsonify({
            'output': '\n'.join(output_buffer),
            'error': error if error else '',
            'input_required': False
        })

    except Exception as e:
        cleanup_files(temp_file)
        return jsonify({'error': str(e), 'input_required': False})


def handle_compiled_language_execution(language, code, user_inputs):
    if language == 'java':
        return handle_java_execution(code, user_inputs)
    elif language == 'cpp':
        return handle_cpp_execution(code, user_inputs)
    elif language == 'c':
        return handle_c_execution(code, user_inputs)

def handle_cpp_execution(code, user_inputs):
    try:
        # Write and compile
        with open('temp.cpp', 'w') as f:
            f.write(code)

        compile_result = subprocess.run(['g++', 'temp.cpp', '-o', 'temp'], capture_output=True, text=True)
        if compile_result.returncode != 0:
            cleanup_files('temp.cpp', './temp')
            return jsonify({
                'error': f'Compilation error:\n{compile_result.stderr}',
                'input_required': False
            })

        # Program execution
        expected_inputs = code.count('cin >>')
        received_inputs = len(user_inputs) if user_inputs else 0
        output_buffer = []

        process = subprocess.Popen(
            './temp',
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        def read_output():
            try:
                ready = select.select([process.stdout], [], [], 0.1)[0]
                if ready:
                    line = process.stdout.readline()
                    if line:
                        return line.rstrip()
            except:
                pass
            return None

        try:
            # Initial read
            while True:
                line = read_output()
                if not line:
                    break
                output_buffer.append(line)

            # Process needs input
            if expected_inputs > received_inputs:
                cleanup_files('temp.cpp', './temp')
                return jsonify({
                    'output': format_output('\n'.join(output_buffer)),
                    'error': '',
                    'input_required': True
                })

            # Send existing inputs if any
            if user_inputs:
                for input_value in user_inputs:
                    process.stdin.write(f"{input_value}\n")
                    process.stdin.flush()

                    # Read output after input
                    while True:
                        line = read_output()
                        if not line:
                            break
                        output_buffer.append(line)

                    # Check if more input needed
                    if len(user_inputs) < expected_inputs:
                        cleanup_files('temp.cpp', './temp')
                        return jsonify({
                            'output': format_output('\n'.join(output_buffer)),
                            'error': '',
                            'input_required': True
                        })

            # Get remaining output
            output, error = process.communicate(timeout=1)
            if output:
                output_buffer.extend(output.splitlines())

            cleanup_files('temp.cpp', './temp')
            return jsonify({
                'output': format_output('\n'.join(output_buffer)),
                'error': error if error else '',
                'input_required': False
            })

        except subprocess.TimeoutExpired:
            process.kill()
            cleanup_files('temp.cpp', './temp')
            if received_inputs < expected_inputs:
                return jsonify({
                    'output': format_output('\n'.join(output_buffer)),
                    'error': '',
                    'input_required': True
                })
            return jsonify({
                'error': 'Execution timed out',
                'input_required': False
            })

    except Exception as e:
        cleanup_files('temp.cpp', './temp')
        return jsonify({'error': str(e), 'input_required': False})

def handle_c_execution(code, user_inputs):
    try:
        # Compile
        with open('temp.c', 'w') as f:
            f.write(code)

        compile_result = subprocess.run(['gcc', 'temp.c', '-o', 'temp'], capture_output=True, text=True)
        if compile_result.returncode != 0:
            cleanup_files('temp.c', './temp')
            return jsonify({'error': f'Compilation error:\n{compile_result.stderr}', 'input_required': False})

        expected_inputs = code.count('scanf')
        received_inputs = len(user_inputs) if user_inputs else 0
        output_buffer = []

        process = subprocess.Popen(
            './temp',
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        def read_until_input():
            """Read output until input is needed"""
            while True:
                ready = select.select([process.stdout], [], [], 0.1)[0]
                if not ready:
                    break
                line = process.stdout.readline()
                if not line:
                    break
                output_buffer.append(line.rstrip())

        try:
            # Initial read to get first prompt
            read_until_input()

            # Need first input?
            if expected_inputs > received_inputs:
                cleanup_files('temp.c', './temp')
                return jsonify({
                    'output': format_output('\n'.join(output_buffer)),
                    'error': '',
                    'input_required': True
                })

            # Process existing inputs
            if user_inputs:
                for input_value in user_inputs:
                    # Send input
                    process.stdin.write(f"{input_value}\n")
                    process.stdin.flush()

                    # Read output until next input needed
                    read_until_input()

                    # Check if we need more input
                    if len(user_inputs) < expected_inputs:
                        cleanup_files('temp.c', './temp')
                        return jsonify({
                            'output': format_output('\n'.join(output_buffer)),
                            'error': '',
                            'input_required': True
                        })

            # Get final output
            output, error = process.communicate(timeout=0.5)
            if output:
                final_lines = [line.rstrip() for line in output.splitlines() if line.strip()]
                output_buffer.extend(final_lines)

            cleanup_files('temp.c', './temp')
            return jsonify({
                'output': format_output('\n'.join(output_buffer)),
                'error': error if error else '',
                'input_required': False
            })

        except subprocess.TimeoutExpired:
            process.kill()
            cleanup_files('temp.c', './temp')
            if received_inputs < expected_inputs:
                return jsonify({
                    'output': format_output('\n'.join(output_buffer)),
                    'error': '',
                    'input_required': True
                })
            return jsonify({
                'error': 'Execution timed out',
                'input_required': False
            })

    except Exception as e:
        cleanup_files('temp.c', './temp')
        return jsonify({'error': str(e), 'input_required': False})

def read_output(process, output_buffer, timeout=0.1):
    """Read process output until timeout."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        line = process.stdout.readline()
        if not line:
            break
        output_buffer.append(line.rstrip())

def handle_java_execution(code, user_inputs):
    try:
        # Compile
        with open('Main.java', 'w') as f:
            f.write(code)

        compile_result = subprocess.run(['javac', 'Main.java'], capture_output=True, text=True)
        if compile_result.returncode != 0:
            cleanup_files('Main.java', 'Main.class')
            return jsonify({'error': f'Compilation error:\n{compile_result.stderr}', 'input_required': False})

        # Count inputs and setup buffers
        scanner_inputs = ['nextLine()', 'nextInt()', 'next()', 'nextDouble()']
        expected_inputs = sum(code.count(input_type) for input_type in scanner_inputs)
        received_inputs = len(user_inputs) if user_inputs else 0
        output_buffer = []

        process = subprocess.Popen(
            ['java', 'Main'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        # Handle input/output
        def read_output():
            output = []
            while True:
                ready = select.select([process.stdout], [], [], 0.1)[0]
                if not ready:
                    break
                line = process.stdout.readline()
                if not line:
                    break
                output.append(line.rstrip())
            return output

        if user_inputs:
            for input_value in user_inputs:
                lines = read_output()
                output_buffer.extend(lines)
                process.stdin.write(f"{input_value}\n")
                process.stdin.flush()

        lines = read_output()
        output_buffer.extend(lines)

        # Check if more input needed
        if received_inputs < expected_inputs:
            cleanup_files('Main.java', 'Main.class')
            return jsonify({
                'output': format_output('\n'.join(output_buffer)),
                'error': '',
                'input_required': True
            })

        # Get final output
        try:
            output, error = process.communicate(timeout=0.5)
            if output:
                output_buffer.extend(output.splitlines())
        except subprocess.TimeoutExpired:
            process.kill()

        cleanup_files('Main.java', 'Main.class')
        return jsonify({
            'output': format_output('\n'.join(output_buffer)),
            'error': '',
            'input_required': False
        })

    except Exception as e:
        cleanup_files('Main.java', 'Main.class')
        return jsonify({'error': str(e), 'input_required': False})

def detect_input_operation(code, language):
    """Detect if code contains input operations."""
    if language == 'java':
        return 'Scanner' in code and ('nextLine()' in code or 'next()' in code or 'nextInt()' in code)
    elif language == 'cpp':
        return 'cin' in code
    elif language == 'c':
        return 'scanf' in code
    return False

def format_output(output):
    if not output:
        return ''
    # Replace HTML line breaks with actual newlines for proper display
    lines = output.replace('<br>', '\n').splitlines()
    return '\n'.join(line.rstrip() for line in lines)

BOILERPLATE_CODE = {
    'python': '''# Write your Python code here...


print("Welcome to Go Compiler")

print("Best on the go Online Compiler")

# Click Clear button to erase...
''' ,
    'c': '''#include <stdio.h>

int main() {
    // Your code goes here
    return 0;
}
''',
    'cpp': '''#include <iostream>
using namespace std;

int main() {
    // Your code goes here
    return 0;
}
''',
    'java': '''public class Main {
    public static void main(String[] args) {
        // Your code goes here
    }
}
'''
}

# Add new route for getting boilerplate code
@app.route('/get_boilerplate', methods=['GET'])
def get_boilerplate():
    language = request.args.get('language', 'python')
    return jsonify({'code': BOILERPLATE_CODE.get(language, '')})

# Add new route for file download
@app.route('/download_code', methods=['POST'])
def download_code():
    data = request.get_json()
    language = data.get('language', 'python')
    code = data.get('code', '')

    file_extensions = {
        'python': '.py',
        'c': '.c',
        'cpp': '.cpp',
        'java': '.java'
    }

    filename = f"code{file_extensions.get(language, '.txt')}"
    return jsonify({
        'filename': filename,
        'content': code
    })

def analyze_code(code: str, language: str) -> str:
    """Analyze code and provide improvement suggestions using AI"""
    headers = {
        "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = f"""Analyze the following {language} code:

{code}

And Please provide specific suggestions for:
1. Code correctness
2. Optimized approaches



Format your response in clear sections using markdown, with examples where relevant."""

    try:
        response = requests.post(
            HUGGINGFACE_API_URL,
            headers=headers,
            json={
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 1000,
                    "temperature": 0.7,
                    "top_p": 0.95,
                    "do_sample": True,
                    "return_full_text": False
                }
            },
            timeout=30
        )

        if response.status_code == 200:
            suggestions = response.json()[0]["generated_text"]
            return format_suggestions(code, suggestions)
        else:
            return f"// Error: Analysis failed (Status: {response.status_code})"

    except Exception as e:
        return f"// Error during analysis: {str(e)}"

def format_suggestions(code: str, suggestions: str) -> str:
    """Format the analysis output with syntax highlighting and clear sections"""
    result = []
    result.append("<div class='code-suggestions'>")
    result.append("<h2>🔍 Code Analysis Report</h2>")
    result.append("<hr>")

    # Add original code
    result.append("<h3>📌 Original Code:</h3>")
    result.append(f"<pre class='code-block'>{code}</pre>")

    # Clean and format suggestions
    suggestions = suggestions.replace("```", "").strip()

    # Add section headers
    sections = []

    result.append("<h3>💡 Analysis & Suggestions:</h3>")

    # Format each detected section
    found_sections = False
    for section in sections:
        if section.lower() in suggestions.lower():
            found_sections = True
            result.append(f"<h4>🔸 {section}:</h4>")
            # Extract relevant part of suggestions for this section
            section_pattern = re.compile(f"{section}:?(.*?)(?={sections[0]}|$)",
                                      re.IGNORECASE | re.DOTALL)
            matches = section_pattern.findall(suggestions)
            if matches:
                content = matches[0].strip()
                # Format bullet points
                content = re.sub(r'^[\-\*]\s*', '• ', content, flags=re.MULTILINE)
                result.append(f"<p>{content}</p>")

    # If no sections were found in AI response, just append the raw suggestions
    if not found_sections:
        result.append(f"<p>{suggestions}</p>")

    result.append("</div>")
    return ''.join(result)

# Add new route for code analysis
@app.route('/improve_code', methods=['POST'])
def improve_code():
    data = request.get_json()
    language = data.get('language', '')
    code = data.get('code', '')

    suggestions = analyze_code(code, language)
    return jsonify({'suggestions': suggestions})

CODE_TEMPLATES = {
    # Data Structures
    'array': defaultdict(lambda: 'No template', {
        'python': '''def create_array(size):
    return [0] * size

# Example usage
arr = create_array(5)
print(arr)  # [0, 0, 0, 0, 0]''',
        'cpp': '''vector<int> createArray(int size) {
    return vector<int>(size, 0);
}''',
        'java': '''int[] createArray(int size) {
    return new int[size];
}'''
    }),

    # Algorithms
    'sort': defaultdict(lambda: 'No template', {
        'python': '''def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n-i-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
    return arr''',
        'cpp': '''void bubbleSort(vector<int>& arr) {
    int n = arr.size();
    for(int i = 0; i < n-1; i++)
        for(int j = 0; j < n-i-1; j++)
            if(arr[j] > arr[j+1])
                swap(arr[j], arr[j+1]);
}'''
    }),

    # File Operations
    'file': defaultdict(lambda: 'No template', {
        'python': '''def read_file(filename):
    with open(filename, 'r') as file:
        return file.read()

def write_file(filename, content):
    with open(filename, 'w') as file:
        file.write(content)''',
        'cpp': '''string readFile(const string& filename) {
    ifstream file(filename);
    stringstream buffer;
    buffer << file.rdbuf();
    return buffer.str();
}'''
    })
}

def generate_code_from_api(prompt, language):
    """Generate code using Hugging Face API"""
    headers = {
        "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
        "Content-Type": "application/json"
    }

    # More specific prompt for better code generation
    formatted_prompt = (
        f"Write {language} code for: {prompt} , start code from first line, use inline comments.\n"

    )

    try:
        response = requests.post(
            HUGGINGFACE_API_URL,
            headers=headers,
            json={
                "inputs": formatted_prompt,
                "parameters": {
                    "max_new_tokens": 800,  # Increased token limit
                    "temperature": 0.3,     # Lower temperature for more focused output
                    "top_p": 0.95,
                    "do_sample": True,
                    "return_full_text": False
                }
            },
            timeout=30
        )

        if response.status_code == 200:
            generated_text = response.json()[0]["generated_text"]
            return extract_clean_code(generated_text, language)
        else:
            return f"// Error: API request failed (Status: {response.status_code})"

    except Exception as e:
        return f"// Error: {str(e)}"

def extract_clean_code(text, language):
    """Extract clean code from generated text"""
    # Remove markdown code blocks
    code = re.sub(r'```.*?\n', '', text)
    code = re.sub(r'```', '', code)

    # Remove explanatory text
    lines = []
    for line in code.split('\n'):
        if line.strip() and not line.startswith(('Here', 'This', '//', '#')):
            lines.append(line)

    return '\n'.join(lines).strip()

def remove_duplicate_code(code):
    """Remove duplicated code blocks"""
    # Split into blocks and remove duplicates while preserving order
    blocks = [block.strip() for block in code.split('\n\n') if block.strip()]
    unique_blocks = []
    seen = set()

    for block in blocks:
        if block not in seen:
            unique_blocks.append(block)
            seen.add(block)

    return '\n\n'.join(unique_blocks)
@app.route('/generate_code', methods=['POST'])

def generate_code():
    data = request.get_json()
    prompt = data.get('prompt', '').strip()
    language = data.get('language', 'python')

    if not prompt:
        return jsonify({'error': 'No prompt provided'})

    try:
        # Format prompt for better code generation
        formatted_prompt = (
            f"Write complete, working {language} code for: {prompt}\n"
            "Return only the code implementation without any explanations."
        )

        # Call API with formatted prompt
        headers = {
            "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
            "Content-Type": "application/json"
        }

        response = requests.post(
            HUGGINGFACE_API_URL,
            headers=headers,
            json={
                "inputs": formatted_prompt,
                "parameters": {
                    "max_new_tokens": 1000,
                    "temperature": 0.3,
                    "top_p": 0.95,
                    "do_sample": True,
                    "return_full_text": False
                }
            },
            timeout=30
        )

        if response.status_code == 200:
            generated_code = response.json()[0]["generated_text"]

            # Clean up generated code
            generated_code = extract_clean_code(generated_code, language)

            # Add basic structure if missing
            generated_code = format_code_structure(generated_code, language)

            return jsonify({
                'code': generated_code,
                'language': language
            })
        else:
            return jsonify({'error': f'API request failed: {response.status_code}'})

    except Exception as e:
        return jsonify({'error': f'Error generating code: {str(e)}'})
def format_code_structure(code, language):
    """Add basic code structure if missing"""
    if not code:
        return code

    if language == 'python':
        if not any(keyword in code for keyword in ['def ', 'class ']):
            indented_code = '\n    '.join(code.split('\n'))
            code = f"def main():\n    {indented_code}"
            if 'if __name__' not in code:
                code += "\n\nif __name__ == '__main__':\n    main()"

    elif language == 'java':
        if 'class' not in code:
            indented_code = '\n        '.join(code.split('\n'))
            code = f"""public class Main {{
    public static void main(String[] args) {{
        {indented_code}
    }}
}}"""

    elif language in ['c', 'cpp']:
        includes = '#include <iostream>\nusing namespace std;\n\n' if language == 'cpp' else '#include <stdio.h>\n\n'
        if 'main' not in code:
            indented_code = '\n    '.join(code.split('\n'))
            code = f"""{includes}int main() {{
    {indented_code}
    return 0;
}}"""

    return code
# Add this at the top of app.py with other constants
KEYWORDS = {
    'array': ['array', 'list', 'vector'],
    'sort': ['sort', 'ordering', 'bubble', 'algorithm'],
    'file': ['file', 'read', 'write', 'open']
}

# Add this at the bottom of app.py
if __name__ == '__main__':
    app.run(debug=True)
