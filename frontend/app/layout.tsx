import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { SettingsProvider } from "./components/ui/settings/settings-provider";
import "./globals.css";
import "./markdown.css";
import { Providers } from './components/providers/upload-provider';
import { UserProvider } from './contexts/user-context';
import { ProcessingStacksProvider } from "./components/ui/processing/processing-stacks-provider";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "idapt",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <UserProvider>
          <Providers>
            <SettingsProvider>
              <ProcessingStacksProvider>
                {children}
              </ProcessingStacksProvider>
            </SettingsProvider>
          </Providers>
        </UserProvider>
      </body>
    </html>
  );
}
