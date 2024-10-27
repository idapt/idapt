import type { NextApiRequest, NextApiResponse } from 'next';
import prisma from '../lib/prisma';

const deleteFile = async (req: NextApiRequest, res: NextApiResponse) => {
    const { id } = req.body;

    try {
        const deletedFile = await prisma.file.delete({
            where: { id },
        });

        res.status(200).json({ message: 'File deleted successfully', file: deletedFile });
    } catch (error) {
        console.error('Error deleting file:', error);
        res.status(500).json({ error: 'Error deleting file' });
    }
};

export default deleteFile;