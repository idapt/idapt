const DEFAULT_BACKOFF_OPTIONS = {
  initialDelay: 1000,
  maxDelay: 30000,
  maxAttempts: 5
};

export async function withBackoff<T>(
  fn: () => Promise<T>,
  options = DEFAULT_BACKOFF_OPTIONS
): Promise<T> {
  let attempts = 0;
  let delay = options.initialDelay;

  while (attempts < options.maxAttempts) {
    try {
      return await fn();
    } catch (error) {
      attempts++;
      if (attempts === options.maxAttempts) {
        throw error;
      }
      await new Promise(resolve => setTimeout(resolve, delay));
      delay = Math.min(delay * 2, options.maxDelay);
    }
  }
  throw new Error('Max attempts reached');
} 