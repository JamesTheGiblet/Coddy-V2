// C:\Users\gilbe\Documents\GitHub\Coddy_V2\Coddy\ui\react-app\src\RefactorCode.js

import React, { useState } from 'react';

// Use an environment variable for the API base URL
// In React, custom environment variables must be prefixed with REACT_APP_
// Provide a fallback for local development if the environment variable is not set.
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://127.0.0.1:8000';

const RefactorCode = () => {
    const [filePath, setFilePath] = useState('');
    const [originalCode, setOriginalCode] = useState('');
    const [instructions, setInstructions] = useState('');
    const [refactoredCode, setRefactoredCode] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleRefactor = async () => {
        setLoading(true);
        setError(null);
        setRefactoredCode('');

        try {
            const response = await fetch(`${API_BASE_URL}/api/code/refactor`, { // MODIFIED: Using API_BASE_URL
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    file_path: filePath,
                    original_code: originalCode,
                    instructions: instructions,
                    user_profile: {} // Placeholder for actual user profile data
                }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to refactor code.');
            }

            const data = await response.json();
            setRefactoredCode(data.refactored_code);
        } catch (err) {
            console.error('Refactoring error:', err);
            setError(err.message || 'An unknown error occurred during refactoring.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="p-6 bg-gray-800 rounded-lg shadow-xl flex flex-col h-full">
            <h2 className="text-3xl font-bold text-indigo-400 mb-6">Code Refactoring</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 flex-1">
                {/* Input Section */}
                <div className="flex flex-col space-y-4">
                    <div>
                        <label htmlFor="filePath" className="block text-gray-300 text-sm font-bold mb-2">
                            File Path:
                        </label>
                        <input
                            type="text"
                            id="filePath"
                            className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline bg-gray-700 border-gray-600 text-white"
                            value={filePath}
                            onChange={(e) => setFilePath(e.target.value)}
                            placeholder="e.g., my_module/my_file.py"
                        />
                    </div>
                    <div>
                        <label htmlFor="originalCode" className="block text-gray-300 text-sm font-bold mb-2">
                            Original Code:
                        </label>
                        <textarea
                            id="originalCode"
                            className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline bg-gray-700 border-gray-600 text-white h-40 resize-y"
                            value={originalCode}
                            onChange={(e) => setOriginalCode(e.target.value)}
                            placeholder="Paste the code to refactor here..."
                        ></textarea>
                    </div>
                    <div>
                        <label htmlFor="instructions" className="block text-gray-300 text-sm font-bold mb-2">
                            Refactoring Instructions:
                        </label>
                        <textarea
                            id="instructions"
                            className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline bg-gray-700 border-gray-600 text-white h-32 resize-y"
                            value={instructions}
                            onChange={(e) => setInstructions(e.target.value)}
                            placeholder="e.g., Make this code more Pythonic, improve readability, optimize performance..."
                        ></textarea>
                    </div>
                    <button
                        onClick={handleRefactor}
                        className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline transition duration-200 ease-in-out transform hover:scale-105"
                        disabled={loading}
                    >
                        {loading ? 'Refactoring...' : 'Refactor Code'}
                    </button>
                    {error && <p className="text-red-500 text-sm mt-2">{error}</p>}
                </div>

                {/* Output Section */}
                <div className="flex flex-col">
                    <h3 className="text-xl font-bold text-gray-300 mb-3">Refactored Code:</h3>
                    <div className="bg-gray-700 p-4 rounded-lg flex-1 overflow-auto border border-gray-600">
                        <pre className="text-gray-200 whitespace-pre-wrap font-mono text-sm">
                            {refactoredCode || (loading ? 'Awaiting refactored code...' : 'Refactored code will appear here.')}
                        </pre>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default RefactorCode;