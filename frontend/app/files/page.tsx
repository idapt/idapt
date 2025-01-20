import Header from "@/app/components/header";
import { Settings } from "@/app/components/settings";
import { NavMenu } from "@/app/components/nav/nav-menu";
import { FileManager } from "@/app/components/file-manager/file-manager";
import { ProcessingStacks } from "@/app/components/processing/processing-stacks";

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
      <ProcessingStacks />
    </main>
  );
} 