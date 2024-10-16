import React from 'react';

interface FileActionsProps {
    selectedFile: string; // Assuming selectedFile is a string representing the file name
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
        const newName = prompt('Enter new name:');
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
        <div>
            <button onClick={handleMove}>Move</button>
            <button onClick={handleRename}>Rename</button>
            <button onClick={handleDelete}>Delete</button>
        </div>
    );
};

export default FileActions;