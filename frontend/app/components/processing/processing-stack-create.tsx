import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../ui/dialog';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Textarea } from '../ui/textarea';
import { useClientConfig } from '@/app/components/chat/hooks/use-config';
import { useApiClient } from '@/app/lib/api-client';

interface ProcessingStackCreateProps {
  isOpen: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export function ProcessingStackCreate({ isOpen, onClose, onCreated }: ProcessingStackCreateProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [extensions, setExtensions] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { backend } = useClientConfig();
  const { fetchWithAuth } = useApiClient();

  const handleSubmit = async () => {
    try {
      setIsSubmitting(true);
      const extensionList = extensions
        .split(',')
        .map(ext => ext.trim())
        .filter(ext => ext)
        .map(ext => ext.startsWith('.') ? ext : `.${ext}`);

      const response = await fetchWithAuth(`${backend}/api/stacks/stacks`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          display_name: name,
          description,
          supported_extensions: extensionList,
          steps: []
        })
      });
  
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to create stack');
      }
  
      onCreated();
      onClose();
    } catch (error) {
      console.error('Failed to create stack:', error);
      window.alert((error as Error).message || 'Failed to create stack');
    } finally {
      setIsSubmitting(false);
      setName('');
      setDescription('');
      setExtensions('');
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create New Processing Stack</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium">Name</label>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter stack name"
            />
          </div>
          <div>
            <label className="text-sm font-medium">Description</label>
            <Textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Enter stack description"
            />
          </div>
          <div>
            <label className="text-sm font-medium">Supported File Extensions</label>
            <Input
              value={extensions}
              onChange={(e) => setExtensions(e.target.value)}
              placeholder="e.g. .pdf, .txt, .md"
            />
            <p className="text-sm text-muted-foreground mt-1">
              Separate extensions with commas
            </p>
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={onClose}>Cancel</Button>
            <Button 
              onClick={handleSubmit} 
              disabled={!name.trim() || isSubmitting}
            >
              Create Stack
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
} 