'use client';

import { useState } from 'react';
import { Copy, Check } from 'lucide-react';

interface CopyButtonProps {
  text: string;
  className?: string;
}

export function CopyButton({ text, className = "" }: CopyButtonProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy: ', err);
    }
  };

  return (
    <button
      onClick={handleCopy}
      className={`inline-flex items-center justify-center p-1 rounded-md hover:bg-sage-100 transition-colors text-sage-600 hover:text-sage-700 ${className}`}
      title="コピーする"
    >
      {copied ? (
        <Check className="w-4 h-4 text-green-600 animate-in fade-in zoom-in duration-200" />
      ) : (
        <Copy className="w-4 h-4" />
      )}
    </button>
  );
}
