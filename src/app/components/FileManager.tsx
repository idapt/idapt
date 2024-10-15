import React from 'react';
import FileUpload from './FileUpload';
import FileList from './FileList';

const FileManager: React.FC = () => {
    return (
        <div className="container mx-auto p-4">
            <h1 className="text-2xl font-bold mb-4">File Manager</h1>
            <FileUpload />
            <FileList />
        </div>
    );
};

export default FileManager;