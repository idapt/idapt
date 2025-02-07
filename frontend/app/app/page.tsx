'use client';
// Simply redirect to the chat page if the user is authenticated, otherwise redirect to the login page
import { redirect } from 'next/navigation';
import { useAuth } from '@/app/components/auth/auth-context';

export default function AppPage() {
  const { isAuthenticated } = useAuth();
  if (isAuthenticated) {
    return redirect('/app/chat');
  } else {
    return redirect('/auth/login');
  }
}