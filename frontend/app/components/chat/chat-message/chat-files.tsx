import { DocumentPreview } from "@/app/components/ui/document-preview";
import { DocumentFileData } from "@/app/components/chat";

export function ChatFiles({ data }: { data: DocumentFileData }) {
  if (!data.files.length) return null;
  return (
    <div className="flex gap-2 items-center">
      {data.files.map((file, index) => (
        <DocumentPreview key={file.id} file={file} />
      ))}
    </div>
  );
}
