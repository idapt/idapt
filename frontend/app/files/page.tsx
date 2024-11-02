import Header from "@/app/components/header";
import { Settings } from "../components/ui/settings";
import { NavMenu } from "../components/ui/nav/nav-menu";
import { FileManager } from "../components/ui/file-manager/file-manager";

export default function Files() {
  return (
    <main className="h-screen w-screen flex justify-center items-center background-gradient">
      <Settings />
      <NavMenu />
      <div className="space-y-0 w-[90%] h-full">
        <Header />
        <div className="flex h-[calc(95vh-64px)] min-h-[400px]">
          <FileManager />
        </div>
      </div>
    </main>
  );
}