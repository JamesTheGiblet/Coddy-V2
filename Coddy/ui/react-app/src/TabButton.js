import React from 'react';

const TabButton = ({ icon, label, active, onClick }) => (
  <button
    onClick={onClick}
    className={`p-2 rounded-md flex flex-col items-center justify-center text-xs font-medium transition-all duration-200 ${
      active ? 'bg-indigo-700 text-white shadow-md' : 'text-gray-400 hover:bg-gray-700 hover:text-indigo-300'
    }`}
  >
    {icon}
    <span className="mt-1">{label}</span>
  </button>
);

export default TabButton;
