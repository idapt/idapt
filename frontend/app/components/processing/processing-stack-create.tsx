import { useState } from 'react';
import { Button } from '@/app/components/ui/button';
import { Input } from '@/app/components/ui/input';
import { useApiClient } from '@/app/lib/api-client';
import { createProcessingStackRouteApiStacksStacksPost } from '@/app/client';

interface ProcessingStackCreateProps {
  isOpen: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export function ProcessingStackCreate({ isOpen, onClose, onCreated }: ProcessingStackCreateProps) {
  const [name, setName] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const client = useApiClient();

  if (!isOpen) return null;

  const handleSubmit = async () => {
    try {
      setIsSubmitting(true);

      await createProcessingStackRouteApiStacksStacksPost({
        client,
        body: {
          display_name: name
        }
      });
  
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
    <div className="space-y-4 p-4 border rounded-lg">
      <h4 className="font-medium">Create New Processing Stack</h4>
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
    </div>
  );
} 