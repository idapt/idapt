import { createContext, useContext, useState, useEffect } from 'react';
import { loginForAccessSkTokenApiAuthTokenPost } from '@/app/client/sdk.gen';
import { parseJwt } from '@/app/lib/utils';

type AuthContextType = {
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
  userUuid: string | null;
  email: string | null;
};

const AuthContext = createContext<AuthContextType>(null!);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState<string | null>(null);
  const [userUuid, setUserUuid] = useState<string | null>(null);
  const [email, setEmail] = useState<string | null>(null);

  useEffect(() => {
    const initializeAuth = () => {
      const storedToken = localStorage.getItem('authToken');
      if (storedToken) setToken(storedToken);
      const storedUserUuid = localStorage.getItem('userUuid');
      if (storedUserUuid) setUserUuid(storedUserUuid);
      const storedEmail = localStorage.getItem('email');
      if (storedEmail) setEmail(storedEmail);
      setLoading(false);
    };
    
    initializeAuth();
  }, []);

  const login = async (email: string, password: string) => {
    const response = await loginForAccessSkTokenApiAuthTokenPost({
      body: {
        username: email,
        password: password,
        grant_type: 'password'
      }
    });
    
    if (response.data) {
      localStorage.setItem('authToken', response.data.access_token);
      setToken(response.data.access_token);
      localStorage.setItem('email', email);
      setEmail(email);
      // Get user uuid from jwt token
      const decodedToken = parseJwt(response.data.access_token);
      localStorage.setItem('userUuid', decodedToken.sub);
      setUserUuid(decodedToken.sub);
    }
  };

  const logout = () => {
    localStorage.removeItem('authToken');
    localStorage.removeItem('userUuid');
    localStorage.removeItem('email');
    setToken(null);
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <AuthContext.Provider value={{
      token,
      login,
      logout,
      isAuthenticated: !!token,
      userUuid,
      email
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);