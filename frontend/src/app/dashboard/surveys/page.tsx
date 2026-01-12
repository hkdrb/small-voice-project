"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import axios from "axios";
import { Plus, FileText, Loader2 } from "lucide-react";

interface Survey {
  id: number;
  title: string;
  uuid: string;
  is_active: boolean;
}

export default function SurveyListPage() {
  const router = useRouter();
  const [surveys, setSurveys] = useState<Survey[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSurveys = async () => {
      try {
        const res = await axios.get("/api/dashboard/surveys", { withCredentials: true });
        setSurveys(res.data);
      } catch (error: any) {
        if (error.response && error.response.status === 401) {
          router.push('/login');
          return;
        }
        console.error("Failed to fetch surveys", error);
      } finally {
        setLoading(false);
      }
    };
    fetchSurveys();
  }, []);

  if (loading) return <div className="p-8"><Loader2 className="animate-spin h-8 w-8 text-sage-primary" /></div>;

  return (
    <div className="flex flex-col h-full bg-slate-50">
      <header className="bg-white border-b border-slate-200 h-16 flex items-center px-8 justify-between sticky top-0 z-10">
        <h1 className="text-xl font-bold text-slate-800">フォーム管理</h1>
        <Link href="/dashboard/surveys/new">
          <button className="flex items-center gap-2 px-4 py-2 btn-primary text-sm">
            <Plus className="h-4 w-4" />
            新規作成
          </button>
        </Link>
      </header>

      <div className="p-8">
        {surveys.length === 0 ? (
          <div className="text-center py-24 glass-card">
            <div className="mb-4 text-slate-300 mx-auto w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center">
              <FileText className="h-8 w-8" />
            </div>
            <p className="text-slate-500 mb-6 text-lg">まだフォームがありません</p>
            <Link href="/dashboard/surveys/new">
              <button className="px-6 py-2 btn-primary">
                新しく作成する
              </button>
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {surveys.map(survey => (
              <div key={survey.id} className="glass-card !p-6 hover:shadow-lg transition-all group">
                <div className="flex justify-between items-start mb-4">
                  <span className={`px-2 py-1 rounded-md text-xs font-bold ${survey.is_active ? 'bg-green-100 text-green-700' : 'bg-slate-100 text-slate-500'}`}>
                    {survey.is_active ? '受付中' : '停止中'}
                  </span>
                </div>
                <h3 className="text-lg font-bold text-sage-dark mb-2">{survey.title}</h3>
                <p className="text-xs text-slate-400 mb-6 truncate font-mono">{survey.uuid}</p>

                <div className="flex gap-2">
                  <Link href={`/survey/${survey.uuid}`} target="_blank" className="text-xs bg-slate-100 px-3 py-2 rounded-lg hover:bg-slate-200 transition-colors font-medium">
                    回答ページへ ↗
                  </Link>
                  <button className="text-xs bg-sage-light text-sage-dark px-3 py-2 rounded-lg hover:bg-sage-primary hover:text-white transition-colors font-medium">
                    編集
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
