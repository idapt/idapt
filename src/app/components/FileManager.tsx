import React, { useState } from 'react';
import FileList from './FileList';
import FileUpload from './FileUpload';

interface File {
    id: number;
    name: string;
    size: string;
    type: string;
    folderId: number | null;
}

interface Folder {
    id: number;
    name: string;
}

const FileManager: React.FC = () => {
    const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid'); // Set default to 'grid'
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [currentFolderId, setCurrentFolderId] = useState<number | null>(null);
    const [path, setPath] = useState<Folder[]>([]);

    const handleSelectFile = (file: File | null) => {
        setSelectedFile(file);
    };

    const handleNavigateFolder = (folderId: number | null, folderName?: string) => {
        if (folderId === null) {
            setPath([]);
        } else {
            setPath((prevPath) => {
                const newPath = [...prevPath];
                const existingIndex = newPath.findIndex(folder => folder.id === folderId);
                if (existingIndex !== -1) {
                    return newPath.slice(0, existingIndex + 1);
                }
                return [...newPath, { id: folderId, name: folderName || '' }];
            });
        }
        setCurrentFolderId(folderId);
    };

    const handleBreadcrumbClick = (index: number) => {
        const newPath = path.slice(0, index + 1);
        setPath(newPath);
        setCurrentFolderId(newPath[index].id);
    };

    return (
        <div className="min-h-screen bg-white p-4">
            <h1 className="text-3xl font-bold text-center mb-4">Idapt File Manager</h1>
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
            <div className="top-bar sticky top-0 bg-white shadow p-4 flex items-center">
                <span
                    className="cursor-pointer"
                    onClick={() => handleNavigateFolder(null)}
                >
                    🏠 Home
                </span>
                {path.map((folder, index) => (
                    <React.Fragment key={folder.id}>
                        <span className="mx-2">→</span>
                        <span
                            className="cursor-pointer"
                            onClick={() => handleBreadcrumbClick(index)}
                        >
                            {folder.name}
                        </span>
                    </React.Fragment>
                ))}
            </div>
            <div>
                <FileList
                    viewMode={viewMode}
                    onSelectFile={handleSelectFile}
                    onNavigateFolder={handleNavigateFolder}
                />
            </div>
        </div>
    );
};

export default FileManager;