# core/code_generator.py

import ast
import asyncio
from typing import Optional, List
from core.idea_synth import IdeaSynthesizer # Re-use the LLM logic
from pathlib import Path # Import Path

class CodeGenerator:
    """
    Generates code snippets, functions, and classes based on natural language descriptions.
    """

    def __init__(self, user_id: str = "default_user_codegen"):
        self.user_id = user_id
        self.llm_comm = IdeaSynthesizer(user_id)

    async def generate_function(
        self,
        description: str,
        function_name: str,
        args: Optional[List[str]] = None,
        return_type: str = "str"
    ) -> str:
        """
        Generates a Python function based on a description.

        Args:
            description: A natural language description of what the function should do.
            function_name: The desired name for the function.
            args: A list of arguments for the function, e.g., ["path: str", "data: dict"].
            return_type: The return type of the function.

        Returns:
            A string containing the generated Python function code.
        """
        print(f"Generating function '{function_name}'...")

        arg_str = ", ".join(args) if args else ""

        prompt = f"""
        Generate a complete, robust Python function with the following specifications.
        The function must include a clear docstring, type hints, and basic error handling where appropriate.

        Function Name: {function_name}
        Arguments: {arg_str}
        Return Type: {return_type}
        Description: {description}

        Please provide only the Python code for the function, starting with 'def {function_name}' and nothing else.
        """

        try:
            # Using a lower temperature for more predictable code generation
            generated_code = await self.llm_comm.summarize_text(prompt, temperature=0.2, top_p=0.9)
            # Clean up the response to ensure it's just the code block
            if "```python" in generated_code:
                generated_code = generated_code.split("```python")[1].split("```")[0]
            
            return generated_code.strip()
        except Exception as e:
            print(f"Error generating function: {e}")
            return f"# Failed to generate function '{function_name}': {e}"

    async def refactor_code(self, original_code: str, instruction: str) -> str:
        """
        Refactors a block of Python code based on a given instruction.

        Args:
            original_code: The original Python code as a string.
            instruction: The natural language instruction for refactoring.

        Returns:
            A string containing the refactored Python code.
        """
        print(f"Refactoring code with instruction: '{instruction}'...")

        prompt = f"""
        You are an expert Python programmer tasked with refactoring code.
        Please refactor the following Python code based on the provided instruction.
        Return only the complete, refactored code block. Do not add any explanations,
        introductions, or markdown formatting like ```python.

        Instruction:
        ---
        {instruction}
        ---

        Original Code:
        ---
        {original_code}
        ---

        Refactored Code:
        """

        try:
            # Using a lower temperature for more predictable code generation
            refactored_code = await self.llm_comm.summarize_text(prompt, temperature=0.1, top_p=0.9)
            # Clean up the response to ensure it's just the code block
            if "```python" in refactored_code:
                refactored_code = refactored_code.split("```python")[1].split("```")[0]
            elif "```" in refactored_code:
                refactored_code = refactored_code.split("```")[1].split("```")[0]
            return refactored_code.strip()
        except Exception as e:
            print(f"Error refactoring code: {e}")
            return f"# Failed to refactor code: {e}\n\n{original_code}"

    async def generate_tests_for_file(self, source_code: str, original_file_path: Path) -> str:
        """
        Generates pytest unit tests for a given block of Python source code.

        Args:
            source_code: The original Python code as a string.
            original_file_path: The Path object of the original source file.
                                This is crucial for determining correct import paths.

        Returns:
            A string containing the generated pytest code.
        """
        print(f"Generating unit tests for source code from {original_file_path.name}...")

        module_name = original_file_path.stem

        prompt = f"""
        You are an expert Python testing engineer. Your task is to write a comprehensive suite of unit tests for the provided Python code using the `pytest` framework.

        The original source code comes from a file named `{original_file_path.name}`.
        When writing imports for functions/classes from this source code, assume they can be imported like:
        `from {module_name} import <function_name>` or `from {module_name} import <ClassName>`.

        - Analyze the provided source code to understand its functions, classes, and methods.
        - Generate clear, concise, and effective `pytest` tests.
        - Cover normal use cases, edge cases, and potential error conditions.
        - **Ensure necessary imports are included, using the module name `{module_name}` as specified above.**
        - Return only the complete, runnable Python code for the tests. Do not add any explanations,
        introductions, or markdown formatting like ```python.

        Source Code to Test:
        ---
        {source_code}
        ---

        Pytest Test Code:
        """

        try:
            generated_tests = await self.llm_comm.summarize_text(prompt, temperature=0.2, top_p=0.9)

            if "```python" in generated_tests:
                generated_tests = generated_tests.split("```python")[1].split("```")[0]
            elif "```" in generated_tests:
                generated_tests = generated_tests.split("```")[1].split("```")[0]

            generated_tests = generated_tests.strip()

            # --- Start Robust Post-processing for Imports (Revised) ---
            generated_lines = generated_tests.splitlines()
            
            # 1. Ensure 'import pytest' is at the top
            if "import pytest" not in generated_lines:
                generated_lines.insert(0, "import pytest")
            
            # 2. Extract top-level function/class names from the source code
            top_level_names = []
            try:
                source_tree = ast.parse(source_code)
                for node in source_tree.body:
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        top_level_names.append(node.name)
            except SyntaxError:
                print(f"Warning: Source code has a syntax error. Cannot extract names for imports.")
                top_level_names = []

            # 3. Construct the required 'from module import names' statement
            required_module_import = ""
            if top_level_names:
                required_module_import = f"from {module_name} import {', '.join(sorted(top_level_names))}"

            # 4. Check if the required module import exists in the generated tests
            has_required_module_import = False
            for line in generated_lines:
                # Simple check: does any line contain 'from <module_name> import'?
                if f"from {module_name} import" in line:
                    has_required_module_import = True
                    break
            
            # 5. If the required module import is missing, insert it right after 'import pytest'
            if not has_required_module_import and required_module_import:
                insert_index = 1 if generated_lines and generated_lines[0] == "import pytest" else 0
                generated_lines.insert(insert_index, required_module_import)
                # Add an extra newline for better formatting if it's not the first line
                if insert_index > 0:
                    generated_lines.insert(insert_index + 1, "") # Add a blank line after imports

            return "\n".join(generated_lines).strip()
            # --- End Robust Post-processing ---

        except Exception as e:
            print(f"Error generating unit tests: {e}")
            return f"# Failed to generate unit tests: {e}\n\n"


# Example Usage
async def main_test_code_gen():
    print("\n--- Testing CodeGenerator ---")
    code_gen = CodeGenerator()

    description = "Reads a file from a given path and returns its content as a string. It should handle FileNotFoundError."
    function_code = await code_gen.generate_function(
        description=description,
        function_name="read_file_content",
        args=["file_path: str"],
        return_type="str"
    )
    print("\n--- Generated Function ---")
    print(function_code)

    print("\n--- Testing Test Generation ---")
    sample_code = """
def add(a, b):
    return a + b

class Calculator:
    def multiply(self, x, y):
        return x * y
"""
    # Create a dummy path for the example usage
    dummy_path = Path("sample_module.py")
    test_code = await code_gen.generate_tests_for_file(sample_code, dummy_path)
    print("\n--- Generated Test Code ---")
    print(test_code)
    print("\n--- End of CodeGenerator Tests ---")

if __name__ == "__main__":
    asyncio.run(main_test_code_gen())