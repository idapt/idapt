import type { NextApiRequest, NextApiResponse } from 'next';
import formidable from 'formidable'; // Importing formidable
import prisma from '../../lib/prisma'; // Adjust the import based on your project structure
import fs from 'fs';

export const config = {
    api: {
        bodyParser: false,
    },
};

const uploadFile = async (req: NextApiRequest, res: NextApiResponse) => {
    const form = formidable({ keepExtensions: true }); // Use formidable directly

    form.parse(req, async (err, fields, files) => {
        if (err) {
            console.error('Error parsing the files:', err);
            return res.status(500).json({ error: 'Error in file upload' });
        }

        const file = files.file[0];
        if (!file) {
            return res.status(400).json({ error: 'No file uploaded' });
        }

        const filePath = file.filepath;
        const fileContent = fs.readFileSync(filePath, 'utf-8'); // Read file content

        try {
            // Create a new file entry in the PostgreSQL database
            const newFile = await prisma.file.create({
                data: {
                    name: file.originalFilename || file.newFilename,
                    content: fileContent, // Store the file content
                },
            });

            res.status(200).json({ message: 'File uploaded successfully', file: newFile });
        } catch (error) {
            console.error('Error saving file to database:', error);
            return res.status(500).json({ error: 'Error saving file to database' });
        } finally {
            // Clean up the uploaded file from the server
            if (fs.existsSync(filePath)) {
                fs.unlinkSync(filePath);
            }
        }
    });
};

export default uploadFile;
