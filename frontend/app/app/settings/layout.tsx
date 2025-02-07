import { SettingsProvider } from "@/app/components/settings/settings-provider";

export default function SettingsLayout({ children }: { children: React.ReactNode }) {
    return (
        <SettingsProvider>
            {children}
        </SettingsProvider>
    );
}
