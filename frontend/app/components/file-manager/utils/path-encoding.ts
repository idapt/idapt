import { Buffer } from 'buffer';

export function encodePathSafe(path: string): string {
  if (!path) return '';
  return Buffer.from(path)
    .toString('base64')
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    //.replace(/=+$/, '');
}

export function decodePathSafe(encoded: string): string {
  if (!encoded) return '';
  // Add back padding if needed
  encoded = encoded.replace(/-/g, '+').replace(/_/g, '/');
  while (encoded.length % 4) {
    encoded += '=';
  }
  return Buffer.from(encoded, 'base64').toString();
} 