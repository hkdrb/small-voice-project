'use client';

import { Suspense, useEffect, useState } from 'react';
import { useRouter } from "next/navigation";
import Image from "next/image";
import axios from "axios";
import Link from 'next/link';
import { LayoutDashboard, FileText, Key, LogOut, Menu, BarChart2, Folder, Upload, Users, ClipboardList } from "lucide-react";
import { useSearchParams } from 'next/navigation';
import DashboardHeader from "@/components/dashboard/DashboardHeader";
import DashboardTabs from "@/components/dashboard/DashboardTabs";
import SurveyManager from "@/components/dashboard/SurveyManager";
import AnalysisRunner from "@/components/dashboard/AnalysisRunner";
import CsvImporter from "@/components/dashboard/CsvImporter";
import MemberList from "@/components/dashboard/MemberList";

// Types
interface Session {
  id: number;
  title: string;
  theme: string;
  is_published: boolean;
  created_at: string;
}

function DashboardContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const urlTab = searchParams?.get('tab');

  const [activeTab, setActiveTab] = useState('reports');
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSurveys, setActiveSurveys] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState<any | null>(null);

  // Sync activeTab with URL
  useEffect(() => {
    if (urlTab) {
      setActiveTab(urlTab);
    }
  }, [urlTab]);

  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        setLoading(true);

        // 1. Fetch User (to determine Role)
        const userRes = await axios.get('/api/auth/me', {
          withCredentials: true
        });
        const currentUser = userRes.data;
        setUser(currentUser);

        const isAdmin = currentUser.role === 'system_admin' || currentUser.org_role === 'admin';

        // 2. Set Default Tab based on Role (if not overridden by URL)
        if (!urlTab) {
          if (isAdmin) {
            setActiveTab('analysis');
          } else {
            setActiveTab('answers');
          }
        }

        // 3. Fetch Sessions (Reports)
        const sessionRes = await axios.get('/api/dashboard/sessions', {
          withCredentials: true
        }).catch(() => ({ data: [] }));

        if (sessionRes.data && Array.isArray(sessionRes.data)) {
          setSessions(sessionRes.data);
        }

        // 4. Fetch Active Surveys (for Answering) - User only
        if (!isAdmin) {
          const surveyRes = await axios.get('/api/dashboard/surveys', {
            withCredentials: true
          }).catch(() => ({ data: [] }));
          if (surveyRes.data && Array.isArray(surveyRes.data)) {
            // Filter for active only
            setActiveSurveys(surveyRes.data.filter((s: any) => s.is_active));
          }
        }

      } catch (error: any) {
        // Handle Unauthorized Access (Redirect) silently
        if (error.response && error.response.status === 401) {
          // Do not console.error here to avoid Next.js error overlay
          router.push('/login');
          return;
        }

        console.error('Failed to load dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchInitialData();
  }, []); // Run once on mount

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="flex flex-col items-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-sage-primary mb-4"></div>
          <p className="text-slate-500 font-medium">Loading...</p>
        </div>
      </div>
    );
  }

  const isAdmin = user?.role === 'system_admin' || user?.org_role === 'admin';

  return (
    <div className="h-full flex flex-col">
      <DashboardHeader />

      <div className="flex-1 overflow-y-auto p-6">
        <DashboardTabs
          activeTab={activeTab}
          isAdmin={isAdmin}
          onTabChange={(tab) => {
            setActiveTab(tab);
            router.push(`/dashboard?tab=${tab}`);
          }}
        />


        <div className="mt-6 animate-in fade-in slide-in-from-bottom-2 duration-300">

          {/* 1. Analysis (Admin) */}
          {activeTab === 'analysis' && isAdmin && (
            <AnalysisRunner onSuccess={() => setActiveTab('reports')} />
          )}

          {/* 2. Reports (Shared) */}
          {activeTab === 'reports' && (
            <div>
              {sessions.length === 0 ? (
                <div className="text-center py-24 glass-card">
                  <p className="text-slate-400 mb-6 text-lg">まだレポートがありません</p>
                  {isAdmin && (
                    <button onClick={() => setActiveTab('analysis')} className="px-6 py-3 btn-primary">
                      分析を開始する
                    </button>
                  )}
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {sessions.map(sess => (
                    <Link href={`/dashboard/sessions/${sess.id}`} key={sess.id}>
                      <div className="glass-card !p-6 hover:translate-y-[-4px] hover:shadow-lg transition-all cursor-pointer group h-full flex flex-col justify-between">
                        <div>
                          <div className="flex justify-between items-start mb-4">
                            <span className={`px-2 py-1 rounded-md text-xs font-bold ${sess.is_published ? 'bg-green-100 text-green-700' : 'bg-slate-100 text-slate-500'}`}>
                              {sess.is_published ? '公開中' : '下書き'}
                            </span>
                            <span className="text-slate-400 text-xs font-bold">{new Date(sess.created_at).toLocaleDateString()}</span>
                          </div>
                          <h3 className="text-lg font-bold text-sage-dark mb-2 line-clamp-2 group-hover:text-amber-500 transition-colors">{sess.title}</h3>
                          <p className="text-slate-500 text-sm mb-6 line-clamp-2">テーマ: {sess.theme}</p>
                        </div>
                        <div className="flex items-center text-sage-primary text-sm font-bold group-hover:translate-x-1 transition-transform">
                          詳細を見る →
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* 3. Answers (User) */}
          {activeTab === 'answers' && !isAdmin && (
            <div className="glass-card p-6 rounded-xl">
              <h2 className="text-lg font-bold text-gray-800 mb-4">📢 回答受付中のアンケート</h2>
              {activeSurveys.length > 0 ? (
                <div className="space-y-4">
                  {activeSurveys.map(survey => (
                    <div key={survey.id} className="p-4 border border-gray-100 rounded-lg hover:bg-sage-50/50 transition-colors flex items-center justify-between">
                      <div>
                        <h3 className="font-bold text-gray-800">{survey.title}</h3>
                      </div>
                      <Link href={`/survey/${survey.uuid}`} className="btn-primary py-2 px-4 text-sm no-underline inline-block">
                        回答する
                      </Link>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <p>現在、回答可能なアンケートはありません。</p>
                </div>
              )}
            </div>
          )}

          {/* 4. Surveys (Admin) */}
          {activeTab === 'surveys' && isAdmin && (
            <SurveyManager user={user} />
          )}

          {/* 5. Requests (User) */}
          {activeTab === 'requests' && !isAdmin && (
            <div className="space-y-4">
              <SurveyManager user={user} />
            </div>
          )}

          {/* 6. Import (Admin) */}
          {activeTab === 'import' && isAdmin && (
            <CsvImporter />
          )}

          {/* 7. Members (Admin) */}
          {activeTab === 'members' && isAdmin && (
            <MemberList user={user} />
          )}

        </div>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <Suspense fallback={
      <div className="flex h-screen items-center justify-center">
        <div className="flex flex-col items-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-sage-primary mb-4"></div>
          <p className="text-slate-500 font-medium">Loading...</p>
        </div>
      </div>
    }>
      <DashboardContent />
    </Suspense>
  );
}
