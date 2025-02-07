import { useAuth } from '@/app/components/auth/auth-context';
import { Input } from '@/app/components/ui/input';
import { Label } from '@/app/components/ui/label';
import { Button } from '@/app/components/ui/button';
import { useState, useEffect } from 'react';
import Image from 'next/image';
import Link from 'next/link';

export function AuthForm({ mode: initialMode }: { mode: 'login' | 'register' }) {
  const [mode, setMode] = useState<'login' | 'register'>(initialMode);
  const [emailValue, setEmailValue] = useState('');
  const { login, register } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const savedEmail = localStorage.getItem('email');
    if (savedEmail) setEmailValue(savedEmail);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    
    const formData = new FormData(e.currentTarget as HTMLFormElement);
    const email = formData.get('email') as string;
    const password = formData.get('password') as string;

    try {
      if (mode === 'login') {
        await login(email, password);
      } else {
        await register(email, password);
      }
    } catch (err) {
      setError(mode === 'login' 
        ? 'Invalid credentials. Please try again.'
        : 'Registration failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md">
      <div className="mb-8 flex justify-center">
        <a href="https://www.idapt.ai/">
          <Image 
            src="/images/idapt_logo.png" 
            alt="Idapt Logo"
            width={120}
            height={40}
          />
        </a>
      </div>
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div className="flex flex-col gap-2">
          <Label htmlFor="email">Email Address</Label>
          <Input
            id="email"
            name="email"
            type="email"
            placeholder="user@example.com"
            autoComplete="email"
            required
            autoFocus
            value={emailValue}
            onChange={(e) => setEmailValue(e.target.value)}
          />
        </div>

        <div className="flex flex-col gap-2">
          <Label htmlFor="password">Password</Label>
          <Input
            id="password"
            name="password"
            type="password"
            required
            minLength={8}
          />
        </div>

        {error && <p className="text-red-500 text-sm">{error}</p>}

        <Button type="submit" disabled={isLoading} className="w-full">
          {isLoading 
            ? (mode === 'login' ? 'Signing in...' : 'Creating account...')
            : (mode === 'login' ? 'Sign In' : 'Sign Up')}
        </Button>

        <div className="mt-4 text-center text-sm">
          <Link 
            href={mode === 'login' ? '/auth/register' : '/auth/login'}
            className="text-primary underline hover:text-primary/80"
          >
            {mode === 'login' 
              ? "Don't have an account? Register here"
              : "Already have an account? Login here"}
          </Link>
        </div>
      </form>
    </div>
  );
}