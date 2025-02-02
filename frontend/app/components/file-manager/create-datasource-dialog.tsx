"use client";

import { useState } from "react";

import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/app/components/ui/dialog";
import { Input } from "@/app/components/ui/input";
import { Button } from "@/app/components/ui/button";
import { Textarea } from "@/app/components/ui/textarea";
import { useDatasources } from "./hooks/use-datasources";

interface CreateDatasourceDialogProps {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export function CreateDatasourceDialog({ open, onClose, onCreated }: CreateDatasourceDialogProps) {
  const { createDatasource } = useDatasources();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [embeddingSettingIdentifier, setEmbeddingSettingIdentifier] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCreate = async () => {
    if (!name.trim()) return;

    try {
      setLoading(true);
      setError(null);

      await createDatasource(name.trim(), {
        type: "FILES",
        description: description,
        settings_json: "{}",
        embedding_setting_identifier: embeddingSettingIdentifier,
      });

      onCreated();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create datasource');
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
        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Name</label>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter datasource name"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Description</label>
            <Textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Enter datasource description"
              rows={3}
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Embedding Setting Identifier</label>
            <Input
              value={embeddingSettingIdentifier}
              onChange={(e) => setEmbeddingSettingIdentifier(e.target.value)}
              placeholder="Enter embedding setting identifier"
            />
          </div>

          {error && (
            <p className="text-sm text-red-500 mt-1">{error}</p>
          )}

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