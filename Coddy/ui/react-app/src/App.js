// Coddy/ui/react-app/src/App.js
import React, { useState, useEffect, useRef } from 'react';
// For icons, using lucide-react as specified for web page icons
// Make sure to install: npm install lucide-react
// Corrected import: 'Memory' icon is not directly exported, using 'Brain' instead.
import { Terminal, Lightbulb, Brain, GitBranch, MessageSquareText, CheckCircle, Clock } from 'lucide-react';
import TabButton from './TabButton';

// Base URL for your Express backend
const API_BASE_URL = 'http://localhost:3000';
// WebSocket URL for the Python WebSocket server
const WEBSOCKET_URL = 'ws://localhost:8080'; // Matches Python websocket_server.py

// Main App Component
const App = () => {
  const [activeTab, setActiveTab] = useState('terminal'); // 'terminal', 'roadmap', 'memory', 'patterns', 'ideas'
  const [terminalOutput, setTerminalOutput] = useState([]);
  const [commandInput, setCommandInput] = useState('');
  const [roadmapData, setRoadmapData] = useState(null);
  const [memoryData, setMemoryData] = useState([]);
  const [patternData, setPatternData] = useState([]);
  const [ideaGenerationInput, setIdeaGenerationInput] = useState('');
  const [weirdMode, setWeirdMode] = useState(false);
  const [constraints, setConstraints] = useState('');
  const [numSolutions, setNumSolutions] = useState(1);
  const [generatedIdeas, setGeneratedIdeas] = useState([]);
  const [isLoadingIdeas, setIsLoadingIdeas] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');

  const terminalOutputRef = useRef(null); // Ref for auto-scrolling terminal
  const wsRef = useRef(null); // Ref to hold the WebSocket instance

  // --- WebSocket Logic ---
  useEffect(() => {
    const connectWebSocket = () => {
      console.log("Attempting to connect to WebSocket:", WEBSOCKET_URL);
      const ws = new WebSocket(WEBSOCKET_URL);

      ws.onopen = () => {
        console.log("WebSocket connected.");
        wsRef.current = ws; // Store WebSocket instance in ref
        setTerminalOutput(prev => [...prev, { type: 'info', text: 'Connected to Coddy real-time logstream.' }]);
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          // Handle different types of messages from Python CLI
          // 'command' type: the user's input command (e.g., Coddy> exec dir)
          // 'response' type: output from executed commands (STDOUT, STDERR, etc.)
          // 'info', 'success', 'error', 'warning', 'critical': various log levels/messages
          // 'status' type: specific status updates meant for the UI status bar
          setTerminalOutput(prev => [...prev, { type: message.type || 'log', text: message.text || event.data }]);
          // If a status message comes through, update UI status
          if (message.type === 'status') {
              setStatusMessage(message.text);
          }
        } catch (e) {
          // If message is not JSON, display as raw log
          setTerminalOutput(prev => [...prev, { type: 'log', text: event.data }]);
        }
      };

      ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        setTerminalOutput(prev => [...prev, { type: 'error', text: 'WebSocket error occurred. Retrying in 5s...' }]);
        setStatusMessage('WebSocket disconnected. Retrying...');
        if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
            ws.close(); // Ensure connection is closed on error
        }
      };

      ws.onclose = (event) => {
        console.log("WebSocket disconnected:", event.code, event.reason);
        setTerminalOutput(prev => [...prev, { type: 'info', text: 'Disconnected from Coddy real-time logstream. Attempting to reconnect...' }]);
        setStatusMessage('WebSocket disconnected.');
        // Attempt to reconnect after a delay
        setTimeout(connectWebSocket, 5000);
      };
    };

    connectWebSocket(); // Initial connection attempt

    // Cleanup function: close WebSocket when component unmounts
    return () => {
      if (wsRef.current) {
        wsRef.current.onclose = null; // Prevent reconnect attempts on intended close
        wsRef.current.close();
        console.log("WebSocket cleanup: connection closed.");
      }
    };
  }, []); // Run once on component mount

  // Auto-scroll terminal output to bottom
  useEffect(() => {
    if (terminalOutputRef.current) {
      terminalOutputRef.current.scrollTop = terminalOutputRef.current.scrollHeight;
    }
  }, [terminalOutput]);


  // --- Fetch Data from Backend APIs ---
  const fetchData = async (endpoint, setState, errorMsg) => {
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setState(data.data);
      setStatusMessage(''); // Clear any previous status messages
    } catch (error) {
      console.error(errorMsg, error);
      setStatusMessage(`Error: ${errorMsg}. Check console for details.`);
    }
  };

  // Fetch all data when component mounts or activeTab changes
  useEffect(() => {
    if (activeTab === 'roadmap' && !roadmapData) {
      fetchData('/api/roadmap', setRoadmapData, 'Failed to fetch roadmap data.');
    } else if (activeTab === 'memory' && memoryData.length === 0) {
      fetchData('/api/memory', setMemoryData, 'Failed to fetch memory data.');
    } else if (activeTab === 'patterns' && patternData.length === 0) {
      fetchData('/api/pattern', setPatternData, 'Failed to fetch pattern data.');
    }
  }, [activeTab, roadmapData, memoryData, patternData]);


  // --- Terminal Logic ---
  const handleCommandSubmit = async (e) => {
    e.preventDefault();
    if (!commandInput.trim()) return;

    const command = commandInput.trim();
    // Do NOT update terminalOutput directly here for commands,
    // as it will be streamed back from Python CLI via WebSocket.
    setCommandInput('');
    setStatusMessage('Executing command...');

    // Simple command parsing and API interaction (similar to Python CLI)
    let apiEndpoint = '';
    let method = 'GET';
    let body = null;
    let successMessage = '';
    let errorMessage = ''; 

    try {
        const parts = command.split(' ');
        const mainCommand = parts[0].toLowerCase();
        

        // Commands like read, write, list, exec, show context, checkpoint load
        // are expected to be processed by the Python CLI and streamed via WebSocket.
        // We will send the raw command via WebSocket to the Python CLI.
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) { // Check if WebSocket is open using wsRef
            // Send the command directly to the WebSocket server for Python CLI to pick up
            // A more sophisticated system would have a dedicated command channel or endpoint
            wsRef.current.send(JSON.stringify({ type: 'cli_input', command: command }));
            // The response (including the echoed command) will come via the onmessage handler
            // For now, we manually echo the command here to give immediate feedback.
            setTerminalOutput(prev => [...prev, { type: 'command', text: `Coddy> ${command}` }]);
            setStatusMessage(`Command sent to Python CLI for execution.`);
            // For checkpoint save, we still handle it directly to update backend from UI for now
            // as this is an API call, not a CLI execution command.
            if (mainCommand === 'checkpoint' && parts[1] && parts[1].toLowerCase() === 'save') {
                const checkpointName = parts[2];
                const message = parts.slice(3).join(' ').replace(/"/g, '').trim(); // Remove quotes
                if (!checkpointName) {
                    setTerminalOutput(prev => [...prev, { type: 'error', text: 'Usage: checkpoint save <name> [message]' }]);
                    setStatusMessage('Invalid checkpoint command.');
                    return;
                }
                apiEndpoint = '/api/memory';
                method = 'POST';
                body = {
                    content: JSON.stringify({ type: 'checkpoint', name: checkpointName, message: message || `Checkpoint ${checkpointName} saved.` }),
                    tags: ['checkpoint', checkpointName],
                    session_id: 'ui_session', // Static UI session ID for now
                    user_id: 'ui_user' // Static UI user ID for now
                };
                successMessage = `Checkpoint '${checkpointName}' saved via UI API.`; // Clarify it's via UI API
                errorMessage = `Failed to save checkpoint '${checkpointName}' via UI API.`;
                
                // Execute API call if endpoint defined (only for checkpoint save here)
                const response = await fetch(`${API_BASE_URL}${apiEndpoint}`, {
                    method: method,
                    headers: { 'Content-Type': 'application/json' },
                    body: body ? JSON.stringify(body) : null,
                });

                if (!response.ok) {
                    const errorText = await response.text();
                    throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
                }

                await response.json(); // Consume the response body
                setTerminalOutput(prev => [...prev, { type: 'success', text: successMessage }]);
                setStatusMessage('Command executed successfully.');
                fetchData('/api/memory', setMemoryData, `Failed to refresh memory data.`);
            }
            return; // Exit after sending via WS or handling checkpoint save
        } else {
            // If WebSocket is not connected, fall back to simulated message
            setTerminalOutput(prev => [...prev, { type: 'error', text: 'WebSocket connection not active. Cannot send command to Python CLI.' }]);
            setStatusMessage('WS not connected.');
            return;
        }

    } catch (error) {
        console.error("CLI Command Execution Error:", error);
        setTerminalOutput(prev => [...prev, { type: 'error', text: `Error: ${errorMessage || error.message}` }]);
        setStatusMessage(`Command failed: ${error.message}`);
    }
  };

  // --- Idea Generation Logic ---
  const handleGenerateIdeas = async () => {
    setIsLoadingIdeas(true);
    setGeneratedIdeas([]); // Clear previous ideas
    setStatusMessage('Generating ideas...');

    const payload = {
      base_idea: ideaGenerationInput,
      weird_mode: weirdMode,
      constraints: constraints.split(',').map(c => c.trim()).filter(c => c),
      num_solutions: numSolutions
    };

    try {
      const API_KEY_FOR_GEMINI = ''; // Canvas will inject the API key at runtime

      if (!API_KEY_FOR_GEMINI) {
        setStatusMessage("Error: Gemini API Key is not configured for client-side use.");
        setIsLoadingIdeas(false);
        return;
      }
      
      const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${API_KEY_FOR_GEMINI}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            contents: [{"role": "user", "parts": [{"text": generateIdeaPrompt(payload)}]}],
            generationConfig: {
                temperature: weirdMode ? 0.9 : 0.7,
                topP: 0.95,
                responseMimeType: "text/plain"
            }
          })
      });

      if (!response.ok) {
          const errorBody = await response.json();
          throw new Error(`HTTP error! status: ${response.status}. Details: ${JSON.stringify(errorBody)}`);
      }

      const result = await response.json();
      let rawIdea = '';
      if (result.candidates && result.candidates[0].content && result.candidates[0].content.parts) {
          rawIdea = result.candidates[0].content.parts[0].text;
      } else {
          throw new Error("Invalid response structure from LLM.");
      }

      // Parse multiple ideas
      let parsedIdeas = [];
      if (numSolutions > 1) {
          const itemRegex = /^\s*\d+\.\s*(.*?)(?=\n\s*\d+\.\s*|$)/gm; // Global multiline for all matches
          parsedIdeas = Array.from(rawIdea.matchAll(itemRegex)).map(match => match[1].trim());
          // Fallback if numbered list not found
          if (parsedIdeas.length === 0) {
             parsedIdeas = rawIdea.split('\n\n').filter(line => line.trim());
          }
          parsedIdeas = parsedIdeas.slice(0, numSolutions); // Limit to requested count
      } else {
          parsedIdeas.push(rawIdea.trim());
      }

      setGeneratedIdeas(parsedIdeas);
      setStatusMessage('Ideas generated successfully!');
    } catch (error) {
      console.error("Idea Generation Error:", error);
      setGeneratedIdeas([`Failed to generate ideas: ${error.message}`]);
      setStatusMessage(`Error generating ideas: ${error.message}`);
    } finally {
      setIsLoadingIdeas(false);
    }
  };

  // Helper to generate the prompt string (mimicking Python IdeaSynthesizer)
  const generateIdeaPrompt = (payload) => {
    let prompt_template = `Generate an idea for: '${payload.base_idea}'.\n`;
    if (payload.constraints && payload.constraints.length > 0) {
        prompt_template += `Consider the following constraints: ${payload.constraints.join(", ")}.\n`;
    }
    if (payload.weird_mode) {
        prompt_template += 'Make it exceptionally creative, unconventional, and push the boundaries of typical solutions. Embrace chaotic and surprising elements.';
    } else {
        prompt_template += 'Provide a practical and innovative solution.';
    }
    if (payload.num_solutions > 1) {
        prompt_template += `\nGenerate ${payload.num_solutions} distinct solutions, presented as a numbered list (1., 2., 3., etc.) without any introductory or concluding remarks, just the list items.`;
    }
    return prompt_template;
  };


  // --- UI Layout ---
  return (
    <div className="min-h-screen flex flex-col bg-gray-900 text-gray-100 font-inter rounded-lg shadow-lg overflow-hidden">
      {/* Header */}
      <header className="flex items-center justify-between p-4 bg-gray-800 border-b border-gray-700 rounded-t-lg">
        <h1 className="text-2xl font-bold text-indigo-400">Coddy V2 UI</h1>
        {statusMessage && (
            <div className="px-3 py-1 text-sm bg-blue-700 text-blue-100 rounded-full animate-pulse">
                {statusMessage}
            </div>
        )}
      </header>

      {/* Main Content Area */}
      <main className="flex flex-1">
        {/* Sidebar Navigation */}
        <nav className="w-20 bg-gray-800 p-2 border-r border-gray-700 flex flex-col items-center space-y-4 rounded-bl-lg">
          <TabButton icon={<Terminal size={24} />} label="Terminal" active={activeTab === 'terminal'} onClick={() => setActiveTab('terminal')} />
          <TabButton icon={<Lightbulb size={24} />} label="Ideas" active={activeTab === 'ideas'} onClick={() => setActiveTab('ideas')} />
          <TabButton icon={<GitBranch size={24} />} label="Roadmap" active={activeTab === 'roadmap'} onClick={() => setActiveTab('roadmap')} />
          <TabButton icon={<Brain size={24} />} label="Memory" active={activeTab === 'memory'} onClick={() => setActiveTab('memory')} />
          <TabButton icon={<MessageSquareText size={24} />} label="Patterns" active={activeTab === 'patterns'} onClick={() => setActiveTab('patterns')} />
        </nav>

        {/* Content Panel */}
        <section className="flex-1 p-6 overflow-auto">
          {/* Terminal Tab */}
          {activeTab === 'terminal' && (
            <div className="flex flex-col h-full">
              <div ref={terminalOutputRef} className="flex-1 bg-gray-950 p-4 rounded-lg border border-gray-700 overflow-y-auto text-sm leading-relaxed mb-4">
                {terminalOutput.map((line, index) => (
                  <div key={index} className={
                    line.type === 'command' ? 'text-green-400 font-mono' :
                    line.type === 'error' ? 'text-red-400' :
                    line.type === 'success' ? 'text-blue-400' :
                    'text-gray-200'
                  }>
                    {line.text}
                  </div>
                ))}
              </div>
              <form onSubmit={handleCommandSubmit} className="flex space-x-2">
                <input
                  type="text"
                  value={commandInput}
                  onChange={(e) => setCommandInput(e.target.value)}
                  placeholder="Type Coddy command..."
                  className="flex-1 p-3 bg-gray-700 border border-gray-600 rounded-md text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
                <button
                  type="submit"
                  className="px-5 py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-md shadow-lg transition duration-200 ease-in-out transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  Run
                </button>
              </form>
            </div>
          )}

          {/* Ideas Tab */}
          {activeTab === 'ideas' && (
            <div className="flex flex-col space-y-4">
              <h2 className="text-xl font-semibold text-indigo-300 mb-2">Idea Synthesizer</h2>
              <textarea
                className="w-full p-3 bg-gray-700 border border-gray-600 rounded-md text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500 h-24"
                placeholder="Enter your base idea (e.g., 'a new productivity app')..."
                value={ideaGenerationInput}
                onChange={(e) => setIdeaGenerationInput(e.target.value)}
              ></textarea>
              <div className="flex items-center space-x-4">
                <label className="flex items-center space-x-2 text-gray-300">
                  <input
                    type="checkbox"
                    checked={weirdMode}
                    onChange={(e) => setWeirdMode(e.target.checked)}
                    className="form-checkbox h-5 w-5 text-indigo-600 rounded"
                  />
                  <span>Weird Mode</span>
                </label>
                <input
                  type="number"
                  min="1"
                  max="5"
                  value={numSolutions}
                  onChange={(e) => setNumSolutions(parseInt(e.target.value))}
                  className="w-20 p-2 bg-gray-700 border border-gray-600 rounded-md text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
                <span className="text-gray-300">Solutions</span>
              </div>
              <input
                type="text"
                className="w-full p-3 bg-gray-700 border border-gray-600 rounded-md text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="Constraints (comma-separated, e.g., 'must use AI, must be visual')"
                value={constraints}
                onChange={(e) => setConstraints(e.target.value)}
              />
              <button
                onClick={handleGenerateIdeas}
                disabled={isLoadingIdeas}
                className="px-5 py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-md shadow-lg transition duration-200 ease-in-out transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoadingIdeas ? 'Generating...' : 'Generate Ideas'}
              </button>

              {generatedIdeas.length > 0 && (
                <div className="bg-gray-950 p-4 rounded-lg border border-gray-700 overflow-y-auto text-sm leading-relaxed mt-4">
                  <h3 className="text-lg font-semibold text-blue-300 mb-2">Generated Ideas:</h3>
                  {generatedIdeas.map((idea, index) => (
                    <div key={index} className="mb-4 pb-4 border-b border-gray-800 last:border-b-0">
                      <p className="whitespace-pre-wrap text-gray-200">{idea}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Roadmap Tab */}
          {activeTab === 'roadmap' && (
            <div>
              <h2 className="text-xl font-semibold text-indigo-300 mb-4">Roadmap Overview</h2>
              {roadmapData ? (
                roadmapData.phases && roadmapData.phases.length > 0 ? (
                  roadmapData.phases.map(phase => (
                    <div key={phase.number} className="bg-gray-800 p-4 rounded-lg mb-4 border border-gray-700">
                      <h3 className="text-lg font-bold text-blue-400 mb-2">
                        Phase {phase.number}: {phase.title}
                      </h3>
                      <p className="text-gray-300 text-sm mb-2">
                        <span className="font-semibold">Goal:</span> {phase.goal}
                      </p>
                      <p className="text-gray-300 text-sm mb-2">
                        <span className="font-semibold">Success:</span> {phase.success}
                      </p>
                      {phase.tasks && phase.tasks.length > 0 && (
                        <div className="mt-2">
                          <h4 className="font-semibold">Tasks:</h4>
                          <ul className="list-none pl-0">
                            {phase.tasks.map(task => (
                              <li key={task.id} className="flex items-center text-gray-200 text-sm mt-1">
                                {task.status === 'completed' ? <CheckCircle size={16} className="text-green-500 mr-2" /> : <Clock size={16} className="text-yellow-500 mr-2" />}
                                {task.description} <span className="text-gray-500 ml-2">({task.status})</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {phase.evaluation && (
                        <div className="mt-2 text-sm text-gray-400">
                          <h4 className="font-semibold">Evaluation:</h4>
                          <p><strong>Tests Created:</strong> {phase.evaluation.tests_created}</p>
                          <p><strong>My Evaluation:</strong> {phase.evaluation.my_evaluation}</p>
                        </div>
                      )}
                    </div>
                  ))
                ) : (
                  <p className="text-gray-400">No roadmap phases found.</p>
                )
              ) : (
                <p className="text-gray-400">Loading roadmap...</p>
              )}
            </div>
          )}

          {/* Memory Logs Tab */}
          {activeTab === 'memory' && (
            <div>
              <h2 className="text-xl font-semibold text-indigo-300 mb-4">Memory Logs</h2>
              {memoryData && memoryData.length > 0 ? (
                memoryData.map((mem, index) => (
                  <div key={index} className="bg-gray-800 p-4 rounded-lg mb-3 border border-gray-700 text-sm">
                    <p className="text-gray-400"><span className="font-semibold">ID:</span> {mem._id}</p>
                    <p className="text-gray-300"><span className="font-semibold">Timestamp:</span> {new Date(mem.timestamp).toLocaleString()}</p>
                    <p className="text-gray-300"><span className="font-semibold">Content:</span> <pre className="whitespace-pre-wrap break-words font-mono text-gray-200">{JSON.stringify(mem.content, null, 2)}</pre></p>
                    <p className="text-gray-300"><span className="font-semibold">Tags:</span> {mem.tags ? mem.tags.join(', ') : 'None'}</p>
                    <p className="text-gray-400"><span className="font-semibold">Session ID:</span> {mem.session_id || 'N/A'}</p>
                    <p className="text-gray-400"><span className="font-semibold">User ID:</span> {mem.user_id || 'N/A'}</p>
                  </div>
                ))
              ) : (
                <p className="text-gray-400">No memory logs found. Perform some commands or actions.</p>
              )}
            </div>
          )}

          {/* Patterns Tab */}
          {activeTab === 'patterns' && (
            <div>
              <h2 className="text-xl font-semibold text-indigo-300 mb-4">Detected Patterns</h2>
              {patternData && patternData.length > 0 ? (
                patternData.map((pattern, index) => (
                  <div key={index} className="bg-gray-800 p-4 rounded-lg mb-3 border border-gray-700 text-sm">
                    <p className="text-gray-300"><span className="font-semibold">Type:</span> {pattern.pattern_type}</p>
                    <p className="text-gray-300"><span className="font-semibold">Description:</span> {pattern.description}</p>
                    <p className="text-gray-300"><span className="font-semibold">Data:</span> <pre className="whitespace-pre-wrap break-words font-mono text-gray-200">{JSON.stringify(pattern.data, null, 2)}</pre></p>
                    <p className="text-gray-400"><span className="font-semibold">Timestamp:</span> {new Date(pattern.timestamp).toLocaleString()}</p>
                    <p className="text-gray-400"><span className="font-semibold">User ID:</span> {pattern.user_id || 'N/A'}</p>
                  </div>
                ))
              ) : (
                <p className="text-gray-400">No patterns detected or stored yet. Use the CLI to build up activity!</p>
              )}
            </div>
          )}
        </section>
      </main>

      {/* Footer */}
      <footer className="p-3 bg-gray-800 border-t border-gray-700 text-center text-gray-500 text-xs rounded-b-lg">
        Coddy V2 UI - Beta Tester Readiness Point
      </footer>
    </div>
  );
};

export default App;