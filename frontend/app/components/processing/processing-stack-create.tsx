import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../ui/dialog';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { useClientConfig } from '@/app/components/chat/hooks/use-config';
import { useApiClient } from '@/app/lib/api-client';

interface ProcessingStackCreateProps {
  isOpen: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export function ProcessingStackCreate({ isOpen, onClose, onCreated }: ProcessingStackCreateProps) {
  const [name, setName] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { backend } = useClientConfig();
  const { fetchWithAuth } = useApiClient();

  const handleSubmit = async () => {
    try {
      setIsSubmitting(true);

      const response = await fetchWithAuth(`${backend}/api/stacks/stacks`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          display_name: name
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