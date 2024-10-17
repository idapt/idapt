import type { NextApiRequest, NextApiResponse } from 'next';

const chatHandler = async (req: NextApiRequest, res: NextApiResponse) => {
    const { message } = req.body;
    const host = process.env.OLLAMA_API_HOST || 'localhost';
    const port = process.env.OLLAMA_API_PORT || '5000';

    try {
        // Ensure the correct endpoint is used
        const response = await fetch(`http://${host}:${port}/api/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                model: 'llama3.1:8b', // Replace with your model name
                messages: [{ role: 'user', content: message }],
                stream: false // Set to true if you want streaming
            }),
        });

        if (!response.ok) {
            throw new Error(`Ollama API returned status ${response.status}`);
        }

        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            throw new Error('Ollama API did not return JSON');
        }

        const data = await response.json();
        res.status(200).json({ reply: data.message.content });
    } catch (error) {
        console.error('Error communicating with Ollama API:', error);
        res.status(500).json({ error: 'Failed to get response from AI' });
    }
};

export default chatHandler;
