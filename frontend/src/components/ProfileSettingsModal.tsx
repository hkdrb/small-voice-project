import React, { useState } from 'react';
import axios from 'axios';
import { User, Lock, X } from 'lucide-react';

interface ProfileSettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  user: {
    name?: string;
    email?: string;
  } | null;
}

export default function ProfileSettingsModal({ isOpen, onClose, user }: ProfileSettingsModalProps) {
  const [name, setName] = useState(user?.name || '');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage(null);

    try {
      // Build payload
      const payload: any = {};
      if (name) payload.name = name;
      if (password) payload.password = password;

      if (Object.keys(payload).length === 0) {
        setLoading(false);
        return;
      }

      await axios.put('/api/auth/me', payload, { withCredentials: true });
      setMessage({ type: 'success', text: 'プロフィールを更新しました' });
      setPassword(''); // Clear password field
      setTimeout(() => {
        window.location.reload(); // Reload to reflect changes
      }, 1000);
    } catch (error: any) {
      console.error('Failed to update profile:', error);
      setMessage({
        type: 'error',
        text: error.response?.data?.message || 'プロフィールの更新に失敗しました'
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-md overflow-hidden animate-in zoom-in-95 duration-200">

        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between bg-gray-50/50">
          <h2 className="text-lg font-bold text-gray-800 flex items-center gap-2">
            <User className="h-5 w-5 text-sage-primary" />
            プロフィール設定
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors p-1 rounded-full hover:bg-gray-100"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">

          {message && (
            <div className={`p-3 rounded-lg text-sm font-medium ${message.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
              }`}>
              {message.text}
            </div>
          )}

          <div className="space-y-2">
            <label className="text-sm font-bold text-gray-700 block">
              名前
            </label>
            <div className="relative">
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="名前を入力"
                className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-sage-primary/20 focus:border-sage-primary transition-all"
              />
              <User className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-bold text-gray-700 block">
              新しいパスワード
              <span className="ml-2 text-xs font-normal text-gray-400">（変更する場合のみ入力）</span>
            </label>
            <div className="relative">
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-sage-primary/20 focus:border-sage-primary transition-all"
              />
              <Lock className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
            </div>
          </div>

          <div className="pt-4 flex justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-800 hover:bg-gray-50 rounded-lg transition-colors"
            >
              キャンセル
            </button>
            <button
              type="submit"
              disabled={loading}
              className={`
                px-6 py-2 text-sm font-bold text-white rounded-lg shadow-sm transition-all
                ${loading
                  ? 'bg-slate-300 cursor-not-allowed'
                  : 'bg-sage-primary hover:bg-sage-dark hover:shadow-md active:scale-95'
                }
              `}
            >
              {loading ? '保存中...' : '変更を保存'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
