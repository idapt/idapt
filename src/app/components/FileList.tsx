import React, { useEffect, useState } from 'react';
import FileActions from './FileActions';

interface File {
    id: string;
    name: string;
}

const FileList: React.FC = () => {
    const [files, setFiles] = useState<File[]>([]);
    const [selectedFile, setSelectedFile] = useState<File | null>(null);

    useEffect(() => {
        const fetchFiles = async () => {
            const response = await fetch('/api/files'); // Adjust the API endpoint as necessary
            const data = await response.json();
            setFiles(data);
        };

        fetchFiles();
    }, []);

    const handleSelectFile = (file: File) => {
        setSelectedFile(file);
    };

    const handleMove = async (newPath: string) => {
        if (selectedFile) {
            await fetch(`/api/move`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ id: selectedFile.id, newPath }),
            });
            // Refresh the file list after moving
            fetchFiles();
        }
    };

    const handleRename = async (newName: string) => {
        if (selectedFile) {
            await fetch(`/api/rename`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ id: selectedFile.id, newName }),
            });
            // Refresh the file list after renaming
            fetchFiles();
        }
    };

    const handleDelete = async () => {
        if (selectedFile) {
            await fetch(`/api/delete`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ id: selectedFile.id }),
            });
            // Refresh the file list after deletion
            fetchFiles();
        }
    };

    return (
        <div>
            <ul>
                {files.map((file) => (
                    <li key={file.id} onClick={() => handleSelectFile(file)}>
                        {file.name}
                    </li>
                ))}
            </ul>
            {selectedFile && (
                <FileActions
                    selectedFile={selectedFile.name}
                    onMove={handleMove}
                    onRename={handleRename}
                    onDelete={handleDelete}
                />
            )}
        </div>
    );
};

export default FileList;