"use client";

import { ProcessingStacksButton } from './processing-stacks-button';
import { ProcessingStacksDialog } from './processing-stacks-dialog';
import { useProcessingStacksDialog } from './processing-stacks-provider';

export function ProcessingStacks() {
  const { isOpen, openProcessingStacks, closeProcessingStacks } = useProcessingStacksDialog();

  return (
    <>
      <ProcessingStacksButton onClick={openProcessingStacks} />
      <ProcessingStacksDialog isOpen={isOpen} onClose={closeProcessingStacks} />
    </>
  );
} 