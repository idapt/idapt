import React, { useEffect, useState } from 'react';

interface File {
    id: number;
    name: string;
    size: string;
    type: string;
}

interface FileListProps {
    viewMode: 'grid' | 'list';
    onSelectFile: (file: File | null) => void;
}

const FileList: React.FC<FileListProps> = ({ viewMode, onSelectFile }) => {
    const [files, setFiles] = useState<File[]>([]);

    useEffect(() => {
        const fetchFiles = async () => {
            const response = await fetch('/api/files');
            const data = await response.json();
            setFiles(data);
        };

        fetchFiles();
    }, []);

    const handleSelectFile = (file: File) => {
        onSelectFile(file);
    };

    return (
        <div className={`p-4 ${viewMode === 'grid' ? 'grid grid-cols-3 gap-4' : 'grid grid-cols-1'}`}>
            {files.map((file) => (
                <div
                    key={file.id}
                    className="border p-4 rounded shadow hover:shadow-lg transition cursor-pointer"
                    onClick={() => handleSelectFile(file)}
                >
                    <div className="font-semibold">{file.name}</div>
                    <div className="text-gray-500">{file.size}</div>
                    <div className="text-gray-400">{file.type}</div>
                </div>
            ))}
        </div>
    );
};

export default FileList;