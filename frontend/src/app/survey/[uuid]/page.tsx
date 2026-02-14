"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import axios from "axios";
import { Send, CheckCircle, ClipboardList } from "lucide-react";
import DashboardHeader from "@/components/dashboard/DashboardHeader";
// Removed DashboardTabs import as it's not needed

interface Question {
  id: number;
  text: string;
  is_required: boolean;
  order: number;
}

interface Survey {
  id: number;
  uuid: string;
  title: string;
  description: string;
  is_active: boolean;
  questions: Question[];
  has_answered: boolean;
}

export default function SurveyPage() {
  const params = useParams();
  const uuid = params?.uuid;
  const router = useRouter();

  const [survey, setSurvey] = useState<Survey | null>(null);
  const [answers, setAnswers] = useState<{ [key: number]: string }>({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [hasAlreadyAnswered, setHasAlreadyAnswered] = useState(false);
  const [user, setUser] = useState<any | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!uuid) return;

    const fetchSurveyAndUser = async () => {
      try {
        // Fetch survey
        const res = await axios.get(`/api/surveys/uuid/${uuid}`, { withCredentials: true });
        setSurvey(res.data);

        if (res.data.has_answered) {
          setHasAlreadyAnswered(true);
        }

        // Fetch user (to show dashboard navigation if logged in)
        try {
          const userRes = await axios.get('/api/auth/me', { withCredentials: true });
          setUser(userRes.data);
        } catch (authError) {
          // If 401, just don't show dashboard navigation
          setUser(null);
        }
      } catch (e: any) {
        console.error(e);
        setError("フォームが見つかりません。権限がないか、URLが間違っています。");
      } finally {
        setLoading(false);
      }
    };
    fetchSurveyAndUser();
  }, [uuid]);


  const handleAnswerChange = (qId: number, val: string) => {
    setAnswers(prev => ({ ...prev, [qId]: val }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!survey) return;

    // Validation
    for (const q of survey.questions) {
      if (q.is_required && !answers[q.id]?.trim()) {
        alert(`「${q.text}」は必須項目です`);
        return;
      }
    }

    setSubmitting(true);
    try {
      const payload = {
        answers: Object.entries(answers).map(([qId, content]) => ({
          question_id: Number(qId),
          content: content
        }))
      };

      await axios.post(`/api/surveys/${survey.id}/response`, payload, { withCredentials: true });
      setIsSubmitted(true);
      window.scrollTo(0, 0);
    } catch (e) {
      console.error(e);
      alert("送信に失敗しました。時間をおいて再試行してください。");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-sage-light flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-sage-primary"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-sage-light flex flex-col">
        {user && (
          <DashboardHeader
            title="エラー"
            showBack={true}
          />
        )}
        <div className="flex-1 flex items-center justify-center p-4">
          <div className="glass-card p-8 max-w-md w-full text-center">
            <p className="text-red-500 font-bold mb-4">{error}</p>
            <button onClick={() => router.push("/dashboard")} className="text-sage-primary underline">
              ホームへ戻る
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (isSubmitted) {
    return (
      <div className="min-h-screen bg-linear-to-br from-sage-light to-white flex flex-col">
        {user && (
          <DashboardHeader
            title="送信完了"
            showBack={true}
          />
        )}
        <div className="flex-1 flex items-center justify-center p-4">
          <div className="glass-card max-w-lg w-full p-10 text-center animate-in zoom-in-95 duration-300">
            <div className="w-20 h-20 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto mb-6">
              <CheckCircle className="h-10 w-10" />
            </div>
            <h2 className="text-2xl font-bold text-sage-dark mb-4">回答ありがとうございます！</h2>
            <p className="text-slate-600 mb-8">あなたの回答は正常に送信されました。</p>
            <button onClick={() => router.push("/dashboard")} className="btn-primary w-full py-3">
              ダッシュボードへ戻る
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (hasAlreadyAnswered) {
    return (
      <div className="min-h-screen bg-linear-to-br from-sage-light to-white flex flex-col">
        {user && (
          <DashboardHeader
            title="回答済み"
            showBack={true}
          />
        )}
        <div className="flex-1 flex items-center justify-center p-4">
          <div className="glass-card max-w-lg w-full p-10 text-center animate-in zoom-in-95 duration-300">
            <div className="w-20 h-20 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center mx-auto mb-6">
              <CheckCircle className="h-10 w-10" />
            </div>
            <h2 className="text-2xl font-bold text-sage-dark mb-4">このアンケートは回答済みです</h2>
            <p className="text-slate-600 mb-8">ご協力ありがとうございました。</p>
            <button onClick={() => router.push("/dashboard")} className="btn-primary w-full py-3">
              ダッシュボードへ戻る
            </button>
          </div>
        </div>
      </div>
    );
  }

  const isAdmin = user?.role === 'system_admin' || user?.org_role === 'admin';
  const displayTab = isAdmin ? 'surveys' : 'answers';

  return (
    <div className="min-h-screen bg-linear-to-br from-sage-light to-white flex flex-col">
      {user && (
        <>
          <DashboardHeader
            title="アンケート回答"
            icon={<ClipboardList className="h-5 w-5" />}
            showBack={true}
            backHref="/dashboard"
          />
        </>
      )}

      <div className={`flex-1 overflow-y-auto py-12 px-4 sm:px-6 ${!user ? 'pt-12' : ''}`}>
        <div className="max-w-2xl mx-auto">
          {!user && (
            <div className="text-center mb-10">
              <img src="/logo.svg" alt="Small Voice" className="h-16 mx-auto mb-4" />
            </div>
          )}
          <div className="text-center mb-10">
            <h1 className="text-3xl font-extrabold text-sage-dark mb-2">{survey?.title}</h1>
            <p className="text-slate-600">{survey?.description}</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6 animate-in slide-in-from-bottom-4 duration-500 pb-20">
            {survey?.questions.sort((a, b) => a.order - b.order).map((q) => (
              <div key={q.id} className="glass-card p-6 !rounded-2xl shadow-sm hover:shadow-md transition-shadow duration-300">
                <label className="block text-lg font-bold text-gray-800 mb-2">
                  {q.text}
                  {q.is_required && <span className="ml-2 text-xs text-red-600 bg-red-100 px-2 py-1 rounded-md align-middle">必須</span>}
                </label>
                <textarea
                  value={answers[q.id] || ""}
                  onChange={(e) => handleAnswerChange(q.id, e.target.value)}
                  className="w-full glass-input p-4 text-base min-h-[120px] resize-y"
                  placeholder="回答を入力してください..."
                />
              </div>
            ))}

            <div className="pt-4">
              <button
                type="submit"
                disabled={submitting}
                className={`
                                  w-full btn-primary py-4 text-lg shadow-lg flex items-center justify-center gap-2
                                  ${submitting ? 'opacity-70 cursor-not-allowed' : 'hover:scale-[1.02]'}
                              `}
              >
                {submitting ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                    送信中...
                  </>
                ) : (
                  <>
                    <span>回答を送信する</span>
                    <Send className="h-5 w-5" />
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
