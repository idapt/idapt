import type { NextApiRequest, NextApiResponse } from 'next';
import prisma from '../../lib/prisma';

const fetchFiles = async (req: NextApiRequest, res: NextApiResponse) => {
    const { folderId } = req.query;

    try {
        const files = await prisma.file.findMany({
            where: {
                folderId: folderId ? Number(folderId) : null,
            },
        });

        const folders = await prisma.folder.findMany({
            where: {
                parentId: folderId ? Number(folderId) : null,
            },
        });

        res.status(200).json({ files, folders });
    } catch (error) {
        console.error('Error fetching files:', error);
        res.status(500).json({ error: 'Unable to fetch files' });
    }
};

export default fetchFiles;