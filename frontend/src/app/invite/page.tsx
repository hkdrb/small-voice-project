'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import axios from 'axios';
import { Lock, CheckCircle2, Loader2, AlertCircle, Eye, EyeOff } from 'lucide-react';
import Image from 'next/image';

function InviteContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get('token');

  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState('');

  if (!token) {
    return (
      <div className="text-center">
        <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
        <h2 className="text-xl font-bold text-gray-800 mb-2">無効なURLです</h2>
        <p className="text-gray-500">招待トークンが見つかりません。管理者にお問い合わせください。</p>
      </div>
    );
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      return setErrorMessage("パスワードが一致しません");
    }
    if (password.length < 8) {
      return setErrorMessage("パスワードは8文字以上で入力してください");
    }

    setLoading(true);
    setErrorMessage("");

    try {
      // 招待・リセット共通のパスワード設定エンドポイント (backend/api/auth.py に実装済みと想定)
      await axios.post('/api/auth/reset-password', {
        token: token,
        new_password: password
      });
      setStatus('success');
      setTimeout(() => router.push('/login'), 3000);
    } catch (err: any) {
      setErrorMessage(err.response?.data?.detail || "パスワードの設定に失敗しました。期限切れの可能性があります。");
      setStatus('error');
    } finally {
      setLoading(false);
    }
  };

  if (status === 'success') {
    return (
      <div className="text-center animate-in fade-in duration-500">
        <CheckCircle2 className="h-16 w-16 text-green-500 mx-auto mb-6" />
        <h2 className="text-2xl font-bold text-gray-800 mb-4">設定完了！</h2>
        <p className="text-gray-600 mb-8">パスワードが正常に設定されました。<br />3秒後にログイン画面へ移動します。</p>
        <button onClick={() => router.push('/login')} className="btn-primary px-8 py-3">ログイン画面へ</button>
      </div>
    );
  }

  return (
    <div className="w-full max-w-sm mx-auto">
      <h2 className="text-2xl font-bold text-sage-dark text-center mb-2">パスワードの設定</h2>
      <p className="text-center text-slate-500 mb-8 text-sm">Small Voice へようこそ！<br />新しく使用するパスワードを設定してください。</p>

      <form onSubmit={handleSubmit} className="space-y-5">
        <div>
          <label className="block text-sm font-bold text-sage-dark mb-1 ml-1">新しいパスワード</label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Lock className="h-5 w-5 text-slate-400" />
            </div>
            <input
              type={showPassword ? "text" : "password"}
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="block w-full pl-10 pr-10 py-3 glass-input ring-0 outline-none"
              placeholder="8文字以上"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-600"
            >
              {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
            </button>
          </div>
        </div>

        <div>
          <label className="block text-sm font-bold text-sage-dark mb-1 ml-1">パスワードの確認</label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Lock className="h-5 w-5 text-slate-400" />
            </div>
            <input
              type={showConfirmPassword ? "text" : "password"}
              required
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="block w-full pl-10 pr-10 py-3 glass-input ring-0 outline-none"
              placeholder="同じパスワードを入力"
            />
            <button
              type="button"
              onClick={() => setShowConfirmPassword(!showConfirmPassword)}
              className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-600"
            >
              {showConfirmPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
            </button>
          </div>
        </div>

        {errorMessage && (
          <div className="bg-red-50 border border-red-100 text-red-600 text-xs p-3 rounded-xl flex items-center shadow-sm">
            <AlertCircle className="w-4 h-4 mr-2" />
            {errorMessage}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full flex justify-center py-3 px-4 btn-primary disabled:opacity-70 disabled:cursor-not-allowed group"
        >
          {loading ? (
            <Loader2 className="animate-spin h-5 w-5" />
          ) : (
            <>
              設定を保存してログイン
            </>
          )}
        </button>
      </form>
    </div>
  );
}

export default function InvitePage() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-2xl glass-card overflow-hidden px-12 py-16">
        <div className="flex justify-center mb-8">
          <div className="h-16 w-56 relative">
            <Image src="/logo.svg" alt="Small Voice Logo" fill className="object-contain" priority />
          </div>
        </div>

        <Suspense fallback={<div className="flex justify-center"><Loader2 className="animate-spin h-8 w-8 text-sage-primary" /></div>}>
          <InviteContent />
        </Suspense>
      </div>
      <div className="mt-8 text-xs text-slate-500 font-medium italic">
        © SmallVoice Inc.
      </div>
    </div>
  );
}
