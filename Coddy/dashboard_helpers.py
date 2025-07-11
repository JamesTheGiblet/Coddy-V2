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
            st.stop()  # Stop execution of further subtasks for this turn

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
                
        else:
            st.warning(f"Command `{command}` is not supported for automatic execution in the dashboard yet.")
    except Exception as e:
        st.error(f"Failed to execute subtask `{subtask}`: {e}")