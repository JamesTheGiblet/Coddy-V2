import json
import asyncio # Import asyncio for async operations
import re # Import regex for robust JSON parsing
from dotenv import load_dotenv
import os
from typing import List, Dict, Any, Optional # Added for type hints

# NEW: Import LLMProvider for type hinting
from core.llm_provider import LLMProvider
from core.logging_utility import get_logger # NEW: Import get_logger

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
        self.logger = get_logger(__name__) # NEW: Initialize logger
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
            self.logger.info(f"Decomposing goal '{goal}' using LLM with user profile.")
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
                self.logger.debug(f"LLM raw response for decomposition: {response_content[:500]}...")

                # The LLM might return the JSON list wrapped in markdown or with extra text.
                # We need to robustly extract the JSON part before parsing.
                json_str = response_content

                # First, try to find a JSON code block
                json_match = re.search(r"```json\s*([\s\S]*?)\s*```", response_content, re.IGNORECASE)
                if json_match:
                    json_str = json_match.group(1)
                    self.logger.debug("Extracted JSON from markdown block.")
                else:
                    # If no code block, find the content between the first '[' and last ']'
                    start_index = response_content.find('[')
                    end_index = response_content.rfind(']')
                    if start_index != -1 and end_index != -1 and end_index > start_index:
                        json_str = response_content[start_index : end_index + 1]
                        self.logger.debug("Extracted JSON by finding array delimiters.")
                    else:
                        self.logger.warning("Could not find JSON in markdown or by array delimiters. Attempting to parse raw response.")

                tasks = json.loads(json_str)
                if isinstance(tasks, list) and all(isinstance(task, str) for task in tasks):
                    self.logger.info("LLM successfully decomposed goal into a list of strings.")
                    return tasks
                else:
                    self.logger.warning(f"LLM returned a valid JSON object, but it was not a list of strings. Raw response: {response_content}")
                    return [f"Error: LLM returned invalid task list format. Raw: {response_content}"]
            except json.JSONDecodeError as e:
                # Handle JSON decoding errors from the LLM response
                self.logger.error(f"Error decoding JSON from LLM response: {e}. Raw response was: {response_content}", exc_info=True)
                return [f"Error: LLM did not return valid JSON. {e}"]
            except Exception as e:
                # Catch any other exceptions during the LLM call
                self.logger.error(f"Error during LLM call for decomposition: {e}", exc_info=True)
                return [f"Error during LLM call: {e}"]
        
        # Fallback to existing placeholder decomposition logic if no user_profile is provided
        # or if the LLM-based decomposition fails.
        self.logger.info(f"Falling back to hardcoded decomposition logic for goal: '{goal}'")
        goal_lower = goal.lower().strip()

        # NEW: Derive a project name from the goal
        # Sanitize the goal to create a valid directory name
        project_name_raw = re.sub(r'[^\w\s-]', '', goal_lower).strip() # Remove non-alphanumeric except space/hyphen
        project_name = project_name_raw.replace(' ', '_') # Replace spaces with underscores
        if not project_name: # Fallback if goal is empty or only special chars
            project_name = "generated_project"
            self.logger.debug("Project name derived as 'generated_project' due to empty/special character goal.")

        # Hardcoded decomposition logic for specific keywords (can be replaced by LLM over time)
        if "funny clock" in goal_lower:
            tasks = []
            self.logger.debug("Applying 'funny clock' decomposition logic.")
            
            # Always include README.md, roadmap.md, and requirements.txt
            # MODIFIED: Prepend project_name to output_file paths
            tasks.append(f'generate_code "Generate a basic README.md file for a new software project based on the goal: \'{goal}\'. Include sections for project title, description, installation, usage, and contribution." "{project_name}/README.md"')
            tasks.append(f'generate_code "Generate a basic requirements.txt file for a Python project based on the goal: \'{goal}\'. Include common dependencies like \'requests\', \'asyncio\', \'json\', \'tkinter\' (if GUI), etc., if applicable." "{project_name}/requirements.txt"')
            tasks.append(f'generate_code "Generate a high-level roadmap.md for a new software project based on the goal: \'{goal}\'. Include phases like \'Phase 1: Core Functionality\', \'Phase 2: Enhancements\', \'Phase 3: Deployment\'." "{project_name}/roadmap.md"')


            # Determine language and display based on goal, otherwise default
            if "web" in goal_lower or "browser" in goal_lower:
                html_prompt = "HTML structure for a web page with a div to display a funny clock. Include a title and link to style.css and script_time.js, script_jokes.js, and script_animations.js."
                css_prompt = "CSS for a web-based funny clock. Style the clock div with a large, centered font (e.g., Comic Sans), rounded corners, and a playful background. Make it responsive."
                js_time_prompt = "JavaScript to get the current time and display it in a humorous format (e.g., using silly units like 'dog years' or 'banana minutes') in the clock div. Update every second."
                js_jokes_prompt = "JavaScript to add a random joke or funny message that updates periodically on the webpage, separate from the clock display."
                js_animations_prompt = "JavaScript to add simple emoji animations or visual effects to the clock display, updating every second."
                
                self.logger.debug(f"Generating HTML with prompt: '{html_prompt}'")
                tasks.append(f'generate_code "{html_prompt}" "{project_name}/index.html"')
                self.logger.debug(f"Generating CSS with prompt: '{css_prompt}'")
                tasks.append(f'generate_code "{css_prompt}" "{project_name}/style.css"')
                self.logger.debug(f"Generating JavaScript (Time) with prompt: '{js_time_prompt}'")
                tasks.append(f'generate_code "{js_time_prompt}" "{project_name}/script_time.js"')
                self.logger.debug(f"Generating JavaScript (Jokes) with prompt: '{js_jokes_prompt}'")
                tasks.append(f'generate_code "{js_jokes_prompt}" "{project_name}/script_jokes.js"')
                self.logger.debug(f"Generating JavaScript (Animations) with prompt: '{js_animations_prompt}'")
                tasks.append(f'generate_code "{js_animations_prompt}" "{project_name}/script_animations.js"')
                
                tasks.extend([
                    # MODIFIED: Update write command path to include project_name
                    f'write {project_name}/index.html "<!DOCTYPE html>\\n<html lang=\\"en\\">\\n<head>\\n    <meta charset=\\"UTF-8\\">\\n    <meta name=\\"viewport\\" content=\\"width=device-width, initial-scale=1.0\\">\\n    <title>Funny Clock</title>\\n    <link rel=\\"stylesheet\\" href=\\"style.css\\">\\n</head>\\n<body>\\n    <div id=\\"clock-container\\">\\n        <div id=\\"clock\\"></div>\\n        <div id=\\"joke-display\\"></div>\\n    </div>\\n    <script src=\\"script_time.js\\"></script>\\n    <script src=\\"script_jokes.js\\"></script>\\n    <script src=\\"script_animations.js\\"></script>\\n</body>\\n</html>"',
                    # REMOVED: Redundant 'read' commands for newly generated web files
                    f'exec "start {project_name}/index.html" # Command to open the HTML file in a browser (Windows specific, may need adjustment for Linux/macOS)'
                ])
            else: # Default to Python console application
                self.logger.debug("Applying Python console application decomposition logic.")
                time_formatter_prompt = "Python function to get the current time and format it humorously (e.g., using silly units or phrases like 'o'clock-o-rama')."
                message_generator_prompt = "Python function named 'get_funny_message' that returns a random, silly message from a predefined list of at least 5 messages."
                sound_effects_prompt = "Python function named 'play_silly_sound' that prints a message indicating a sound would play, as a placeholder for a very short, random sound effect (e.g., a 'boing' or 'ding-dong')."
                
                # Simplified console visual effects: focus on basic text styling and colon animation
                console_effects_prompt = "Python functions for console text styling. Include a function to apply a simple, noticeable text effect (e.g., bold, different color using ANSI escape codes, or a simple ASCII art border) to a given string, suitable for a digital display. Also, include a function to return a simple animated colon character (e.g., alternating between ':' and ' '). Do not use external libraries for complex font rendering or advanced GUI elements."
                
                # Main funny clock application, integrating all components
                funny_clock_app_prompt = "Python console application that continuously displays the current funny time, a humorous message, and applies simple console text styling. It should update every second. Integrate the 'time_formatter' function from time_formatter.py, the 'get_funny_message' function from message_generator.py, and the console text styling functions from console_effects.py. Also, call 'play_silly_sound' from sound_effects.py at the start of each minute. Ensure a clear console output with a refresh mechanism."

                self.logger.debug(f"Generating Python (Time Formatter) with prompt: '{time_formatter_prompt}'")
                tasks.append(f'generate_code "{time_formatter_prompt}" "{project_name}/time_formatter.py"')
                self.logger.debug(f"Generating Python (Message Generator) with prompt: '{message_generator_prompt}'")
                tasks.append(f'generate_code "{message_generator_prompt}" "{project_name}/message_generator.py"')
                self.logger.debug(f"Generating Python (Sound Effects) with prompt: '{sound_effects_prompt}'")
                tasks.append(f'generate_code "{sound_effects_prompt}" "{project_name}/sound_effects.py"')
                self.logger.debug(f"Generating Python (Console Effects) with prompt: '{console_effects_prompt}'")
                tasks.append(f'generate_code "{console_effects_prompt}" "{project_name}/console_effects.py"')
                self.logger.debug(f"Generating Python (Funny Clock Application) with prompt: '{funny_clock_app_prompt}'")
                tasks.append(f'generate_code "{funny_clock_app_prompt}" "{project_name}/funny_clock.py"')
                
                tasks.extend([
                    f'exec "python {project_name}/funny_clock.py"',
                    # REMOVED: Redundant 'read' commands for newly generated console files
                ])
            return tasks

        elif "calculator" in goal_lower and "code" in goal_lower:
            self.logger.debug("Applying 'calculator' decomposition logic.")
            # Always include README.md, roadmap.md, and requirements.txt for new code generation
            tasks = []
            tasks.append(f'generate_code "Generate a basic README.md file for a new Python calculator project." "{project_name}/README.md"')
            tasks.append(f'generate_code "Generate a basic requirements.txt file for a Python calculator project. Include common dependencies if applicable." "{project_name}/requirements.txt"')
            tasks.append(f'generate_code "Generate a high-level roadmap.md for a Python calculator project." "{project_name}/roadmap.md"')
            
            # Decompose into generate_code and then read
            tasks.extend([
                f'generate_code "Python calculator with add, subtract, multiply, divide functions" "{project_name}/calculator.py"',
                # REMOVED: Redundant 'read' command for calculator.py
            ])
            return tasks

        elif "read" in goal_lower and "create" in goal_lower:
            self.logger.debug("Applying 'read and create' decomposition logic.")
            # For this specific "read and create" scenario, we might not need all boilerplate files,
            # but if it implies a new mini-project, we can add them.
            # For now, keeping it focused on the original intent.
            return [
                f"write {project_name}/test_script.py print(\"Hello, Coddy AI!\")", # Changed to 'write' command
                # REMOVED: Redundant 'read' command for test_script.py
            ]
        elif "flesh out the plan" in goal_lower or goal_lower == "hello" or goal_lower == "plan":
            self.logger.debug("Applying 'flesh out the plan' decomposition logic.")
            # For plan requests, we can also suggest generating these files
            return [
                "ask_question: To help me flesh out the plan, could you please provide more details? What specific task or project are you thinking about, or what kind of code do you need?",
                f'generate_code "Generate a basic README.md for a project based on the current discussion." "{project_name}/README.md"',
                f'generate_code "Generate a basic requirements.txt for a project based on the current discussion." "{project_name}/requirements.txt"',
                f'generate_code "Generate a high-level roadmap.md for a project based on the current discussion." "{project_name}/roadmap.md"'
            ]
        else:
            self.logger.debug("Applying generic fallback decomposition logic.")
            # Generic fallback if no specific hardcoded logic matches and no user profile for LLM
            # Always include README.md, roadmap.md, and requirements.txt
            tasks = []
            tasks.append(f'generate_code "Generate a basic README.md file for a new software project based on the goal: \'{goal}\'. Include sections for project title, description, installation, usage, and contribution." "{project_name}/README.md"')
            tasks.append(f'generate_code "Generate a basic requirements.txt file for a Python project based on the goal: \'{goal}\'. Include common dependencies if applicable." "{project_name}/requirements.txt"')
            tasks.append(f'generate_code "Generate a high-level roadmap.md for a new software project based on the goal: \'{goal}\'. Include phases like \'Phase 1: Core Functionality\', \'Phase 2: Enhancements\', \'Phase 3: Deployment\'." "{project_name}/roadmap.md"')
            
            tasks.extend([
                f"LLM-based decomposition for: {goal} (Placeholder)",
                "Consider breaking down complex tasks further",
                "This is a simulated decomposition."
            ])
            return tasks
