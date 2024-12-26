import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { SettingsProvider } from "./components/ui/settings";
import "./globals.css";
import "./markdown.css";
import { Providers } from './components/providers/upload-provider';

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
        <Providers>
          <SettingsProvider>{children}</SettingsProvider>
        </Providers>
      </body>
    </html>
  );
}
