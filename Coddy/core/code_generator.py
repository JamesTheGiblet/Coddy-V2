# core/code_generator.py

import asyncio
from typing import Optional, List
from core.idea_synth import IdeaSynthesizer # Re-use the LLM logic

class CodeGenerator:
    """
    Generates code snippets, functions, and classes based on natural language descriptions.
    """

    def __init__(self, user_id: str = "default_user_codegen"):
        self.user_id = user_id
        # We can reuse the IdeaSynthesizer for its LLM communication capabilities
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
    print("\n--- End of CodeGenerator Tests ---")

if __name__ == "__main__":
    asyncio.run(main_test_code_gen())