import type { NextApiRequest, NextApiResponse } from 'next';
import prisma from '../../lib/prisma';

const fetchFiles = async (req: NextApiRequest, res: NextApiResponse) => {
    try {
        const files = await prisma.file.findMany(); // Removed the include statement

        res.status(200).json(files);
    } catch (error) {
        console.error('Error fetching files:', error); // Log the error for debugging
        res.status(500).json({ error: 'Unable to fetch files' });
    }
};

export default fetchFiles;