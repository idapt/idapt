import React, { useState } from 'react';

const Chat: React.FC = () => {
    const [messages, setMessages] = useState<{ user: string; text: string }[]>([]);
    const [input, setInput] = useState('');

    const handleSend = async () => {
        if (!input.trim()) return;

        const userMessage = { user: 'You', text: input };
        setMessages([...messages, userMessage]);
        setInput(''); // Clear the input immediately

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    messages: messages.map(msg => ({
                        role: msg.user === 'You' ? 'user' : 'assistant',
                        content: msg.text
                    })).concat({ role: 'user', content: input }),
                }),
            });

            if (!response.body) throw new Error('ReadableStream not supported in this browser.');

            const reader = response.body.getReader();
            const decoder = new TextDecoder('utf-8');
            let botMessage = { user: 'Bot', text: '' };
            setMessages((prevMessages) => [...prevMessages, botMessage]);

            const processStream = async () => {
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    
                    const chunk = decoder.decode(value);
                    const lines = chunk.split('\n\n');
                    
                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            const jsonStr = line.slice(6);
                            try {
                                const parsed = JSON.parse(jsonStr);
                                
                                if (parsed.message && parsed.message.content) {
                                    botMessage.text += parsed.message.content;
                                    setMessages((prevMessages) => {
                                        const newMessages = [...prevMessages];
                                        newMessages[newMessages.length - 1] = { ...botMessage };
                                        return newMessages;
                                    });
                                }
                            } catch (e) {
                                console.error('Error parsing JSON:', e);
                            }
                        }
                    }
                }
            };

            await processStream();
        } catch (error) {
            console.error('Error in handleSend:', error);
            // Handle error (e.g., show an error message to the user)
        }
    };

    const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter') {
            handleSend();
        }
    };

    return (
        <div className="flex flex-col h-screen bg-gray-100">
            <div className="flex-1 overflow-y-auto p-4">
                {messages.map((msg, index) => (
                    <div
                        key={index}
                        className={`mb-2 p-3 rounded-lg ${
                            msg.user === 'You' ? 'bg-gray-300 self-end' : 'bg-white'
                        } shadow-sm`}
                    >
                        <strong>{msg.user}:</strong> {msg.text}
                    </div>
                ))}
            </div>
            <div className="p-4 bg-white border-t border-gray-200 flex items-center">
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Type a message..."
                    className="flex-grow p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
                />
                <button
                    onClick={handleSend}
                    className="ml-2 p-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-400"
                >
                    <svg
                        xmlns="http://www.w3.org/2000/svg"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        className="w-5 h-5"
                    >
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M5 12h14M12 5l7 7-7 7"
                        />
                    </svg>
                </button>
            </div>
        </div>
    );
};

export default Chat;
