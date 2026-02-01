'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import axios from 'axios';
import { Plus, Edit2, Check, X, Building, Trash2 } from 'lucide-react';

interface Organization {
  id: number;
  name: string;
  description: string;
  created_at: string;
}

export default function OrganizationManager() {
  const router = useRouter();
  const [orgs, setOrgs] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);

  // Create Form
  const [newOrgName, setNewOrgName] = useState('');
  const [newOrgDesc, setNewOrgDesc] = useState('');

  // Edit State
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editName, setEditName] = useState('');
  const [editDesc, setEditDesc] = useState('');

  useEffect(() => {
    fetchOrgs();
  }, []);

  const fetchOrgs = async () => {
    try {
      setLoading(true);
      const res = await axios.get('/api/organizations', { withCredentials: true });
      console.log("Fetched organizations:", res.data);
      setOrgs(res.data);
    } catch (error: any) {
      console.error("Failed to fetch organizations:", error.response?.data || error.message);
      if (error.response && error.response.status === 401) {
        router.push('/login');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!newOrgName) return alert("組織名は必須です");
    try {
      await axios.post('/api/organizations', {
        name: newOrgName,
        description: newOrgDesc
      }, { withCredentials: true });

      setNewOrgName('');
      setNewOrgDesc('');
      setIsCreating(false);
      fetchOrgs();
      alert("組織を作成しました");
    } catch (error) {
      alert("作成に失敗しました (重複している可能性があります)");
    }
  };

  const startEdit = (org: Organization) => {
    setEditingId(org.id);
    setEditName(org.name);
    setEditDesc(org.description || '');
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditName('');
    setEditDesc('');
  };

  const handleUpdate = async (id: number) => {
    if (!editName) return alert("組織名は必須です");
    try {
      await axios.put(`/api/organizations/${id}`, {
        name: editName,
        description: editDesc
      }, { withCredentials: true });

      setEditingId(null);
      fetchOrgs();
    } catch (error) {
      alert("更新に失敗しました");
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("本当に削除しますか？\nこの操作は取り消せません。")) return;
    try {
      await axios.delete(`/api/organizations/${id}`, { withCredentials: true });
      fetchOrgs();
    } catch (error: any) {
      alert(error.response?.data?.detail || "削除に失敗しました");
    }
  };

  if (loading) return <div>読み込み中...</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
          <Building className="h-5 w-5" />
          組織一覧
        </h2>
        <button
          onClick={() => setIsCreating(!isCreating)}
          className="btn-primary px-4 py-2 flex items-center gap-2"
        >
          <Plus className="h-4 w-4" />
          新規作成
        </button>
      </div>

      {isCreating && (
        <div className="glass-card p-6 animate-in slide-in-from-top-2">
          <h3 className="font-bold mb-4">組織を新規作成</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-bold text-gray-700 mb-1">組織名 (必須)</label>
              <input
                type="text"
                className="glass-input w-full p-2"
                value={newOrgName}
                onChange={(e) => setNewOrgName(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-sm font-bold text-gray-700 mb-1">説明</label>
              <textarea
                className="glass-input w-full p-2"
                value={newOrgDesc}
                onChange={(e) => setNewOrgDesc(e.target.value)}
              />
            </div>
            <div className="flex gap-2 justify-end">
              <button onClick={() => setIsCreating(false)} className="px-4 py-2 text-gray-500 hover:bg-gray-100 rounded-lg">キャンセル</button>
              <button onClick={handleCreate} className="btn-primary px-4 py-2">作成</button>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 gap-4">
        {orgs.length === 0 ? (
          <div className="text-center py-12 glass-card">
            <p className="text-gray-400">組織が登録されていません</p>
          </div>
        ) : orgs.map(org => (
          <div key={org.id} className="glass-card p-4 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            {editingId === org.id ? (
              <div className="w-full flex flex-col md:flex-row gap-4 items-start md:items-center">
                <div className="flex-1 w-full space-y-2">
                  <input
                    type="text"
                    className="glass-input w-full p-2"
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                  />
                  <textarea
                    className="glass-input w-full p-2 text-sm"
                    value={editDesc}
                    onChange={(e) => setEditDesc(e.target.value)}
                  />
                </div>
                <div className="flex gap-2">
                  <button onClick={() => handleUpdate(org.id)} className="p-2 bg-green-100 text-green-700 rounded-full hover:bg-green-200">
                    <Check className="h-4 w-4" />
                  </button>
                  <button onClick={cancelEdit} className="p-2 bg-red-100 text-red-700 rounded-full hover:bg-red-200">
                    <X className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ) : (
              <>
                <div className="flex-1">
                  <h3 className="font-bold text-lg text-gray-800">{org.name}</h3>
                  <p className="text-sm text-gray-500">{org.description || "説明なし"}</p>
                </div>
                <div className="flex items-center gap-1 text-sm text-gray-400">
                  <button onClick={() => startEdit(org)} className="p-2 hover:bg-sage-50 text-slate-400 hover:text-sage-600 rounded-lg transition-colors" title="編集">
                    <Edit2 className="h-4 w-4" />
                  </button>
                  <button onClick={() => handleDelete(org.id)} className="p-2 hover:bg-red-50 text-slate-400 hover:text-red-600 rounded-lg transition-colors" title="削除">
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
