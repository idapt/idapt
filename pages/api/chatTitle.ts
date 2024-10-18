import { NextApiRequest, NextApiResponse } from 'next';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
    if (req.method === 'POST') {
        try {
            const { userMessage, botMessage } = req.body;
            if (!userMessage || !botMessage) {
                return res.status(400).json({ error: 'User and bot messages are required' });
            }

            const host = process.env.OLLAMA_API_HOST || 'localhost'; // TODO Remove that
            const port = process.env.OLLAMA_API_PORT || '5000'; // TODO Remove that

            // Directly call the Ollama API to generate a title
            const response = await fetch(`http://${host}:${port}/api/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    model: 'llama3.1:8b',
                    messages: [
                        { role: 'user', content: userMessage },
                        { role: 'assistant', content: botMessage }
                    ],
                    stream: false // Ensure we are not streaming
                }),
            });

            if (!response.ok) {
                throw new Error('Failed to generate title from LLM');
            }

            const data = await response.json();
            console.log('LLM API response:', data);
            const title = data.message.content || 'Generated Title'; // Extract title from message content

            res.status(200).json({ title });
        } catch (error) {
            console.error('Error generating chat title:', error);
            res.status(500).json({ error: 'Failed to generate chat title' });
        }
    } else {
        res.setHeader('Allow', ['POST']);
        res.status(405).end(`Method ${req.method} Not Allowed`);
    }
}
