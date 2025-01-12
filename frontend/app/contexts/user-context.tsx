'use client';

import { createContext, useContext, ReactNode } from 'react';

interface UserContextType {
  userId: string;
}

const UserContext = createContext<UserContextType>({ userId: 'user' });

export function UserProvider({ children }: { children: ReactNode }) {
  // For now, we'll use a static user ID
  const userId = 'user';

  return (
    <UserContext.Provider value={{ userId }}>
      {children}
    </UserContext.Provider>
  );
}

export function useUser() {
  return useContext(UserContext);
} 