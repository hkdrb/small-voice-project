'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import axios from 'axios';
import { Building, Users, Settings, Menu } from 'lucide-react';
import OrganizationManager from '@/components/admin/OrganizationManager';
import UserManager from '@/components/admin/UserManager';
import { TabsList, TabsTrigger } from '@/components/ui/Tabs';
import { useSidebar } from '@/components/SidebarContext';

export default function SystemAdminPage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState('orgs');
  const [loading, setLoading] = useState(true);
  const [authorized, setAuthorized] = useState(false);
  const { toggleMobileMenu } = useSidebar();

  useEffect(() => {
    // Verify System Admin Access
    const checkAuth = async () => {
      try {
        const res = await axios.get('/api/auth/me', { withCredentials: true });
        if (res.data.role !== 'system_admin') {
          router.push('/dashboard');
          return;
        }
        setAuthorized(true);
      } catch (e: any) {
        if (e.response && e.response.status === 401) {
          router.push('/login');
          return;
        }
        router.push('/login'); // Fallback for other errors in auth check
      } finally {
        setLoading(false);
      }
    };
    checkAuth();
  }, [router]);

  if (loading) return <div className="flex justify-center items-center h-screen">Loading...</div>;
  if (!authorized) return null;

  return (
    <div className="h-full flex flex-col">
      <header className="h-16 flex items-center justify-between px-4 md:px-6 border-b border-white/40 shrink-0 bg-white/50 backdrop-blur-sm sticky top-0 z-20">
        <div className="flex items-center">
          <button
            onClick={toggleMobileMenu}
            className="md:hidden mr-3 p-1.5 rounded-lg hover:bg-slate-100 transition-colors"
          >
            <Menu className="h-6 w-6 text-slate-600" />
          </button>
          <h1 className="text-xl font-bold text-sage-dark flex items-center gap-2">
            <Settings className="h-5 w-5" />
            システム管理
          </h1>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto p-6">
        <TabsList className="bg-white/50 p-1 rounded-xl border border-white/20 shadow-sm mb-6 w-full flex justify-start overflow-x-auto">
          <TabsTrigger
            value="orgs"
            activeTab={activeTab}
            onClick={() => setActiveTab('orgs')}
            className="flex items-center px-4 py-2 cursor-pointer"
          >
            <Building className="w-4 h-4 mr-2" />
            組織管理
          </TabsTrigger>
          <TabsTrigger
            value="users"
            activeTab={activeTab}
            onClick={() => setActiveTab('users')}
            className="flex items-center px-4 py-2 cursor-pointer"
          >
            <Users className="w-4 h-4 mr-2" />
            ユーザー管理
          </TabsTrigger>
        </TabsList>

        <div className="animate-in fade-in slide-in-from-bottom-2">
          {activeTab === 'orgs' && <OrganizationManager />}
          {activeTab === 'users' && <UserManager />}
        </div>
      </div>
    </div>
  );
}
