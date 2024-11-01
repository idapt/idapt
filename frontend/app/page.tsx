import Header from "@/app/components/header";
import { Settings } from "./components/ui/settings";
import ChatSection from "./components/chat-section";

export default function Home() {
  return (
    <main className="h-screen w-screen flex justify-center items-center background-gradient">
      <Settings />
      <div className="space-y-0 w-[90%] h-full">
        <Header />
        <div className="flex h-[calc(95vh-64px)] min-h-[400px]">
          <ChatSection />
        </div>
      </div>
    </main>
  );
}
