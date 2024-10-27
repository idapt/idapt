import React, { useEffect, useState } from 'react';
import ContextMenu from './ContextMenu';

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

interface FileListProps {
    viewMode: 'grid' | 'list';
    onSelectFile: (file: File | null) => void;
    onNavigateFolder: (folderId: number | null) => void;
}

const FileList: React.FC<FileListProps> = ({ viewMode, onSelectFile, onNavigateFolder }) => {
    const [files, setFiles] = useState<File[]>([]);
    const [folders, setFolders] = useState<Folder[]>([]);
    const [currentFolderId, setCurrentFolderId] = useState<number | null>(null);
    const [contextMenu, setContextMenu] = useState<{ x: number; y: number } | null>(null);

    useEffect(() => {
        const fetchFilesAndFolders = async () => {
            try {
                const response = await fetch(`/api/files?folderId=${currentFolderId}`);
                const data = await response.json();
                setFiles(data.files || []);
                setFolders(data.folders || []);
            } catch (error) {
                console.error('Error fetching files and folders:', error);
            }
        };

        fetchFilesAndFolders();
    }, [currentFolderId]);

    const handleSelectFile = (file: File) => {
        onSelectFile(file);
    };

    const handleNavigateFolder = (folderId: number | null) => {
        setCurrentFolderId(folderId);
        onNavigateFolder(folderId);
    };

    const handleContextMenu = (event: React.MouseEvent) => {
        event.preventDefault();
        setContextMenu({ x: event.clientX, y: event.clientY });
    };

    const handleNewFolder = async () => {
        const folderName = prompt('Enter folder name:');
        if (folderName) {
            try {
                const response = await fetch('/api/createFolder', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ name: folderName }),
                });
                if (response.ok) {
                    fetchFilesAndFolders();
                } else {
                    console.error('Error creating folder');
                }
            } catch (error) {
                console.error('Error creating folder:', error);
            }
        }
        setContextMenu(null);
    };

    return (
        <div
            className={`p-4 ${viewMode === 'grid' ? 'grid grid-cols-3 gap-4' : 'grid grid-cols-1'}`}
            onContextMenu={handleContextMenu}
        >
            {folders.map((folder) => (
                <div
                    key={folder.id}
                    className="border p-4 rounded shadow hover:shadow-lg transition cursor-pointer"
                    onClick={() => handleNavigateFolder(folder.id)}
                >
                    <div className="font-semibold">{folder.name}</div>
                </div>
            ))}
            {files.map((file) => (
                <div
                    key={file.id}
                    className="border p-4 rounded shadow hover:shadow-lg transition cursor-pointer"
                    onClick={() => handleSelectFile(file)}
                    draggable
                >
                    <div className="font-semibold">{file.name}</div>
                    <div className="text-gray-500">{file.size}</div>
                    <div className="text-gray-400">{file.type}</div>
                </div>
            ))}
            {contextMenu && (
                <ContextMenu
                    x={contextMenu.x}
                    y={contextMenu.y}
                    onNewFolder={handleNewFolder}
                    onClose={() => setContextMenu(null)}
                />
            )}
        </div>
    );
};

export default FileList;