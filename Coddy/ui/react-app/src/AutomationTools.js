import React, { useState } from 'react';

const AutomationTools = () => {
    const [changelogOutput, setChangelogOutput] = useState('');
    const [stubOutput, setStubOutput] = useState('');
    const [loadingChangelog, setLoadingChangelog] = useState(false);
    const [loadingStub, setLoadingStub] = useState(false);
    const [error, setError] = useState(null);

    const runAutomation = async (endpoint, setLoadingState, setOutputState) => {
        setLoadingState(true);
        setError(null);
        setOutputState('');

        try {
            const response = await fetch(`http://127.0.0.1:8000/api/automation/${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ /* No specific body needed for these simple triggers yet */ }),
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

    return (
        <div className="p-6 bg-gray-800 rounded-lg shadow-xl flex flex-col h-full">
            <h2 className="text-3xl font-bold text-indigo-400 mb-6">Automation Tools</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 flex-1">
                {/* Changelog Generator */}
                <div className="flex flex-col bg-gray-700 p-4 rounded-lg border border-gray-600">
                    <h3 className="text-xl font-bold text-gray-300 mb-3">Changelog Generator</h3>
                    <button
                        onClick={() => runAutomation('generate-changelog', setLoadingChangelog, setChangelogOutput)}
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
                    <button
                        onClick={() => runAutomation('generate-todo-stubs', setLoadingStub, setStubOutput)}
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
