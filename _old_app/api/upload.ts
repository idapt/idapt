import type { NextApiRequest, NextApiResponse } from 'next';
import formidable from 'formidable';
import prisma from '../lib/prisma';
import fs from 'fs';

export const config = {
    api: {
        bodyParser: false,
    },
};

const uploadFile = async (req: NextApiRequest, res: NextApiResponse) => {
    const form = formidable({ keepExtensions: true });

    form.parse(req, async (err, fields, files) => {
        if (err) {
            console.error('Error parsing the files:', err);
            return res.status(500).json({ error: 'Error in file upload' });
        }

        const uploadedFiles = Array.isArray(files.files) ? files.files : [files.files];
        const totalFiles = uploadedFiles.length;
        let uploadedCount = 0;

        for (const file of uploadedFiles) {
            if (!file) {
                return res.status(400).json({ error: 'No file uploaded' });
            }

            const filePath = file.filepath;
            const fileContent = fs.readFileSync(filePath, 'utf-8');

            try {
                const newFile = await prisma.file.create({
                    data: {
                        name: file.originalFilename || file.newFilename,
                        content: fileContent,
                    },
                });
                uploadedCount++;
                const percentage = Math.round((uploadedCount / totalFiles) * 100);
                console.log(`Uploaded ${uploadedCount} of ${totalFiles} files (${percentage}%)`);
            } catch (error) {
                console.error('Error saving file to database:', error);
                return res.status(500).json({ error: 'Error saving file to database' });
            } finally {
                if (fs.existsSync(filePath)) {
                    fs.unlinkSync(filePath);
                }
            }
        }

        res.status(200).json({ message: 'All files uploaded successfully', totalFiles });
    });
};

export default uploadFile;