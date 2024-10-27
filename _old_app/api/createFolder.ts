import type { NextApiRequest, NextApiResponse } from 'next';
import prisma from '../lib/prisma';

const createFolder = async (req: NextApiRequest, res: NextApiResponse) => {
    const { name } = req.body;

    try {
        const newFolder = await prisma.folder.create({
            data: { name },
        });

        res.status(200).json({ message: 'Folder created successfully', folder: newFolder });
    } catch (error) {
        console.error('Error creating folder:', error);
        res.status(500).json({ error: 'Error creating folder' });
    }
};

export default createFolder;