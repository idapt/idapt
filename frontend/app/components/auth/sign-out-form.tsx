import { Button } from '@/app/components/ui/button';
import { useAuth } from '@/app/components/auth/auth-context';

export const SignOutForm = () => {
  const { logout } = useAuth();

  return (
    <Button 
      onClick={logout}
      variant="ghost"
      className="text-red-500 hover:text-red-600"
    >
      Sign Out
    </Button>
  );
};