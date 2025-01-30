import Header from "@/app/components/header";
import { Settings } from "@/app/components/settings";
import { ResetButton } from "@/app/components/chat/reset-button";
import { NavMenu } from "@/app/components/nav/nav-menu";
import ChatSection from "@/app/components/chat-section";

export default function App() {
  return (
    <main className="h-screen w-screen flex justify-center items-center background-gradient">
      <ResetButton />
      <Settings />
      <NavMenu />
      <div className="space-y-0 w-[90%] h-full">
        <Header />
        <div className="flex h-[calc(95vh-64px)] min-h-[400px]">
          <ChatSection />
        </div>
      </div>
    </main>
  );
}
