import React from 'react';

interface FileActionsProps {
    selectedFile: {
        id: number;
        name: string;
    };
    onMove: (fileId: number, newName: string) => void;
    onRename: (fileId: number, newName: string) => void;
    onDelete: (fileId: number) => void;
}

const FileActions: React.FC<FileActionsProps> = ({ selectedFile, onMove, onRename, onDelete }) => {
    const handleMove = () => {
        const newPath = prompt('Enter new path:');
        if (newPath) {
            onMove(selectedFile.id, newPath);
        }
    };

    const handleRename = () => {
        const newName = prompt('Enter new name:', selectedFile.name);
        if (newName) {
            onRename(selectedFile.id, newName);
        }
    };

    const handleDelete = () => {
        if (confirm(`Are you sure you want to delete ${selectedFile.name}?`)) {
            onDelete(selectedFile.id);
        }
    };

    return (
        <div className="flex justify-between mt-4">
            <button className="bg-blue-500 text-white px-4 py-2 rounded" onClick={handleMove}>Move</button>
            <button className="bg-yellow-500 text-white px-4 py-2 rounded" onClick={handleRename}>Rename</button>
            <button className="bg-red-500 text-white px-4 py-2 rounded" onClick={handleDelete}>Delete</button>
        </div>
    );
};

export default FileActions;