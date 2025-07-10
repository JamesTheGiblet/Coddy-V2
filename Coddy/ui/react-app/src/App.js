// Coddy/ui/react-app/src/App.js
import React, { useState, useEffect } from 'react'; // Added useEffect
import TabButton from './TabButton';
import RoadmapDisplay from './RoadmapDisplay';
import GitHistoryDisplay from './GitHistoryDisplay';
import IdeaSynthPlayground from './components/IdeaSynthPlayground';
import RefactorCode from './RefactorCode'; // NEW: Import RefactorCode component
import FileExplorer from './FileExplorer'; // NEW: Import FileExplorer component
import AutomationTools from './AutomationTools'; // NEW: Import AutomationTools component

function App() {
  const [activeTab, setActiveTab] = useState('roadmap'); // Default active tab
  const [profileError, setProfileError] = useState(null); // State for profile loading error

  // Function to fetch user profile on component mount
  useEffect(() => {
    const fetchUserProfile = async () => {
      try {
        const response = await fetch('http://127.0.0.1:8000/api/profile');
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Failed to load user profile.');
        }
        // const profileData = await response.json();
        // console.log("User Profile Loaded:", profileData); // Log profile data if needed
        setProfileError(null); // Clear any previous errors
      } catch (error) {
        console.error('Error loading user profile:', error);
        setProfileError(`API Error loading user profile (${error.message}). Personalization may be limited.`);
      }
    };

    fetchUserProfile();
  }, []); // Empty dependency array means this runs once on mount

  // Function to render content based on the active tab
  const renderContent = () => {
    switch (activeTab) {
      case 'roadmap':
        return <RoadmapDisplay />;
      case 'git-history':
        return <GitHistoryDisplay />;
      case 'idea-synth':
        return <IdeaSynthPlayground />;
      case 'refactor': // NEW: Refactor tab content
        return <RefactorCode />;
      case 'file-explorer': // NEW: File Explorer tab content
        return <FileExplorer />;
      case 'automation': // NEW: Automation tab content
        return <AutomationTools />;
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
          {/* NEW: Refactor Tab */}
          <TabButton
            icon={<i className="fas fa-magic text-2xl"></i>}
            label="Refactor"
            active={activeTab === 'refactor'}
            onClick={() => setActiveTab('refactor')}
          />
          {/* NEW: File Explorer Tab */}
          <TabButton
            icon={<i className="fas fa-folder-open text-2xl"></i>}
            label="Files"
            active={activeTab === 'file-explorer'}
            onClick={() => setActiveTab('file-explorer')}
          />
          {/* NEW: Automation Tab */}
          <TabButton
            icon={<i className="fas fa-robot text-2xl"></i>}
            label="Automation"
            active={activeTab === 'automation'}
            onClick={() => setActiveTab('automation')}
          />
        </nav>
      </header>

      {/* Profile Error Display */}
      {profileError && (
        <div className="bg-red-800 text-white p-3 text-center font-medium">
          {profileError}
        </div>
      )}

      {/* Main Content Area */}
      <main className="flex-1 p-6 flex items-stretch">
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
