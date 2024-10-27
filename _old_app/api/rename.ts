import type { NextApiRequest, NextApiResponse } from 'next';
import prisma from '../lib/prisma';

const renameFile = async (req: NextApiRequest, res: NextApiResponse) => {
    const { id, newName } = req.body;

    try {
        const updatedFile = await prisma.file.update({
            where: { id },
            data: { name: newName },
        });

        res.status(200).json({ message: 'File renamed successfully', file: updatedFile });
    } catch (error) {
        console.error('Error renaming file:', error);
        res.status(500).json({ error: 'Error renaming file' });
    }
};

export default renameFile;