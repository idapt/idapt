import { createContext, useContext, useState, useEffect } from 'react';
import { loginForAccessSkTokenRouteApiAuthTokenPost, registerRouteApiAuthRegisterPost } from '@/app/client/sdk.gen';
import { parseJwt } from '@/app/lib/utils';
import { sha256Hash } from '@/app/lib/hash';
import { useRouter } from 'next/navigation';

type AuthContextType = {
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
  userUuid: string | null;
  email: string | null;
  register: (email: string, password: string) => Promise<void>;
};

const AuthContext = createContext<AuthContextType>(null!);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState<string | null>(null);
  const [userUuid, setUserUuid] = useState<string | null>(null);
  const [email, setEmail] = useState<string | null>(null);
  const router = useRouter();

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
    const hashedEmail = await sha256Hash(email);
    const hashedPassword = await sha256Hash(password);
    
    const response = await loginForAccessSkTokenRouteApiAuthTokenPost({
      body: {
        username: hashedEmail,
        password: hashedPassword,
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
      router.push('/app/chat');
    }
  };

  const register = async (email: string, password: string) => {
    const hashedEmail = await sha256Hash(email);
    const hashedPassword = await sha256Hash(password);
    
    const response = await registerRouteApiAuthRegisterPost({
      body: {
        user_uuid: hashedEmail,
        hashed_password: hashedPassword
      }
    });
    
    if (response.data) {
      localStorage.setItem('authToken', response.data.access_token);
      setToken(response.data.access_token);
      localStorage.setItem('email', email);
      setEmail(email);
      const decodedToken = parseJwt(response.data.access_token);
      localStorage.setItem('userUuid', decodedToken.sub);
      setUserUuid(decodedToken.sub);
      router.push('/app/chat');
    }
  };

  const logout = () => {
    localStorage.removeItem('authToken');
    localStorage.removeItem('userUuid');
    localStorage.removeItem('email');
    setToken(null);
  };

  if (loading) {
    // Show a loading spinner at the center of the screen
    return <div className="flex justify-center items-center h-screen">
      <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-gray-900 dark:border-white"></div>
    </div>;
  }

  return (
    <AuthContext.Provider value={{
      token,
      login,
      register,
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