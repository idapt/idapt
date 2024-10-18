import { NextApiRequest, NextApiResponse } from 'next';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const { id } = req.query;

  if (req.method === 'DELETE') {
      try {
          const chatId = parseInt(id as string, 10);

          // First, delete all messages related to this chat
          await prisma.message.deleteMany({
              where: { chatId: chatId },
          });

          // Then, delete the chat itself
          await prisma.chat.delete({
              where: { id: chatId },
          });

          res.status(200).json({ message: 'Chat deleted successfully' });
      } catch (error) {
          console.error('Error deleting chat:', error);
          res.status(500).json({ error: 'Failed to delete chat' });
      }
  } else if (req.method === 'PATCH') {
    try {
        const chatId = parseInt(id as string, 10);
        const { message } = req.body;

        if (!message || !message.content || !message.user) {
            return res.status(400).json({ error: 'Invalid message data' });
        }

        await prisma.message.create({
            data: {
                content: message.content,
                user: message.user,
                chatId: chatId,
            },
        });

        res.status(200).json({ message: 'Message added successfully' });
    } catch (error) {
        console.error('Error adding message:', error);
        res.status(500).json({ error: 'Failed to add message' });
    }
} else {
      res.setHeader('Allow', ['DELETE']);
      res.status(405).end(`Method ${req.method} Not Allowed`);
  }
}