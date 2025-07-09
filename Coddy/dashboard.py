# C:\Users\gilbe\Documents\GitHub\Coddy V2\Coddy\dashboard.py

import streamlit as st
import asyncio
import shlex
import httpx # Import httpx to catch specific exceptions
import dashboard_api # Import the API client we just created
import nest_asyncio # Import nest_asyncio
import os # Import the os module for path operations
import json # Added for handling JSON input/output for profile settings

# Apply nest_asyncio to allow nested event loops, which is common in environments
# like Streamlit where an event loop might already be running.
nest_asyncio.apply()

# --- Helper Function for Async Calls in Streamlit ---
def run_async_in_streamlit(coro_factory):
    """
    Runs an asynchronous coroutine within the synchronous Streamlit environment.
    Takes a callable (coro_factory) that returns the coroutine to be run.
    This ensures the coroutine is created within the correct event loop context.
    """
    try:
        # Get the current event loop (patched by nest_asyncio)
        loop = asyncio.get_event_loop()
    except RuntimeError:
        # If no loop is running, create a new one. This is a fallback.
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    # If the loop.is_closed() is True, it means the event loop was closed
    # and we need to create a new one for subsequent async operations.
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # Create the coroutine within the current active loop context
    coro = coro_factory()
    
    # Run the coroutine until complete
    return loop.run_until_complete(coro)


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
            st.stop() # Stop execution of further subtasks for this turn

        else:
            st.warning(f"Command `{command}` is not supported for automatic execution in the dashboard yet.")
    except Exception as e:
        st.error(f"Failed to execute subtask `{subtask}`: {e}")

# --- Custom CSS for Coddy Portal Styling ---
# This CSS aims to give the Streamlit app a sleek, dark, and modern "portal" feel
# Inspired by the Coddy Portal with neon lines, wobbly blobs (simulated with shadows/borders),
# and a strong "Async to the Bone" vibe.
custom_css = """
<style>
    /* Import Google Font - Inter for a modern look */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

    /* Overall Page Styling */
    html, body {
        font-family: 'Inter', sans-serif;
        background-color: #0d1117; /* Even darker, GitHub-like background */
        color: #e0e0e0; /* Light text for dark background */
    }

    /* Streamlit Main Container */
    .main .block-container {
        padding-top: 2rem;
        padding-right: 2rem;
        padding-left: 2rem;
        padding-bottom: 2rem;
        background-color: #161b22; /* Slightly lighter dark background for content area */
        border-radius: 15px; /* Rounded corners for the main content block */
        box-shadow: 0 0 15px rgba(0, 255, 255, 0.2), /* Subtle neon blue glow */
                    0 0 30px rgba(0, 255, 255, 0.1);
        border: 1px solid #00bcd4; /* Thin neon blue border */
    }

    /* Sidebar Styling */
    .st-emotion-cache-1ldf05w { /* Target sidebar container */
        background-color: #010409; /* Even darker for sidebar */
        border-radius: 15px;
        padding: 1.5rem 1rem; /* More padding */
        margin-right: 1.5rem;
        box-shadow: 0 0 10px rgba(233, 69, 96, 0.2), /* Neon pink glow */
                    0 0 20px rgba(233, 69, 96, 0.1);
        border: 1px solid #e94560; /* Thin neon pink border */
    }
    .st-emotion-cache-1ldf05w .st-emotion-cache-1wivc8w { /* Target sidebar radio buttons */
        background-color: #161b22; /* Match main content background */
        border-radius: 10px; /* More rounded */
        padding: 0.75rem 1rem; /* More padding */
        margin-bottom: 0.75rem;
        border: 1px solid transparent; /* Default transparent border */
        transition: background-color 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease;
    }
    .st-emotion-cache-1ldf05w .st-emotion-cache-1wivc8w:hover {
        background-color: #2e4a86; /* Darker blue on hover */
        border-color: #00e5ff; /* Neon blue border on hover */
        box-shadow: 0 0 8px rgba(0, 255, 255, 0.4);
    }
    /* Selected radio button style */
    .st-emotion-cache-1ldf05w .st-emotion-cache-1wivc8w[data-testid="stSidebarNavLink"] {
        background-color: #0f3460; /* Darker blue for selected */
        border-color: #e94560; /* Neon pink border for selected */
        box-shadow: 0 0 10px rgba(233, 69, 96, 0.4);
    }


    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: #00e5ff; /* Vibrant neon blue for primary headers */
        font-weight: 700; /* Bolder */
        text-shadow: 0 0 5px rgba(0, 255, 255, 0.6); /* Subtle neon glow for headers */
        margin-bottom: 1.2rem;
    }
    h1 { font-size: 2.5rem; }
    h2 { color: #e94560; text-shadow: 0 0 3px rgba(233, 69, 96, 0.5); } /* Accent for subheaders */
    h3 { color: #00bcd4; } /* Another accent for sub-subheaders */


    /* Buttons */
    .stButton > button {
        background-color: #e94560; /* Neon pink accent for buttons */
        color: white;
        border-radius: 10px; /* More rounded corners for buttons */
        border: 2px solid #e94560; /* Matching border */
        padding: 0.8rem 1.8rem; /* Larger padding */
        font-weight: 600; /* Semibold */
        transition: background-color 0.3s ease, transform 0.2s ease, box-shadow 0.3s ease, border-color 0.3s ease;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.4); /* Deeper shadow */
    }
    .stButton > button:hover {
        background-color: #ba374e; /* Darker accent on hover */
        transform: translateY(-3px); /* More pronounced lift effect */
        border-color: #00e5ff; /* Border changes to neon blue on hover */
        box-shadow: 0 6px 15px rgba(0, 0, 0, 0.5), 0 0 15px rgba(0, 255, 255, 0.6); /* Stronger glow on hover */
    }
    .stButton > button:active {
        transform: translateY(0);
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3);
    }

    /* Text Inputs and Text Areas */
    .stTextInput > div > div > input,
    .stTextArea > div > textarea {
        background-color: #0d1117; /* Match body background for inputs */
        color: #e0e0e0;
        border-radius: 10px; /* More rounded corners for inputs */
        border: 1px solid #0f3460; /* Subtle border */
        padding: 0.8rem;
        transition: border-color 0.3s ease, box-shadow 0.3s ease;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > textarea:focus {
        border-color: #00e5ff; /* Neon blue accent on focus */
        box-shadow: 0 0 0 0.1rem #00e5ff, 0 0 10px rgba(0, 255, 255, 0.6); /* Stronger glow effect on focus */
        outline: none;
    }

    /* Code Blocks */
    .stCodeBlock {
        background-color: #282c34; /* Editor-like dark background for code */
        border-radius: 10px;
        padding: 1.2rem;
        border: 1px solid #0f3460;
        box-shadow: 0 0 8px rgba(0, 255, 255, 0.1);
    }

    /* Info/Success/Error Messages */
    .stAlert {
        border-radius: 10px;
        border: 1px solid; /* Add border for alerts */
    }
    .stAlert.info {
        background-color: #0f3460;
        color: #e0e0e0;
        border-color: #00bcd4;
    }
    .stAlert.success {
        background-color: #1e6e44;
        color: white;
        border-color: #388e3c;
    }
    .stAlert.error {
        background-color: #8c2f39;
        color: white;
        border-color: #d32f2f;
    }

    /* Spinner */
    .stSpinner > div > div {
        border-top-color: #00e5ff !important; /* Neon blue spinner */
    }

    /* Checkbox */
    .stCheckbox > label {
        color: #e0e0e0;
    }

    /* Markdown elements for better readability */
    p {
        line_height: 1.6;
        margin_bottom: 1rem;
    }
    a {
        color: #00e5ff; /* Neon blue links */
        text_decoration: none;
        transition: color 0.3s ease;
    }
    a:hover {
        color: #e94560; /* Pink on hover */
        text_decoration: underline;
    }
</style>
"""

# --- Streamlit App Configuration ---
st.set_page_config(
    page_title="Coddy Dashboard",
    layout="wide", # Use wide layout for more screen real estate
    initial_sidebar_state="expanded", # Keep sidebar expanded by default
)

# Inject custom CSS
st.markdown(custom_css, unsafe_allow_html=True)

st.title("🚀 Coddy: The Sentient Loop Dashboard")
st.markdown("Your AI Dev Companion, Reimagined. (API-First Client)")

# --- Sidebar Navigation ---
st.sidebar.title("Navigation")
# Added "Automation" to the navigation
page = st.sidebar.radio("Go to", ["Roadmap", "File Explorer", "Workspace", "Refactor", "Automation", "Personalization", "Coming Soon..."])

# --- Main Content Area ---
if page == "Roadmap":
    st.header("🗺️ Project Roadmap")
    st.write("View the current development roadmap fetched from the Coddy API.")

    # Button to trigger fetching the roadmap
    if st.button("Load Roadmap from API"):
        with st.spinner("Fetching roadmap..."):
            try:
                # Pass a lambda that returns the coroutine
                roadmap_content = run_async_in_streamlit(lambda: dashboard_api.get_roadmap())
                st.markdown(roadmap_content) # Render Markdown content
            except httpx.RequestError:
                st.error("🚨 Connection Error: Could not connect to Coddy API. Please ensure the backend server is running at `http://127.0.0.1:8000`.")
            except httpx.HTTPStatusError as e:
                st.error(f"⚠️ API Error ({e.response.status_code}): {e.response.json().get('detail', 'An API error occurred.')}")
            except Exception as e:
                st.error(f"🔥 An unexpected error occurred: {e}")

elif page == "File Explorer":
    st.header("📂 File Explorer")
    st.write("Browse and view contents of files in your project via the Coddy API.")

    col1, col2 = st.columns([0.7, 0.3])
    with col1:
        # Provide clearer instruction for relative paths
        current_path = st.text_input(
            "Enter directory path to list (relative to the 'Coddy' project directory, e.g., '.', 'core', 'backend'):",
            value="."
        )
    with col2:
        if st.button("List Contents"):
            # Client-side validation for path
            if os.path.isabs(current_path):
                st.error("Please enter a relative path. Absolute paths are not supported from the dashboard.")
                st.stop() # Stop execution to prevent API call
            if current_path.startswith(".."):
                st.error("Accessing directories above the project root (e.g., '..') is not allowed.")
                st.stop() # Stop execution to prevent API call

            with st.spinner(f"Listing contents of '{current_path}'..."):
                try:
                    # Pass a lambda that returns the coroutine
                    files_and_dirs = run_async_in_streamlit(lambda: dashboard_api.list_files(current_path))
                    if files_and_dirs:
                        st.subheader(f"Contents of `{current_path}`:")
                        for item in files_and_dirs:
                            st.write(f"- {item}")
                    else:
                        st.info(f"No items found in '{current_path}' or directory is empty.")
                except httpx.RequestError:
                    st.error("🚨 Connection Error: Could not connect to Coddy API. Is the backend running?")
                except httpx.HTTPStatusError as e:
                    st.error(f"⚠️ API Error ({e.response.status_code}): {e.response.json().get('detail', 'An API error occurred.')}")
                except Exception as e:
                    st.error(f"🔥 An unexpected error occurred: {e}")

    st.markdown("---")
    st.subheader("Read File Content")
    file_to_read = st.text_input("Enter file path to read:", value="dashboard_api.py")
    if st.button("Read File Content"):
        with st.spinner(f"Reading '{file_to_read}'..."):
            try:
                # Pass a lambda that returns the coroutine
                content = run_async_in_streamlit(lambda: dashboard_api.read_file(file_to_read))
                st.success(f"Content of `{file_to_read}`:")
                st.code(content, language="python") # Assuming Python code for now
            except httpx.RequestError:
                st.error("🚨 Connection Error: Could not connect to Coddy API. Is the backend running?")
            except httpx.HTTPStatusError as e:
                st.error(f"⚠️ API Error ({e.response.status_code}): {e.response.json().get('detail', 'An API error occurred.')}")
            except Exception as e:
                st.error(f"🔥 An unexpected error occurred: {e}")

elif page == "Workspace":
    st.header("🧠 Coddy AI Assistant")
    st.write("Enter high-level instructions or complex tasks for Coddy to decompose and execute.")
    
    # Initialize session state for subtasks and user profile
    if 'subtasks' not in st.session_state:
        st.session_state.subtasks = []
    if 'user_profile' not in st.session_state:
        st.session_state.user_profile = {} # Initialize empty profile

    # Load user profile if not already loaded (e.g., if user navigates directly to Workspace)
    if not st.session_state.user_profile:
        with st.spinner("Loading user profile for personalization..."):
            try:
                st.session_state.user_profile = run_async_in_streamlit(lambda: dashboard_api.get_user_profile())
            except httpx.RequestError:
                st.warning("Could not connect to Coddy API to load user profile. Personalization may be limited.")
            except httpx.HTTPStatusError as e:
                st.warning(f"API Error loading user profile ({e.response.status_code}): {e.response.json().get('detail', 'An API error occurred.')}. Personalization may be limited.")
            except Exception as e:
                st.warning(f"An unexpected error occurred loading user profile: {e}. Personalization may be limited.")

    tab_assistant, tab_writer = st.tabs(["🧠 AI Assistant", "📝 File Writer"])

    with tab_assistant:
        user_instruction = st.text_area("What do you want Coddy to do?", height=150, key="ai_instruction_input")

        if st.button("Decompose Task", key="decompose_button"):
            if not user_instruction.strip():
                st.warning("Please enter an instruction for Coddy to decompose.")
                st.session_state.subtasks = [] # Clear previous subtasks
            else:
                with st.spinner("Decomposing your instruction via API..."):
                    try:
                        # Pass the user profile to the decompose_task API call
                        subtasks = run_async_in_streamlit(lambda: dashboard_api.decompose_task(
                            user_instruction, 
                            user_profile=st.session_state.user_profile
                        ))
                        st.session_state.subtasks = subtasks
                    except httpx.RequestError:
                        st.session_state.subtasks = []
                        st.error("🚨 Connection Error: Could not connect to Coddy API. Is the backend running?")
                    except httpx.HTTPStatusError as e:
                        st.session_state.subtasks = []
                        detail = e.response.json().get('detail', 'An API error occurred.')
                        st.error(f"⚠️ API Error ({e.response.status_code}): {detail}")
                        st.info("Please try a more detailed instruction, or break it down yourself for now.")
                    except Exception as e:
                        st.session_state.subtasks = []
                        st.error(f"🔥 An unexpected error occurred during decomposition: {e}")

        # Display the plan and the execution button if there are subtasks
        if st.session_state.subtasks:
            st.subheader("Execution Plan")
            for i, subtask in enumerate(st.session_state.subtasks):
                st.markdown(f"**{i+1}.** `{subtask}`")
            
            if st.button("🚀 Execute Plan", key="execute_plan_button"):
                with st.expander("Execution Log", expanded=True):
                    # Pass a lambda that returns asyncio.gather
                    run_async_in_streamlit(lambda: asyncio.gather(*(execute_subtask(subtask) for subtask in st.session_state.subtasks)))
                    st.balloons()
                    st.success("Plan execution finished!")

    with tab_writer:
        st.header("📝 File Writer")
        st.write("Write new files or update existing ones via the Coddy API.")

        write_path = st.text_input("Enter file path to write (e.g., new_file.txt):", value="new_file_from_dashboard.txt", key="file_writer_path")
        write_content = st.text_area("Enter content to write:", value="Hello from Coddy Dashboard!", height=200, key="file_writer_content")

        if st.button("Write File", key="file_writer_button"):
            with st.spinner(f"Writing to '{write_path}'..."):
                try:
                    # Pass a lambda that returns the coroutine
                    message = run_async_in_streamlit(lambda: dashboard_api.write_file(write_path, write_content))
                    st.success(message)
                    # Optionally, show the content after writing
                    if st.checkbox("Show content after writing?", key="show_content_checkbox"):
                        # Pass a lambda that returns the coroutine
                        read_back_content = run_async_in_streamlit(lambda: dashboard_api.read_file(write_path))
                        st.code(read_back_content)
                except httpx.RequestError:
                    st.error("🚨 Connection Error: Could not connect to Coddy API. Is the backend running?")
                except httpx.HTTPStatusError as e:
                    st.error(f"⚠️ API Error ({e.response.status_code}): {e.response.json().get('detail', 'An API error occurred.')}")
                except Exception as e:
                    st.error(f"🔥 An unexpected error occurred: {e}")

elif page == "Refactor": # NEW: Refactor Page
    st.header("♻️ Code Refactoring")
    st.write("Provide instructions to refactor existing code files.")

    # Initialize user_profile if not already loaded (important for personalization)
    if 'user_profile' not in st.session_state:
        st.session_state.user_profile = {} # Initialize empty profile
        with st.spinner("Loading user profile for personalization..."):
            try:
                st.session_state.user_profile = run_async_in_streamlit(lambda: dashboard_api.get_user_profile())
            except httpx.RequestError:
                st.warning("Could not connect to Coddy API to load user profile. Personalization may be limited.")
            except httpx.HTTPStatusError as e:
                st.warning(f"API Error loading user profile ({e.response.status_code}): {e.response.json().get('detail', 'An API error occurred.')}. Personalization may be limited.")
            except Exception as e:
                st.warning(f"An unexpected error occurred loading user profile: {e}. Personalization may be limited.")

    refactor_file_path = st.text_input("Enter the path to the file you want to refactor:", key="refactor_file_path")
    refactor_instructions = st.text_area("Describe how you want to refactor the code (e.g., 'extract method for X', 'rename variable Y to Z', 'improve readability'):", height=150, key="refactor_instructions")

    if st.button("Refactor Code", key="refactor_button"):
        if not refactor_file_path.strip():
            st.error("Please provide a file path to refactor.")
        elif not refactor_instructions.strip():
            st.error("Please provide refactoring instructions.")
        else:
            with st.spinner(f"Refactoring '{refactor_file_path}'..."):
                try:
                    # First, read the original content of the file
                    original_content = run_async_in_streamlit(lambda: dashboard_api.read_file(refactor_file_path))
                    if not original_content:
                        st.error(f"Could not read content from '{refactor_file_path}'. Please ensure the file exists and is readable.")
                        st.stop()

                    # Call the refactor API
                    refactored_code_response = run_async_in_streamlit(lambda: dashboard_api.refactor_code(
                        file_path=refactor_file_path,
                        original_code=original_content,
                        instructions=refactor_instructions,
                        user_profile=st.session_state.user_profile
                    ))
                    
                    refactored_code = refactored_code_response.get("refactored_code", "")

                    if refactored_code:
                        st.subheader("Refactored Code Preview:")
                        st.code(refactored_code, language="python") # Assuming Python, can be dynamic later

                        # Option to write the refactored code back to the file
                        if st.checkbox(f"Apply refactored code to '{refactor_file_path}'?", key="apply_refactor_checkbox"):
                            if st.button("Confirm Apply Refactoring", key="confirm_apply_refactor_button"):
                                with st.spinner(f"Applying refactored code to '{refactor_file_path}'..."):
                                    write_message = run_async_in_streamlit(lambda: dashboard_api.write_file(refactor_file_path, refactored_code))
                                    st.success(write_message)
                                    st.success(f"Refactoring applied to '{refactor_file_path}' successfully!")
                    else:
                        st.warning("Refactoring operation returned no changes or an empty result.")

                except httpx.RequestError:
                    st.error("🚨 Connection Error: Could not connect to Coddy API. Is the backend running?")
                except httpx.HTTPStatusError as e:
                    detail = e.response.json().get('detail', 'An API error occurred.')
                    st.error(f"⚠️ API Error ({e.response.status_code}): {detail}")
                except Exception as e:
                    st.error(f"🔥 An unexpected error occurred during refactoring: {e}")

elif page == "Automation": # NEW: Automation Page
    st.header("⚙️ Automation Tools")
    st.write("Trigger automated tasks to streamline your development workflow.")

    # Initialize user_profile if not already loaded (important for personalization)
    if 'user_profile' not in st.session_state:
        st.session_state.user_profile = {} # Initialize empty profile
        with st.spinner("Loading user profile for personalization..."):
            try:
                st.session_state.user_profile = run_async_in_streamlit(lambda: dashboard_api.get_user_profile())
            except httpx.RequestError:
                st.warning("Could not connect to Coddy API to load user profile. Personalization may be limited.")
            except httpx.HTTPStatusError as e:
                st.warning(f"API Error loading user profile ({e.response.status_code}): {e.response.json().get('detail', 'An API error occurred.')}. Personalization may be limited.")
            except Exception as e:
                st.warning(f"An unexpected error occurred loading user profile: {e}. Personalization may be limited.")

    st.subheader("Generate Changelog")
    st.write("Automatically generate a changelog based on recent Git commits.")
    changelog_path = st.text_input("Enter output file path for changelog (e.g., CHANGELOG.md):", value="CHANGELOG.md", key="changelog_path")
    if st.button("Generate Changelog", key="generate_changelog_button"):
        if not changelog_path.strip():
            st.error("Please provide an output file path for the changelog.")
        else:
            with st.spinner("Generating changelog..."):
                try:
                    changelog_response = run_async_in_streamlit(lambda: dashboard_api.generate_changelog(
                        output_file=changelog_path,
                        user_profile=st.session_state.user_profile
                    ))
                    generated_changelog = changelog_response.get("changelog_content", "")
                    if generated_changelog:
                        st.success(f"Changelog generated and saved to '{changelog_path}'!")
                        st.subheader("Generated Changelog Preview:")
                        st.code(generated_changelog, language="markdown")
                    else:
                        st.warning("Changelog generation returned empty content.")
                except httpx.RequestError:
                    st.error("🚨 Connection Error: Could not connect to Coddy API. Is the backend running?")
                except httpx.HTTPStatusError as e:
                    detail = e.response.json().get('detail', 'An API error occurred.')
                    st.error(f"⚠️ API Error ({e.response.status_code}): {detail}")
                except Exception as e:
                    st.error(f"🔥 An unexpected error occurred during changelog generation: {e}")

    st.markdown("---")
    st.subheader("Generate TODO Stubs")
    st.write("Scan files for TODO comments and generate detailed stubs or issues.")
    todo_scan_path = st.text_input("Enter directory/file path to scan for TODOs (e.g., . or my_module.py):", value=".", key="todo_scan_path")
    todo_output_file = st.text_input("Enter output file path for TODO stubs (e.g., TODO_STUBS.md):", value="TODO_STUBS.md", key="todo_output_file")
    if st.button("Generate TODO Stubs", key="generate_todo_stubs_button"):
        if not todo_scan_path.strip() or not todo_output_file.strip():
            st.error("Please provide both a scan path and an output file path for TODO stubs.")
        else:
            with st.spinner("Generating TODO stubs..."):
                try:
                    todo_stubs_response = run_async_in_streamlit(lambda: dashboard_api.generate_todo_stubs(
                        scan_path=todo_scan_path,
                        output_file=todo_output_file,
                        user_profile=st.session_state.user_profile
                    ))
                    generated_stubs = todo_stubs_response.get("stubs_content", "")
                    if generated_stubs:
                        st.success(f"TODO stubs generated and saved to '{todo_output_file}'!")
                        st.subheader("Generated TODO Stubs Preview:")
                        st.code(generated_stubs, language="markdown")
                    else:
                        st.warning("TODO stub generation returned empty content.")
                except httpx.RequestError:
                    st.error("🚨 Connection Error: Could not connect to Coddy API. Is the backend running?")
                except httpx.HTTPStatusError as e:
                    detail = e.response.json().get('detail', 'An API error occurred.')
                    st.error(f"⚠️ API Error ({e.response.status_code}): {detail}")
                except Exception as e:
                    st.error(f"🔥 An unexpected error occurred during TODO stub generation: {e}")


elif page == "Personalization": # NEW: Personalization Page
    st.header("✨ Your Personalization Settings")
    st.write("Manage your Coddy profile to tailor its suggestions, prompts, and creative outputs.")

    if 'user_profile' not in st.session_state:
        st.session_state.user_profile = {} # Initialize empty profile

    # Fetch and display current profile
    if st.button("Load My Profile"):
        with st.spinner("Loading profile..."):
            try:
                profile_data = run_async_in_streamlit(lambda: dashboard_api.get_user_profile())
                st.session_state.user_profile = profile_data
                st.success("Profile loaded successfully!")
            except httpx.RequestError:
                st.error("🚨 Connection Error: Could not connect to Coddy API. Is the backend running?")
            except httpx.HTTPStatusError as e:
                st.error(f"⚠️ API Error ({e.response.status_code}): {e.response.json().get('detail', 'An API error occurred.')}")
            except Exception as e:
                st.error(f"🔥 An unexpected error occurred while loading profile: {e}")

    if st.session_state.user_profile:
        st.subheader("Current Profile Data:")
        st.json(st.session_state.user_profile)

        st.markdown("---")
        st.subheader("Update Preferences")

        # Input fields for various profile attributes
        st.markdown("#### LLM Provider Configuration (JSON)")
        llm_config_str = st.text_area(
            "Enter LLM Provider Config (JSON format):",
            value=json.dumps(st.session_state.user_profile.get('llm_provider_config', {}), indent=2),
            height=150,
            key="llm_config_input"
        )

        st.markdown("#### Idea Synthesizer Settings")
        idea_synth_persona = st.text_input(
            "Idea Synth Persona:",
            value=st.session_state.user_profile.get('idea_synth_persona', 'default'),
            key="idea_synth_persona_input"
        )
        idea_synth_creativity = st.slider(
            "Idea Synth Creativity (0.0 - 1.0):",
            min_value=0.0,
            max_value=1.0,
            value=float(st.session_state.user_profile.get('idea_synth_creativity', 0.7)),
            step=0.1,
            key="idea_synth_creativity_input"
        )

        st.markdown("#### Coding Style Preferences (JSON)")
        coding_style_str = st.text_area(
            "Enter Coding Style Preferences (JSON format):",
            value=json.dumps(st.session_state.user_profile.get('coding_style_preferences', {}), indent=2),
            height=150,
            key="coding_style_input"
        )

        st.markdown("#### Preferred Languages")
        preferred_languages_str = st.text_input(
            "Enter Preferred Languages (comma-separated, e.g., Python,JavaScript):",
            value=", ".join(st.session_state.user_profile.get('preferred_languages', [])),
            key="preferred_languages_input"
        )

        st.markdown("#### Common Patterns (JSON)")
        common_patterns_str = st.text_area(
            "Enter Common Patterns (JSON format):",
            value=json.dumps(st.session_state.user_profile.get('common_patterns', {}), indent=2),
            height=150,
            key="common_patterns_input"
        )

        if st.button("Save Profile Changes", key="save_profile_button"):
            try:
                # Parse JSON inputs
                parsed_llm_config = json.loads(llm_config_str)
                parsed_coding_style = json.loads(coding_style_str)
                parsed_common_patterns = json.loads(common_patterns_str)
                parsed_preferred_languages = [lang.strip() for lang in preferred_languages_str.split(',') if lang.strip()]

                updated_profile = {
                    "llm_provider_config": parsed_llm_config,
                    "idea_synth_persona": idea_synth_persona,
                    "idea_synth_creativity": idea_synth_creativity,
                    "coding_style_preferences": parsed_coding_style,
                    "preferred_languages": parsed_preferred_languages,
                    "common_patterns": parsed_common_patterns
                }

                with st.spinner("Saving profile changes..."):
                    # Call the API to update the profile
                    run_async_in_streamlit(lambda: dashboard_api.set_user_profile(updated_profile))
                    st.success("Profile updated successfully!")
                    # Reload profile to reflect changes
                    st.session_state.user_profile = run_async_in_streamlit(lambda: dashboard_api.get_user_profile())
            except json.JSONDecodeError as e:
                st.error(f"JSON parsing error: Please ensure your JSON inputs are valid. Error: {e}")
            except httpx.RequestError:
                st.error("🚨 Connection Error: Could not connect to Coddy API. Is the backend running?")
            except httpx.HTTPStatusError as e:
                st.error(f"⚠️ API Error ({e.response.status_code}): {e.response.json().get('detail', 'An API error occurred.')}")
            except Exception as e:
                st.error(f"🔥 An unexpected error occurred while saving profile: {e}")

        st.markdown("---")
        st.subheader("Reset Profile")
        if st.button("Clear My Profile (Reset to Default)", key="clear_profile_button"):
            # Streamlit's button logic can be tricky with confirmations.
            # A common pattern is to use st.session_state for confirmation states.
            if st.session_state.get('confirm_clear', False):
                if st.button("Confirm Clear Profile", key="confirm_clear_profile_button_actual"):
                    with st.spinner("Clearing profile..."):
                        try:
                            run_async_in_streamlit(lambda: dashboard_api.clear_user_profile())
                            st.session_state.user_profile = run_async_in_streamlit(lambda: dashboard_api.get_user_profile()) # Reload default
                            st.success("Profile reset to default!")
                            st.session_state.confirm_clear = False # Reset confirmation
                        except httpx.RequestError:
                            st.error("🚨 Connection Error: Could not connect to Coddy API. Is the backend running?")
                        except httpx.HTTPStatusError as e:
                            st.error(f"⚠️ API Error ({e.response.status_code}): {e.response.json().get('detail', 'An API error occurred.')}")
                        except Exception as e:
                            st.error(f"🔥 An unexpected error occurred while clearing profile: {e}")
            else:
                st.warning("Are you sure you want to clear your profile? This action cannot be undone.")
                st.session_state.confirm_clear = st.button("Yes, Clear Profile", key="confirm_clear_profile_button_prompt")
    else:
        st.info("Click 'Load My Profile' to view and manage your personalization settings.")

    st.markdown("---")
    st.subheader("Provide Feedback")
    st.write("Help Coddy learn by rating its performance on the last interaction.")
    
    feedback_rating = st.slider("Rating (1-5):", min_value=1, max_value=5, value=3, step=1, key="feedback_rating_input")
    feedback_comment = st.text_area("Optional Comment:", key="feedback_comment_input")

    if st.button("Submit Feedback", key="submit_feedback_button"):
        if not feedback_comment.strip():
            st.warning("Please provide a comment for your feedback.")
        else:
            with st.spinner("Submitting feedback..."):
                try:
                    run_async_in_streamlit(lambda: dashboard_api.add_feedback(
                        rating=feedback_rating,
                        comment=feedback_comment
                    ))
                    st.success("Thank you for your feedback! It helps Coddy improve.")
                    # Clear the comment box by updating its key or value
                    st.session_state.feedback_comment_input = "" 
                    # Optionally reload profile to show updated feedback log
                    if st.session_state.user_profile:
                        st.session_state.user_profile = run_async_in_streamlit(lambda: dashboard_api.get_user_profile())
                except httpx.RequestError:
                    st.error("🚨 Connection Error: Could not connect to Coddy API. Is the backend running?")
                except httpx.HTTPStatusError as e:
                    st.error(f"⚠️ API Error ({e.response.status_code}): {e.response.json().get('detail', 'An API error occurred.')}")
                except Exception as e:
                    st.error(f"🔥 An unexpected error occurred while submitting feedback: {e}")


elif page == "Coming Soon...":
    st.header("🚧 More Features on the Horizon!")
    st.info("Stay tuned for more exciting Coddy features, including Memory Logs, Git Insights, and the Idea Synthesizer Playground, all powered by the Coddy API!")

st.sidebar.markdown("---")
st.sidebar.info("Coddy: The Sentient Loop Dashboard")
st.sidebar.info("Async to the Bone. Terminal to UI.")
