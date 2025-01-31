'use client';

import { User, LogOut, Moon, Sun, UserIcon } from 'lucide-react';
import { useTheme } from 'next-themes';
import { Button } from '@/app/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from '@/app/components/ui/dropdown-menu';
import { useUser } from '@/app/contexts/user-context';

export function SidebarUserNav() {
  const { theme, setTheme } = useTheme();
  const { userId } = useUser();

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="w-full justify-start gap-2">
          <UserIcon className="h-5 w-5" />
          <span className="truncate">{userId}</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}>
          {theme === 'light' ? (
            <>
              <Moon className="h-4 w-4 mr-2" />
              Dark Mode
            </>
          ) : (
            <>
              <Sun className="h-4 w-4 mr-2" />
              Light Mode
            </>
          )}
        </DropdownMenuItem>
        {/* <DropdownMenuSeparator /> */}
        {/* <DropdownMenuItem onClick={logout}>
          <LogOut className="h-4 w-4 mr-2" />
          Logout
        </DropdownMenuItem> */}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
