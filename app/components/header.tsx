import Image from "next/image";

export default function Header() {
  return (
    <div className="z-10 max-w-5xl w-full flex items-center justify-center font-mono text-sm">
      <div className="fixed top-0 left-0 right-0 flex h-auto items-center justify-center bg-gradient-to-t from-white via-white dark:from-black dark:via-black lg:bg-none lg:static lg:w-auto lg:mb-0">
        <a
          href="https://idapt.ai/"
          className="flex items-center justify-center font-nunito text-lg font-bold gap-2"
        >
          <Image
            className="rounded-xl"
            src="/idaptLogo.png"
            alt="idapt Logo"
            width={100}
            height={100}
            priority
          />
        </a>
      </div>
    </div>
  );
}
