'use client';

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Users, Shield, Settings } from 'lucide-react';
import Link from 'next/link';

interface Member {
  id: number;
  username: string;
  email: string;
  role: string;
}

export default function MemberList({ user }: { user: any }) {
  const [members, setMembers] = useState<Member[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchMembers = async () => {
      if (!user?.current_org_id) return;
      try {
        setLoading(true);
        const res = await axios.get(`/api/organizations/${user.current_org_id}/members`, { withCredentials: true });
        setMembers(res.data);
      } catch (error) {
        console.error("Failed to fetch members", error);
      } finally {
        setLoading(false);
      }
    };
    fetchMembers();
  }, [user?.current_org_id]);

  if (loading) return <div className="text-center py-12">読み込み中...</div>;

  return (
    <div className="max-w-4xl mx-auto glass-card p-4 md:p-8 animate-in fade-in slide-in-from-bottom-2">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-8">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-sage-100 text-sage-600 rounded-full flex items-center justify-center shrink-0">
            <Users className="h-6 w-6" />
          </div>
          <div>
            <h2 className="text-xl md:text-2xl font-bold text-sage-dark">メンバーリスト</h2>
            <p className="text-slate-500 text-xs sm:text-sm">組織に参加しているメンバー一覧</p>
          </div>
        </div>
        {user?.role === 'system_admin' && (
          <Link href="/admin/system" className="btn-primary px-4 py-2.5 flex items-center gap-2 text-sm w-full sm:w-auto justify-center">
            <Settings className="h-4 w-4" /> システム管理を開く
          </Link>
        )}
      </div>

      {/* Desktop Table View */}
      <div className="hidden md:block overflow-hidden rounded-xl border border-gray-200">
        <table className="w-full text-left text-sm">
          <thead className="bg-sage-50 text-sage-700 font-bold uppercase">
            <tr>
              <th className="px-6 py-4 border-b border-gray-200">名前</th>
              <th className="px-6 py-4 border-b border-gray-200">メールアドレス</th>
              <th className="px-6 py-4 border-b border-gray-200">権限</th>
              <th className="px-6 py-4 border-b border-gray-200 text-right">ステータス</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 bg-white">
            {members.length > 0 ? members.map(m => (
              <tr key={m.id} className="hover:bg-gray-50/50 transition-colors">
                <td className="px-6 py-4 font-bold text-gray-800">{m.username}</td>
                <td className="px-6 py-4 text-gray-500 font-mono">{m.email}</td>
                <td className="px-6 py-4">
                  <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold ${m.role === 'admin' ? 'bg-amber-100 text-amber-700 border border-amber-200' : 'bg-slate-100 text-slate-500 border border-slate-200'}`}>
                    {m.role === 'admin' && <Shield className="h-3 w-3" />}
                    {m.role === 'admin' ? '組織管理者' : '一般メンバー'}
                  </span>
                </td>
                <td className="px-6 py-4 text-right">
                  <span className="inline-flex items-center gap-1.5 text-green-600 text-xs font-bold">
                    <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></span>
                    Active
                  </span>
                </td>
              </tr>
            )) : (
              <tr>
                <td colSpan={4} className="px-6 py-12 text-center text-slate-400">
                  メンバーがいません
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Mobile Card View */}
      <div className="md:hidden space-y-4">
        {members.length > 0 ? members.map(m => (
          <div key={m.id} className="bg-white p-4 rounded-xl border border-gray-100 shadow-sm space-y-3">
            <div className="flex justify-between items-start">
              <div>
                <div className="font-bold text-gray-800">{m.username}</div>
                <div className="text-xs text-slate-400 font-mono mt-0.5">{m.email}</div>
              </div>
              <span className="text-green-600 text-[10px] font-bold px-1.5 py-0.5 bg-green-50 rounded border border-green-100">
                Active
              </span>
            </div>
            <div className="pt-2 border-t border-gray-50 flex justify-between items-center">
              <span className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-lg text-xs font-bold ${m.role === 'admin' ? 'bg-amber-50 text-amber-700 border border-amber-100' : 'bg-slate-50 text-slate-500 border border-slate-100'}`}>
                {m.role === 'admin' && <Shield className="h-3 w-3" />}
                {m.role === 'admin' ? '組織管理者' : '一般メンバー'}
              </span>
            </div>
          </div>
        )) : (
          <div className="p-8 text-center text-slate-400 bg-white rounded-xl border border-dashed border-gray-200">
            メンバーがいません
          </div>
        )}
      </div>

      <div className="mt-8 pt-4 border-t border-gray-100 text-center text-xs text-slate-400">
        ※ メンバーの追加・招待はシステム管理画面から可能です
      </div>
    </div>
  );
}
