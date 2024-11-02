"use client";

import { FileItem } from "./file-item";

export function FileGrid() {
  // Placeholder data - will be replaced with real data later
  const files = [
    { name: "Document.pdf", type: "file", size: "2.4 MB", modified: "2024-03-31" },
    { name: "Images", type: "folder", modified: "2024-03-30" },
    { name: "Report.docx", type: "file", size: "1.2 MB", modified: "2024-03-29" },
  ];

  return (
    <div className="grid grid-cols-4 gap-4">
      {files.map((file) => (
        <FileItem
          key={file.name}
          name={file.name}
          type={file.type as "file" | "folder"}
          size={file.size}
          modified={file.modified}
        />
      ))}
    </div>
  );
} 