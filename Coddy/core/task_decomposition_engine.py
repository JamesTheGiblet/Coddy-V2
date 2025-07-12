# c:\Users\gilbe\Documents\GitHub\Coddy V2\Coddy/core/task_decomposition_engine.py

import json
import asyncio # Import asyncio for async operations
import re # Import regex for robust JSON parsing
from dotenv import load_dotenv
import os
from typing import List, Dict, Any, Optional # Added for type hints

# NEW: Import LLMProvider for type hinting
from core.llm_provider import LLMProvider

# Load environment variables from .env file
load_dotenv() 

class TaskDecompositionEngine:
    """
    Decomposes high-level goals into smaller, executable subtasks,
    with the ability to tailor the decomposition based on a user's profile.
    """
    # MODIFIED: Accept llm_provider instance directly
    def __init__(self, llm_provider: LLMProvider):
        """
        Initializes the TaskDecompositionEngine with an LLM provider.
        The LLM configuration can be dynamically influenced by user profile settings.
        """
        self.llm_provider = llm_provider # Store the LLMProvider instance
        # Removed internal ChatGoogleGenerativeAI instantiation

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
            Each subtask should be a command that Coddy can execute (e.g., 'read <file>', 'write <file> <content>', 'list <dir>', 'exec <command>', 'generate_code "<prompt>" "<output_file>"').

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
                # MODIFIED: Use the injected llm_provider to generate text, explicitly requesting gemini-2.0-flash
                response_content = await self.llm_provider.generate_text(
                    prompt=prompt_template,
                    temperature=float(creativity), # Pass creativity as temperature
                    model_name="gemini-2.0-flash" # Explicitly request gemini-2.0-flash for higher limits
                )

                # The LLM might return the JSON list wrapped in markdown or with extra text.
                # We need to robustly extract the JSON part before parsing.
                json_str = response_content

                # First, try to find a JSON code block
                json_match = re.search(r"```json\s*([\s\S]*?)\s*```", response_content, re.IGNORECASE)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    # If no code block, find the content between the first '[' and last ']'
                    start_index = response_content.find('[')
                    end_index = response_content.rfind(']')
                    if start_index != -1 and end_index != -1 and end_index > start_index:
                        json_str = response_content[start_index : end_index + 1]

                tasks = json.loads(json_str)
                if isinstance(tasks, list) and all(isinstance(task, str) for task in tasks):
                    return tasks
                else:
                    print(f"Warning: LLM returned a valid JSON object, but it was not a list of strings. Raw response: {response_content}")
                    return [f"Error: LLM returned invalid task list format. Raw: {response_content}"]
            except json.JSONDecodeError as e:
                # Handle JSON decoding errors from the LLM response
                print(f"Error decoding JSON from LLM response: {e}. Raw response was: {response_content}")
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
            tasks = []
            
            # Always include README.md, roadmap.md, and requirements.txt
            tasks.append(f'generate_code "Generate a basic README.md file for a new software project based on the goal: \'{goal}\'. Include sections for project title, description, installation, usage, and contribution." "README.md"')
            tasks.append(f'generate_code "Generate a basic requirements.txt file for a Python project based on the goal: \'{goal}\'. Include common dependencies like \'requests\', \'asyncio\', \'json\', \'tkinter\' (if GUI), etc., if applicable." "requirements.txt"')
            tasks.append(f'generate_code "Generate a high-level roadmap.md for a new software project based on the goal: \'{goal}\'. Include phases like \'Phase 1: Core Functionality\', \'Phase 2: Enhancements\', \'Phase 3: Deployment\'." "roadmap.md"')


            # Determine language and display based on goal, otherwise default
            if "web" in goal_lower or "browser" in goal_lower:
                html_prompt = "HTML structure for a web page with a div to display a funny clock. Include a title and link to style.css and script_time.js, script_jokes.js, and script_animations.js."
                css_prompt = "CSS for a web-based funny clock. Style the clock div with a large, centered font (e.g., Comic Sans), rounded corners, and a playful background. Make it responsive."
                js_time_prompt = "JavaScript to get the current time and display it in a humorous format (e.g., using silly units like 'dog years' or 'banana minutes') in the clock div. Update every second."
                js_jokes_prompt = "JavaScript to add a random joke or funny message that updates periodically on the webpage, separate from the clock display."
                js_animations_prompt = "JavaScript to add simple emoji animations or visual effects to the clock display, updating every second."
                
                print(f"DEBUG: Generating HTML with prompt: '{html_prompt}'")
                tasks.append(f'generate_code "{html_prompt}" "index.html"')
                print(f"DEBUG: Generating CSS with prompt: '{css_prompt}'")
                tasks.append(f'generate_code "{css_prompt}" "style.css"')
                print(f"DEBUG: Generating JavaScript (Time) with prompt: '{js_time_prompt}'")
                tasks.append(f'generate_code "{js_time_prompt}" "script_time.js"')
                print(f"DEBUG: Generating JavaScript (Jokes) with prompt: '{js_jokes_prompt}'")
                tasks.append(f'generate_code "{js_jokes_prompt}" "script_jokes.js"')
                print(f"DEBUG: Generating JavaScript (Animations) with prompt: '{js_animations_prompt}'")
                tasks.append(f'generate_code "{js_animations_prompt}" "script_animations.js"')
                
                tasks.extend([
                    # Removed 'write index.html' as it's now handled by generate_code with output_file
                    # Removed 'read' commands for newly generated files
                    'exec "start index.html" # Command to open the HTML file in a browser (Windows specific, may need adjustment for Linux/macOS)'
                ])
            else: # Default to Python console application
                time_formatter_prompt = "Python function to get the current time and format it humorously (e.g., using silly units or phrases like 'o'clock-o-rama')."
                message_generator_prompt = "Python function named 'get_funny_message' that returns a random, silly message from a predefined list of at least 5 messages."
                sound_effects_prompt = "Python function named 'play_silly_sound' that prints a message indicating a sound would play, as a placeholder for a very short, random sound effect (e.g., a 'boing' or 'ding-dong')."
                
                # Simplified console visual effects: focus on basic text styling and colon animation
                console_effects_prompt = "Python functions for console text styling. Include a function to apply a simple, noticeable text effect (e.g., bold, different color using ANSI escape codes, or a simple ASCII art border) to a given string, suitable for a digital display. Also, include a function to return a simple animated colon character (e.g., alternating between ':' and ' '). Do not use external libraries for complex font rendering or advanced GUI elements."
                
                # Main funny clock application, integrating all components
                funny_clock_app_prompt = "Python console application that continuously displays the current funny time, a humorous message, and applies simple console text styling. It should update every second. Integrate the 'time_formatter' function from time_formatter.py, the 'get_funny_message' function from message_generator.py, and the console text styling functions from console_effects.py. Also, call 'play_silly_sound' from sound_effects.py at the start of each minute. Ensure a clear console output with a refresh mechanism."

                print(f"DEBUG: Generating Python (Time Formatter) with prompt: '{time_formatter_prompt}'")
                tasks.append(f'generate_code "{time_formatter_prompt}" "time_formatter.py"')
                print(f"DEBUG: Generating Python (Message Generator) with prompt: '{message_generator_prompt}'")
                tasks.append(f'generate_code "{message_generator_prompt}" "message_generator.py"')
                print(f"DEBUG: Generating Python (Sound Effects) with prompt: '{sound_effects_prompt}'")
                tasks.append(f'generate_code "{sound_effects_prompt}" "sound_effects.py"')
                print(f"DEBUG: Generating Python (Console Effects) with prompt: '{console_effects_prompt}'")
                tasks.append(f'generate_code "{console_effects_prompt}" "console_effects.py"')
                print(f"DEBUG: Generating Python (Funny Clock Application) with prompt: '{funny_clock_app_prompt}'")
                tasks.append(f'generate_code "{funny_clock_app_prompt}" "funny_clock.py"')
                
                tasks.extend([
                    'exec "python funny_clock.py"',
                    # Removed 'read' commands for newly generated files
                ])
            return tasks

        elif "calculator" in goal_lower and "code" in goal_lower:
            # Always include README.md, roadmap.md, and requirements.txt for new code generation
            tasks = []
            tasks.append(f'generate_code "Generate a basic README.md file for a new Python calculator project." "README.md"')
            tasks.append(f'generate_code "Generate a basic requirements.txt file for a Python calculator project. Include common dependencies if applicable." "requirements.txt"')
            tasks.append(f'generate_code "Generate a high-level roadmap.md for a Python calculator project." "roadmap.md"')
            
            # Decompose into generate_code and then read
            tasks.extend([
                'generate_code "Python calculator with add, subtract, multiply, divide functions" "calculator.py"',
                "read calculator.py"
            ])
            return tasks

        elif "read" in goal_lower and "create" in goal_lower:
            # For this specific "read and create" scenario, we might not need all boilerplate files,
            # but if it implies a new mini-project, we can add them.
            # For now, keeping it focused on the original intent.
            return [
                "write test_script.py print(\"Hello, Coddy AI!\")", # Changed to 'write' command
                "read test_script.py"
            ]
        elif "flesh out the plan" in goal_lower or goal_lower == "hello" or goal_lower == "plan":
            # For plan requests, we can also suggest generating these files
            return [
                "ask_question: To help me flesh out the plan, could you please provide more details? What specific task or project are you thinking about, or what kind of code do you need?",
                f'generate_code "Generate a basic README.md for a project based on the current discussion." "README.md"',
                f'generate_code "Generate a basic requirements.txt for a project based on the current discussion." "requirements.txt"',
                f'generate_code "Generate a high-level roadmap.md for a project based on the current discussion." "roadmap.md"'
            ]
        else:
            # Generic fallback if no specific hardcoded logic matches and no user profile for LLM
            # Always include README.md, roadmap.md, and requirements.txt
            tasks = []
            tasks.append(f'generate_code "Generate a basic README.md file for a new software project based on the goal: \'{goal}\'. Include sections for project title, description, installation, usage, and contribution." "README.md"')
            tasks.append(f'generate_code "Generate a basic requirements.txt file for a Python project based on the goal: \'{goal}\'. Include common dependencies if applicable." "requirements.txt"')
            tasks.append(f'generate_code "Generate a high-level roadmap.md for a new software project based on the goal: \'{goal}\'. Include phases like \'Phase 1: Core Functionality\', \'Phase 2: Enhancements\', \'Phase 3: Deployment\'." "roadmap.md"')
            
            tasks.extend([
                f"LLM-based decomposition for: {goal} (Placeholder)",
                "Consider breaking down complex tasks further",
                "This is a simulated decomposition."
            ])
            return tasks
