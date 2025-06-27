import React, { useState } from 'react';

export default function IdeaSynthPlayground() {
  const [baseIdea, setBaseIdea] = useState('');
  const [constraints, setConstraints] = useState('');
  const [weirdMode, setWeirdMode] = useState(false);
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setResults([]);
    setError(null);

    try {
      const res = await fetch('/api/idea-synth', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ idea: baseIdea, constraints, weirdMode }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Unknown error');
      setResults(data.ideas || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="p-6 bg-gray-800 rounded-lg shadow-xl min-h-full">
      <h2 className="text-3xl font-bold text-white mb-6 text-center">
        <i className="fas fa-lightbulb mr-3"></i>Idea Synthesizer Playground
      </h2>
      <form onSubmit={handleSubmit} className="space-y-6 max-w-2xl mx-auto">
        <div>
          <label htmlFor="baseIdea" className="block text-sm font-medium text-gray-300 mb-1">Base Idea or Problem</label>
          <input
            id="baseIdea"
            type="text"
            value={baseIdea}
            onChange={(e) => setBaseIdea(e.target.value)}
            className="mt-1 block w-full bg-gray-700 border-gray-600 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm text-white p-3"
            placeholder="A new way to test React apps..."
            required
          />
        </div>
        <div>
          <label htmlFor="constraints" className="block text-sm font-medium text-gray-300 mb-1">Constraints (comma-separated)</label>
          <input
            id="constraints"
            type="text"
            value={constraints}
            onChange={(e) => setConstraints(e.target.value)}
            className="mt-1 block w-full bg-gray-700 border-gray-600 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm text-white p-3"
            placeholder="must be visual, must use AI..."
          />
        </div>
        <div className="flex items-start">
          <div className="flex items-center h-5">
            <input
              id="weirdMode"
              type="checkbox"
              checked={weirdMode}
              onChange={(e) => setWeirdMode(e.target.checked)}
              className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 rounded"
            />
          </div>
          <div className="ml-3 text-sm">
            <label htmlFor="weirdMode" className="font-medium text-gray-300">Weird Mode</label>
            <p className="text-gray-500">Embrace chaotic and surprising elements.</p>
          </div>
        </div>
        <div>
          <button
            type="submit"
            disabled={isLoading}
            className="w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-gray-500 transition-colors"
          >
            {isLoading ? (
              <><i className="fas fa-spinner fa-spin mr-2"></i>Generating...</>
            ) : (
              'Synthesize Ideas'
            )}
          </button>
        </div>
      </form>

      <div className="mt-8 max-w-2xl mx-auto">
        {error && <div className="mt-2 text-red-400 bg-red-900/50 p-3 rounded-md">{error}</div>}
        {results.length > 0 && (
          <div>
            <h3 className="text-xl font-semibold text-gray-200">Results:</h3>
            <ul className="mt-4 space-y-3 bg-gray-900/50 p-4 rounded-md border border-gray-700">
              {results.map((r, i) => (
                <li key={i} className="text-gray-300 p-2 border-b border-gray-700 last:border-b-0">{r}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
