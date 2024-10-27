import React, { useState } from 'react';

interface SettingsMenuProps {
    onClose: () => void;
}

const SettingsMenu: React.FC<SettingsMenuProps> = ({ onClose }) => {
    const [syncedFolderPath, setSyncedFolderPath] = useState('');

    const handleSave = () => {
        // Save the synced folder path logic here
        console.log('Synced folder path:', syncedFolderPath);
        onClose();
    };

    return (
        <div className="fixed inset-0 bg-gray-800 bg-opacity-50 flex justify-center items-center">
            <div className="bg-white p-6 rounded shadow-lg">
                <h2 className="text-xl font-bold mb-4">Settings</h2>
                <div className="mb-4">
                    <label className="block text-gray-700">Synced Folder Path</label>
                    <input
                        type="text"
                        className="mt-1 block w-full border border-gray-300 rounded p-2"
                        value={syncedFolderPath}
                        onChange={(e) => setSyncedFolderPath(e.target.value)}
                        placeholder="Enter the path to your synced folder"
                    />
                </div>
                <div className="flex justify-end">
                    <button
                        className="bg-blue-500 text-white px-4 py-2 rounded mr-2"
                        onClick={handleSave}
                    >
                        Save
                    </button>
                    <button
                        className="bg-gray-300 text-gray-700 px-4 py-2 rounded"
                        onClick={onClose}
                    >
                        Cancel
                    </button>
                </div>
            </div>
        </div>
    );
};

export default SettingsMenu;

