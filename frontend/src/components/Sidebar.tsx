'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname, useSearchParams } from 'next/navigation';
import { LayoutDashboard, FileText, Key, LogOut, Menu, BarChart2, Folder, Upload, Users, ClipboardList, ChevronDown, User as UserIcon, Settings, UserCircle, Building, MessageSquare, Home } from "lucide-react";
import axios from 'axios';
import ProfileSettingsModal from './ProfileSettingsModal';

interface SidebarProps {
  user: {
    role: string;
    org_role?: string;
    current_org_id?: number;
    name?: string;
    username?: string;
    email?: string;
  } | null;
  onLogout?: () => void;
  isMobileOpen: boolean;
  setIsMobileOpen: (isOpen: boolean) => void;
  onMobileClose: () => void;
}

export default function Sidebar({ user, onLogout, isMobileOpen, setIsMobileOpen, onMobileClose }: SidebarProps) {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  // State
  const [availableOrgs, setAvailableOrgs] = useState<any[]>([]);
  const [internalUser, setInternalUser] = useState<any | null>(user);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Derived state
  const currentUser = internalUser || user;
  const isAdmin = currentUser?.role === 'system_admin' || currentUser?.org_role === 'admin';
  const isSystemAdmin = currentUser?.role === 'system_admin';

  useEffect(() => {
    // Skip fetching on auth pages
    if (pathname === '/login' || pathname === '/register' || pathname === '/') {
      return;
    }

    const fetchUser = async () => {
      if (!user) {
        try {
          const res = await axios.get('/api/auth/me', { withCredentials: true });
          setInternalUser(res.data);
        } catch (e: any) {
          if (e.response?.status !== 401) {
            console.error("Failed to fetch user in Sidebar", e);
          }
        }
      } else {
        setInternalUser(user);
      }
    };

    const fetchOrgs = async () => {
      try {
        const res = await axios.get('/api/auth/my-orgs', { withCredentials: true });
        setAvailableOrgs(res.data);
      } catch (e) {
        console.error("Failed to fetch organizations", e);
      }
    };

    fetchUser();
    fetchOrgs();
  }, [user, pathname]);

  const handleOrgChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newOrgId = e.target.value;
    try {
      await axios.post('/api/auth/switch-org', { org_id: newOrgId });
      window.location.reload();
    } catch (error) {
      console.error("Failed to switch organization", error);
      alert("組織の切り替えに失敗しました");
    }
  };

  const navItems = [
    { href: '/dashboard?tab=analysis', label: 'データ分析実行', icon: <BarChart2 className="h-5 w-5" />, tab: 'analysis', adminOnly: true },
    { href: '/dashboard?tab=reports', label: 'レポート閲覧', icon: <FileText className="h-5 w-5" />, tab: 'reports' },
    { href: '/dashboard?tab=answers', label: 'アンケート回答', icon: <Folder className="h-5 w-5" />, tab: 'answers' },
    { href: '/dashboard?tab=casual', label: '雑談掲示板', icon: <MessageSquare className="h-5 w-5" />, tab: 'casual' },
    { href: '/dashboard?tab=surveys', label: 'フォーム作成・管理', icon: <ClipboardList className="h-5 w-5" />, tab: 'surveys', adminOnly: true },
    { href: '/dashboard?tab=requests', label: 'フォーム申請', icon: <Upload className="h-5 w-5" />, tab: 'requests', userOnly: true },
    { href: '/dashboard?tab=import', label: 'CSVインポート', icon: <Upload className="h-5 w-5" />, tab: 'import', adminOnly: true },
    { href: '/dashboard?tab=members', label: 'メンバーリスト', icon: <Users className="h-5 w-5" />, tab: 'members', adminOnly: true },
    {
      href: pathname === '/admin/system' ? '/dashboard' : '/admin/system',
      label: pathname === '/admin/system' ? 'ホーム' : 'システム管理',
      icon: pathname === '/admin/system' ? <LayoutDashboard className="h-5 w-5" /> : <Settings className="h-5 w-5" />,
      tab: pathname === '/admin/system' ? 'dashboard' : 'system_admin',
      systemAdminOnly: true
    },
  ];

  // Helper to determine if link is active
  const isActive = (itemHref: string, itemTab: string | null) => {
    const currentTab = searchParams.get('tab');
    const currentPath = pathname;

    // For /admin/system, check path directly
    if (itemHref.startsWith('/admin/system')) {
      return currentPath === itemHref;
    }

    // For dashboard items, check path and tab
    if (itemHref.startsWith('/dashboard')) {
      // If itemTab is null, it means it's the default dashboard without a tab
      if (itemTab === null) {
        return currentPath === '/dashboard' && !currentTab;
      }
      // Otherwise, check if the current tab matches the item's tab
      return currentPath === '/dashboard' && currentTab === itemTab;
    }

    return false;
  };

  // State for profile menu toggle - REMOVED

  const handleLogout = async () => {
    if (onLogout) {
      onLogout();
      return;
    }

    try {
      await axios.post('/api/auth/logout', {}, { withCredentials: true });
    } catch (error) {
      console.error("Logout failed", error);
    } finally {
      // Force full reload to clear state and ensure middleware runs on back navigation attempt
      // Using href ensures a new navigation entry, pushing the dashboard to history but ensuring cache is re-evaluated.
      // Ideally, we want to clear history, which isn't possible, but 'no-store' header handles the back button case.
      window.location.replace('/login');
    }
  };

  // Hide sidebar on auth/public pages
  const isAuthPage = pathname === '/login' || pathname === '/register' || pathname === '/forgot-password' || pathname === '/invite' || pathname === '/' || pathname.startsWith('/survey');
  if (isAuthPage) {
    return null;
  }

  // --- Mobile Sidebar Implementation (Current Design) ---
  const MobileSidebar = (
    <aside className={`
      w-64 h-screen shrink-0 pb-6 flex flex-col border-r border-white/40 bg-white/30 backdrop-blur-md overflow-hidden
      fixed inset-y-0 left-0 z-50 transition-transform duration-300 ease-in-out
      md:hidden
      ${isMobileOpen ? 'translate-x-0 shadow-2xl' : '-translate-x-full'}
    `}>
      {/* Logo Area */}
      <div className="h-16 flex items-center px-6 border-b border-white/40 shrink-0">
        <Link href="/dashboard" className="flex items-center gap-2 group" onClick={onMobileClose}>
          <div className="w-8 h-8 bg-sage-primary rounded-lg flex items-center justify-center text-white shadow-lg group-hover:scale-105 transition-transform duration-300">
            <span className="font-bold text-lg">S</span>
          </div>
          <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-sage-dark to-sage-primary">
            Small Voice
          </span>
        </Link>
      </div>

      {/* User Info / Org Switcher */}
      <div className="p-4 border-b border-white/40 bg-white/20">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-full bg-linear-to-br from-sage-300 to-sage-500 flex items-center justify-center text-white shadow-md">
            <UserIcon className="h-5 w-5" />
          </div>
          <div className="overflow-hidden">
            <p className="font-bold text-sage-dark truncate text-sm">{currentUser?.name || currentUser?.username || 'ゲスト'}</p>
            <p className="text-xs text-slate-500 truncate">{currentUser?.email}</p>
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-gray-500 mb-2 uppercase tracking-wide">
            所属組織 / プロジェクト
          </label>
          <div className="relative">
            <select
              value={currentUser?.current_org_id || ''}
              onChange={handleOrgChange}
              className="w-full appearance-none glass-input px-4 py-3 text-base pr-8 cursor-pointer"
            >
              {availableOrgs.length === 0 && (
                <option value={currentUser?.current_org_id}>{currentUser?.role === 'system_admin' ? 'システム管理' : 'デフォルト組織'}</option>
              )}
              {availableOrgs.map(org => (
                <option key={org.id} value={org.id}>{org.name}</option>
              ))}
            </select>
            <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-500">
              <ChevronDown className="h-4 w-4" />
            </div>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-1 custom-scrollbar">
        {navItems
          .filter(item => {
            if (item.adminOnly && !isAdmin) return false;
            if (item.userOnly && isAdmin) return false;
            if (item.systemAdminOnly && !isSystemAdmin) return false;
            return true;
          })
          .map((item) => (
            <Link
              key={item.href}
              href={item.href}
              onClick={onMobileClose}
              className={`
                flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 group
                ${isActive(item.href.split('?')[0], item.tab)
                  ? 'bg-sage-primary text-white shadow-md'
                  : 'text-slate-600 hover:bg-white/50 hover:text-sage-dark'
                }
              `}
            >
              <div className={`transition-transform duration-200 ${isActive(item.href.split('?')[0], item.tab) ? 'scale-110' : 'group-hover:scale-110'}`}>
                {item.icon}
              </div>
              <span className="font-medium text-sm">{item.label}</span>
            </Link>
          ))}
      </nav>

      {/* Footer Actions */}
      <div className="p-4 border-t border-white/40 bg-white/20">
        <button
          onClick={handleLogout}
          className="flex items-center justify-center gap-3 w-full py-3.5 rounded-xl text-red-500 font-bold bg-red-500/10 hover:bg-red-500/20 transition-all duration-200 group active:scale-[0.98]"
        >
          <LogOut className="h-5 w-5 group-hover:-translate-x-1 transition-transform" />
          <span className="text-sm">ログアウト</span>
        </button>
      </div>
    </aside>
  );

  // --- Desktop Sidebar Implementation (Restored Design) ---
  const DesktopSidebar = (
    <aside className="hidden md:flex w-64 h-screen flex-col bg-gray-50 border-r border-gray-200 sticky top-0 overflow-y-auto shrink-0 z-30">
      <div className="p-6">
        {/* Logo */}
        <div className="mb-8">
          <Link href="/dashboard">
            <h1 className="text-2xl font-bold text-sage-800 tracking-tight drop-shadow-sm font-sans">Small Voice</h1>
          </Link>
        </div>

        {/* Org Switcher */}
        <div className="mb-6">
          <label className="block text-xs font-bold text-gray-500 mb-2">所属組織 / プロジェクト</label>
          <div className="relative">
            <select
              value={currentUser?.current_org_id || ''}
              onChange={handleOrgChange}
              className="w-full bg-slate-100 border border-slate-200 text-gray-700 text-sm rounded-lg p-2.5 pr-8 appearance-none cursor-pointer focus:outline-none focus:border-sage-500 focus:ring-1 focus:ring-sage-200 transition-colors"
            >
              {availableOrgs.length === 0 && (
                <option value={currentUser?.current_org_id}>{currentUser?.role === 'system_admin' ? 'システム管理' : 'デフォルト組織'}</option>
              )}
              {availableOrgs.map(org => (
                <option key={org.id} value={org.id}>{org.name}</option>
              ))}
            </select>
            <ChevronDown className="absolute right-3 top-3 w-4 h-4 text-gray-400 pointer-events-none" />
          </div>
        </div>

        {/* User Card */}
        <div className="mb-6">
          <label className="block text-xs font-bold text-gray-500 mb-2">ユーザーアカウント</label>
          <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100">
            <div className="font-bold text-gray-800 text-sm mb-0.5">{currentUser?.name || currentUser?.username || 'ゲスト'}</div>
            <div className="text-[10px] text-gray-400 mb-2 truncate">{currentUser?.email}</div>
            <span className="inline-block border border-gray-200 rounded px-2 py-0.5 text-[10px] font-bold text-gray-600">
              {currentUser?.role === 'system_admin' ? 'システム管理者' : currentUser?.org_role === 'admin' ? '管理者' : 'メンバー'}
            </span>
          </div>
        </div>

        {/* Navigation */}
        <nav className="space-y-1 mb-8">
          {navItems
            .filter(item => {
              if (item.adminOnly && !isAdmin) return false;
              if (item.userOnly && isAdmin) return false;
              if (item.systemAdminOnly && !isSystemAdmin) return false;

              // Hide dashboard session/tab items on PC (they are shown as tabs in the content area)
              // Only top-level links like /dashboard (Home) or /admin/system should remain.
              if (item.href.includes('/dashboard') && item.href.includes('?tab=')) return false;

              return true;
            })
            .map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`
                    flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 group
                    ${isActive(item.href.split('?')[0], item.tab)
                    ? 'bg-sage-100 text-sage-900 font-bold'
                    : 'text-gray-500 hover:bg-gray-100 hover:text-gray-900'
                  }
                `}
              >
                <div className={`transition-transform duration-200 ${isActive(item.href.split('?')[0], item.tab) ? 'scale-110' : 'group-hover:scale-110'}`}>
                  {item.icon}
                </div>
                <span className="text-sm font-medium">{item.label}</span>
              </Link>
            ))}

          <div className="mt-4 pt-4 border-t border-gray-200">
            <button
              onClick={() => setIsModalOpen(true)}
              className="w-full flex items-center gap-3 px-3 py-2.5 text-gray-500 hover:bg-gray-100 rounded-lg cursor-pointer transition-colors"
            >
              <UserCircle className="h-5 w-5" />
              <span className="text-sm font-medium">プロフィール設定</span>
            </button>
          </div>
        </nav>
      </div>

      {/* Footer */}
      <div className="mt-auto p-6 mb-8">
        <button
          onClick={handleLogout}
          className="flex items-center justify-center gap-2.5 w-full py-3 rounded-xl text-red-500 font-bold bg-red-500/5 hover:bg-red-500/10 transition-all duration-200 group active:scale-[0.98] border border-red-500/10"
        >
          <LogOut className="w-4 h-4 group-hover:-translate-x-0.5 transition-transform" />
          <span className="text-sm">ログアウト</span>
        </button>
      </div>
    </aside>
  );


  return (
    <>
      {/* Mobile Overlay */}
      {isMobileOpen && (
        <div
          className="fixed inset-0 bg-black/40 backdrop-blur-sm z-40 md:hidden transition-opacity"
          onClick={onMobileClose}
        />
      )}

      {MobileSidebar}
      {DesktopSidebar}

      <ProfileSettingsModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        user={currentUser}
      />
    </>
  );
}
