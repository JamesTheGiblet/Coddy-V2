import React, { useState, useEffect } from 'react';

const FileExplorer = () => {
    const [currentPath, setCurrentPath] = useState('.');
    const [files, setFiles] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [fileContent, setFileContent] = useState('');
    const [readingFile, setReadingFile] = useState(false);
    const [selectedFile, setSelectedFile] = useState(null);

    const fetchFiles = async (path) => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch(`http://127.0.0.1:8000/api/files/list?path=${encodeURIComponent(path)}`);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to list files.');
            }
            const data = await response.json();
            setFiles(data.items);
            setCurrentPath(path);
        } catch (err) {
            console.error('File list error:', err);
            setError(err.message || 'An unknown error occurred while listing files.');
            setFiles([]); // Clear files on error
        } finally {
            setLoading(false);
        }
    };

    const readFileContent = async (filePath) => {
        setReadingFile(true);
        setError(null);
        setFileContent('');
        setSelectedFile(filePath);
        try {
            const response = await fetch(`http://127.0.0.1:8000/api/files/read?path=${encodeURIComponent(filePath)}`);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to read file.');
            }
            const data = await response.json();
            setFileContent(data.content);
        } catch (err) {
            console.error('Read file error:', err);
            setError(err.message || 'An unknown error occurred while reading file.');
            setFileContent(''); // Clear content on error
        } finally {
            setReadingFile(false);
        }
    };

    useEffect(() => {
        fetchFiles('.');
    }, []);

    const handleItemClick = (item) => {
        if (item.endsWith('/')) { // It's a directory
            fetchFiles(`${currentPath}/${item}`);
        } else { // It's a file
            readFileContent(`${currentPath}/${item}`);
        }
    };

    const handleGoBack = () => {
        const pathParts = currentPath.split('/');
        if (pathParts.length > 1) {
            const newPath = pathParts.slice(0, -1).join('/') || '.';
            fetchFiles(newPath);
        }
    };

    return (
        <div className="p-6 bg-gray-800 rounded-lg shadow-xl flex flex-col h-full">
            <h2 className="text-3xl font-bold text-indigo-400 mb-6">File Explorer</h2>
            
            <div className="flex items-center space-x-4 mb-4">
                <button
                    onClick={handleGoBack}
                    className="bg-gray-700 hover:bg-gray-600 text-white font-bold py-2 px-4 rounded-full focus:outline-none focus:shadow-outline transition duration-200 ease-in-out"
                    disabled={currentPath === '.'}
                >
                    <i className="fas fa-arrow-left"></i> Back
                </button>
                <span className="text-gray-300 text-lg font-mono bg-gray-700 px-4 py-2 rounded-lg">
                    {currentPath === '.' ? '/' : currentPath}
                </span>
            </div>

            {error && <p className="text-red-500 text-sm mb-4">{error}</p>}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 flex-1">
                {/* File List */}
                <div className="bg-gray-700 p-4 rounded-lg border border-gray-600 overflow-auto max-h-96 md:max-h-full">
                    <h3 className="text-xl font-bold text-gray-300 mb-3">Contents:</h3>
                    {loading ? (
                        <p className="text-gray-400">Loading files...</p>
                    ) : (
                        <ul className="space-y-2">
                            {files.map((item, index) => (
                                <li
                                    key={index}
                                    className={`flex items-center p-2 rounded-md cursor-pointer transition duration-150 ease-in-out 
                                                ${item.endsWith('/') ? 'text-blue-400 hover:bg-gray-600' : 'text-green-400 hover:bg-gray-600'}
                                                ${selectedFile === `${currentPath}/${item}` ? 'bg-indigo-700' : ''}`}
                                    onClick={() => handleItemClick(item)}
                                >
                                    <i className={`mr-2 ${item.endsWith('/') ? 'fas fa-folder' : 'fas fa-file'}`}></i>
                                    {item}
                                </li>
                            ))}
                        </ul>
                    )}
                </div>

                {/* File Content Display */}
                <div className="flex flex-col">
                    <h3 className="text-xl font-bold text-gray-300 mb-3">
                        {selectedFile ? `Content of: ${selectedFile.split('/').pop()}` : 'Select a file to view content:'}
                    </h3>
                    <div className="bg-gray-700 p-4 rounded-lg flex-1 overflow-auto border border-gray-600">
                        <pre className="text-gray-200 whitespace-pre-wrap font-mono text-sm">
                            {readingFile ? 'Loading file content...' : fileContent || 'No file selected or content is empty.'}
                        </pre>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default FileExplorer;
