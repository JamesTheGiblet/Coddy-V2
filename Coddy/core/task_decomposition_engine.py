# c:\Users\gilbe\Documents\GitHub\Coddy V2\Coddy/core/task_decomposition_engine.py
import json
import asyncio # Import asyncio for async operations
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os
from typing import List, Dict, Any, Optional # Added for type hints

# Load environment variables from .env file
load_dotenv() 

class TaskDecompositionEngine:
    """
    Decomposes high-level goals into smaller, executable subtasks,
    with the ability to tailor the decomposition based on a user's profile.
    """
    def __init__(self):
        """
        Initializes the TaskDecompositionEngine, setting up the LLM.
        The LLM configuration can be dynamically influenced by user profile settings.
        """
        # Initialize the LLM with a default model and API key.
        # Temperature can be overridden by user profile later.
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-pro", # Default model for decomposition
            temperature=0.7,    # Default creativity/randomness
            GEMINI_API_KEY=os.getenv("GEMINI_API_KEY")
        )
        if not os.getenv("GEMINI_API_KEY"):
            print("Warning: GEMINI_API_KEY not found in environment variables. LLM calls for decomposition may fail.")


    async def decompose(self, goal: str, user_profile: Optional[Dict[str, Any]] = None) -> list[str]:
        """
        Decompose a high-level goal into smaller, executable subtasks,
        tailoring the process based on the user's profile if provided.

        Args:
            goal (str): A natural language description of the task.
            user_profile (Optional[Dict[str, Any]]): The user's personalization profile,
                                                      containing preferences like coding style,
                                                      preferred languages, persona, and creativity.

        Returns:
            list[str]: A list of subtasks, each formatted as a Coddy command string.
        """
        # If user_profile is provided, prioritize LLM-based decomposition with personalization
        if user_profile:
            # Extract relevant personalization settings from the user profile
            preferred_languages = user_profile.get('preferred_languages', [])
            coding_style = user_profile.get('coding_style_preferences', {})
            persona = user_profile.get('idea_synth_persona', 'default')
            creativity = user_profile.get('idea_synth_creativity', 0.7)

            # Construct dynamic style hints based on user's coding style and preferred languages
            style_hints = []
            if coding_style:
                # Convert coding style preferences to a readable string for the LLM
                style_hints.append(f"Your preferred coding style includes: {json.dumps(coding_style)}.")
            if preferred_languages:
                style_hints.append(f"You primarily work with these languages: {', '.join(preferred_languages)}.")
            
            style_hint_str = " ".join(style_hints) if style_hints else ""

            # Define the prompt template for the LLM, incorporating user preferences
            prompt_template = f"""
            As an expert software development assistant, your task is to decompose a high-level development goal into a list of smaller, actionable, and executable subtasks.
            Each subtask should be a command that Coddy can execute (e.g., 'read <file>', 'write <file> <content>', 'list <dir>', 'exec <command>', 'generate_code "<prompt>" "<output_file>"', 'ask_question: <question>').

            Consider the following user preferences and context when generating the subtasks:
            - User Persona/Tone Preference: {persona} (e.g., concise, detailed, humorous, formal)
            - Creativity Level: {creativity} (higher values mean more creative, less predictable suggestions for decomposition)
            {style_hint_str}

            The goal to decompose is: "{goal}"

            Please return the subtasks as a JSON list of strings. Each string must be a valid Coddy command.
            Example format:
            ["read main.py", "generate_code \"create a function to calculate factorial\" \"math_utils.py\"", "exec python math_utils.py"]
            """

            try:
                # Make the asynchronous call to the LLM for decomposition
                response = await self.llm.ainvoke(prompt_template)
                
                # Extract the content from the LLM response object
                response_content = response.content if hasattr(response, 'content') else str(response)
                
                # Attempt to parse the LLM's response as a JSON list of strings
                tasks = json.loads(response_content)
                if isinstance(tasks, list) and all(isinstance(task, str) for task in tasks):
                    return tasks
                else:
                    # Log a warning if the LLM returns an invalid format but attempt to return it as a single string
                    print(f"Warning: LLM returned invalid task list format. Raw response: {response_content}")
                    return [f"Error: LLM returned invalid task list format. Raw: {response_content}"]
            except json.JSONDecodeError as e:
                # Handle JSON decoding errors from the LLM response
                print(f"Error decoding JSON from LLM response: {e}. Raw response: {response_content}")
                return [f"Error: LLM did not return valid JSON. {e}"]
            except Exception as e:
                # Catch any other exceptions during the LLM call
                print(f"Error during LLM call for decomposition: {e}")
                return [f"Error during LLM call: {e}"]
        
        # Fallback to existing placeholder decomposition logic if no user_profile is provided
        # or if the LLM-based decomposition fails.
        goal_lower = goal.lower().strip()

        # Hardcoded decomposition logic for specific keywords (can be replaced by LLM over time)
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
                # If all questions are answered, proceed to generate code for funny clock
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
            # Generic fallback if no specific hardcoded logic matches and no user profile for LLM
            return [
                f"LLM-based decomposition for: {goal} (Placeholder)",
                "Consider breaking down complex tasks further",
                "This is a simulated decomposition."
            ]
