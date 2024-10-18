import React, { useState, useRef, useEffect } from 'react';

const Chat: React.FC = () => {
    const [messages, setMessages] = useState<{ user: string; text: string }[]>([]);
    const [input, setInput] = useState('');
    const messagesEndRef = useRef<HTMLDivElement | null>(null);
    const chatContainerRef = useRef<HTMLDivElement | null>(null);

    const handleSend = async () => {
        if (!input.trim()) return;

        const userMessage = { user: 'You', text: input };
        setMessages((prevMessages) => [...prevMessages, userMessage]);
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

    const scrollToBottom = () => {
        if (messagesEndRef.current) {
            messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    };

    const isUserAtBottom = () => {
        if (chatContainerRef.current) {
            const { scrollTop, scrollHeight, clientHeight } = chatContainerRef.current;
            return scrollHeight - scrollTop <= clientHeight + 50; // Allow a small buffer
        }
        return false;
    };

    useEffect(() => {
        if (isUserAtBottom()) {
            scrollToBottom();
        }
    }, [messages]);

    return (
        <div className="flex flex-col h-screen bg-gray-100">
            <div ref={chatContainerRef} className="flex-1 overflow-y-auto p-4">
                {messages.map((msg, index) => (
                    <div key={index} className={`flex ${msg.user === 'You' ? 'justify-end' : 'justify-start'} mb-2`}>
                        <div className={`max-w-full lg:max-w-2xl ${msg.user === 'You' ? 'bg-gray-300 text-black rounded-lg p-3' : 'bg-transparent text-gray-800'}`}>
                            {msg.text}
                        </div>
                    </div>
                ))}
                <div ref={messagesEndRef} />
            </div>
            <div className="p-4 bg-white border-t border-gray-300 flex items-center">
                <input
                    type="text"
                    className="flex-grow p-2 border border-gray-300 rounded-lg mr-2"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                    placeholder="Type your message..."
                />
                <button
                    onClick={handleSend}
                    className="p-2 bg-blue-500 text-white rounded-full hover:bg-blue-600 focus:outline-none"
                >
                    <svg
                        xmlns="http://www.w3.org/2000/svg"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        className="w-6 h-6"
                    >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M12 5l7 7-7 7" />
                    </svg>
                </button>
            </div>
        </div>
    );
};

export default Chat;
