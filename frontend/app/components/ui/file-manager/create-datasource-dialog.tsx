import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../dialog";
import { Input } from "../input";
import { Button } from "../button";
import { useClientConfig } from "../chat/hooks/use-config";
import { useApiClient } from "@/app/lib/api-client";

interface CreateDatasourceDialogProps {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export function CreateDatasourceDialog({ open, onClose, onCreated }: CreateDatasourceDialogProps) {
  const { backend } = useClientConfig();
  const { fetchWithAuth } = useApiClient();
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCreate = async () => {
    if (!name.trim()) return;

    try {
      setLoading(true);
      setError(null);
      const response = await fetchWithAuth(`${backend}/api/datasources`, {
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
        const data = await response.json();
        throw new Error(data.detail || 'Failed to create datasource');
      }

      onCreated();
      onClose();
      setName("");
    } catch (error) {
      console.error('Failed to create datasource:', error);
      setError(error instanceof Error ? error.message : 'Failed to create datasource');
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
          <div>
            <Input
              value={name}
              onChange={(e) => {
                setName(e.target.value);
                setError(null);
              }}
              placeholder="Enter datasource name"
            />
            {error && (
              <p className="text-sm text-red-500 mt-1">{error}</p>
            )}
          </div>
          <div className="flex justify-end space-x-2">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button onClick={handleCreate} disabled={loading}>
              {loading ? 'Creating...' : 'Create'}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
} 