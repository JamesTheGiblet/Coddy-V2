// Coddy/ui/react-app/src/App.js
import React, { useState } from 'react';
import TabButton from './TabButton';
import RoadmapDisplay from './RoadmapDisplay';
import GitHistoryDisplay from './GitHistoryDisplay';
import IdeaSynthPlayground from './components/IdeaSynthPlayground';

function App() {
  const [activeTab, setActiveTab] = useState('roadmap'); // Default active tab

  // Function to render content based on the active tab
  const renderContent = () => {
    switch (activeTab) {
      case 'roadmap':
        return <RoadmapDisplay />;
      case 'git-history':
        return <GitHistoryDisplay />;
      case 'idea-synth':
        return <IdeaSynthPlayground />;
      default:
        return <RoadmapDisplay />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 antialiased flex flex-col">
      {/* Header/Navbar */}
      <header className="bg-gray-800 shadow-lg py-4 px-6 flex justify-between items-center">
        <div className="flex items-center">
          <img src="%PUBLIC_URL%/logo192.png" alt="Coddy Logo" className="h-10 w-10 mr-3 rounded-full" />
          <h1 className="text-3xl font-extrabold text-white">Coddy V2</h1>
          <span className="ml-3 text-indigo-400 text-lg font-medium">Your AI Dev Companion</span>
        </div>
        
        {/* Navigation Tabs */}
        <nav className="flex space-x-4">
          <TabButton
            icon={<i className="fas fa-map-marked-alt text-2xl"></i>}
            label="Roadmap"
            active={activeTab === 'roadmap'}
            onClick={() => setActiveTab('roadmap')}
          />
          <TabButton
            icon={<i className="fas fa-code-branch text-2xl"></i>}
            label="Git History"
            active={activeTab === 'git-history'}
            onClick={() => setActiveTab('git-history')}
          />
          <TabButton
            icon={<i className="fas fa-lightbulb text-2xl"></i>}
            label="Idea Synth"
            active={activeTab === 'idea-synth'}
            onClick={() => setActiveTab('idea-synth')}
          />
        </nav>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 p-6 flex items-stretch"> {/* Use flex and items-stretch to make children fill height */}
        <div className="container mx-auto">
          {renderContent()}
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-gray-800 text-gray-400 py-4 text-center text-sm shadow-inner mt-auto">
        &copy; {new Date().getFullYear()} Coddy V2. All rights reserved. Built with Vibe.
      </footer>
    </div>
  );
}


export default App;