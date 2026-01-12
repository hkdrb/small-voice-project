'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import axios from 'axios';
import { Plus, Edit2, Check, X, Users, Trash2 } from 'lucide-react';

interface User {
  id: number;
  username: string;
  email: string;
  role: string;
  organizations: { org_id: number, name: string, role: string }[];
}

interface Organization {
  id: number;
  name: string;
}

export default function UserManager() {
  const router = useRouter();
  const [users, setUsers] = useState<User[]>([]);
  const [orgs, setOrgs] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);

  // Form State
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [isSystemAdmin, setIsSystemAdmin] = useState(false);
  const [orgAssignments, setOrgAssignments] = useState<{ [key: number]: { joined: boolean, role: string } }>({});

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [usersRes, orgsRes] = await Promise.all([
        axios.get('/api/users', { withCredentials: true }),
        axios.get('/api/organizations', { withCredentials: true })
      ]);
      setUsers(usersRes.data);
      setOrgs(orgsRes.data);

      initAssignments(orgsRes.data);
    } catch (error: any) {
      console.error("Failed to fetch data", error);
      if (error.response && error.response.status === 401) {
        router.push('/login');
      }
    } finally {
      setLoading(false);
    }
  };

  const initAssignments = (orgList: Organization[], existingUser?: User) => {
    const assignments: any = {};
    orgList.forEach((o: Organization) => {
      const existing = existingUser?.organizations.find(uorg => uorg.org_id === o.id);
      assignments[o.id] = {
        joined: !!existing,
        role: existing ? existing.role : 'general'
      };
    });
    setOrgAssignments(assignments);
  };

  const startCreate = () => {
    setEmail(''); setUsername(''); setIsSystemAdmin(false);
    initAssignments(orgs);
    setIsCreating(true);
    setEditingUser(null);
  };

  const startEdit = (u: User) => {
    setEmail(u.email); setUsername(u.username); setIsSystemAdmin(u.role === 'system_admin');
    initAssignments(orgs, u);
    setEditingUser(u);
    setIsCreating(false);
  };

  const handleSave = async () => {
    if (!email || !username) return alert("必須項目を入力してください");

    const assignments = isSystemAdmin ? [] : Object.entries(orgAssignments)
      .filter(([_, val]) => val.joined)
      .map(([id, val]) => ({
        org_id: parseInt(id),
        role: val.role
      }));

    if (!isSystemAdmin && assignments.length === 0) {
      return alert("一般ユーザーは少なくとも1つの組織に所属させる必要があります");
    }

    try {
      if (editingUser) {
        // Update user
        await axios.put(`/api/users/${editingUser.id}`, {
          email, username, role: isSystemAdmin ? 'system_admin' : 'system_user',
          org_assignments: assignments
        }, { withCredentials: true });
        alert("ユーザー情報を更新しました");
      } else {
        await axios.post('/api/users', {
          email, username, is_system_admin: isSystemAdmin, org_assignments: assignments
        }, { withCredentials: true });
        alert("ユーザーを作成しました (招待メールが送信されました)");
      }

      setIsCreating(false);
      setEditingUser(null);
      fetchData();
    } catch (error: any) {
      const msg = error.response?.data?.detail || "エラーが発生しました";
      alert(`エラー: ${msg}`);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("本当に削除しますか？")) return;
    try {
      await axios.delete(`/api/users/${id}`, { withCredentials: true });
      fetchData();
    } catch (error: any) {
      const msg = error.response?.data?.detail || "削除に失敗しました";
      alert(`エラー: ${msg}`);
    }
  };

  const toggleOrgJoin = (orgId: number) => {
    setOrgAssignments(prev => ({
      ...prev,
      [orgId]: { ...prev[orgId], joined: !prev[orgId].joined }
    }));
  };

  const changeOrgRole = (orgId: number, role: string) => {
    setOrgAssignments(prev => ({
      ...prev,
      [orgId]: { ...prev[orgId], role: role }
    }));
  };

  if (loading) return <div>読み込み中...</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
          <Users className="h-5 w-5" />
          ユーザー一覧
        </h2>
        <button onClick={startCreate} className="btn-primary px-4 py-2 flex items-center gap-2">
          <Plus className="h-4 w-4" /> 新規作成
        </button>
      </div>

      {isCreating && (
        <div className="glass-card p-6 animate-in slide-in-from-top-2">
          <h3 className="font-bold mb-4">ユーザーを新規作成</h3>
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-bold text-gray-700 mb-1">Email (ログインID)</label>
                <input type="email" className="glass-input w-full p-2" value={email} onChange={e => setEmail(e.target.value)} />
              </div>
              <div>
                <label className="block text-sm font-bold text-gray-700 mb-1">表示名</label>
                <input type="text" className="glass-input w-full p-2" value={username} onChange={e => setUsername(e.target.value)} />
              </div>
            </div>

            <div className="flex items-center gap-2 py-2">
              <input type="checkbox" id="sysadmin" checked={isSystemAdmin} onChange={e => setIsSystemAdmin(e.target.checked)} className="w-4 h-4 text-sage-600 rounded" />
              <label htmlFor="sysadmin" className="font-bold text-gray-700 cursor-pointer">システム管理者権限を与える</label>
            </div>

            {!isSystemAdmin && (
              <div className="border border-gray-200 rounded-lg p-4 bg-white/50">
                <h4 className="text-sm font-bold text-gray-600 mb-2">所属組織と権限の設定</h4>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {orgs.map(org => {
                    const reqState = orgAssignments[org.id] || { joined: false, role: 'general' };
                    return (
                      <div key={org.id} className="flex items-center justify-between p-2 hover:bg-white rounded">
                        <div className="flex items-center gap-2">
                          <input type="checkbox" checked={reqState.joined} onChange={() => toggleOrgJoin(org.id)} className="w-4 h-4" />
                          <span className={reqState.joined ? "text-gray-900" : "text-gray-400"}>{org.name}</span>
                        </div>
                        {reqState.joined && (
                          <select value={reqState.role} onChange={(e) => changeOrgRole(org.id, e.target.value)} className="text-xs border rounded p-1">
                            <option value="general">一般ユーザー</option>
                            <option value="admin">組織管理者</option>
                          </select>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
            {isSystemAdmin && <p className="text-sm text-sage-600">※ システム管理者はすべての組織に対して管理権限を持ちます。</p>}
          </div>

          <div className="flex gap-2 justify-end mt-6">
            <button onClick={() => { setIsCreating(false); setEditingUser(null); }} className="px-4 py-2 text-gray-500 hover:bg-gray-100 rounded-lg">キャンセル</button>
            <button onClick={handleSave} className="btn-primary px-4 py-2">作成 (招待メール送信)</button>
          </div>
        </div>
      )}

      <div className="overflow-x-auto rounded-xl border border-gray-200 shadow-sm bg-white mt-4">
        <table className="w-full text-left text-sm whitespace-nowrap">
          <thead className="bg-sage-50 text-sage-700 font-bold uppercase">
            <tr>
              <th className="px-6 py-4">ユーザー</th>
              <th className="px-6 py-4">システム権限</th>
              <th className="px-6 py-4">所属組織 (組織内権限)</th>
              <th className="px-6 py-4 text-right">操作</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {users.map(u => {
              const isEditing = editingUser?.id === u.id;

              if (isEditing) {
                return (
                  <tr key={u.id} className="bg-sage-50/50">
                    <td className="px-6 py-4 align-top">
                      <div className="flex flex-col gap-2 min-w-[200px]">
                        <div>
                          <label className="text-[10px] font-bold text-gray-400 uppercase">Email</label>
                          <input type="email" className="glass-input w-full p-1.5 text-xs ml-1" value={email} onChange={e => setEmail(e.target.value)} />
                        </div>
                        <div>
                          <label className="text-[10px] font-bold text-gray-400 uppercase">表示名</label>
                          <input type="text" className="glass-input w-full p-1.5 text-xs ml-1" value={username} onChange={e => setUsername(e.target.value)} />
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 align-top">
                      <div className="flex items-center gap-2 mt-5">
                        <input type="checkbox" id={`sysadmin_${u.id}`} checked={isSystemAdmin} onChange={e => setIsSystemAdmin(e.target.checked)} className="w-4 h-4 text-sage-600 rounded" />
                        <label htmlFor={`sysadmin_${u.id}`} className="text-xs font-bold text-gray-700 cursor-pointer">システム管理者</label>
                      </div>
                    </td>
                    <td className="px-6 py-4 align-top">
                      {!isSystemAdmin ? (
                        <div className="max-h-32 overflow-y-auto border border-gray-100 rounded-lg p-2 bg-white/50 min-w-[250px]">
                          {orgs.map(org => {
                            const reqState = orgAssignments[org.id] || { joined: false, role: 'general' };
                            return (
                              <div key={org.id} className="flex items-center justify-between gap-4 py-1 border-b border-gray-50 last:border-0">
                                <label className="flex items-center gap-2 cursor-pointer truncate">
                                  <input type="checkbox" checked={reqState.joined} onChange={() => toggleOrgJoin(org.id)} className="w-3.5 h-3.5 shrink-0" />
                                  <span className={`text-[11px] truncate ${reqState.joined ? 'text-gray-900 font-medium' : 'text-gray-400'}`}>{org.name}</span>
                                </label>
                                {reqState.joined && (
                                  <select value={reqState.role} onChange={(e) => changeOrgRole(org.id, e.target.value)} className="text-[10px] border rounded px-1 py-0.5 bg-white">
                                    <option value="general">一般メンバー</option>
                                    <option value="admin">組織管理者</option>
                                  </select>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      ) : (
                        <div className="mt-5 text-[11px] text-sage-600 italic">全組織への管理権限あり</div>
                      )}
                    </td>
                    <td className="px-6 py-4 text-right align-top">
                      <div className="flex justify-end gap-1 mt-4">
                        <button onClick={handleSave} className="p-2 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition-colors" title="保存">
                          <Check className="h-4 w-4" />
                        </button>
                        <button onClick={() => setEditingUser(null)} className="p-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors" title="キャンセル">
                          <X className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              }

              return (
                <tr key={u.id} className="hover:bg-slate-50 transition-colors group">
                  <td className="px-6 py-4">
                    <div className="font-bold text-gray-800">{u.username}</div>
                    <div className="text-xs text-slate-400 font-mono">{u.email}</div>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${u.role === 'system_admin' ? 'bg-purple-100 text-purple-700' : 'bg-slate-100 text-slate-500'}`}>
                      {u.role === 'system_admin' ? 'システム管理者' : '-'}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex flex-wrap gap-1 max-w-sm">
                      {u.organizations?.length > 0 ? (
                        u.organizations.map(org => (
                          <span key={org.org_id} className="inline-flex items-center px-2 py-0.5 rounded-full bg-sage-50 text-sage-700 border border-sage-100 text-[10px] font-medium">
                            {org.name} <span className="mx-1 text-sage-300">|</span> {org.role === 'admin' ? '組織管理者' : '一般ユーザー'}
                          </span>
                        ))
                      ) : u.role !== 'system_admin' && (
                        <span className="text-[10px] text-gray-300 italic">未所属</span>
                      )}
                      {u.role === 'system_admin' && (
                        <span className="text-[10px] text-purple-400 italic">全組織アクセス可能</span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex justify-end gap-1 opacity-60 group-hover:opacity-100 transition-opacity">
                      <button onClick={() => startEdit(u)} className="p-2 text-slate-400 hover:text-sage-600 hover:bg-sage-50 rounded-lg transition-colors" title="編集">
                        <Edit2 className="h-4 w-4" />
                      </button>
                      <button onClick={() => handleDelete(u.id)} className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors" title="削除">
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
