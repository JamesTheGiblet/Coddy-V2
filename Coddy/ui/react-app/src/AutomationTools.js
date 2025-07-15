// C:\Users\gilbe\Documents\GitHub\Coddy_V2\Coddy\ui\react-app\src\AutomationTools.js

import React, { useState } from 'react';

// Use an environment variable for the API base URL
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://127.0.0.1:8000'; // MODIFIED: Use env var

const AutomationTools = () => {
    const [changelogOutput, setChangelogOutput] = useState('');
    const [stubOutput, setStubOutput] = useState('');
    const [loadingChangelog, setLoadingChangelog] = useState(false);
    const [loadingStub, setLoadingStub] = useState(false);
    const [error, setError] = useState(null);

    // NEW: State for input fields
    const [changelogOutputFile, setChangelogOutputFile] = useState('CHANGELOG.md');
    const [todoStubScanPath, setTodoStubScanPath] = useState('./Coddy/core'); // Default to core directory
    const [todoStubOutputFile, setTodoStubOutputFile] = useState('TODO_STUBS.md');

    // MODIFIED: runAutomation to accept data for the body
    const runAutomation = async (endpoint, setLoadingState, setOutputState, payloadData = {}) => {
        setLoadingState(true);
        setError(null);
        setOutputState('');

        try {
            const response = await fetch(`${API_BASE_URL}/api/automation/${endpoint}`, { // MODIFIED: Use API_BASE_URL
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payloadData), // MODIFIED: Send dynamic payloadData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `Failed to run ${endpoint}.`);
            }

            const data = await response.json();
            setOutputState(data.message || JSON.stringify(data, null, 2));
        } catch (err) {
            console.error(`Automation error for ${endpoint}:`, err);
            setError(err.message || `An unknown error occurred during ${endpoint}.`);
        } finally {
            setLoadingState(false);
        }
    };

    const handleGenerateChangelog = () => {
        const payload = { output_file: changelogOutputFile };
        runAutomation('generate-changelog', setLoadingChangelog, setChangelogOutput, payload);
    };

    const handleGenerateTodoStubs = () => {
        const payload = { 
            scan_path: todoStubScanPath,
            output_file: todoStubOutputFile
        };
        runAutomation('generate-todo-stubs', setLoadingStub, setStubOutput, payload);
    };


    return (
        <div className="p-6 bg-gray-800 rounded-lg shadow-xl flex flex-col h-full">
            <h2 className="text-3xl font-bold text-indigo-400 mb-6">Automation Tools</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 flex-1">
                {/* Changelog Generator */}
                <div className="flex flex-col bg-gray-700 p-4 rounded-lg border border-gray-600">
                    <h3 className="text-xl font-bold text-gray-300 mb-3">Changelog Generator</h3>
                    {/* NEW: Input for Changelog Output File */}
                    <div className="mb-4">
                        <label htmlFor="changelogOutputFile" className="block text-gray-300 text-sm font-bold mb-2">
                            Output File:
                        </label>
                        <input
                            type="text"
                            id="changelogOutputFile"
                            className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline bg-gray-600 border-gray-500 text-white"
                            value={changelogOutputFile}
                            onChange={(e) => setChangelogOutputFile(e.target.value)}
                            placeholder="e.g., CHANGELOG.md"
                        />
                    </div>
                    <button
                        onClick={handleGenerateChangelog} // MODIFIED: Use new handler
                        className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline transition duration-200 ease-in-out transform hover:scale-105"
                        disabled={loadingChangelog}
                    >
                        {loadingChangelog ? 'Generating...' : 'Generate Changelog'}
                    </button>
                    <div className="mt-4 bg-gray-800 p-3 rounded-lg overflow-auto h-40 text-sm">
                        <pre className="text-gray-200 whitespace-pre-wrap font-mono">
                            {changelogOutput || (loadingChangelog ? 'Awaiting changelog...' : 'Changelog output will appear here.')}
                        </pre>
                    </div>
                </div>

                {/* TODO Stub Generator */}
                <div className="flex flex-col bg-gray-700 p-4 rounded-lg border border-gray-600">
                    <h3 className="text-xl font-bold text-gray-300 mb-3">TODO Stub Generator</h3>
                    {/* NEW: Input for TODO Stub Scan Path */}
                    <div className="mb-2">
                        <label htmlFor="todoStubScanPath" className="block text-gray-300 text-sm font-bold mb-2">
                            Scan Path (Directory or File):
                        </label>
                        <input
                            type="text"
                            id="todoStubScanPath"
                            className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline bg-gray-600 border-gray-500 text-white"
                            value={todoStubScanPath}
                            onChange={(e) => setTodoStubScanPath(e.target.value)}
                            placeholder="e.g., ./src/my_module or ./src/my_file.py"
                        />
                    </div>
                    {/* NEW: Input for TODO Stub Output File */}
                    <div className="mb-4">
                        <label htmlFor="todoStubOutputFile" className="block text-gray-300 text-sm font-bold mb-2">
                            Output File:
                        </label>
                        <input
                            type="text"
                            id="todoStubOutputFile"
                            className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline bg-gray-600 border-gray-500 text-white"
                            value={todoStubOutputFile}
                            onChange={(e) => setTodoStubOutputFile(e.target.value)}
                            placeholder="e.g., TODO_STUBS.md"
                        />
                    </div>
                    <button
                        onClick={handleGenerateTodoStubs} // MODIFIED: Use new handler
                        className="bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline transition duration-200 ease-in-out transform hover:scale-105"
                        disabled={loadingStub}
                    >
                        {loadingStub ? 'Generating...' : 'Generate TODO Stubs'}
                    </button>
                    <div className="mt-4 bg-gray-800 p-3 rounded-lg overflow-auto h-40 text-sm">
                        <pre className="text-gray-200 whitespace-pre-wrap font-mono">
                            {stubOutput || (loadingStub ? 'Awaiting TODO stubs...' : 'TODO stub output will appear here.')}
                        </pre>
                    </div>
                </div>
            </div>
            {error && <p className="text-red-500 text-sm mt-4 text-center col-span-2">{error}</p>}
        </div>
    );
};

export default AutomationTools;