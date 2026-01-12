'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import axios from 'axios';
import { Mail, ArrowLeft, Loader2, CheckCircle2 } from 'lucide-react';
import Image from 'next/image';
import Link from 'next/link';

export default function ForgotPasswordPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<'idle' | 'success'>('idle');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await axios.post('/api/auth/request-reset', { email });
      setStatus('success');
    } catch (err: any) {
      setError(err.response?.data?.detail || "エラーが発生しました");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-2xl glass-card overflow-hidden px-12 py-16">
        <div className="flex justify-center mb-8">
          <div className="h-16 w-56 relative">
            <Image src="/logo.svg" alt="Small Voice Logo" fill className="object-contain" priority />
          </div>
        </div>

        {status === 'success' ? (
          <div className="text-center animate-in fade-in duration-500">
            <CheckCircle2 className="h-16 w-16 text-green-500 mx-auto mb-6" />
            <h2 className="text-2xl font-bold text-gray-800 mb-4">リセットメールを送信しました</h2>
            <p className="text-gray-600 mb-8">
              入力いただいたメールアドレスに、パスワード再設定用のリンクを送信しました。<br />
              ターミナルのログを確認してください（ローカル環境の場合）。
            </p>
            <Link href="/login" className="btn-primary px-8 py-3 flex items-center justify-center gap-2 max-w-sm mx-auto">
              ログイン画面に戻る
            </Link>
          </div>
        ) : (
          <div className="w-full max-w-sm mx-auto">
            <h2 className="text-2xl font-bold text-sage-dark text-center mb-2">パスワードの再設定</h2>
            <p className="text-center text-slate-500 mb-8 text-sm">登録済みのメールアドレスを入力してください。<br />再設定用のリンクをお送りします。</p>

            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label className="block text-sm font-bold text-sage-dark mb-1 ml-1">メールアドレス</label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Mail className="h-5 w-5 text-slate-400" />
                  </div>
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="block w-full pl-10 pr-3 py-3 glass-input ring-0 outline-none"
                    placeholder="name@company.com"
                  />
                </div>
              </div>

              {error && (
                <div className="bg-red-50 border border-red-100 text-red-600 text-xs p-3 rounded-xl flex items-center shadow-sm">
                  <span className="mr-2">⚠️</span>
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full flex justify-center py-3 px-4 btn-primary disabled:opacity-70 disabled:cursor-not-allowed"
              >
                {loading ? <Loader2 className="animate-spin h-5 w-5" /> : "リセットメールを送信"}
              </button>
            </form>

            <div className="mt-8 text-center">
              <Link href="/login" className="text-sm text-slate-400 hover:text-sage-primary transition-colors font-medium flex items-center justify-center gap-2">
                <ArrowLeft className="h-4 w-4" /> ログイン画面に戻る
              </Link>
            </div>
          </div>
        )}
      </div>
      <div className="mt-8 text-xs text-slate-500 font-medium italic">
        © SmallVoice Inc.
      </div>
    </div>
  );
}
