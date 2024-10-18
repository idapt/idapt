import { NextApiRequest, NextApiResponse } from 'next';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  switch (req.method) {
    case 'POST':
      return createChat(req, res);
    case 'GET':
      return getChats(req, res);
    case 'PATCH':
      return updateChatTitle(req, res);
    default:
      res.setHeader('Allow', ['POST', 'GET', 'PATCH']);
      res.status(405).end(`Method ${req.method} Not Allowed`);
  }
}

async function createChat(req: NextApiRequest, res: NextApiResponse) {
  try {
    const { initialMessage } = req.body;
    if (!initialMessage || !initialMessage.content || !initialMessage.user) {
      return res.status(400).json({ error: 'Invalid initial message' });
    }
    const chat = await prisma.chat.create({
      data: {
        title: 'New Chat',
        messages: {
          create: {
            content: initialMessage.content,
            user: initialMessage.user,
          },
        },
      },
    });
    res.status(201).json(chat);
  } catch (error) {
    console.error('Error creating chat:', error);
    res.status(500).json({ error: 'Failed to create chat' });
  }
}

async function getChats(req: NextApiRequest, res: NextApiResponse) {
  try {
    const chats = await prisma.chat.findMany({
      include: {
        messages: true,
      },
    });
    res.status(200).json(chats);
  } catch (error) {
    console.error('Error retrieving chats:', error);
    res.status(500).json({ error: 'Failed to retrieve chats' });
  }
}

async function updateChatTitle(req: NextApiRequest, res: NextApiResponse) {
  try {
    const { chatId, newTitle } = req.body;
    if (!chatId || !newTitle) {
      return res.status(400).json({ error: 'Invalid request data' });
    }
    const chat = await prisma.chat.update({
      where: { id: chatId },
      data: { title: newTitle },
    });
    res.status(200).json(chat);
  } catch (error) {
    console.error('Error updating chat title:', error);
    res.status(500).json({ error: 'Failed to update chat title' });
  }
}