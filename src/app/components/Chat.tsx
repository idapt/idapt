import React, { useState, useRef, useEffect } from 'react';

const Chat: React.FC = () => {
    const [messages, setMessages] = useState<{ user: string; text: string }[]>([]);
    const [input, setInput] = useState('');
    const [chatHistory, setChatHistory] = useState<{ id: number; title: string; messages: { user: string; text: string }[] }[]>([]);
    const [currentChatId, setCurrentChatId] = useState<number | null>(null);
    const [isHistoryVisible, setIsHistoryVisible] = useState(true);
    const messagesEndRef = useRef<HTMLDivElement | null>(null);
    const chatContainerRef = useRef<HTMLDivElement | null>(null);
    const inputRef = useRef<HTMLTextAreaElement | null>(null);

    const fetchChatHistory = async () => {
        try {
            const response = await fetch('/api/chatHistory');
            if (!response.ok) {
                throw new Error('Failed to fetch chat history');
            }
            const data = await response.json();
            setChatHistory(data);
        } catch (error) {
            console.error('Error fetching chat history:', error);
        }
    };

    useEffect(() => {
        fetchChatHistory();
    }, []);

    useEffect(() => {
        if (currentChatId !== null) {
            // Removed debug log
        }
    }, [currentChatId]);

    const handleSend = async () => {
        if (!input.trim()) return;

        const userMessage = { user: 'You', text: input };
        setMessages((prevMessages) => [...prevMessages, userMessage]);
        setInput(''); // Clear the input immediately

        try {
            let chat;
            let tempChatId = currentChatId; // Temporary variable to hold chat ID if currentChatId is null as the update of it is async
            if (currentChatId === null) {
                const response = await fetch('/api/chatHistory', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        initialMessage: { content: userMessage.text, user: userMessage.user },
                    }),
                });

                if (!response.ok) {
                    throw new Error('Failed to create chat');
                }

                chat = await response.json();
                setCurrentChatId(chat.id); // Set the currentChatId to the new chat's ID
                setChatHistory((prevHistory) => [...prevHistory, chat]);
                tempChatId = chat.id; // Update tempChatId to the new chat ID
            } else {
                // Save the user message to the database
                await fetch(`/api/chatHistory/${currentChatId}`, {
                    method: 'PATCH',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        message: { content: userMessage.text, user: userMessage.user },
                    }),
                });
            }
            // Fetch response from LLM API
            const llmResponse = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    messages: [...messages, userMessage].map(msg => ({
                        role: msg.user === 'You' ? 'user' : 'assistant',
                        content: msg.text
                    })),
                    chatId: tempChatId, // Use tempChatId for the chat ID
                }),
            });

            if (!llmResponse.body) throw new Error('ReadableStream not supported in this browser.');

            const reader = llmResponse.body.getReader();
            const decoder = new TextDecoder('utf-8');
            let botMessage = { user: 'Bot', text: '' };

            while (true) {
                const { done, value } = await reader.read();
                if (done) {
                    break;
                }

                const chunk = decoder.decode(value, { stream: true });

                const lines = chunk.split('\n\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const jsonStr = line.slice(6);
                        try {
                            const parsed = JSON.parse(jsonStr);

                            if (parsed.message && parsed.message.content) {
                                botMessage.text += parsed.message.content;

                                // Update messages state with the current bot message
                                setMessages((prevMessages) => {
                                    const newMessages = [...prevMessages];
                                    if (newMessages.length > 0 && newMessages[newMessages.length - 1].user === 'Bot') {
                                        newMessages[newMessages.length - 1].text = botMessage.text;
                                    } else {
                                        newMessages.push({ ...botMessage });
                                    }
                                    return newMessages;
                                });
                            }
                        } catch (e) {
                            console.error('Error parsing JSON:', e);
                        }
                    }
                }
            }
            // Save the complete bot message to the database after generation
            if (tempChatId !== null) {
                await fetch(`/api/chatHistory/${tempChatId}`, {
                    method: 'PATCH',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        message: { content: botMessage.text, user: botMessage.user },
                    }),
                });
            }

            // Check if the chat title is still the default "new chat" name
            const currentChat = chatHistory.find((c) => c.id === tempChatId);
            if (currentChat && currentChat.title === 'New Chat') {
                // TODO Fix this as it dont generate the title and always returns an Generated Title
                // Request a chat title from the LLM using the user and bot messages
                const titleResponse = await fetch('/api/chatTitle', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        userMessage: userMessage.text,
                        botMessage: botMessage.text,
                    }),
                });
                if (!titleResponse.ok) {
                    throw new Error('Failed to generate chat title');
                }

                const { title } = await titleResponse.json();
                // Update the chat title in the chat history
                setChatHistory((prevHistory) =>
                    prevHistory.map((c) => (c.id === tempChatId ? { ...c, title } : c))
                );

                // Update the chat title in the database  // TODO Fix this as it always returns an error and dont update the title in thee db
                await fetch(`/api/chatHistory/${tempChatId}`, {
                    method: 'PATCH',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        chatId: tempChatId, // Ensure this is the correct variable
                        newTitle: title,    // Ensure this is the correct variable
                    }),
                });
            }

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

    const adjustTextareaHeight = () => {
        if (inputRef.current) {
            inputRef.current.style.height = 'auto'; // Reset height
            const maxHeight = window.innerHeight / 3; // One third of the screen height
            inputRef.current.style.height = `${Math.min(inputRef.current.scrollHeight, maxHeight)}px`;
        }
    };

    useEffect(() => {
        adjustTextareaHeight();
    }, [input]);

    const toggleHistoryVisibility = () => {
        setIsHistoryVisible(!isHistoryVisible);
    };

    const selectChat = (chatId: number) => {
        const selectedChat = chatHistory.find(chat => chat.id === chatId);
        if (selectedChat) {
            setCurrentChatId(chatId);
            setMessages(selectedChat.messages ? selectedChat.messages.map(msg => ({ user: msg.user, text: msg.content })) : []);
        } else {
            console.error('Selected chat is undefined');
            setCurrentChatId(null);
            setMessages([]);
        }
    };

    const deleteChat = async (chatId: number) => {
        try {
            const response = await fetch(`/api/chatHistory/${chatId}`, {
                method: 'DELETE',
            });

            if (!response.ok) {
                throw new Error('Failed to delete chat');
            }

            // Update the chat history state to remove the deleted chat
            setChatHistory((prevHistory) => prevHistory.filter(chat => chat.id !== chatId));

            // If the deleted chat is the current chat, reset to a new chat
            if (currentChatId === chatId) {
                setCurrentChatId(null);
                setMessages([]);
            }
        } catch (error) {
            console.error('Error deleting chat:', error);
        }
    };

    const createNewChat = () => {
        setCurrentChatId(null);
        setMessages([]);
    };

    return (
        <div className="flex h-screen">
            <div
                className={`history-menu ${isHistoryVisible ? 'translate-x-0' : '-translate-x-full'} transition-transform duration-300 ease-in-out bg-white border-r border-gray-300 p-4 overflow-y-auto`}
            >
                <div className="flex justify-between items-center mb-4">
                    <button onClick={toggleHistoryVisibility} className="p-2 text-blue-500">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <rect x="3" y="3" width="18" height="18" rx="2" ry="2" strokeWidth="2" stroke="currentColor" fill="none" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 8h8M8 12h8m-8 4h8" />
                        </svg>
                    </button>
                    <button onClick={createNewChat} className="p-2 bg-blue-500 text-white rounded-full hover:bg-blue-600 flex items-center justify-center">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                        </svg>
                    </button>
                </div>
                <ul className="space-y-2">
                    {chatHistory.map((chat) => (
                        <li
                            key={chat.id}
                            className="cursor-pointer hover:bg-gray-200 p-2 rounded flex justify-between items-center"
                            onClick={() => selectChat(chat.id)}
                        >
                            <span>{chat.title}</span>
                            <button
                                onClick={(e) => {
                                    e.stopPropagation(); // Prevent triggering the selectChat function
                                    deleteChat(chat.id);
                                }}
                                className="opacity-0 hover:opacity-100 transition-opacity duration-200"
                            >
                                <svg
                                    xmlns="http://www.w3.org/2000/svg"
                                    className="h-5 w-5 text-gray-500 hover:text-gray-700"
                                    fill="none"
                                    viewBox="0 0 24 24"
                                    stroke="currentColor"
                                >
                                    <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth={2}
                                        d="M6 18L18 6M6 6l12 12"
                                    />
                                </svg>
                            </button>
                        </li>
                    ))}
                </ul>
            </div>
            {!isHistoryVisible && (
                <button onClick={toggleHistoryVisibility} className="absolute top-4 left-4 p-2 text-blue-500">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <rect x="3" y="3" width="18" height="18" rx="2" ry="2" strokeWidth="2" stroke="currentColor" fill="none" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 8h8M8 12h8m-8 4h8" />
                    </svg>
                </button>
            )}
            <div className={`flex-1 flex flex-col ${isHistoryVisible ? 'w-3/4' : 'w-full'}`}>
                <div ref={chatContainerRef} className="flex-1 overflow-y-auto p-4">
                    {messages.map((msg, index) => (
                        <div key={index} className={`flex ${msg.user === 'You' ? 'justify-end' : 'justify-start'} mb-3`}>
                            <div className={`max-w-full lg:max-w-2xl break-words ${msg.user === 'You' ? 'bg-gray-300 text-black rounded-full p-3 mr-2' : 'bg-transparent text-gray-800 rounded-full p-3'}`}>
                                {msg.text}
                            </div>
                        </div>
                    ))}
                    <div ref={messagesEndRef} />
                </div>
                <div className="p-4 bg-white border-t border-gray-300 flex items-center">
                    <textarea
                        ref={inputRef}
                        className="flex-grow p-2 border border-gray-300 rounded-lg mr-2 resize-none overflow-y-auto"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                                e.preventDefault();
                                handleSend();
                            }
                        }}
                        placeholder="Type your message..."
                        rows={1}
                        style={{ maxHeight: '33vh' }} // Limit to one third of the viewport height
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
        </div>
    );
};

export default Chat;
