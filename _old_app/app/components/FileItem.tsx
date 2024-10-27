import React from 'react';

interface FileItemProps {
    file: {
        id: number;
        name: string;
        size: string;
        type: string;
    };
}

const FileItem: React.FC<FileItemProps> = ({ file }) => {
    return (
        <div className="flex flex-col">
            <span className="font-semibold">{file.name}</span>
            <span className="text-gray-500">{file.size}</span>
            <span className="text-gray-400">{file.type}</span>
        </div>
    );
};

export default FileItem;