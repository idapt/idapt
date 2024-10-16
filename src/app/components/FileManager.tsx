"use client";

import React, { useState } from 'react';
import FileList from './FileList';
import FileUpload from './FileUpload';

const FileManager: React.FC = () => {
    const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid'); // Set default to 'grid'
    const [selectedFile, setSelectedFile] = useState<File | null>(null);

    const handleSelectFile = (file: File | null) => {
        setSelectedFile(file);
    };
    const [currentFolderId, setCurrentFolderId] = useState<number | null>(null);

    const handleNavigateFolder = (folderId: number | null) => {
        setCurrentFolderId(folderId);
        // Additional logic for navigating folders can be added here
    };

    return (
        <div className="min-h-screen bg-white p-4">
            <h1 className="text-3xl font-bold text-center mb-4">File Manager</h1>
            <div className="flex justify-between mb-4">
                <FileUpload selectedFile={selectedFile} />
                <div>
                    <button
                        className={`px-4 py-2 rounded ${viewMode === 'list' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
                        onClick={() => setViewMode('list')}
                    >
                        List View
                    </button>
                    <button
                        className={`px-4 py-2 rounded ${viewMode === 'grid' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
                        onClick={() => setViewMode('grid')}
                    >
                        Grid View
                    </button>
                </div>
            </div>
            <div>
            <FileList
                viewMode="grid"
                onSelectFile={handleSelectFile} 
                onNavigateFolder={handleNavigateFolder} // Pass the function here
                />
            </div>
        </div>
    );
};

export default FileManager;