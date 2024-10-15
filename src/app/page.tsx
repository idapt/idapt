// src/app/page.tsx

import React from 'react';
import FileUpload from './components/FileUpload';

const HomePage: React.FC = () => {
    return (
        <div>
            <h1>File Upload</h1>
            <FileUpload />
        </div>
    );
};

export default HomePage;