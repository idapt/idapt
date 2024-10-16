import React from 'react';

interface ContextMenuProps {
    x: number;
    y: number;
    onNewFolder: () => void;
    onClose: () => void;
}

const ContextMenu: React.FC<ContextMenuProps> = ({ x, y, onNewFolder, onClose }) => {
    return (
        <div
            className="absolute bg-white border shadow-md"
            style={{ top: y, left: x }}
            onMouseLeave={onClose}
        >
            <ul className="list-none p-2">
                <li
                    className="cursor-pointer hover:bg-gray-200 p-2"
                    onClick={onNewFolder}
                >
                    New Folder
                </li>
            </ul>
        </div>
    );
};

export default ContextMenu;

