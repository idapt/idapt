import Image from "next/image";

export default function Header() {
  return (
    <div className="z-10 w-full flex items-center justify-left">
      <div className="flex items-center justify-center py-2">
        <a
          href="https://www.idapt.ai/"
          className="flex items-center justify-center font-nunito text-lg font-bold gap-2 ml-4"
        >
          <Image
            className="rounded-xl"
            src="/images/idapt_logo.png"
            alt="Idapt Logo"
            width={100}
            height={50}
            priority
          />
        </a>
      </div>
    </div>
  );
}
