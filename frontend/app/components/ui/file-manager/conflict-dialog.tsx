import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../dialog";
import { Button } from "../button";
import { FileConflict } from "@/app/types/vault";

interface ConflictDialogProps {
  conflict: FileConflict;
  onResolve: (resolution: ConflictResolution) => void;
  remainingConflicts: number;
}

export function ConflictDialog({ conflict, onResolve, remainingConflicts }: ConflictDialogProps) {
  return (
    <Dialog open={true}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>File Already Exists</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <p>
            The file "{conflict.name}" already exists at path "{conflict.path}".
            What would you like to do?
          </p>
          <div className="flex justify-end space-x-2">
            <Button variant="outline" onClick={() => onResolve('skip')}>
              Skip
            </Button>
            {remainingConflicts > 0 && (
              <Button variant="outline" onClick={() => onResolve('skip_all')}>
                Skip All
              </Button>
            )}
            <Button variant="outline" onClick={() => onResolve('overwrite')}>
              Overwrite
            </Button>
            {remainingConflicts > 0 && (
              <Button variant="default" onClick={() => onResolve('overwrite_all')}>
                Overwrite All
              </Button>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
} 