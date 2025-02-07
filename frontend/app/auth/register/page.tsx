'use client';

import { AuthForm } from '@/app/components/auth/auth-form';

export default function RegisterPage() {
  return (
    <div className="flex h-screen w-screen items-center justify-center bg-background">
      <AuthForm mode="register" />
    </div>
  );
}






