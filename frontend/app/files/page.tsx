import Header from "@/app/components/header";
import { Settings } from "../components/ui/settings";
import { NavMenu } from "../components/ui/nav/nav-menu";

export default function Files() {
  return (
    <main className="h-screen w-screen flex justify-center items-center background-gradient">
      <Settings />
      <NavMenu />
      <div className="space-y-0 w-[90%] h-full">
        <Header />
        <div className="flex h-[calc(95vh-64px)] min-h-[400px]">
          {/* Files content will go here */}
          <div className="w-full flex items-center justify-center text-gray-500">
            Files management coming soon...
          </div>
        </div>
      </div>
    </main>
  );
}