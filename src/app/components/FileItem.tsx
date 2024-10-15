// components/FileItem.tsx
import React from 'react';

interface FileItemProps {
    file: {
        id: number;
        name: string;
        size: string;
        type: string;
    };
    onMove: (fileId: number) => void;
    onRename: (fileId: number, newName: string) => void;
    onDelete: (fileId: number) => void;
}

const FileItem: React.FC<FileItemProps> = ({ file, onMove, onRename, onDelete }) => {
    const handleRename = () => {
        const newName = prompt('Enter new file name:', file.name);
        if (newName) {
            onRename(file.id, newName);
        }
    };

    return (
        <div className="file-item flex justify-between items-center p-2 border-b">
            <div className="file-info">
                <span className="file-name">{file.name}</span>
                <span className="file-size">{file.size}</span>
                <span className="file-type">{file.type}</span>
            </div>
            <div className="file-actions flex space-x-2">
                <button onClick={() => onMove(file.id)} className="bg-blue-500 text-white px-2 py-1 rounded">
                    Move
                </button>
                <button onClick={handleRename} className="bg-yellow-500 text-white px-2 py-1 rounded">
                    Rename
                </button>
                <button onClick={() => onDelete(file.id)} className="bg-red-500 text-white px-2 py-1 rounded">
                    Delete
                </button>
            </div>
        </div>
    );
};

export default FileItem;
