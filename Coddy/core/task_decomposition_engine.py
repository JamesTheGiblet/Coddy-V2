# c:\Users\gilbe\Documents\GitHub\Coddy V2\Coddy/core/task_decomposition_engine.py
import json
import asyncio # Import asyncio for async operations
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os

class TaskDecompositionEngine:
    async def decompose(self, goal: str) -> list[str]: # Made the method async
        """
        Decompose a high-level goal into smaller, executable subtasks.

        Args:
            goal (str): A natural language description of the task.

        Returns:
            list[str]: A list of subtasks.
        """
        # TODO: Replace with actual LLM integration
        # This is a placeholder and needs to be implemented
        # using a library like Langchain or a direct API call
        # to an LLM service (e.g., OpenAI, Gemini, etc.)
        # Here's a basic example using a hypothetical `llm_service`
        # (you'll need to install and configure the actual LLM library)

        # Simulate an async operation for now
        await asyncio.sleep(0.1) 

        # prompt = f"""Decompose the following development goal into smaller, 
        # executable subtasks: "{goal}".  Return the subtasks as a JSON list of strings."""

        # try:
        #     response = await llm_service.generate_text(prompt) # Ensure LLM call is awaited
        #     tasks = json.loads(response) # Assuming the LLM returns JSON
        #     if isinstance(tasks, list) and all(isinstance(task, str) for task in tasks):
        #         return tasks
        #     else:
        #         return ["Error: LLM returned invalid task list."]
        # except Exception as e:
        #     return [f"Error during LLM call: {e}"]
        
        # Placeholder decomposition logic for iterative questioning
        goal_lower = goal.lower().strip()

        # Check for "funny clock" and then ask questions iteratively
        if "funny clock" in goal_lower:
            if not any(lang in goal_lower for lang in ["python", "javascript", "html", "java", "c++"]):
                return [
                    "ask_question: What programming language should the funny clock be in?"
                ]
            elif not any(element in goal_lower for element in ["ascii", "emoji", "graphical", "gui", "web"]):
                return [
                    "ask_question: What kind of 'funny' elements or display style should it have (e.g., ASCII art, emojis, graphical, GUI, web-based)?"
                ]
            elif not any(app_type in goal_lower for app_type in ["console", "terminal", "gui", "web-based", "browser"]):
                return [
                    "ask_question: Should it be a console/terminal application, a GUI application, or a web-based application?"
                ]
            else:
                # If all questions are answered, proceed to generate code
                return [
                    f'generate_code "{goal}" "funny_clock.py"',
                    "read funny_clock.py"
                ]
        elif "calculator" in goal_lower and "code" in goal_lower:
            # Decompose into generate_code and then read
            return [
                'generate_code "Python calculator with add, subtract, multiply, divide functions" "calculator.py"',
                "read calculator.py"
            ]
        elif "read" in goal_lower and "create" in goal_lower:
             return [
                "write test_script.py print(\"Hello, Coddy AI!\")", # Changed to 'write' command
                "read test_script.py"
            ]
        elif "flesh out the plan" in goal_lower or goal_lower == "hello" or goal_lower == "plan":
            return [
                "ask_question: To help me flesh out the plan, could you please provide more details? What specific task or project are you thinking about, or what kind of code do you need?"
            ]
        else:
            return [
                f"LLM-based decomposition for: {goal} (Placeholder)",
                "Consider breaking down complex tasks further",
                "This is a simulated decomposition."
            ]

