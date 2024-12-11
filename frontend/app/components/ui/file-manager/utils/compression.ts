import pako from 'pako';

export function compressData(data: string): Uint8Array {
  try {
    // Convert base64 string to binary data
    const binaryData = atob(data.split(',')[1]);
    const bytes = new Uint8Array(binaryData.length);
    for (let i = 0; i < binaryData.length; i++) {
      bytes[i] = binaryData.charCodeAt(i);
    }
    
    // Compress the binary data
    const compressed = pako.deflate(bytes, { level: 6 });
    
    // Convert back to base64
    return compressed;
  } catch (error) {
    console.error('Compression error:', error);
    throw error;
  }
}

export function arrayBufferToBase64(buffer: Uint8Array): string {
  let binary = '';
  const bytes = new Uint8Array(buffer);
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
} 