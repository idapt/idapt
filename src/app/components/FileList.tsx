import React, { useEffect, useState } from 'react';
import FileItem from './FileItem';
import FileActions from './FileActions';

interface File {
    id: number;
    name: string;
    size: string;
    type: string;
}

const FileList: React.FC = () => {
    const [files, setFiles] = useState<File[]>([]);
    const [selectedFile, setSelectedFile] = useState<File | null>(null);

    const fetchFiles = async () => {
        try {
            const response = await fetch('/api/files');
            const data = await response.json();
            console.log('Fetched files:', data);
            if (Array.isArray(data)) {
                setFiles(data);
            } else {
                console.error('Expected an array but got:', data);
            }
        } catch (error) {
            console.error('Error fetching files:', error);
        }
    };

    useEffect(() => {
        fetchFiles(); // Call fetchFiles when the component mounts
    }, []);

    const handleSelectFile = (file: File) => {
        setSelectedFile(file);
    };

    const handleMove = async (fileId: number, newName: string) => {
        await fetch(`/api/move`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ id: fileId, newName }),
        });
        fetchFiles(); // Call fetchFiles after moving the file
    };

    const handleRename = async (fileId: number, newName: string) => {
        await fetch(`/api/rename`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ id: fileId, newName }),
        });
        fetchFiles(); // Call fetchFiles after renaming the file
    };

    const handleDelete = async (fileId: number) => {
        await fetch(`/api/delete`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ id: fileId }),
        });
        fetchFiles(); // Call fetchFiles after deleting the file
    };

    return (
        <div>
            <ul>
                {files.map((file) => (
                    <li key={file.id} onClick={() => handleSelectFile(file)}>
                        <FileItem file={file} onMove={handleMove} onRename={handleRename} onDelete={handleDelete} />
                    </li>
                ))}
            </ul>
            {selectedFile && (
                <FileActions
                    selectedFile={selectedFile}
                    onMove={handleMove}
                    onRename={handleRename}
                    onDelete={handleDelete}
                />
            )}
        </div>
    );
};

export default FileList;