import React, { useState, useEffect } from 'react';

const GitHistoryDisplay = () => {
  const [commits, setCommits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // In a real application, this would fetch data from a WebSocket
  // For now, we'll use mock data.
  useEffect(() => {
    const fetchGitHistory = async () => {
      setLoading(true);
      setError(null);
      try {
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 700));
        const mockCommits = [
          { hash: 'a1b2c3d', author: 'James Giblet', date: '2025-06-26', message: 'feat: Implement GitAnalyzer core functions' },
          { hash: 'e4f5g6h', author: 'James Giblet', date: '2025-06-25', message: 'refactor: Improve CLI prompt with dynamic Git branch' },
          { hash: 'i7j8k9l', author: 'Coddy AI', date: '2025-06-24', message: 'chore: Update project dependencies for React UI' },
          { hash: 'm0n1o2p', author: 'James Giblet', date: '2025-06-23', message: 'fix: Resolve websocket connection stability issues' },
          { hash: 'q3r4s5t', author: 'Coddy AI', date: '2025-06-22', message: 'docs: Initial roadmap structure added to README' },
        ];
        setCommits(mockCommits);
      } catch (err) {
        setError("Failed to load Git history.");
        console.error("Error fetching Git history:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchGitHistory();
  }, []);

  if (loading) return <div className="text-gray-400 text-center py-4">Loading Git History...</div>;
  if (error) return <div className="text-red-400 text-center py-4">Error: {error}</div>;

  return (
    <div className="p-6 bg-gray-800 rounded-lg shadow-xl min-h-full">
      <h2 className="text-3xl font-bold text-white mb-6 text-center">Git Commit History</h2>
      <div className="space-y-4">
        {commits.map((commit) => (
          // Using commit.hash as key for better list performance and stability
          <div key={commit.hash} className="bg-gray-700 p-4 rounded-lg shadow-inner flex items-start">
            <div className="mr-4 text-indigo-400 text-xl">
              {/* Font Awesome icon for branch, added aria-hidden for accessibility */}
              <i className="fas fa-code-branch" aria-hidden="true"></i>
            </div>
            <div className="flex-1">
              <p className="text-gray-100 font-semibold text-lg">{commit.message}</p>
              <p className="text-gray-300 text-sm mt-1">
                <span className="font-mono bg-gray-600 px-2 py-0.5 rounded-md text-xs mr-2">
                  {commit.hash.substring(0, 7)}
                </span>
                <span className="text-gray-400">by {commit.author} on {commit.date}</span>
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default GitHistoryDisplay;
