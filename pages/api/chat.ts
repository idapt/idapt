import type { NextApiRequest, NextApiResponse } from 'next';

const chatHandler = async (req: NextApiRequest, res: NextApiResponse) => {
    const { messages } = req.body;
    const host = process.env.OLLAMA_API_HOST || 'localhost';
    const port = process.env.OLLAMA_API_PORT || '5000';

    try {
        const response = await fetch(`http://${host}:${port}/api/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                model: 'llama3.1:8b',
                messages: messages,
                stream: true
            }),
        });

        if (!response.body) {
            throw new Error('ReadableStream not supported in this environment.');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');

        res.writeHead(200, {
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
        });

        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            buffer += decoder.decode(value, { stream: true });

            let boundary = buffer.indexOf('\n');
            while (boundary !== -1) {
                const line = buffer.slice(0, boundary).trim();
                buffer = buffer.slice(boundary + 1);
                
                if (line) {
                    try {
                        const parsedLine = JSON.parse(line);
                        res.write(`data: ${JSON.stringify(parsedLine)}\n\n`);
                        // Flush the response to ensure immediate sending
                        if (res.flush) {
                            res.flush();
                        }
                    } catch (e) {
                        console.error('Error parsing JSON:', e);
                    }
                }
                
                boundary = buffer.indexOf('\n');
            }
        }

        res.end();
    } catch (error) {
        console.error('Error in chat handler:', error);
        res.status(500).json({ error: 'An error occurred while processing the request.' });
    }
};

export default chatHandler;
