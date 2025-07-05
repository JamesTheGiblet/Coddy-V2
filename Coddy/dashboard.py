# C:\Users\gilbe\Documents\GitHub\Coddy V2\Coddy\dashboard.py

import streamlit as st
import asyncio
import shlex
import httpx # Import httpx to catch specific exceptions
import dashboard_api # Import the API client we just created

# Import the TaskDecompositionEngine for AI Assistant functionality
from core.task_decomposition_engine import TaskDecompositionEngine

# --- Helper Function for Async Calls in Streamlit ---
# Streamlit runs synchronously, so we need a way to execute async functions.
# This function wraps an async function call, allowing it to be awaited.
def run_async_in_streamlit(async_func):
    """
    Runs an asynchronous function within the synchronous Streamlit environment.
    """
    return asyncio.run(async_func)

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
        line-height: 1.6;
        margin-bottom: 1rem;
    }
    a {
        color: #00e5ff; /* Neon blue links */
        text-decoration: none;
        transition: color 0.3s ease;
    }
    a:hover {
        color: #e94560; /* Pink on hover */
        text-decoration: underline;
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
# Added "AI Assistant" to the navigation
page = st.sidebar.radio("Go to", ["Roadmap", "File Explorer", "Workspace", "Coming Soon..."])

# --- Main Content Area ---
if page == "Roadmap":
    st.header("🗺️ Project Roadmap")
    st.write("View the current development roadmap fetched from the Coddy API.")

    # Button to trigger fetching the roadmap
    if st.button("Load Roadmap from API"):
        with st.spinner("Fetching roadmap..."):
            try:
                # Call the async function from dashboard_api.py
                roadmap_content = run_async_in_streamlit(dashboard_api.get_roadmap())
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
        current_path = st.text_input("Enter directory path to list:", value=".")
    with col2:
        if st.button("List Contents"):
            with st.spinner(f"Listing contents of '{current_path}'..."):
                try:
                    files_and_dirs = run_async_in_streamlit(dashboard_api.list_files(current_path))
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
                content = run_async_in_streamlit(dashboard_api.read_file(file_to_read))
                st.success(f"Content of `{file_to_read}`:")
                st.code(content, language="python") # Assuming Python code for now
            except httpx.RequestError:
                st.error("🚨 Connection Error: Could not connect to Coddy API. Is the backend running?")
            except httpx.HTTPStatusError as e:
                st.error(f"⚠️ API Error ({e.response.status_code}): {e.response.json().get('detail', 'An API error occurred.')}")
            except Exception as e:
                st.error(f"🔥 An unexpected error occurred: {e}")

elif page == "Workspace":
    tab_assistant, tab_writer = st.tabs(["🧠 AI Assistant", "📝 File Writer"])

    with tab_assistant:
        st.header("🧠 Coddy AI Assistant")
        st.write("Enter high-level instructions or complex tasks for Coddy to decompose and execute.")
        
        # Initialize session state for subtasks
        if 'subtasks' not in st.session_state:
            st.session_state.subtasks = []

        user_instruction = st.text_area("What do you want Coddy to do?", height=150, key="ai_instruction_input")

        if st.button("Decompose Task", key="decompose_button"):
            if not user_instruction.strip():
                st.warning("Please enter an instruction for Coddy to decompose.")
                st.session_state.subtasks = [] # Clear previous subtasks
            else:
                with st.spinner("Decomposing your instruction..."):
                    try:
                        decomposition_engine = TaskDecompositionEngine()
                        # The engine is now async, so we need to run it in the loop
                        subtasks = run_async_in_streamlit(decomposition_engine.decompose(user_instruction))

                        if subtasks and not (len(subtasks) == 1 and "Error:" in subtasks[0]):
                            st.session_state.subtasks = subtasks
                        else:
                            st.session_state.subtasks = []
                            st.warning(f"Coddy could not decompose your task, or it was too simple: {subtasks[0] if subtasks else 'Unknown issue'}")
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
                    run_async_in_streamlit(asyncio.gather(*(execute_subtask(subtask) for subtask in st.session_state.subtasks)))
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
                    message = run_async_in_streamlit(dashboard_api.write_file(write_path, write_content))
                    st.success(message)
                    # Optionally, show the content after writing
                    if st.checkbox("Show content after writing?", key="show_content_checkbox"):
                        read_back_content = run_async_in_streamlit(dashboard_api.read_file(write_path))
                        st.code(read_back_content)
                except httpx.RequestError:
                    st.error("🚨 Connection Error: Could not connect to Coddy API. Is the backend running?")
                except httpx.HTTPStatusError as e:
                    st.error(f"⚠️ API Error ({e.response.status_code}): {e.response.json().get('detail', 'An API error occurred.')}")
                except Exception as e:
                    st.error(f"🔥 An unexpected error occurred: {e}")

elif page == "Coming Soon...":
    st.header("🚧 More Features on the Horizon!")
    st.info("Stay tuned for more exciting Coddy features, including Memory Logs, Git Insights, and the Idea Synthesizer Playground, all powered by the Coddy API!")

st.sidebar.markdown("---")
st.sidebar.info("Coddy: The Sentient Loop Dashboard")
st.sidebar.info("Async to the Bone. Terminal to UI.")