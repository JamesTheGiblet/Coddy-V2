# c:\Users\gilbe\Documents\GitHub\Coddy_V2\Coddy\dashboard_helpers.py

import streamlit as st
import shlex
import dashboard_api

async def execute_subtask(subtask: str):
    """Parses and executes a single subtask string via the dashboard_api."""
    st.markdown(f"▶️ **Executing:** `{subtask}`")
    try:
        parts = shlex.split(subtask)
        if not parts:
            st.warning("Skipping empty subtask.")
            return

        command = parts[0].lower()
        args = parts[1:]

        if command == "read":
            if not args:
                st.error("`read` command requires a file path.")
                return
            path = args[0]
            with st.spinner(f"Reading `{path}`..."):
                content = await dashboard_api.read_file(path)
                st.text_area(f"Content of `{path}`", value=content, height=150, disabled=True)
            st.success(f"Read `{path}` successfully.")
        
        elif command == "write":
            if len(args) < 2:
                st.error("`write` command requires a file path and content.")
                return
            path = args[0]
            content = " ".join(args[1:])
            with st.spinner(f"Writing to `{path}`..."):
                message = await dashboard_api.write_file(path, content)
            st.success(message)

        elif command == "list":
            path = args[0] if args else "."
            with st.spinner(f"Listing contents of `{path}`..."):
                items = await dashboard_api.list_files(path)
                st.json({"directory": path, "items": items})
            st.success(f"Listed contents of `{path}`.")
        
        elif command == "generate_code":
            if len(args) < 2:
                st.error("`generate_code` command requires a prompt and an output file path.")
                return
            
            prompt = args[0]
            output_file = args[1]
            
            st.info(f"Generating code with prompt: '{prompt}' and saving to '{output_file}'...")
            with st.spinner(f"Generating code for '{output_file}'..."):
                # Pass the user profile to the generate_code API call
                generated_code_response = await dashboard_api.generate_code(
                    prompt, 
                    user_profile=st.session_state.user_profile if 'user_profile' in st.session_state else {}
                )
                generated_code = generated_code_response.get("code", "")
                
                if generated_code:
                    st.success("Code generated successfully. Now writing to file...")
                    # Use the existing write_file API to save the generated code
                    write_message = await dashboard_api.write_file(output_file, generated_code)
                    st.success(write_message)
                    st.code(generated_code, language="python") # Display generated code
                else:
                    st.error("Code generation returned empty content.")

        elif command == "ask_question":
            if not args:
                st.error("`ask_question` command requires a question string.")
                return
            question = " ".join(args)
            st.info(f"🤔 Coddy asks: {question}")
            # Clear subtasks so "Execute Plan" button disappears and user can input new instruction
            st.session_state.subtasks = [] 
            st.stop()   # Stop execution of further subtasks for this turn

        elif command == "exec":
            if not args:
                st.error("`exec` command requires a command string.")
                return
            full_command = " ".join(args)
            with st.spinner(f"Executing shell command: `{full_command}`..."):
                result = await dashboard_api.execute_shell_command(full_command)
                st.info("Shell Command Output:")
                if result.get("stdout"):
                    st.code(result["stdout"], language="bash")
                if result.get("stderr"):
                    st.error(f"STDERR:\n{result['stderr']}")
                st.success(f"Command finished with exit code: {result['return_code']}")
        
        # NEW: Example of adding support for a 'refactor' command
        elif command == "refactor":
            if len(args) < 3:
                st.error("`refactor` command requires file_path, original_code (or fetch implicitly), and instructions.")
                st.info("Usage: `refactor <file_path> <original_code_string> \"<instructions>\"`")
                st.info("Alternatively, you can provide just file_path and instructions, and I'll try to read the file.")
                return
            
            file_path = args[0]
            # Try to infer if the second arg is original code or part of instructions
            # This is a simplification; a more robust parser would be needed.
            # For now, let's assume the user provides file path, then original code as a single string (potentially quoted), then instructions.
            # A better approach would be to prompt for original_code if not provided or read file automatically.
            
            original_code = ""
            instructions = ""

            if len(args) == 2: # Assuming file_path and instructions only
                file_path = args[0]
                instructions = args[1]
                st.info(f"Attempting to read original code from '{file_path}' for refactoring.")
                try:
                    original_code = await dashboard_api.read_file(file_path)
                    if not original_code.strip():
                        st.error(f"File '{file_path}' is empty or could not be read. Cannot refactor empty code.")
                        return
                except Exception as read_e:
                    st.error(f"Error reading file '{file_path}': {read_e}. Please provide original_code explicitly if unable to read.")
                    return
            elif len(args) >= 3: # Assuming file_path, original_code_string, instructions
                file_path = args[0]
                original_code = args[1]
                instructions = " ".join(args[2:]) # The rest are instructions

            if not original_code or not instructions:
                 st.error("Missing original code or refactoring instructions.")
                 return

            st.info(f"Refactoring '{file_path}' with instructions: '{instructions}'...")
            with st.spinner(f"Refactoring '{file_path}'..."):
                refactored_response = await dashboard_api.refactor_code(
                    file_path, 
                    original_code, 
                    instructions,
                    user_profile=st.session_state.user_profile if 'user_profile' in st.session_state else {}
                )
                refactored_code = refactored_response.get("refactored_code", "")

                if refactored_code:
                    st.success("Code refactored successfully.")
                    st.code(refactored_code, language="python")
                    if st.button(f"Write refactored code to {file_path}"):
                        write_message = await dashboard_api.write_file(file_path, refactored_code)
                        st.success(write_message)
                else:
                    st.error("Refactoring returned empty content.")

        else:
            st.warning(f"Command `{command}` is not supported for automatic execution in the dashboard yet.")
            st.info("To add support for new commands, modify the `execute_subtask` function in `dashboard_helpers.py`.")
            st.info("You can add new `elif command == \"your_command\":` blocks and call the appropriate `dashboard_api` functions.")
    except Exception as e:
        st.error(f"Failed to execute subtask `{subtask}`: {e}")