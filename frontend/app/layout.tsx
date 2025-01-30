
import type { Metadata } from 'next';
import { Toaster } from 'sonner';

import { SettingsProvider } from "@/app/components/settings/settings-provider";
import "@/app/globals.css";
import "@/app/markdown.css";
import { Providers } from "@/app/components/providers/upload-provider";
import { UserProvider } from "@/app/contexts/user-context";
import { ProcessingStacksProvider } from "@/app/components/processing/processing-stacks-provider";
import { ThemeProvider } from '@/app/components/theme/theme-provider';

import './globals.css';
import { SidebarProvider } from './components/ui/sidebar';

export const metadata: Metadata = {
  metadataBase: new URL('https://idapt.ai'),
  title: 'idapt',
  description: 'idapt is a private personal data management platform that allows you to create your own personal AI by regrouping your data from multiple sources (Files, Emails, Google Drive, etc.) and allow your AI assistant to use it in your chats to provide a fully personalized experience.',
};

export const viewport = {
  maximumScale: 1, // Disable auto-zoom on mobile Safari
};

const LIGHT_THEME_COLOR = 'hsl(0 0% 100%)';
const DARK_THEME_COLOR = 'hsl(240deg 10% 3.92%)';
const THEME_COLOR_SCRIPT = `\
(function() {
  var html = document.documentElement;
  var meta = document.querySelector('meta[name="theme-color"]');
  if (!meta) {
    meta = document.createElement('meta');
    meta.setAttribute('name', 'theme-color');
    document.head.appendChild(meta);
  }
  function updateThemeColor() {
    var isDark = html.classList.contains('dark');
    meta.setAttribute('content', isDark ? '${DARK_THEME_COLOR}' : '${LIGHT_THEME_COLOR}');
  }
  var observer = new MutationObserver(updateThemeColor);
  observer.observe(html, { attributes: true, attributeFilter: ['class'] });
  updateThemeColor();
})();`;

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      // `next-themes` injects an extra classname to the body element to avoid
      // visual flicker before hydration. Hence the `suppressHydrationWarning`
      // prop is necessary to avoid the React hydration mismatch warning.
      // https://github.com/pacocoursey/next-themes?tab=readme-ov-file#with-app
      suppressHydrationWarning
    >
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: THEME_COLOR_SCRIPT,
          }}
        />
      </head>
      <body className="antialiased">
        <ThemeProvider
          attribute="class"
          defaultTheme="light"
          enableSystem
          disableTransitionOnChange
        >
          <UserProvider>
            <SidebarProvider>
              <Providers>
                <SettingsProvider>
                  <ProcessingStacksProvider>
                    <Toaster position="top-center" />
                    {children}
                  </ProcessingStacksProvider>
                </SettingsProvider>
              </Providers>
            </SidebarProvider>
          </UserProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
