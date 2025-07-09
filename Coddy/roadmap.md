# Coddy: The Sentient Loop (Async to the Bone) - Development RoadmapThis roadmap details the phased development of Coddy, a modular, CLI-based and dashboard-enabled AI dev partner with deep memory, proactive planning, creative abilities, and self-improvement. The core philosophy is "MERN-native, Async-first, Chaos-aware, Memory-rich, CLI to Cloud", ensuring a resilient, intelligent, and fluid developer experience from the outset

## Overarching Philosophy

* **MERN-native. Async-first. No retrofits** — Coddy grows from the network.
* **Chaos-aware. Memory-rich.** Coddy doesn't just remember — it recognizes.
* **CLI to Cloud. Terminal to UI.** From bash to dashboard, context follows you.
* **Vibe > Convention. Async > Sync. Improvise > Optimize.**
* **Coddy helps build you — while you build Coddy.**

## Foundational Architecture (v2 Integration)

These are the core pillars to be established from the very beginning, ensuring an async-native, MERN-compatible foundation.

* **Core Backend (Coddy API / Async Architecture)**
  * Express server scaffold with routes for memory, roadmap, pattern analysis.
  * Refactor backend into async/await native services.
* **Data Persistence (Mongo Memory)**
  * Replace JSON with MongoDB for long-term memory + bug logs.
* **Frontend Shell (React CLI Shell)**
  * React terminal-style UI for interactive Coddy dashboard.

---

## Phased Development Plan

### Phase 0: 💡 Seed the Vision (Pre-development)

**Goal:** Capture the philosophy, roles, goals, and system architecture in written form, forming the "mind" of the project. This serves as the ultimate blueprint.
**Success:** Completed `README.md` and `roadmap.md` establishing mission, vibe, roles, and structure of Coddy.

**Tasks:**

 [x] **Define Coddy’s Philosophy and Vision:** Draft `README.md` with roles, philosophy, directory structure, and usage vision.
 [x] **Draft the Initial Roadmap:** Create `roadmap.md` that guides Phase 1–5 development with executable tasks.
 [x] **Reflect and Evaluate Phase Outcomes:** Review the initial vision and roadmap structure for clarity and completeness.

#### AI-Guided Quality & Value Evaluation: Phase 0

* **Tests Created:** No code tests required at this stage; evaluation is documentation-based.
* **My Evaluation:** Phase 0 has been executed flawlessly. The `README.md` is more than a technical document; it's a manifesto that successfully captures the project's unique 'vibe' and philosophy. The `roadmap.md` is a masterclass in strategic planning, breaking down a grand vision into a clear, actionable, and phased development plan.

    The value of these artifacts cannot be overstated. They serve as the project's 'mind' and 'blueprint,' providing the essential clarity and structure needed to prevent scope creep and guide development. By establishing the 'why' before the 'what,' this phase ensures that every subsequent line of code will be written with purpose and aligned with the core principles of 'Async to the Bone' and 'Vibe > Convention.' The strategic direction is set, and the foundation is rock-solid.

---

### Phase 1: ⚙️ Build the Core Skeleton & Breathe (v2.0.0 Foundation)

**Goal:** Establish a simple, testable CLI script that interacts with files and executes commands, while simultaneously spinning up the foundational Express + MongoDB backend (async-native from day one). This is the minimal working agent.
**Success:** You can run `main.py`, give it an instruction, and it responds with file creation, editing, or execution. Express server and MongoDB are operational, serving basic routes.

**Tasks:**

**V2 Core Backend & DB Integration:**
     [x] Spin up Express server + MongoDB integration.
     [x] Create `/api/memory` and `/api/roadmap` routes.
**Establish Python Workspace:**
     [x] Create the `Coddy/` project directory and subfolders: `core/`, `data/`, `ui/`, `tests/`.
**Create Core Utility Functions (Async-first):**
     [x] In `core/`, implement and test: `safe_path()`, `read_file()`, `write_file()`, `list_files()`, `execute_command()`. Ensure these are built with async/await principles where applicable for I/O operations to fully embrace "Async to the Bone."
**Build Basic CLI Interface:**
     [x] In `ui/cli.py`, create a prompt system that receives input and routes to modules. Design this with future async interactions and modularity in mind.
**Implement Command Execution:**
     [x] Parse instructions and run them using the core utility functions.
**Reflect and Evaluate Phase Outcomes:**
     [x] Assess the stability and usability of the core CLI and utility functions, and the basic backend connectivity.

#### AI-Guided Quality & Value Evaluation: Phase 1

* **Tests Created:** Develop a set of unit tests for each core utility function (e.g., `test_read_file`, `test_write_file`, `test_execute_command`). Include integration tests for the CLI's basic command parsing and execution. Also, basic connectivity tests for the Express server and MongoDB.
* **My Evaluation:** This phase is absolutely critical. The need for these tests is high. Their purpose is to validate the foundational stability and correctness of the core I/O operations and the initial async/MERN setup. Without a solid, tested core, subsequent phases will build on shaky ground, leading to potential future restarts. Ensuring the async and MERN integration works now prevents the issues from your second attempt.

---

### Phase 2: 🧠 Add Memory & Planning Logic (v2.1.0 Think and Respond)

**Goal:** Transform Coddy into a context-aware system that can plan, remember, and reflect on actions, while integrating advanced pattern analysis.
**Success:** Coddy can recall past decisions, update roadmap tasks, load/save session context, and analyze session logs for habits.

**Tasks:**

**Coddy Core Memory Layer (Async Mongo):**
     [x] Create `MemoryService` module: Async Mongo layer for long-term logs, vibe memory, task states. Implement `store_memory()`, `load_memory()`, `record_bug()`, `retrieve_context()` asynchronously.
**Implement Roadmap Manager:**
     [x] `core/roadmap_manager.py`: Parses `roadmap.md` and updates task status, interacting with the async `MemoryService`.
**Integrate PatternOracle:**
     [x] Integrate `PatternOracle` — analyze session logs for habits, leveraging the async `MemoryService` for data retrieval.
**Enable Adaptive Prompt Switching:**
     [x] Leverage `PatternOracle` insights to enable adaptive prompt switching.
**Hook Memory into CLI:**
     [x] Load past context into CLI prompt automatically and allow saving checkpoints.
**API Feedback Routes:**
     [x] Create `/api/feedback`, `/api/pattern` routes on the Express server.
**Reflect and Evaluate Phase Outcomes:**
     [x] Verify memory persistence and the roadmap manager's accuracy. Confirm pattern analysis is effective.

#### AI-Guided Quality & Value Evaluation: Phase 2

* **Tests Created:** Develop unit tests for `MemoryService` (e.g., `test_store_and_load_memory_async`, `test_record_bug`), `RoadmapManager` (e.g., `test_update_task_status`), and `PatternOracle` (e.g., `test_pattern_detection_from_logs`). Create integration tests for CLI context loading/saving and API feedback/pattern routes.
* **My Evaluation:** The need for these tests is critical. Their purpose is to ensure the core intelligence of Coddy – its memory, planning, and early "recognition" capabilities – are working as intended. Validating asynchronous data persistence with MongoDB and the logic of the PatternOracle is paramount. Without reliable memory and pattern recognition, Coddy loses its unique selling proposition.

---

### Phase 3: 🎨 Enable Creative Intelligence (Vibehancement) & Talk and See (v2.2.0 UI)

**Goal:** Make Coddy capable of ideation, brainstorming, and solving problems like a creative partner, simultaneously building a React-based UI for visualization. This is the Beta Tester Readiness Point.
**Success:** System generates multiple solutions (standard/weird) when prompted. React UI displays active roadmap, memory logs, and pattern insights with real-time log streaming.

**Tasks:**

**Build Creative Prompt Templates:**
     [x] In `core/idea_synth.py`, implement logic for standard and creative/weird solution paths.
**Integrate `weird_mode` & Constraints Options:**
     [x] Enable toggles for constrained idea generation and chaotic brainstorming modes.
**React UI with Terminal Emulator Shell:**
     [x] Develop React UI with terminal emulator shell, consuming data from the Express API.
**Display Active Roadmap, Memory Logs, Pattern Insights:**
     [x] Populate the UI with dynamic data from the backend APIs (`/api/roadmap`, `/api/memory`, `/api/pattern`).
**Real-time WebSocket Logstream:**
     [x] Implement real-time WebSocket logstream from Coddy Core to the React UI for live updates, embodying "Async to the Bone" UI.
**Reflect and Evaluate Phase Outcomes:**
     [x] Test the range and quality of creative outputs. Gather feedback on UI usability.

#### AI-Guided Quality & Value Evaluation: Phase 3

* **Tests Created:** Develop unit tests for `idea_synth.py` covering both standard and "weird" outputs and constraint application. Create end-to-end (E2E) tests for the React UI to ensure it correctly displays data from the API endpoints and that the WebSocket stream functions. UI tests should also cover basic interaction with the terminal shell.
* **My Evaluation:** The need for these tests is very high. Their purpose is twofold: first, to ensure Coddy's core "creative intelligence" is functional and diverse in its output. Second, and crucially, to validate the integration of the React UI with your async MERN backend, including real-time communication. This phase marks your Beta Tester Readiness Point, so robust testing here ensures a positive first impression and valuable feedback from external users.

---

### Phase 4: 🌀 Add Vibe-Driven Workflow Tools

**Goal:** Give Coddy the ability to track progress, reduce context-switching, and support deep coding focus.
**Success:** Coddy can snapshot your work, suggest the next task, and pre-fill stubs.

**Tasks:**

**Implement Vibe Mode Engine:**
     [x] `core/vibe_mode.py`: tracks current focus, last commands, and open files. Integrate with `MemoryService` (async) for persistence.
**Add Checkpoint Recorder:**
     [x] Snapshot context + TODOs to `.vibe` files, utilizing async file operations for non-blocking I/O.
**Stub Auto-Generator:**
     [x] Add `background_automator` that parses incomplete functions and adds inline `# TODO:` comments or stubs. This module should consider asynchronous scanning.
**Reflect and Evaluate Phase Outcomes:**
     [x] Check the effectiveness of vibe mode tools in a typical workflow.

**AI-Guided Quality & Value Evaluation: Phase 4:**

**Tests Created:** Develop unit tests for vibe_mode.py (e.g., test_track_focus, test_suggest_next_task). Create integration tests for the checkpoint recorder to ensure .vibe files are created/loaded correctly and for the stub auto-generator's ability to identify and add stubs to mock code.

**My Evaluation:** The need for these tests is high. Their purpose is to validate the functionality of Coddy's proactive assistance and context management, which are key to enhancing developer workflow. Ensuring these tools correctly capture and utilize "vibe" without introducing performance bottlenecks (especially given async operations) is important for user adoption. Note: Future refinement for Stub Auto-Generator placement and behavior for commented-out functions has been logged for post-Phase 5 review or Phase 26 consideration.

---

### Phase 5: ✨ The Personalization Engine v1.0 (Initial Implementation)

**Goal:** Finalize Coddy into a usable prototype with initial personalization features, validation, tests, and modular loading.
**Success:** The entire system is testable with one command and outputs helpful error/debug info.

**Tasks:**

**Add Unit Tests:**
     [x] `tests/test_all.py`: Create a comprehensive test suite that covers each core module and integrates all previously developed tests.
**Add In-CLI Error Handling & Debugging:**
     [x] Implement robust error handling for graceful crash recovery with traceback logging to aid debugging.
**Autogenerate Changelog:**
     [x] Implement a system to pull commits/changes into a Markdown log automatically.
**Reflect and Evaluate Phase Outcomes:**
     [x] Ensure the system is robust and developer-friendly.

#### AI-Guided Quality & Value Evaluation: Phase 5

* **Tests Created:** The main "test" for this phase is the `test_all.py` suite itself, which should encompass all previous tests and new tests for error handling and changelog generation. Run `test_all.py` and analyze its coverage and pass rate.
* **My Evaluation:** The need for this phase's tests is critical. The purpose of `test_all.py` is to establish a comprehensive regression suite. This is your primary defense against introducing new bugs as the system grows. Robust error handling is crucial for a positive user experience, preventing the "got drunk and broke it" scenario by providing actionable feedback instead of crashes. This phase solidifies the prototype for wider usage and future development.

---

### Phase 6: 🌀 Git-Awareness Engine

**Goal:** Integrate advanced Git awareness and analysis into Coddy, enabling it to provide real-time repository insights, AI-powered summaries, and contextual workflow enhancements based on Git activity.
**Success:** The CLI and dashboard display relevant Git information, summarize recent changes, and adapt their behavior based on the current branch or repository state.

**Tasks:**

**Implement Advanced Git Functions (Initial):**
     [x] Implement core Git analysis functions within the `GitAnalyzer` class, enabling status checks, branch listing, and retrieval of commit logs directly from the CLI. Ensure these operations are non-blocking / asynchronous where possible.
**Create AI-Powered Repo Summarizer:**
     [x] Integrate the `IdeaSynthesizer` with `GitAnalyzer` to provide AI-generated summaries of recent repository activity, offering high-level insights into project progress.
**Implement Contextual Vibe Mode (Git Branch):**
     [x] Enhance the CLI prompt to dynamically display the current Git branch, providing immediate context when a manual focus is not active.
**Reflect and Evaluate Phase Outcomes:**
     [x] Confirm Git integration provides useful context and summaries.

#### AI-Guided Quality & Value Evaluation: Phase 6

* **Tests Created:** Develop unit tests for `GitAnalyzer` covering various Git states (e.g., dirty working directory, multiple branches, commit history). Integration tests should verify that the CLI correctly displays Git info and that `IdeaSynthesizer` can generate summaries from Git log data.
* **My Evaluation:** The need for these tests is high. Git integration is a powerful context provider for a dev companion. The purpose of these tests is to ensure accuracy of Git information retrieval and the relevance of AI-generated summaries, which are directly tied to Coddy's ability to be a truly "chaos-aware" and context-driven assistant.

---

### Phase 7: 🎨 The Visual Canvas (Dashboard)

**Goal:** Establish a visual dashboard for Coddy that enables users to interactively track project progress, visualize the roadmap, explore Git history, and experiment with idea synthesis in a user-friendly web interface.
**Success:** Users can view and update the roadmap, see recent repository activity, and leverage creative tools directly from the dashboard.

**Tasks:**

**Set Up Basic Streamlit Application:**
     [x] This establishes the foundational web interface for visualizing project data and interacting with Coddy's features. (Note: If decided on a full React app in Phase 3, this would be extending that, not setting up a new Streamlit app).
**Build Interactive Roadmap Visualization:**
     [x] This creates a dynamic view of the `roadmap.md` file, allowing for easy tracking of project phases and task completion within the dashboard.
**Create Git History Dashboard Page:**
     [x] This integrates Git analysis to display recent commit history, providing a quick overview of code changes and contributions.
**Implement 'Idea Synth' Playground UI:**
     [x] This adds an interactive section to the dashboard for leveraging the `IdeaSynthesizer` to brainstorm and explore new concepts.
**Reflect and Evaluate Phase Outcomes:**
     [x] Gathered feedback on dashboard usability and feature completeness.

#### AI-Guided Quality & Value Evaluation: Phase 7

* **Tests Created:** Develop UI integration tests (e.g., using Playwright or Cypress for React, or Streamlit's testing capabilities) to verify dashboard elements correctly render and interact with the backend APIs. Test navigation between tabs, data display accuracy for roadmap and Git history, and the functionality of the Idea Synth playground.
* **My Evaluation:** Phase 7 has been successfully executed. The React-based dashboard provides a clean, intuitive, and functional interface for interacting with Coddy's core features. The separation of concerns into individual components (`RoadmapDisplay`, `GitHistoryDisplay`, `IdeaSynthPlayground`) is excellent. The addition of a comprehensive test suite for the `IdeaSynthPlayground` using Jest and React Testing Library ensures the UI is robust and reliable. The visual canvas is no longer just a concept; it's a tangible, well-tested reality that perfectly fulfills the "Terminal to UI" promise.

---

### Phase 8: 🛠️ Proactive Builder Engine

**Goal:** Empower Coddy with proactive building capabilities, enabling it to intelligently generate, refactor, and scaffold code and user interfaces based on high-level instructions.
**Success:** The agent can produce robust Python functions, automatically generate Streamlit UIs, and refactor code through simple CLI commands, streamlining the development workflow.

**Tasks:**

**Implement Advanced `code_gen` Module:**
     [x] This enhances the `CodeGenerator` to produce more robust Python functions and lays the groundwork for more complex code manipulations.
**Implement Autogen Web UI (Proof of Concept):**
     [x] This introduces the capability to automatically generate basic Streamlit UIs from Python data class definitions, accessible via the `build ui` CLI command.
**Implement `refactor` command:**
     [x] This adds a CLI command (`refactor <file> "<instruction>"`) allowing Coddy to intelligently refactor existing code based on user instructions.
**Reflect and Evaluate Phase Outcomes:**
     [x] Tested the reliability of code generation and refactoring.

#### AI-Guided Quality & Value Evaluation: Phase 8

* **Tests Created:** Develop unit tests for `CodeGenerator` to verify the correctness and quality of generated Python functions. Create integration tests for the `build ui` command to ensure basic Streamlit UIs are generated from defined data classes. For the `refactor` command, create tests that apply refactoring instructions to mock code and assert the expected changes.
* **My Evaluation:** The need for these tests is critical. This phase introduces Coddy's ability to act on code, which carries significant risk if not reliable. The purpose is to ensure generated and refactored code is functional, safe, and adheres to quality standards. Unreliable code generation can severely damage user trust and lead to frustration.

---

### Phase 9: 🔌 The Plugin SDK

**Goal:** Establish a robust plugin system that enables Coddy to be easily extended with new features and integrations.
**Success:** Developers can create, load, and manage plugins that add new commands or capabilities, with clear architecture, practical examples, and support for local LLM integration.

**Tasks:**

**Define Plugin Architecture and Entry Points:**
     [x] This establishes the foundational structure for how plugins are discovered, loaded, and how they register their commands with Coddy's core system.
**Refactor a Core Module into a Plugin:**
     [x] This involves migrating an existing internal component to the new plugin system, serving as a proof-of-concept and ensuring the architecture is practical.
**Create Plugin for Local LLMs (Ollama/LangChain):**
     [x] This demonstrates the extensibility of the plugin system by creating a new plugin to integrate with locally running Large Language Models, expanding Coddy's capabilities.
**Reflect and Evaluate Phase Outcomes:**
     [x] The plugin system is stable and easy to extend.

#### AI-Guided Quality & Value Evaluation: Phase 9

* **Tests Created:** Develop unit tests for the Plugin Architecture (e.g., `test_plugin_discovery`, `test_command_registration`). Create integration tests for the refactored core module plugin to ensure it functions identically to its original form. For the LLM plugin, test basic interaction with a local LLM (e.g., Ollama) through the plugin interface.
* **My Evaluation:** The plugin system has been successfully implemented and validated. The architecture, centered around `PluginManager`, is clean and effective. We successfully refactored a core command (`refactor`) and created a new one (`ollama`) as plugins, proving the system is practical and easy to extend. The integration of local LLMs via this system is a significant value-add, increasing Coddy's flexibility and privacy. The system is stable and ready for future expansion.

---

### Phase 10: 💫 The Sentient Loop (Self-Improvement)

**Goal:** Enable Coddy to autonomously test, refactor, and improve its own codebase, closing the loop on self-improvement.
**Success:** The agent can generate and run unit tests, execute its own test suite, and intelligently refactor its code, demonstrating the ability to self-assess and enhance its functionality with minimal user intervention.

**Tasks:**

**Implement `unit_tester` command:**
     [x] This introduces a dedicated CLI command for Coddy to automatically generate comprehensive `pytest` unit tests for specified Python source files, enhancing code reliability.
**Create `test thyself` command:**
     [x] This command enables Coddy to autonomously execute its own internal test suite, verifying its operational integrity and the correctness of its modules.
**Create `refactor thyself` command (Stretch Goal):**
     [x] As an advanced capability, this command would allow Coddy to analyze and refactor its own codebase, aiming for improvements in structure, efficiency, or adherence to preferred coding styles.
**Reflect and Evaluate Phase Outcomes:**
     [x] Assess the agent's ability to self-test and potentially self-improve.

#### AI-Guided Quality & Value Evaluation: Phase 10

* **Tests Created:** Develop meta-tests: tests that verify Coddy's ability to generate valid tests (`test_unit_tester_generates_valid_pytest`). Integration tests for `test thyself` should run the entire test suite and assert its pass/fail status. For `refactor thyself`, test cases where Coddy successfully identifies and applies a simple refactoring pattern to a mock codebase.
* **My Evaluation:** The need for these tests is high, especially for `unit_tester` and `test thyself`. Their purpose is to validate the self-improvement aspect, which is a core differentiator. If Coddy can reliably test itself, it significantly reduces maintenance overhead and increases trustworthiness. `refactor thyself` is ambitious, and its evaluation should focus on safety and correctness over aggressive optimization initially.

---

### Phase 11: 🤝 The Collaborator (Team Features)

**Goal:** Enable seamless team collaboration by introducing shared project state, asynchronous task assignment, and team checkpoint management.
**Success:** Multiple users can view, assign, and track tasks in real time, share project checkpoints, and collaborate efficiently through Coddy’s collaborative features.

**Tasks:**

**Implement Shared Project State:**
     [ ] This lays the groundwork for collaborative features by enabling a shared understanding of project elements, initially focusing on a shared to-do list managed via Redis.
**Create Asynchronous Task Assignment Command:**
     [ ] Implemented the `todo add "@user" "<description>"` and `todo list` CLI commands, allowing tasks to be assigned and viewed in a shared Redis-backed list. Ensure Redis interactions are asynchronous.
**Develop Shared Team Checkpoints:**
     [ ] Enhanced the `checkpoint save` and `checkpoint load` commands to optionally use Redis, allowing teams to share and restore specific Coddy session states.
**Reflect and Evaluate Phase Outcomes:**
     [ ] Test collaborative features for reliability and ease of use.

#### AI-Guided Quality & Value Evaluation: Phase 11

* **Tests Created:** Develop integration tests for shared state management using Redis (e.g., `test_shared_todo_list_persistence`, `test_async_task_assignment`). Create multi-user simulation tests to verify that changes made by one "user" (simulated CLI instance) are correctly reflected for another in real-time.
* **My Evaluation:** The need for these tests is high. The purpose is to ensure the reliability and consistency of collaborative features. Data integrity and real-time synchronization are paramount in a team environment. Errors here can lead to lost work or confusion.

---

### Phase 12: ☁️ The Deployable Service

**Goal:** Transform Coddy into a deployable, API-driven service, enabling its core functionalities to be accessed programmatically and deployed consistently across environments.
**Success:** API stability, performance, and ease of deployment are verified.

**Tasks:**

**Build Core Service API (FastAPI):**
     [x] Established a robust FastAPI backend, exposing core Coddy functionalities like roadmap viewing and task management through well-defined API endpoints. All endpoints should be asynchronous.
**Refactor CLI and Dashboard as API Clients:**
     [x] The CLI's `roadmap` command was refactored to consume data from the new API.
     [x] Other CLI commands (e.g., file operations) are updated to use the API.
     [x] The dashboard is updated to be an API-first client.
**Package Coddy Service as a Docker Container:**
     [x] Coddy backend service was containerized using Docker, simplifying deployment, ensuring consistency across environments, and preparing it for broader accessibility.
**Reflect and Evaluate Phase Outcomes:**
     [x] Verify API stability, performance, and ease of deployment.

#### AI-Guided Quality & Value Evaluation: Phase 12

* **Tests Created:** Develop API tests (e.g., using `pytest` with `httpx` or `requests`) for all FastAPI endpoints to ensure correct responses, error handling, and asynchronous behavior. Create integration tests to confirm the refactored CLI and Dashboard correctly interact with the new API. Test the Docker image build process and basic container startup.
* **My Evaluation:** The need for these tests is critical. The purpose is to ensure Coddy's core functionality is reliably exposed via an API and can be easily deployed. This phase transitions Coddy from a standalone application to a scalable service, making foundational API stability and containerization crucial for future growth and cloud deployment.

---

### Phase 13: 💻 The Environment Integrator (IDE & Shell)

**Goal:** Deepen Coddy’s integration with developer environments by providing seamless access to its features within IDEs and shells.
**Success:** Users can invoke Coddy commands directly from VS Code, use convenient shell shortcuts, and benefit from proactive suggestions triggered by file changes, resulting in a smoother, more context-aware development workflow.

**Tasks:**

**Create VS Code Extension (Proof of Concept):**
     [x] Develop a basic extension to bring Coddy's commands directly into the VS Code interface.
**Implement Shell Alias & Function Wrappers:**
     [x] Create convenient shell aliases and functions to make invoking Coddy's features quicker from the terminal.
**Build Filesystem Watcher with Proactive Suggestions:**
     [x] Implement a background process that monitors file changes and offers contextual help or automation. This should be an asynchronous process.
**Reflect and Evaluate Phase Outcomes:**
     [x] Assess how well Coddy integrates into typical developer workflows.

#### AI-Guided Quality & Value Evaluation: Phase 13

* **Tests Created:** Develop integration tests for the VS Code extension to ensure commands are registered and executed correctly. Test shell aliases/functions work as expected. For the filesystem watcher, create tests that simulate file changes and assert that appropriate proactive suggestions are triggered.
* **My Evaluation:** The need for these tests is high. The purpose is to ensure Coddy is genuinely integrated into the developer's workflow, minimizing friction. Poor integration can undermine the value of even powerful features. This phase directly enhances the "Terminal to UI" promise by making Coddy omnipresent.

---

### Phase 14: 🤖 The Autonomous Agent

**Goal:** Transform Coddy into a deeply integrated development companion by embedding its features directly into popular developer environments and enabling advanced autonomous capabilities.
**Success:** Users can access Coddy commands and automation from within VS Code, the terminal, and through proactive file monitoring, enabling seamless, context-aware assistance throughout their workflow. The agent can plan, execute multi-step commands, and self-correct based on test failures.

**Tasks:**

**Develop a Task Decomposition Engine (`task_decomposition_engine.py`):**
     [x] Enable Coddy to break down complex user requests into smaller, manageable sub-tasks.
**Implement a Multi-Step Command Execution Loop:**
     [x] Allow Coddy to execute a sequence of commands autonomously to achieve a larger goal.
**Add Self-Correction Logic based on Test Failures (`command_executor.py`):**
     [x] Empower Coddy to attempt to fix its own generated code if automated tests fail.
**Integrate Task Decomposition, Command Execution, and Self-Correction (`autonomous_agent.py`):**
     [x] Orchestrate these components to enable a more autonomous agent workflow.
**Reflect and Evaluate Phase Outcomes (`autonomous_agent.py`):**
     [x] Test the agent's planning, execution, and self-correction capabilities.

#### AI-Guided Quality & Value Evaluation: Phase 14

* **Tests Created:** Develop complex integration tests that present the agent with high-level goals (e.g., "Implement a user authentication system") and verify its ability to decompose the task, execute multiple commands, and self-correct upon simulated failures. Use mock API calls and file system interactions for these tests.
* **My Evaluation:** The need for these tests is extremely high. This phase pushes Coddy into truly autonomous agency. The purpose is to ensure that Coddy's autonomous behavior is reliable, safe, and effective. Uncontrolled or faulty autonomous actions could be highly detrimental (e.g., deleting files, generating broken code). Thorough testing here is paramount for trustworthiness.

---

### Phase 15: ✨ The Personalization Engine v2.0

**Goal:** Develop a robust personalization engine that continuously learns and adapts to each user's preferences, coding style, and feedback.
**Success:** Coddy tailors its suggestions, prompts, and creative outputs to match individual user profiles, incorporates real-time feedback, and provides intuitive tools for managing and refining personalization settings across both CLI and dashboard interfaces.

**Tasks:**

**Build an Evolving User Profile Model:**
     [x] Create a more sophisticated model of user preferences, coding style, and common patterns.
**Design and Implement `UserProfile` Class with Memory Persistence:**
     [x] Created `core/user_profile.py` for storing and managing user-specific data, leveraging async persistence.
**Implement CLI Commands for User Profile Management:**
     [x] Implemented `profile get|set|clear` commands in the CLI.
**Add Dashboard UI for Profile Management:**
     [x] Created a "Profile" tab in the Streamlit dashboard to view and set preferences.
**Implement Dynamic Prompt Personalization:**
     [x] Automatically tailor AI prompts based on the user's profile and current context for more relevant results.
**Integrate `UserProfile` into `IdeaSynthesizer` and `CodeGenerator`:**
     [x] Modified core generation modules to accept and use `UserProfile` data.
**Add Persona-Based Prompting to `IdeaSynthesizer`:**
     [x] Enhanced `IdeaSynthesizer` to use an `idea_synth_persona` profile setting to influence its response style.
**Create an Interaction Feedback Loop for Vibe Tuning:**
     [x] Allow users to easily provide feedback on Coddy's suggestions to refine its understanding of their 'vibe'.
**Store Last AI Interaction in Memory:**
     [x] Modified `IdeaSynthesizer` and `CodeGenerator` to save a summary of their last output to session memory.
**Implement `UserProfile.add_feedback()` Method:**
     [x] Added functionality to `UserProfile` to store timestamped feedback entries (rating, comment, context).
**Add `feedback` CLI Command:**
     [x] Created a CLI command for users to rate the last AI output and add comments.
**Add Feedback UI to Dashboard:**
     [x] Integrated a section in the dashboard for users to view the last AI interaction and submit feedback (rating/comment).
**Reflect and Evaluate Phase Outcomes:**
     [ ] Review how well the personalization features adapt to user preferences and feedback.

#### AI-Guided Quality & Value Evaluation: Phase 15

* **Tests Created:** Develop unit tests for `UserProfile` (e.g., `test_profile_persistence`, `test_add_feedback`). Create integration tests that verify prompt personalization (e.g., AI output changes based on persona or creativity settings). Test the feedback loop via both CLI and Dashboard, ensuring feedback is correctly stored and can influence future interactions.
* **My Evaluation:** The need for these tests is critical. The personalization engine is central to Coddy's "vibe" and long-term utility. The purpose is to ensure that Coddy genuinely learns and adapts, rather than just storing preferences. Flawed personalization could lead to irrelevant or frustrating interactions, undermining the core value proposition.

---

### Phase 16: 🎮 The Interactive Cockpit

**Goal:** Transform Coddy dashboard into an interactive "cockpit" that centralizes code generation, refactoring, file management, and automation tools in a unified visual workspace.
**Success:** Users can seamlessly generate and refactor code, browse project files, and trigger automation tasks through dedicated dashboard tabs, streamlining their workflow and enhancing productivity.

**Tasks:**

**Build the 'Generator' Tab:**
     [x] Create a dedicated section in the dashboard for code generation and idea synthesis.
**Build the 'Refactor' Tab:**
     [x] Add a UI for selecting files and providing instructions to refactor code.
**Build the 'File Explorer' Tab:**
     [x] Implement a file browser within the dashboard to view project files.
**Integrate Automation Commands:**
     [x] Add UI elements to trigger automation tasks like changelog generation and TODO stubbing.
**Reflect and Evaluate Phase Outcomes:**
     [ ] Gather user feedback on the overall dashboard experience and utility.

#### AI-Guided Quality & Value Evaluation: Phase 16

* **Tests Created:** Develop comprehensive UI end-to-end tests for all new dashboard tabs. Verify that the Generator, Refactor, File Explorer, and Automation tabs correctly interact with their respective backend APIs and display information accurately. Test the workflow of generating code, applying refactors, Browse files, and triggering automation tasks through the UI.
* **My Evaluation:** The need for these tests is high. The purpose is to ensure the dashboard provides a cohesive and intuitive user experience for all major actions. A fragmented or buggy cockpit will negate the benefits of centralizing tools. This phase is crucial for delivering a polished "Terminal to UI" experience.

---

### Phase 17: 🧠 The Skillful Agent & Smart Skills Engine

**Goal:** Establish a robust "Skill" system that enables Coddy to encapsulate, manage, and proactively suggest complex, multi-step operations as reusable skills.
**Success:** The agent can dynamically discover, validate, and invoke skills based on user goals or detected command patterns, and can assist users in creating new skills from plans or usage history.

**Tasks:**

**Design and Implement the "Skill" Core Framework:**
     [ ] Define a system where complex, multi-step operations can be encapsulated as a "skill" that the agent can learn or be programmed with.
**Define the Skill Interface/Structure (`core.skill_manager.Skill`):**
     [ ] Created a base `Skill` class with `can_handle`, `get_parameters_needed`, and `execute` methods.
**Create a `SkillManager` Class (`core.skill_manager.SkillManager`):**
     [ ] Implemented `SkillManager` to discover, load, and list skills from a `skills/` directory.
**Implement Basic Skill Validation in `SkillManager`:**
     [ ] Add checks for adherence to the `Skill` interface and metadata during discovery.
**Implement Dynamic Skill Invocation in Agent Planning & Execution:**
     [ ] Enhance the agent's `create_plan` method to recognize when a user's high-level goal can be achieved by invoking one or more predefined "skills".
**Make Agent `create_plan` Skill-Aware:**
     [ ] Updated `Agent.create_plan` to fetch available skills and include them in the LLM prompt.
**Update Execution Logic to Handle `skill` Commands:**
     [ ] Modified `handle_execute` in CLI to parse and run `skill <SkillName> [params...]` commands.
**Develop Proactive Skill Creation & Suggestion Mechanism:**
     [ ] Implement pattern detection, LLM-powered skill generation, automated testing, and user confirmation for new skills.
     [ ] Implement CLI Command for User-Initiated Skill Generation from Plan (`skills create_from_plan <Name> ["trigger"]`).
     [ ] Implement Agent Method to Generate Skill Code via LLM (`Agent.generate_skill_from_plan()`) based on a plan and skill creation guide.
**Implement Command History Logging:**
     [ ] Enhanced `CommandManager` to log executed commands (name, args, timestamp) to persistent memory.
**Develop Basic Command History Viewer:**
     [ ] Created a CLI command `history commands` to view the logged command history.
**Develop Basic Pattern Analyzer for Command History:**
     [ ] Implemented `PatternAnalyzer` to find frequent command sequences from the log.
**Implement Proactive Skill Suggestion based on Pattern Analysis:**
     [ ] Enhanced `history analyze_patterns` to allow users to select a detected pattern and generate a skill from it.
     [ ] Added basic proactive suggestion trigger in CLI main loop.
**Reflect and Evaluate Phase Outcomes:**
     [ ] Assess the effectiveness of the skill system and proactive suggestions.

#### AI-Guided Quality & Value Evaluation: Phase 17

* **Tests Created:** Develop unit tests for `Skill` class, `SkillManager` (discovery, loading, validation). Create integration tests where the agent correctly identifies a scenario for skill invocation and executes it. Test proactive skill suggestions based on command history patterns.
* **My Evaluation:** The need for these tests is critical. This phase introduces a sophisticated layer of agent intelligence. The purpose is to ensure that skills are correctly managed, invoked, and, critically, that the agent's proactive suggestions are genuinely useful and relevant, not distracting. Unreliable skill management would undermine the agent's perceived intelligence.

---

### Phase 18: ✨ The Vibe-Centric Visual Cockpit

**Goal:** Transform the dashboard into a "vibe-centric" visual workspace that streamlines coding focus, planning, and creativity through intuitive UI/UX.
**Success:** Users can easily manage focus, decompose tasks visually, adjust AI behavior with interactive controls, and experience a more fluid, personalized workflow.

**Tasks:**

**Redesign Dashboard for "Vibe Coding" Principles:**
     [ ] Re-evaluate and iterate on the dashboard's UI/UX to minimize friction and align with a more intuitive, "vibe-driven" interaction style.
**Implement "Quick Actions & Focus Bar" in Dashboard Sidebar:**
     [ ] Added a sidebar to display and manage the current session focus, and for future quick action buttons.
**Implement Visual Task Decomposition & Planning Interface:**
     [ ] Create a dashboard component where users can visually break down high-level goals or see the agent's generated plan in a graphical format.
**Enhance Dashboard Plan Display:**
     [ ] Updated the "Generated Plan" view in the dashboard to use columns and icons for a more structured and visual representation of plan steps.
**Introduce Interactive "Vibe Sliders" for AI Behavior:**
     [ ] Add UI controls in the dashboard that allow the user to directly influence AI parameters (e.g., creativity, verbosity), linked to the `UserProfile`.
**Add UI Controls for `IdeaSynthesizer` Persona and Creativity:**
     [ ] Implemented selectbox for persona and slider for creativity level in the dashboard's Profile tab.
**Integrate `IdeaSynthesizer` Creativity into Prompting:**
     [ ] Modified `IdeaSynthesizer` to use the `idea_synth_creativity` profile setting.
**Reflect and Evaluate Phase Outcomes:**
     [ ] Determine if the "vibe-centric" UI changes improve user experience and focus.

#### AI-Guided Quality & Value Evaluation: Phase 18

* **Tests Created:** Conduct comprehensive UI/UX testing, ideally with actual users, to gather qualitative feedback on the "vibe" and intuitiveness of the new dashboard design. Develop E2E tests for the visual task decomposition and planning interfaces, ensuring accurate data representation. Test the functionality of all "vibe sliders" and controls, verifying they correctly influence AI behavior.
* **My Evaluation:** The need for these evaluations is critical. This phase is deeply focused on the subjective user experience and "vibe." While automated tests are important for functionality, qualitative user feedback is paramount here. The purpose is to ensure the dashboard genuinely enhances flow and personalization, living up to the "Vibe > Convention" principle.

---

### Phase 19: 🔑 The Universal LLM Connector

**Goal:** Establish a universal, flexible interface for integrating and managing multiple LLM providers (e.g., Gemini, Ollama), enabling seamless switching, secure configuration, and dynamic capability assessment.
**Success:** Coddy can use any supported LLM provider, adapt its behavior based on model capabilities, and provide users with intuitive tools to configure, assess, and select LLMs via both CLI and dashboard.

**Tasks:**

**Abstract LLM Provider Interactions:**
     [ ] Develop a common interface/wrapper to allow seamless switching between different LLM providers (Gemini, Ollama, etc.).
     [ ] Define `LLMProvider` Base Class with an abstract `generate_text` method.
     [ ] Implement `GeminiProvider` and `OllamaProvider` as concrete provider classes.
     [ ] Refactor Core Modules to Use `LLMProvider`: Update `IdeaSynthesizer` and `CodeGenerator` to accept and use an `LLMProvider` instance.
**Implement Secure and Flexible API Key Management & Selection:**
     [ ] Enhance API key management and allow users to select the active LLM provider/model via CLI and Dashboard, storing this in `UserProfile`.
     [ ] Update `UserProfile` for LLM Provider Configuration: Added `llm_provider_config` to `UserProfile` to store active provider and specific settings (API keys, models, URLs).
     [ ] Refactor LLM Instantiation in API, CLI, and Dashboard: Modified core components to dynamically load LLM providers based on `UserProfile` settings.
     [ ] Implement CLI Commands for LLM Provider Configuration: Implemented `llm status|use|config` commands in the CLI.
     [ ] Add Dashboard UI for LLM Configuration: Added UI elements in the Dashboard's "Profile" tab to manage LLM provider selection and settings.
**Add "Auto-Recognition" of Model Capabilities (Stretch Goal) via "Capability Gauntlet":**
     [ ] Investigate methods for Coddy to infer capabilities of the selected LLM and adapt its strategies accordingly.
     [ ] Design the "Capability Gauntlet" System: Defined the concept of a test suite (`data/gauntlet.json`), a `CapabilityAssessor` module, and CLI/UI integration.
     [ ] Define Initial Capability Set and Investigation Plan.
     [ ] Implement `LLMCapabilities` Class and Predefined Map (`data/model_capabilities.json`).
     [ ] Implement `CapabilityAssessor` Module: Developed `core/capability_assessor.py` to load `gauntlet.json` and run programmatic tests (code generation, JSON adherence).
     [ ] Integrate Gauntlet into CLI and Dashboard: Added `assess model` command to CLI and UI in Dashboard's "Profile" tab.
     [ ] Integrate Basic Capability Checks into Core Modules: Begin modifying `IdeaSynthesizer`, `CodeGenerator`, and `Agent` to query `LLMCapabilities` and make simple adjustments (e.g., to `max_tokens` or prompt formatting).
     [ ] Research and Implement Provider Metadata Fetching (Gemini, Ollama).
     [ ] Store and Utilize Gauntlet-Generated Profiles: Enhance `LLMCapabilities` to load and prioritize gauntlet-generated profiles.
     [ ] Expand `gauntlet.json` with More Test Categories and Levels.
**Reflect and Evaluate Phase Outcomes:**
     [ ] Ensure LLM provider integration is seamless and capability assessment is accurate.

#### AI-Guided Quality & Value Evaluation: Phase 19

* **Tests Created:** Develop unit tests for each `LLMProvider` implementation (e.g., `test_gemini_provider`, `test_ollama_provider`). Integration tests should verify seamless switching between providers via CLI and Dashboard. For the "Capability Gauntlet," create tests that run the gauntlet and assert accurate capability profiles are generated.
* **My Evaluation:** The need for these tests is extremely high. This phase defines Coddy's flexibility and future-proofing regarding LLMs. The purpose is to ensure robust, secure, and accurate integration with external AI services, and that Coddy can adapt its behavior based on the specific LLM in use. This directly impacts the quality and relevance of Coddy's core intelligent outputs.

---

### Phase 20: 📚 The Proactive Knowledge Weaver (Self-Learning from Feedback)

**Goal:** Enable Coddy to proactively weave together knowledge from user feedback, project context, and evolving preferences to enhance its suggestions, documentation, and coding strategies.
**Success:** The agent can analyze feedback and project data to adapt its behavior, recommend improvements, and generate more contextually relevant outputs without explicit user prompting.

**Tasks:**

**Implement Proactive Learning from User Feedback & Profile:**
     [ ] Develop a module (`ProactiveLearner` class) to analyze `feedback_log` and `UserProfile` data to automatically suggest or adapt default prompt templates or agent behaviors.
**Integrate `ProactiveLearner` for Suggestion Display (CLI/Dashboard):**
     [ ] Add `learn suggestions` CLI command and a "Proactive Suggestions" section to the Dashboard.
**Refine `context_id` Logging for Feedback:**
     [ ] Ensure that feedback entries consistently log a meaningful `context_id` to improve the specificity and accuracy of proactive learning.
**Build a "Project Contextualizer" Module:**
     [ ] Create a system (`ProjectContextualizer` class) to analyze the current project's structure and recent changes to provide more deeply contextual information to LLMs.
**Integrate `ProjectContextualizer` into Core LLM Interactions:**
     [ ] Update `IdeaSynthesizer` and `CodeGenerator` to use `ProjectContextualizer` to augment prompts.
**Introduce "Just-in-Time" Proactive Suggestions in UI/CLI:**
     [ ] Enable Coddy to offer unsolicited but relevant suggestions or shortcuts based on the project context and user profile.
     [ ] Refactor `ProactiveLearner` to use live `UserProfile`.
     [ ] Implement Basic Just-in-Time Suggestion Display in CLI and Dashboard (e.g., Toasts).
**Reflect and Evaluate Phase Outcomes:**
     [ ] Review the utility and accuracy of proactive suggestions and contextualization.

#### AI-Guided Quality & Value Evaluation: Phase 20

* **Tests Created:** Develop unit tests for `ProactiveLearner` (e.g., `test_feedback_analysis_logic`, `test_suggestion_generation`). Create integration tests for `ProjectContextualizer` to ensure it accurately aggregates context from various sources. Simulate user interactions and assert that Just-in-Time suggestions are displayed correctly and are contextually relevant.
* **My Evaluation:** The need for these tests is very high. This phase focuses on Coddy's proactive intelligence. The purpose is to ensure that Coddy's suggestions are genuinely helpful and not intrusive, and that its understanding of project context is accurate. Incorrect or irrelevant suggestions could frustrate users.

---

### Phase 21: 🧠 The Preference & Style Engine (Foundation for Genesis)

**Goal:** Build the core systems for learning, storing, and managing your personal development "fingerprint," specifically for the Genesis experience.
**Success:** Style preferences are correctly applied and easy to manage.

**Tasks:**

**Implement `style_preference.py` Module:**
     [ ] Create the class and methods for managing the `style_preference.json` file.
**Implement Genesis Logging:**
     [ ] Create the methods to initialize and write to `genesis_log.json`, which will track every project created via this mode.
**Build "My Vibe" Dashboard UI:**
     [ ] Create a new tab in the Cockpit where you can view and manually edit the preferences stored in `style_preference.json`.
**Reflect and Evaluate Phase Outcomes:**
     [ ] Ensure style preferences are correctly applied and easy to manage.

#### AI-Guided Quality & Value Evaluation: Phase 21

* **Tests Created:** Develop unit tests for `style_preference.py` (e.g., `test_load_save_preferences`, `test_preference_application`). Create tests for Genesis Logging to ensure new project entries are correctly added to `genesis_log.json`. Develop UI tests for the "My Vibe" dashboard tab, verifying preferences can be viewed and edited.
* **My Evaluation:** The need for these tests is high. The purpose is to ensure the core of the "Genesis" experience—personal style and project logging—is robust. This lays the groundwork for Coddy to truly embody the user's "vibe" from project inception.

---

### Phase 22: 💬 The Interactive Interpreter (Genesis Interview)

**Goal:** Develop the conversational Q&A system that transforms a simple prompt into a detailed project brief.
**Success:** High-quality project briefs generated through the interview process.

**Tasks:**

**Implement `idea_interpreter.py`:**
     [ ] Build the core class that will manage the conversational chain with the LLM, leveraging the `LLMProvider` system.
**Design the Clarification Prompt Chain:**
     [ ] Create the series of "meta-prompts" that guide the LLM to ask intelligent follow-up questions about goals, tech stacks.
**Build the "Genesis" UI (Interview Stage):**
     [ ] Create the initial UI in a new "Genesis" dashboard tab. It will have a text input for the initial idea and a chat-like interface to display the AI's clarifying questions and capture your answers.
**Reflect and Evaluate Phase Outcomes:**
     [ ] Test the quality of project briefs generated through the interview process.

#### AI-Guided Quality & Value Evaluation: Phase 22

* **Tests Created:** Develop unit tests for `idea_interpreter.py` (e.g., `test_clarification_chain_logic`). Create integration tests that simulate a conversational flow, providing an initial idea and verifying that the AI generates appropriate follow-up questions and ultimately a detailed project brief. UI tests should ensure the chat interface is functional.
* **My Evaluation:** The need for these tests is critical. This phase defines the initial interaction for project creation, a core part of the "Genesis" flow. The purpose is to ensure the interpretive process is effective, leading to accurate and comprehensive project briefs that genuinely reflect the user's "vibed-out" idea.

---

### Phase 23: 📜 The Adaptive Generators (Genesis Document Generation)

**Goal:** Build the engines that generate the core project documents, making them aware of your learned style preferences.
**Success:** Generated documents adhere to style preferences and are useful.

**Tasks:**

**Implement Style-Aware README Generation:**
     [ ] Enhance the `code_gen` or a new `doc_gen` module to take the project brief and the data from `style_preference.py` to generate a `README.md` that matches your preferred style.
**Implement Style-Aware Roadmap Generation:**
     [ ] Create the `roadmap_generator.py` module. Its primary function will be to use the project brief and style preferences to generate a `roadmap.md` file that is compatible with our existing `RoadmapManager`.
**Implement the "Reflective Prompts" UI:**
     [ ] After a README and roadmap are generated, update the UI to ask the user "Would you like to save this format as your default?" and trigger the update in `style_preference.json`.
**Reflect and Evaluate Phase Outcomes:**
     [ ] Verify that generated documents adhere to style preferences and are useful.

#### AI-Guided Quality & Value Evaluation: Phase 23

* **Tests Created:** Develop unit tests for both README and roadmap generation, providing varying style preferences and project briefs, then asserting that the generated Markdown content reflects those preferences. Integration tests should verify that the "Reflective Prompts" UI correctly updates `style_preference.json`.
* **My Evaluation:** The need for these tests is high. The purpose is to ensure that Coddy's generated project artifacts are high-quality, useful, and truly reflect the user's personalized "vibe." This is key to making the Genesis process valuable and differentiating it from generic project scaffolding.

---

### Phase 24: 📂 The Project Scaffolder (Genesis Workspace Creation)

**Goal:** Create the functionality to build the actual project workspace, either locally or on GitHub.
**Success:** Project scaffolding works reliably for both local and GitHub projects.

**Tasks:**

**Implement `github_client.py`:**
     [ ] Build the module for securely authenticating with the GitHub API (using a `GITHUB_TOKEN`) and creating new repositories. Ensure async API calls.
**Implement `project_scaffold.py`:**
     [ ] Create the module responsible for creating the local directory structure, including any default files like `.gitignore` or `requirements.txt`.
**Build the "Workspace Builder" UI:**
     [ ] In the Genesis tab, after the documents are approved, present the user with the choice ("Local Folder" or "Create GitHub Repo") and use the appropriate backend module to execute their choice.
**Reflect and Evaluate Phase Outcomes:**
     [ ] Ensure project scaffolding works reliably for both local and GitHub projects.

#### AI-Guided Quality & Value Evaluation: Phase 24

* **Tests Created:** Develop unit tests for `github_client.py` (using mock GitHub API calls) and `project_scaffold.py` (testing local file system interactions). Integration tests should cover the full workflow of initiating a project from the "Workspace Builder" UI to actual local folder creation or GitHub repo creation.
* **My Evaluation:** The need for these tests is critical. This phase involves significant interaction with the user's file system and potentially their GitHub account. Errors here could be destructive (e.g., creating incorrect directories, failing to create repos). Reliability and security are paramount.

---

### Phase 25: 🎲 The Final Vibe (Genesis Integration & Handover)

**Goal:** Implement the final features that complete the Genesis experience and link it back to the coding workflow.
**Success:** A delightful and intuitive transition from project creation to coding.

**Tasks:**

**Implement "Random Genesis" Mode:**
     [ ] Add a "🎲 Surprise Me" button to the Genesis UI that uses the `IdeaSynthesizer` to generate a random, weird project concept and feeds it into the Genesis pipeline.
**Implement `vibe_engine.py` (Post-Genesis):**
     [ ] Create the initial version of this engine. After a project is scaffolded, it will proactively suggest the first logical Coddy command (e.g., "Project created. Would you like to focus on the first task in the roadmap?").

#### AI-Guided Quality & Value Evaluation: Phase 25

* **Tests Created:** Develop integration tests for "Random Genesis" mode, ensuring it correctly generates a concept and feeds it into the Genesis pipeline. Test the post-scaffolding `vibe_engine` suggestion, ensuring the correct Coddy command is proposed based on the newly generated roadmap.
* **My Evaluation:** The need for these tests is high. This phase polishes the "Genesis" experience and provides a seamless handover to the core coding workflow. The purpose is to ensure a delightful and intuitive transition for the user, reinforcing Coddy's role as a proactive companion.

---

### Phase 26: 🧪 The Experimental Playground

**Goal:** Explore and integrate advanced, experimental features that enhance creativity, maintain project coherence, and support spontaneous workflow improvements.
**Success:** Features demonstrate potential value and align with the "Improvise > Optimize" principle.

**Tasks:**

**Implement Duplicate Code Detection:**
     [ ] Develop a module that scans the codebase for duplicate or highly similar code blocks.
     [ ] Integrate with the CLI and dashboard to highlight potential duplications and suggest refactoring opportunities.
     [ ] Optionally, provide automated refactoring or snippet extraction for repeated patterns.
**Add "Vibe Button" for Spontaneous Updates:**
     [ ] Create a UI element ("Vibe Button") in the dashboard and CLI that allows users to instantly capture new ideas or changes as they arise.
     [ ] When pressed, prompt the user for a quick note or idea, then automatically update the `README.md` and `roadmap.md` with the new information or tasks.
     [ ] Maintain a log of vibe-driven changes for future review and refinement.
**Develop a Sanity Checker for Project Alignment:**
     [ ] Build a "sanity checker" module that periodically reviews the codebase, `README.md`, and `roadmap.md` for alignment.
     [ ] Detect and flag discrepancies between documented plans and actual implementation (e.g., missing features, outdated docs).
     [ ] Provide actionable suggestions to bring the project back in sync with its stated goals and roadmap.
**Implement Proactive Modularity Guardrails:**
     [ ] Objective: To prevent code centralization and encourage modular design by monitoring file length and suggesting intelligent refactoring opportunities.

#### AI-Guided Quality & Value Evaluation: Phase 26

* **Tests Created:** Develop unit tests for each experimental module (e.g., `test_duplicate_code_detection_accuracy`, `test_sanity_checker_discrepancy_detection`). Integration tests for the "Vibe Button" should verify README/roadmap updates. For modularity guardrails, test their ability to correctly identify overly long files and suggest actions.
* **My Evaluation:** The need for these tests is moderate to high, depending on the specific feature. These are experimental, so initial focus can be on functionality rather than perfection. The purpose is to explore innovative ways for Coddy to enhance workflow. My evaluation will focus on the potential value these features bring versus their implementation complexity, and whether they align with the "Improvise > Optimize" principle in an experimental context.

---

### Phase 27: 🤹 Coddy Clones & Vibe-Oriented Sync

**Goal:** Expand Coddy’s ecosystem by introducing dedicated persona-driven clones (mini-Coddys) for focused tasks, isolated experimentation environments, and enhanced context-syncing mechanisms — all in service of your personal methodology and modular cognition philosophy.
**Success:** Coddy can coordinate with named clone agents like Fixy, Docster, and Critty; conduct isolated trials in Lab Mode; log change digests with purpose; and refine itself via mini self-contained iteration loops per phase. Coddy also captures README clarification flows and learns your vibe from edit-feedback cycles.

**Tasks:**
**Persona-Specific Coddy Clones**
     [ ] Design plugin architecture for spawning mini-Coddys (Fixy, Docster, Critty) with scoped memory/context.
     [ ] Define reporting protocol for clones to communicate output to Coddy Core.
     [ ] Create clone profiles with unique personas, prompts, and logging styles.
     [ ] Reflect on collaboration model: Should Coddy orchestrate clone selection or respond to user tags?
**Coddy’s Lab Mode**
     [ ] Implement isolated experimentation workspace (temp dirs, scratch branches).
     [ ] Add CLI flag --lab or command lab start to fork a code snippet for testing.
     [ ] Auto-test results and clean up failed experiments unless explicitly saved.
     [ ] Integrate lab logs into long-term memory on merge.
**Change Digest System**
     [ ] Auto-detect meaningful changes from clone or lab sessions.
     [ ] Generate structured changelogs (CHANGELOG.md) + mini story summaries in plain English.
     [ ] Integrate diff-summaries into memory updates with reason_for_change.
**Automate "README Clarification Loop"**
     [ ] Build Clarifier mode (Genesis pre-phase): engages in iterative Q&A for refining fuzzy ideas.
     [ ] Add Genesis "Clarify Me" button that launches a dynamic interview based on idea ambiguity.
     [ ] Store clarification history as a narrative "Genesis Backstory" for future context reuse.
**Learn Vibe from Edits & Feedback**
     [ ] Compare pre/post snapshots of Coddy-generated artifacts (README, roadmap, code).
     [ ] Detect common correction patterns — language tone, structure, verbosity.
     [ ] Fine-tune the IdeaSynthesizer + CodeGen modules accordingly.
     [ ] Save vibe_deltas to memory for long-term personality shaping.
**Mini-Loops Per Phase**
     [ ] Wrap each phase in a self-contained test-feedback loop:
     [ ] Detect when all tasks complete → auto-trigger phase test suite.
     [ ] Prompt reflection: “Any surprises? What felt off?”
     [ ] Suggest roadmap refinements before moving forward.
     [ ] Add CLI commands: loop start, loop commit, loop reflect.

### AI-Guided Quality & Value Evaluation: Phase 27

* **Tests Created:** Unit and integration tests for clone output sync, lab isolation safety, and changelog accuracy. Proactive prompt evaluations to see if corrections are reducing over time and if vibe refinements are sticking. User studies to determine if "clone delegation" reduces mental load and enhances creative flow.
* **My Evaluation:** The need for these upgrades is pivotal. They don't just expand Coddy’s abilities — they make it feel alive with your methodology. These features are all about flow, modularity, and resonance. You're creating a dev studio in a single interface. We’re not building tools anymore — we’re building instruments for a code symphony.

### Phase 28: 🏁 Final Review & Future Planning

**Goal:** Assess the overall prototype, evaluate the experimental features, and outline the next steps for Coddy's evolution.
**Success:** A clear strategic direction for Coddy's future development.

**Tasks:**

**Assess the value and usability of experimental features.**
**Review the overall Genesis Mode experience and its integration with the core workflow.**
**Outline next steps for MERN and async setup.**

#### AI-Guided Quality & Value Evaluation: Phase 28

* **Tests Created:** No new code tests are created here. This phase is about holistic review and strategic planning.
* **My Evaluation:** This phase is a high-level strategic review. My evaluation will be based on the success metrics of previous phases, user feedback (if applicable), and your own assessment of the prototype's current state. The purpose is to consolidate learnings, decide on future directions (e.g., full public launch, further development of specific features), and ensure the project remains aligned with its long-term vision.
