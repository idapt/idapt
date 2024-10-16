import React, { useState } from 'react';

const FileUpload: React.FC = () => {
    const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
    const [uploadProgress, setUploadProgress] = useState<number>(0);
    const [uploadMessage, setUploadMessage] = useState<string>('');

    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        if (event.target.files) {
            setSelectedFiles(Array.from(event.target.files));
        }
    };

    const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
        event.preventDefault();
        if (event.dataTransfer.items) {
            const files = Array.from(event.dataTransfer.items)
                .filter(item => item.kind === 'file')
                .map(item => item.getAsFile())
                .filter((file): file is File => file !== null);
            setSelectedFiles(prevFiles => [...prevFiles, ...files]);
        }
    };

    const handleSubmit = async (event: React.FormEvent) => {
        event.preventDefault();
        if (selectedFiles.length > 0) {
            const formData = new FormData();
            selectedFiles.forEach(file => {
                formData.append('files', file);
            });

            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData,
            });

            if (response.ok) {
                setUploadMessage('Upload successful!');
                setUploadProgress(100);
            } else {
                const errorData = await response.json();
                setUploadMessage(`Upload failed: ${errorData.error}`);
            }
        } else {
            console.error('No files selected');
        }
    };

    return (
        <div>
            <form onSubmit={handleSubmit} onDrop={handleDrop} onDragOver={(e) => e.preventDefault()}>
                <input type="file" multiple onChange={handleFileChange} />
                <button type="submit">Upload</button>
            </form>
            {uploadMessage && (
                <div style={{ backgroundColor: uploadProgress === 100 ? 'lightgreen' : 'lightcoral' }}>
                    {uploadMessage} {uploadProgress}% done
                </div>
            )}
            <div>
                <h4>Selected Files:</h4>
                <ul>
                    {selectedFiles.map((file, index) => (
                        <li key={index}>{file.name}</li>
                    ))}
                </ul>
            </div>
        </div>
    );
};

export default FileUpload;