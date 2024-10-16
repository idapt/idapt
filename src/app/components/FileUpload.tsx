import React, { useState } from 'react';

const FileUpload: React.FC = () => {
    const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
    const [uploadProgress, setUploadProgress] = useState<number>(0);
    const [uploadMessage, setUploadMessage] = useState<string>('');
    const [showToast, setShowToast] = useState<boolean>(false);
    const [isUploading, setIsUploading] = useState<boolean>(false);
    const [uploadedCount, setUploadedCount] = useState<number>(0);
    const [totalFiles, setTotalFiles] = useState<number>(0);

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

            setTotalFiles(selectedFiles.length);
            setIsUploading(true);
            setShowToast(true);
            setUploadMessage('Uploading files...');

            for (const file of selectedFiles) {
                const response = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData,
                });

                if (response.ok) {
                    setUploadedCount(prev => prev + 1);
                    const percentage = Math.round(((uploadedCount + 1) / totalFiles) * 100);
                    setUploadProgress(percentage);
                } else {
                    const errorData = await response.json();
                    setUploadMessage(`Upload failed: ${errorData.error}`);
                }
            }

            setUploadMessage('All files uploaded successfully!');
            setUploadProgress(100);
            setTimeout(() => {
                setShowToast(false);
                setIsUploading(false);
                setUploadedCount(0);
                setTotalFiles(0);
            }, 3000); // Auto-dismiss after 3 seconds
        } else {
            console.error('No files selected');
        }
    };

    const closeToast = () => {
        setShowToast(false);
    };

    return (
        <div>
            <form onSubmit={handleSubmit} onDrop={handleDrop} onDragOver={(e) => e.preventDefault()}>
                <input type="file" multiple onChange={handleFileChange} />
                <button type="submit">Upload</button>
            </form>
            {showToast && (
                <div className="toast" style={{ backgroundColor: isUploading ? 'yellow' : 'lightgreen' }}>
                    <span>
                        {isUploading
                            ? `Uploading ${uploadedCount} of ${totalFiles} files (${uploadProgress}%)`
                            : uploadMessage}
                    </span>
                    <button className="close-button" onClick={closeToast}>✖</button>
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
            <style jsx>{`
                .toast {
                    position: fixed;
                    bottom: 20px;
                    left: 50%;
                    transform: translateX(-50%);
                    color: black;
                    padding: 10px 20px;
                    border-radius: 8px;
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    z-index: 1000;
                }
                .close-button {
                    background: none;
                    border: none;
                    color: black;
                    font-size: 16px;
                    cursor: pointer;
                    margin-left: 10px;
                }
            `}</style>
        </div>
    );
};

export default FileUpload;