import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { SettingsProvider } from "@/app/components/settings/settings-provider";
import "@/app/globals.css";
import "@/app/markdown.css";
import { Providers } from "@/app/components/providers/upload-provider";
import { UserProvider } from "@/app/contexts/user-context";
import { ProcessingStacksProvider } from "@/app/components/processing/processing-stacks-provider";

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
