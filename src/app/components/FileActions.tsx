import React from 'react';

interface FileActionsProps {
    selectedFile: string; // Assuming selectedFile is a string representing the file name
    onMove: (newPath: string) => void;
    onRename: (newName: string) => void;
    onDelete: () => void;
}

const FileActions: React.FC<FileActionsProps> = ({ selectedFile, onMove, onRename, onDelete }) => {
    const handleMove = () => {
        const newPath = prompt('Enter new path:');
        if (newPath) {
            onMove(newPath);
        }
    };

    const handleRename = () => {
        const newName = prompt('Enter new name:');
        if (newName) {
            onRename(newName);
        }
    };

    const handleDelete = () => {
        if (confirm(`Are you sure you want to delete ${selectedFile}?`)) {
            onDelete();
        }
    };

    return (
        <div>
            <button onClick={handleMove}>Move</button>
            <button onClick={handleRename}>Rename</button>
            <button onClick={handleDelete}>Delete</button>
        </div>
    );
};

export default FileActions;