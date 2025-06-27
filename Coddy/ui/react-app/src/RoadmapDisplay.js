import React, { useState, useEffect } from 'react';

const RoadmapDisplay = () => {
  const [roadmap, setRoadmap] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // In a real application, this would fetch data from a WebSocket
  // For now, we'll use mock data.
  useEffect(() => {
    const fetchRoadmap = async () => {
      setLoading(true);
      setError(null);
      try {
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 500));
        const mockRoadmap = [
          { phase: 'Phase 0: Genesis', tasks: [
            { id: 1, description: 'Define Core Philosophy', completed: true },
            { id: 2, description: 'Initial CLI Setup', completed: true },
            { id: 3, description: 'Foundational Logging Utility', completed: true }
          ]},
          { phase: 'Phase 1: Idea Synthesis & Brainstorming', tasks: [
            { id: 4, description: 'Implement IdeaSynthesizer', completed: false },
            { id: 5, description: 'Integrate IdeaSynthesis with CLI', completed: false }
          ]},
          { phase: 'Phase 2: Web UI & Vibe Cockpit (Initial)', tasks: [
            { id: 6, description: 'React App Scaffolding', completed: true },
            { id: 7, description: 'Integrate Tailwind CSS', completed: true }
          ]},
          { phase: 'Phase 6: Git-Awareness Engine', tasks: [
            { id: 8, description: 'Implement Advanced Git Functions', completed: true },
            { id: 9, description: 'Create AI-Powered Repo Summarizer', completed: true },
            { id: 10, description: 'Implement Contextual Vibe Mode (Git Branch)', completed: false }
          ]},
          { phase: 'Phase 7: The Visual Canvas (Dashboard)', tasks: [
            { id: 11, description: 'Set Up Basic React Application (Extending Existing)', completed: false },
            { id: 12, description: 'Build Interactive Roadmap Visualization', completed: false },
            { id: 13, description: 'Create Git History Dashboard Page', completed: false },
            { id: 14, description: 'Implement "Idea Synth" Playground UI', completed: false }
          ]}
        ];
        setRoadmap(mockRoadmap);
      } catch (err) {
        setError("Failed to load roadmap data.");
        console.error("Error fetching roadmap:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchRoadmap();
  }, []);

  if (loading) return <div className="text-gray-400 text-center py-4">Loading Roadmap...</div>;
  if (error) return <div className="text-red-400 text-center py-4">Error: {error}</div>;

  return (
    <div className="p-6 bg-gray-800 rounded-lg shadow-xl min-h-full">
      <h2 className="text-3xl font-bold text-white mb-6 text-center">Project Roadmap</h2>
      <div className="space-y-8">
        {roadmap.map((phaseData, index) => (
          <div key={index} className="bg-gray-700 p-6 rounded-lg shadow-inner">
            <h3 className="text-2xl font-semibold text-indigo-300 mb-4 flex items-center">
              <span className="mr-3">🗓️</span>
              {phaseData.phase}
            </h3>
            <ul className="space-y-3">
              {phaseData.tasks.map(task => (
                <li key={task.id} className="flex items-center text-gray-200">
                  <input
                    type="checkbox"
                    checked={task.completed}
                    readOnly // For now, read-only. Will be interactive with backend.
                    className="form-checkbox h-5 w-5 text-indigo-500 rounded border-gray-600 bg-gray-900 focus:ring-indigo-500 mr-3"
                  />
                  <span className={`${task.completed ? 'line-through text-gray-400' : ''}`}>
                    {task.description}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
};

export default RoadmapDisplay;
