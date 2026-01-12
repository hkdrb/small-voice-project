'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';
import { usePathname, useRouter } from 'next/navigation';
import Image from 'next/image';
import Link from 'next/link';
import {
  Home,
  Settings,
  LogOut,
  User,
  ChevronDown,
  ChevronRight,
  Shield,
  Eye,
  EyeOff
} from 'lucide-react';

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();

  // State
  const [user, setUser] = useState<any>(null);
  const [availableOrgs, setAvailableOrgs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [newPassword, setNewPassword] = useState('');
  const [currentPassword, setCurrentPassword] = useState('');
  const [updating, setUpdating] = useState(false);

  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);

  // Hide sidebar on login, invite, and forgot-password pages
  const isAuthPage = pathname === '/login' || pathname === '/invite' || pathname === '/forgot-password';

  // Fetch User & Orgs
  useEffect(() => {
    if (!isAuthPage) {
      fetchData();
    }
  }, [pathname, isAuthPage]);

  const fetchData = async () => {
    try {
      const [userRes, orgsRes] = await Promise.all([
        axios.get('/api/auth/me'),
        axios.get('/api/auth/my-orgs')
      ]);
      setUser(userRes.data);
      setAvailableOrgs(orgsRes.data);
    } catch (e) {
      // Redirect if 401?
    } finally {
      setLoading(false);
    }
  };

  const handleProfileUpdate = async () => {
    if (!user?.username) return alert("表示名を入力してください");
    try {
      setUpdating(true);
      await axios.put('/api/auth/me', {
        username: user.username,
        password: newPassword || null,
        current_password: currentPassword || null
      });
      alert("プロフィールを更新しました");
      setNewPassword('');
      setCurrentPassword('');
    } catch (e: any) {
      console.error(e);
      const detail = e.response?.data?.detail;
      alert(detail ? `更新に失敗しました: ${detail}` : "更新に失敗しました");
    } finally {
      setUpdating(false);
    }
  };

  const handleOrgChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newOrgId = e.target.value;
    try {
      await axios.post('/api/auth/switch-org', { org_id: Number(newOrgId) }); // Assuming ID is number
      window.location.reload(); // Simple reload to refresh all data context
    } catch (e) {
      console.error("Failed to switch org", e);
    }
  };

  const handleLogout = async () => {
    try {
      await axios.post('/api/auth/logout', {}, { withCredentials: true });
      router.push('/login');
    } catch (e) {
      console.error(e);
    }
  };

  if (isAuthPage) return null;
  if (loading) return null; // Or skeleton

  return (
    <aside className="w-64 h-screen shrink-0 pb-6 flex flex-col border-r border-white/40 bg-white/30 backdrop-blur-md overflow-hidden">
      {/* Logo Area */}
      <div className="p-6">
        <div className="relative w-full h-12 flex items-center">
          <img src="/logo.svg" alt="Small Voice" className="h-10 w-auto" />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-4 space-y-6">
        {/* Organization Switcher */}
        <div>
          <label className="block text-xs font-semibold text-gray-500 mb-2 uppercase tracking-wide">
            所属組織 / プロジェクト
          </label>
          <div className="relative">
            <select
              value={user?.current_org_id || ''}
              onChange={handleOrgChange}
              className="w-full appearance-none glass-input px-3 py-2 text-sm pr-8 cursor-pointer"
            >
              {availableOrgs.map(org => (
                <option key={org.id} value={org.id}>{org.name}</option>
              ))}
            </select>
            <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-500">
              <ChevronDown className="h-4 w-4" />
            </div>
          </div>
        </div>

        <div className="h-px bg-gray-200/50 my-2"></div>

        {/* User Card */}
        <div>
          <label className="block text-xs font-semibold text-gray-500 mb-2 uppercase tracking-wide">
            ユーザーアカウント
          </label>
          <div className="glass-card p-3.5 space-y-2">
            <div className="flex flex-col">
              <p className="text-sm font-semibold text-gray-900 truncate">{user?.username || 'Guest'}</p>
              <p className="text-xs text-gray-500 truncate">{user?.email}</p>
            </div>
            <div className="text-[10px] font-bold uppercase tracking-wider text-sage-800 bg-sage-100/60 px-2 py-0.5 rounded-md w-fit border border-sage-200/50">
              {user?.role === 'system_admin' ? "システム管理者" : (user?.org_role === 'admin' ? "組織管理者" : "一般ユーザー")}
            </div>
          </div>
        </div>

        {/* Navigation Menu */}
        <nav className="space-y-1">
          {/* Dashboard link: Only show if not on dashboard and not system admin? No, the requirement is "one if on the other" */}

          {/* If on system management page, show Dashboard link */}
          {pathname.startsWith('/admin/system') && (
            <Link
              href="/dashboard"
              className="w-full text-left px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center text-gray-700 hover:bg-white/50 hover:text-sage-800"
            >
              <Home className="h-4 w-4 mr-3" />
              ダッシュボード
            </Link>
          )}

          {/* If on dashboard (or other non-admin pages) and is system admin, show System Management link */}
          {user?.role === 'system_admin' && !pathname.startsWith('/admin/system') && (
            <Link
              href="/admin/system"
              className="w-full text-left px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center text-gray-700 hover:bg-white/50 hover:text-sage-800"
            >
              <Settings className="h-4 w-4 mr-3" />
              システム管理
            </Link>
          )}
        </nav>

        <div className="h-px bg-gray-200/50 my-2"></div>

        {/* Profile Edit */}
        <div className="space-y-2">
          <button
            onClick={() => setIsProfileOpen(!isProfileOpen)}
            className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm font-medium transition-colors ${isProfileOpen ? 'bg-white/50 text-sage-800' : 'text-gray-600 hover:bg-white/30 hover:text-gray-900'}`}
          >
            <span>プロフィール設定</span>
            <ChevronDown className={`h-4 w-4 transition-transform ${isProfileOpen ? 'rotate-180' : ''}`} />
          </button>

          {isProfileOpen && (
            <div className="px-3 pb-3 space-y-3 animate-in slide-in-from-top-2 fade-in duration-200">
              <div>
                <label className="block text-xs text-gray-500 mb-1">表示名</label>
                <input
                  type="text"
                  value={user?.username || ''}
                  onChange={(e) => setUser({ ...user, username: e.target.value })}
                  className="glass-input w-full px-2 py-1.5 text-sm"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">現在のパスワード</label>
                <div className="relative">
                  <input
                    type={showCurrentPassword ? "text" : "password"}
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                    placeholder="更新には必須です"
                    className="glass-input w-full px-2 py-1.5 text-sm pr-8"
                  />
                  <button
                    type="button"
                    onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                  >
                    {showCurrentPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">新しいパスワード</label>
                <div className="relative">
                  <input
                    type={showNewPassword ? "text" : "password"}
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="変更する場合のみ入力"
                    className="glass-input w-full px-2 py-1.5 text-sm pr-8"
                  />
                  <button
                    type="button"
                    onClick={() => setShowNewPassword(!showNewPassword)}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                  >
                    {showNewPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>
              <button
                onClick={handleProfileUpdate}
                disabled={updating}
                className="w-full btn-primary py-1.5 text-xs disabled:opacity-50"
              >
                {updating ? '更新中...' : '更新する'}
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Footer / Logout */}
      <div className="p-4 border-t border-white/40">
        <button
          onClick={handleLogout}
          className="flex items-center w-full px-3 py-2 text-sm font-medium text-red-600 hover:bg-red-50 rounded-lg transition-colors"
        >
          <LogOut className="h-4 w-4 mr-3" />
          ログアウト
        </button>
      </div>
    </aside>
  );
}
