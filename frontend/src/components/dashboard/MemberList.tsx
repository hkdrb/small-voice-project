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
    <div className="max-w-4xl mx-auto glass-card p-8 animate-in fade-in slide-in-from-bottom-2">
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-sage-100 text-sage-600 rounded-full flex items-center justify-center">
            <Users className="h-6 w-6" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-sage-dark">メンバーリスト</h2>
            <p className="text-slate-500 text-sm">組織に参加しているメンバー一覧</p>
          </div>
        </div>
        {user?.role === 'system_admin' && (
          <Link href="/admin/system" className="btn-primary px-4 py-2 flex items-center gap-2 text-sm">
            <Settings className="h-4 w-4" /> システム管理を開く
          </Link>
        )}
      </div>

      <div className="overflow-hidden rounded-xl border border-gray-200">
        <table className="w-full text-left text-sm">
          <thead className="bg-sage-50 text-sage-700 font-bold uppercase">
            <tr>
              <th className="px-6 py-4">名前</th>
              <th className="px-6 py-4">メールアドレス</th>
              <th className="px-6 py-4">権限</th>
              <th className="px-6 py-4 text-right">ステータス</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {members.length > 0 ? members.map(m => (
              <tr key={m.id} className="hover:bg-gray-50/50">
                <td className="px-6 py-4 font-bold text-gray-800">{m.username}</td>
                <td className="px-6 py-4 text-gray-500 font-mono">{m.email}</td>
                <td className="px-6 py-4">
                  <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs font-bold ${m.role === 'admin' ? 'bg-amber-100 text-amber-700' : 'bg-slate-100 text-slate-500'}`}>
                    {m.role === 'admin' && <Shield className="h-3 w-3" />}
                    {m.role === 'admin' ? '組織管理者' : '一般メンバー'}
                  </span>
                </td>
                <td className="px-6 py-4 text-right">
                  <span className="text-green-600 text-xs font-bold">● Active</span>
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

      <div className="mt-4 text-center text-xs text-slate-400">
        ※ メンバーの追加・招待はシステム管理画面から可能です
      </div>
    </div>
  );
}
