import React, { useState, useRef } from 'react';

interface FileUploadProps {
    selectedFile: File | null;
}

const FileUpload: React.FC<FileUploadProps> = ({ selectedFile }) => {
    const [uploadProgress, setUploadProgress] = useState<number>(0);
    const [uploadMessage, setUploadMessage] = useState<string>('');
    const [showToast, setShowToast] = useState<boolean>(false);
    const [isUploading, setIsUploading] = useState<boolean>(false);
    const [uploadedCount, setUploadedCount] = useState<number>(0);
    const [totalFiles, setTotalFiles] = useState<number>(0);
    const fileInputRef = useRef<HTMLInputElement | null>(null);

    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        if (event.target.files) {
            uploadFiles(Array.from(event.target.files));
        }
    };

    const uploadFiles = async (files: File[]) => {
        setTotalFiles(files.length);
        setIsUploading(true);
        setShowToast(true);
        setUploadMessage('Uploading files...');

        for (const file of files) {
            const formData = new FormData();
            formData.append('files', file);

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
    };

    const handleUploadClick = () => {
        if (fileInputRef.current) {
            fileInputRef.current.click();
        }
    };

    const closeToast = () => {
        setShowToast(false);
    };

    const handleMove = async () => {
        if (selectedFile) {
            const newName = prompt('Enter new name for the file:');
            if (newName) {
                try {
                    const response = await fetch('/api/move', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ id: selectedFile.id, newName }),
                    });

                    if (response.ok) {
                        alert('File moved successfully');
                    } else {
                        const errorData = await response.json();
                        alert(`Error moving file: ${errorData.error}`);
                    }
                } catch (error) {
                    console.error('Error moving file:', error);
                }
            }
        }
    };

    const handleRename = async () => {
        if (selectedFile) {
            const newName = prompt('Enter new name:', selectedFile.name);
            if (newName) {
                try {
                    const response = await fetch('/api/rename', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ id: selectedFile.id, newName }),
                    });

                    if (response.ok) {
                        alert('File renamed successfully');
                    } else {
                        const errorData = await response.json();
                        alert(`Error renaming file: ${errorData.error}`);
                    }
                } catch (error) {
                    console.error('Error renaming file:', error);
                }
            }
        }
    };

    const handleDelete = async () => {
        if (selectedFile && confirm(`Are you sure you want to delete ${selectedFile.name}?`)) {
            try {
                const response = await fetch('/api/delete', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ id: selectedFile.id }),
                });

                if (response.ok) {
                    alert('File deleted successfully');
                } else {
                    const errorData = await response.json();
                    alert(`Error deleting file: ${errorData.error}`);
                }
            } catch (error) {
                console.error('Error deleting file:', error);
            }
        }
    };

    return (
        <div className="p-4 bg-white rounded shadow-md sticky top-0 z-10">
            <div className="flex justify-between mb-4">
                <div className="flex space-x-2">
                    {selectedFile && (
                        <>
                            <button className="bg-yellow-500 text-white px-4 py-2 rounded" onClick={handleMove}>Move</button>
                            <button className="bg-blue-500 text-white px-4 py-2 rounded" onClick={handleRename}>Rename</button>
                            <button className="bg-red-500 text-white px-4 py-2 rounded" onClick={handleDelete}>Delete</button>
                        </>
                    )}
                    <button
                        className="bg-green-500 text-white px-4 py-2 rounded"
                        onClick={handleUploadClick}
                    >
                        Upload
                    </button>
                </div>
                <input
                    type="file"
                    multiple
                    ref={fileInputRef}
                    onChange={handleFileChange}
                    className="hidden"
                />
            </div>
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