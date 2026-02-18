"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import axios from "axios";
import { Lock, Mail, Eye, EyeOff, Loader2 } from "lucide-react";
import Image from "next/image";
import Link from "next/link";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      // Use relative path for proxy
      const response = await axios.post("/api/auth/login", {
        username: email,
        password: password,
      }, {
        withCredentials: true // Important for cookies
      });

      if (response.status === 200) {
        router.replace("/dashboard");
      }
    } catch (err: any) {
      if (err.response) {
        setError(err.response.data.detail || "ログインに失敗しました");
      } else {
        setError("サーバーに接続できませんでした");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-dvh flex flex-col items-center justify-center p-4">
      {/* Increased max-width and padding as requested by user */}
      <div className="w-full max-w-2xl glass-card overflow-hidden px-12 py-16">
        <div className="">
          <div className="flex justify-center mb-3">
            <div className="h-24 w-80 relative">
              <Image
                src="/logo.svg"
                alt="Small Voice Logo"
                fill
                className="object-contain drop-shadow-sm"
                priority
              />
            </div>
          </div>

          {/* Removed "Small Voice" heading, only subtitle */}
          <p className="text-center text-slate-500 mb-12 font-medium text-lg">小さな声を創造に変える</p>

          <form onSubmit={handleLogin} className="space-y-6 max-w-sm mx-auto">
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
                  autoComplete="username"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-bold text-sage-dark mb-1 ml-1">パスワード</label>
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
                  placeholder="••••••••"
                  autoComplete="current-password"
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

            {error && (
              <div className="bg-white/80 border border-red-200 text-red-600 text-sm p-3 rounded-xl flex items-center shadow-sm">
                <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full flex justify-center py-3 px-4 btn-primary disabled:opacity-70 disabled:cursor-not-allowed"
            >
              {loading ? (
                <Loader2 className="animate-spin h-5 w-5" />
              ) : (
                "ログイン"
              )}
            </button>
          </form>

          <div className="mt-8 text-center">
            <Link href="/forgot-password" title="パスワードの再設定" className="text-sm text-slate-400 hover:text-sage-primary transition-colors font-medium">
              パスワードをお忘れですか？
            </Link>
          </div>
        </div>
      </div>
      <div className="mt-8 text-xs text-slate-500 font-medium">
        © SmallVoice Inc. v2.0
      </div>
    </div>
  );
}
