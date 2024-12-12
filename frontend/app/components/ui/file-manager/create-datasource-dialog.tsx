import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../dialog";
import { Input } from "../input";
import { Button } from "../button";
import { useClientConfig } from "../chat/hooks/use-config";

interface CreateDatasourceDialogProps {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export function CreateDatasourceDialog({ open, onClose, onCreated }: CreateDatasourceDialogProps) {
  const { backend } = useClientConfig();
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);

  const handleCreate = async () => {
    if (!name.trim()) return;

    try {
      setLoading(true);
      const response = await fetch(`${backend}/api/datasources`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: name.trim(),
          type: 'files',
          settings: {}
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to create datasource');
      }

      onCreated();
      onClose();
      setName("");
    } catch (error) {
      console.error('Failed to create datasource:', error);
      alert('Failed to create datasource');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create New Datasource</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 p-4">
          <Input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Enter datasource name"
          />
          <div className="flex justify-end space-x-2">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button onClick={handleCreate} disabled={loading}>
              Create
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
} 