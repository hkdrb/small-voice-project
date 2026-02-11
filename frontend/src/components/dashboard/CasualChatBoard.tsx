import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { MessageSquare, Heart, RefreshCw, BarChart2, CheckCircle2, User, Sparkles, Reply, ChevronDown, ChevronUp } from 'lucide-react';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkBreaks from 'remark-breaks';
import RichTextEditor from '@/components/ui/RichTextEditor';

// Define types locally or import if shared. Since CasualPost is specific here:
interface CasualPost {
  id: number;
  content: string;
  created_at: string;
  user_name: string;
  likes_count: number;
  is_liked_by_me: boolean;
  parent_id?: number | null;
  replies_count: number;
  children?: CasualPost[];
}

interface AnalysisReport {
  id: number;
  created_at: string;
  start_date: string;
  end_date: string;
  is_published: boolean;
  result: {
    recommendations: Recommendation[];
    message?: string;
  };
}

interface Recommendation {
  title: string;
  reason: string;
  survey_description: string;
  suggested_questions: string[];
}

interface CasualChatBoardProps {
  user: any;
}

export default function CasualChatBoard({ user }: CasualChatBoardProps) {
  const [posts, setPosts] = useState<CasualPost[]>([]);
  const [loading, setLoading] = useState(true);
  const [newPostContent, setNewPostContent] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [isComposerOpen, setIsComposerOpen] = useState(false);

  // Analysis State
  const [analyses, setAnalyses] = useState<AnalysisReport[]>([]);
  const [analyzing, setAnalyzing] = useState(false);
  const [selectedAnalysis, setSelectedAnalysis] = useState<AnalysisReport | null>(null);

  // Date range for analysis (default: last 30 days)
  const getDefaultEndDate = () => {
    const today = new Date();
    return today.toISOString().split('T')[0];
  };

  const getDefaultStartDate = () => {
    const date = new Date();
    date.setDate(date.getDate() - 30);
    return date.toISOString().split('T')[0];
  };

  const [startDate, setStartDate] = useState(getDefaultStartDate());
  const [endDate, setEndDate] = useState(getDefaultEndDate());

  const isAdmin = user?.role === 'system_admin' || user?.org_role === 'admin';

  useEffect(() => {
    fetchPosts();
    fetchAnalyses();
  }, [user]);

  const fetchPosts = async () => {
    try {
      if (!loading) setRefreshing(true);
      const res = await axios.get('/api/casual/posts');
      const allPosts = res.data;

      // Build tree structure
      const postsMap = new Map<number, CasualPost>();
      const rootPosts: CasualPost[] = [];

      allPosts.forEach((post: CasualPost) => {
        postsMap.set(post.id, { ...post, children: [] });
      });

      allPosts.forEach((post: CasualPost) => {
        const postWithChildren = postsMap.get(post.id)!;
        if (post.parent_id && postsMap.has(post.parent_id)) {
          postsMap.get(post.parent_id)!.children!.push(postWithChildren);
        } else if (!post.parent_id) {
          rootPosts.push(postWithChildren);
        }
      });

      setPosts(rootPosts);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const fetchAnalyses = async () => {
    try {
      const res = await axios.get('/api/casual/analyses');
      setAnalyses(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  const handleSubmit = async () => {
    if (!newPostContent.trim()) return;

    setSubmitting(true);
    try {
      await axios.post('/api/casual/posts', { content: newPostContent });
      setNewPostContent('');
      setIsComposerOpen(false); // Close modal
      fetchPosts(); // Refresh
    } catch (e) {
      alert('投稿に失敗しました');
    } finally {
      setSubmitting(false);
    }
  };

  const handleLike = async (postId: number) => {
    try {
      const res = await axios.post(`/api/casual/posts/${postId}/like`);
      // Update posts recursively
      const updateLikes = (posts: CasualPost[]): CasualPost[] => {
        return posts.map(p => {
          if (p.id === postId) {
            return { ...p, likes_count: res.data.likes_count, is_liked_by_me: res.data.liked };
          }
          if (p.children) {
            return { ...p, children: updateLikes(p.children) };
          }
          return p;
        });
      };
      setPosts(updateLikes(posts));
    } catch (e) {
      console.error(e);
    }
  };

  const handleAnalyze = async () => {
    if (!confirm(`${startDate} から ${endDate} までの投稿を分析しますか？`)) return;
    setAnalyzing(true);
    try {
      await axios.post('/api/casual/analyze', {}, {
        params: {
          start_date: startDate,
          end_date: endDate
        }
      });
      fetchAnalyses(); // Refresh list
      alert('分析が完了しました');
    } catch (e) {
      alert('分析に失敗しました');
    } finally {
      setAnalyzing(false);
    }
  };

  const toggleVisibility = async (analysis: AnalysisReport) => {
    const action = analysis.is_published ? "非公開" : "公開";
    if (!confirm(`このレポートを${action}にしますか？`)) return;

    try {
      const newStatus = !analysis.is_published;
      await axios.patch(`/api/casual/analyses/${analysis.id}/visibility`, { is_published: newStatus });
      setAnalyses(analyses.map(a => a.id === analysis.id ? { ...a, is_published: newStatus } : a));
      setSelectedAnalysis(null);
    } catch (e) {
      alert('更新に失敗しました');
    }
  };

  const handleCreateForm = async (recommendation: Recommendation) => {
    if (!confirm(`「${recommendation.title}」のフォームを作成しますか？\n非公開状態で作成されます。`)) return;

    try {
      // Create a new survey based on the recommendation
      const questions = recommendation.suggested_questions.map((q, index) => ({
        text: q,
        is_required: false,
        order: index + 1
      }));

      const response = await axios.post('/api/surveys', {
        title: recommendation.title,
        description: recommendation.survey_description || recommendation.reason,
        questions: questions.length > 0 ? questions : [
          { text: 'ご意見をお聞かせください', is_required: false, order: 1 }
        ]
      });

      alert(`フォーム「${recommendation.title}」を作成しました。\nフォーム管理画面から編集・公開できます。`);
    } catch (e: any) {
      console.error('Form creation error:', e);
      alert(`フォームの作成に失敗しました: ${e.response?.data?.detail || e.message}`);
    }
  };

  const handleDeleteAnalysis = async (analysisId: number) => {
    if (!confirm('この分析レポートを削除しますか？')) return;

    try {
      await axios.delete(`/api/casual/analyses/${analysisId}`);
      setAnalyses(analyses.filter(a => a.id !== analysisId));
      if (selectedAnalysis?.id === analysisId) {
        setSelectedAnalysis(null);
      }
      alert('分析レポートを削除しました');
    } catch (e) {
      alert('削除に失敗しました');
    }
  };

  return (
    <div className="flex h-[calc(100vh-220px)] min-h-[500px] gap-6">
      {/* Main Board Area */}
      <div className="flex-1 flex flex-col h-full bg-gradient-to-br from-amber-50/30 via-white to-blue-50/20 rounded-2xl border-2 border-amber-200/40 shadow-lg overflow-hidden relative">
        {/* Board Header - Bulletin Board Style */}
        <div className="shrink-0 bg-gradient-to-r from-amber-100 to-orange-100 border-b-4 border-amber-300 shadow-md">
          <div className="p-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-white rounded-lg shadow-md flex items-center justify-center border-2 border-amber-200">
                <MessageSquare className="w-6 h-6 text-amber-600" />
              </div>
              <div>
                <h2 className="font-bold text-xl text-amber-900 tracking-wide">みんなの声</h2>
                <p className="text-xs text-amber-700/80">日々の気づきや想いを自由に共有する場所</p>
              </div>
            </div>
            <button
              onClick={fetchPosts}
              disabled={refreshing}
              className={`p-2 hover:bg-white/60 rounded-lg transition-all text-amber-600 hover:text-amber-800 hover:shadow-sm ${refreshing ? 'opacity-50 cursor-not-allowed' : ''}`}
              title="更新"
            >
              <RefreshCw className={`w-5 h-5 ${refreshing ? 'animate-spin' : ''}`} />
            </button>
          </div>

          {/* Decorative Pin Header */}
          <div className="h-3 bg-gradient-to-b from-amber-200/50 to-transparent relative">
            <div className="absolute top-0 left-0 right-0 flex justify-around">
              {[...Array(12)].map((_, i) => (
                <div key={i} className="w-2 h-2 bg-red-400 rounded-full shadow-sm border border-red-500/30" />
              ))}
            </div>
          </div>
        </div>



        {/* Posts Area (Scrollable) */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI0MCIgaGVpZ2h0PSI0MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTSAwIDEwIEwgNDAgMTAgTSAxMCAwIEwgMTAgNDAgTSAwIDIwIEwgNDAgMjAgTSAyMCAwIEwgMjAgNDAgTSAwIDMwIEwgNDAgMzAgTSAzMCAwIEwgMzAgNDAiIGZpbGw9Im5vbmUiIHN0cm9rZT0icmdiYSgyNTEsMTkxLDM2LDAuMDUpIiBzdHJva2Utd2lkdGg9IjEiLz48L3BhdHRlcm4+PC9kZWZzPjxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9InVybCgjZ3JpZCkiLz48L3N2Zz4=')] custom-scrollbar">
          {loading ? (
            <div className="flex justify-center py-16">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-4 border-amber-200 border-t-amber-500 mx-auto mb-4"></div>
                <p className="text-amber-600 text-sm font-medium">読み込み中...</p>
              </div>
            </div>
          ) : posts.length === 0 ? (
            <div className="text-center py-20">
              <div className="w-24 h-24 bg-white rounded-2xl shadow-lg flex items-center justify-center mx-auto mb-6 border-4 border-amber-100 rotate-3">
                <MessageSquare className="w-12 h-12 text-amber-200" />
              </div>
              <p className="text-amber-600 text-lg font-bold mb-2">まだ投稿がありません</p>
              <p className="text-amber-500/70 text-sm">最初の声を届けてみませんか？</p>
            </div>
          ) : (
            posts.map((post, index) => (
              <PostNode
                key={post.id}
                post={post}
                index={index}
                user={user}
                onLike={handleLike}
                onRefresh={fetchPosts}
                depth={0}
              />
            ))
          )}
        </div>


        {/* Floating Action Button (FAB) for New Post */}
        <button
          onClick={() => setIsComposerOpen(true)}
          className="absolute bottom-8 right-8 z-30 w-14 h-14 bg-gradient-to-r from-amber-500 to-orange-500 text-white rounded-full shadow-lg hover:shadow-xl hover:scale-110 transition-all flex items-center justify-center group"
          title="新規投稿"
        >
          <MessageSquare className="w-7 h-7 fill-current" />
          <span className="absolute -top-10 right-0 bg-gray-800 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
            投稿する
          </span>
        </button>

        {/* Post Composer Modal */}
        {isComposerOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm animate-in fade-in duration-200" onClick={() => setIsComposerOpen(false)}>
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden ring-1 ring-amber-200" onClick={e => e.stopPropagation()}>
              <div className="p-4 border-b border-amber-100 bg-gradient-to-r from-amber-50 to-white flex justify-between items-center">
                <h3 className="font-bold text-amber-900 flex items-center gap-2">
                  <MessageSquare className="w-5 h-5 text-amber-500" />
                  新しい投稿を作成
                </h3>
                <button
                  onClick={() => setIsComposerOpen(false)}
                  className="w-8 h-8 rounded-full hover:bg-amber-100 flex items-center justify-center text-amber-500 transition-colors"
                >
                  ×
                </button>
              </div>
              <div className="p-6">
                <div className="flex items-start gap-4 mb-4">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-sage-400 to-sage-600 flex items-center justify-center text-white font-bold ring-2 ring-white shadow-md shrink-0">
                    <User className="w-5 h-5" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-bold text-slate-700 mb-1">{user?.name || user?.username || 'あなた'}</p>
                    <p className="text-xs text-slate-400">@みんなの声</p>
                  </div>
                </div>

                <RichTextEditor
                  content={newPostContent}
                  onChange={setNewPostContent}
                  placeholder="最近どうですか？思ったこと、気づいたことを自由に書いてみましょう..."
                  className="min-h-[150px] mb-4 text-base"
                  minHeight="150px"
                />

                <div className="flex justify-end items-center pt-2">
                  <div className="flex gap-3">
                    <button
                      onClick={() => setIsComposerOpen(false)}
                      className="px-4 py-2 text-sm text-slate-500 hover:bg-slate-50 rounded-lg transition-colors font-bold"
                    >
                      キャンセル
                    </button>
                    <button
                      onClick={handleSubmit}
                      disabled={submitting || !newPostContent.trim()}
                      className="btn-primary py-2 px-6 text-sm font-bold disabled:opacity-50 shadow-md hover:shadow-lg transition-all transform hover:scale-105 disabled:transform-none flex items-center gap-2"
                    >
                      {submitting ? (
                        <>
                          <RefreshCw className="w-4 h-4 animate-spin" />
                          送信中...
                        </>
                      ) : (
                        <>
                          <MessageSquare className="w-4 h-4" />
                          投稿する
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Analysis Sidebar (Visible to Admin, or to Members if published analyses exist) */}
      {(isAdmin || analyses.length > 0) && (
        <div className="w-80 flex flex-col h-full bg-white/60 backdrop-blur-md rounded-2xl border border-sage-200/40 shadow-sm overflow-hidden shrink-0">
          <div className="p-4 border-b border-sage-100 bg-gradient-to-br from-sage-50 to-white sticky top-0 z-10">
            <div className="flex items-center mb-2">
              <BarChart2 className="w-5 h-5 text-sage-600 mr-2" />
              <h2 className="font-bold text-sage-800 text-sm">作成フォームの提案</h2>
            </div>
            <p className="text-[10px] text-sage-600 mb-3 leading-relaxed">
              日々の雑談投稿をAIが分析し、作成するフォームを提案します。
            </p>

            {isAdmin && (
              <>
                {/* Date Range Selector */}
                <div className="mb-3 space-y-2">
                  <label className="text-[10px] text-sage-700 font-bold mb-1.5 block">分析対象期間</label>
                  <div className="space-y-2">
                    <div>
                      <label className="text-[9px] text-sage-600 block mb-1">開始日</label>
                      <input
                        type="date"
                        value={startDate}
                        onChange={(e) => setStartDate(e.target.value)}
                        max={endDate}
                        className="w-full px-3 py-1.5 text-xs border border-sage-200 rounded-lg focus:ring-2 focus:ring-sage-200 focus:border-sage-400 outline-none"
                      />
                    </div>
                    <div>
                      <label className="text-[9px] text-sage-600 block mb-1">終了日</label>
                      <input
                        type="date"
                        value={endDate}
                        onChange={(e) => setEndDate(e.target.value)}
                        min={startDate}
                        max={getDefaultEndDate()}
                        className="w-full px-3 py-1.5 text-xs border border-sage-200 rounded-lg focus:ring-2 focus:ring-sage-200 focus:border-sage-400 outline-none"
                      />
                    </div>
                  </div>
                </div>

                <button
                  onClick={handleAnalyze}
                  disabled={analyzing}
                  className="w-full bg-gradient-to-r from-sage-500 to-sage-600 hover:from-sage-600 hover:to-sage-700 text-white py-2 text-xs flex items-center justify-center gap-2 shadow-sm rounded-lg font-bold transition-all"
                >
                  {analyzing ? (
                    <>
                      <RefreshCw className="w-3 h-3 animate-spin" /> 分析中...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-3 h-3" /> AI分析を実行
                    </>
                  )}
                </button>
              </>
            )}
          </div>

          <div className="flex-1 overflow-y-auto p-3 space-y-3 custom-scrollbar">
            {analyses.length === 0 ? (
              <div className="text-center py-10">
                <div className="w-12 h-12 bg-sage-50 rounded-full flex items-center justify-center mx-auto mb-2">
                  <BarChart2 className="w-5 h-5 text-sage-300" />
                </div>
                <p className="text-xs text-gray-400">まだ分析レポートがありません</p>
              </div>
            ) : (
              analyses.map(analysis => (
                <div
                  key={analysis.id}
                  className={`p-3 rounded-lg border cursor-pointer transition-all group hover:shadow-md relative overflow-hidden ${selectedAnalysis?.id === analysis.id
                    ? 'bg-sage-50 border-sage-300 ring-2 ring-sage-200'
                    : 'bg-white border-sage-100 hover:border-sage-200'
                    }`}
                >
                  <div className="flex justify-between items-start mb-1.5 z-10 relative">
                    <span className="text-xs font-bold text-sage-900 flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-sage-500"></span>
                      {format(new Date(analysis.created_at), 'M/d HH:mm', { locale: ja })}
                    </span>
                    {isAdmin && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteAnalysis(analysis.id);
                        }}
                        className="text-red-400 hover:text-red-600 transition-colors p-1 hover:bg-red-50 rounded"
                        title="削除"
                      >
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    )}
                  </div>
                  <div
                    onClick={() => setSelectedAnalysis(analysis)}
                    className="cursor-pointer"
                  >
                    <div className="text-[10px] text-gray-500 truncate mb-2">
                      期間: {format(new Date(analysis.start_date), 'M/d', { locale: ja })} - {format(new Date(analysis.end_date), 'M/d', { locale: ja })}
                    </div>

                    <div className="flex items-center justify-between">
                      <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${analysis.is_published ? 'bg-green-100 text-green-700' : 'bg-slate-100 text-slate-500'
                        }`}>
                        {analysis.is_published ? '公開中' : '下書き'}
                      </span>
                      <span className="text-[10px] text-sage-400 group-hover:translate-x-1 transition-transform">詳細 &gt;</span>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Analysis Detail Modal */}
      {selectedAnalysis && (
        <div className="fixed inset-0 bg-black/30 backdrop-blur-sm z-50 flex items-center justify-center p-6 animate-in fade-in duration-200" onClick={() => setSelectedAnalysis(null)}>
          <div className="bg-white/95 backdrop-blur-xl w-full max-w-2xl max-h-[85vh] rounded-2xl shadow-2xl overflow-hidden flex flex-col ring-1 ring-sage-200/50" onClick={e => e.stopPropagation()}>
            <div className="p-5 border-b border-sage-100 flex justify-between items-center bg-gradient-to-r from-sage-50 to-white">
              <div>
                <h3 className="font-bold text-sage-800 flex items-center gap-2 text-lg">
                  <Sparkles className="w-5 h-5 text-sage-500" />
                  AI分析レポート
                </h3>
                <p className="text-xs text-sage-600 mt-1">作成日時: {format(new Date(selectedAnalysis.created_at), 'yyyy/MM/dd HH:mm', { locale: ja })}</p>
              </div>
              <button onClick={() => setSelectedAnalysis(null)} className="w-8 h-8 rounded-full bg-sage-100 hover:bg-sage-200 flex items-center justify-center text-sage-600 hover:text-sage-800 transition-colors">×</button>
            </div>

            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              <div>
                <h4 className="text-xs font-bold text-sage-600 uppercase tracking-wider mb-4 border-b border-sage-100 pb-2">推奨されるサーベイテーマ</h4>

                {!selectedAnalysis.result || !selectedAnalysis.result.recommendations || selectedAnalysis.result.recommendations.length === 0 ? (
                  <div className="p-8 bg-sage-50 rounded-xl border border-dashed border-sage-200 text-sm text-gray-500 text-center flex flex-col items-center">
                    <CheckCircle2 className="w-8 h-8 text-sage-300 mb-2" />
                    <p>{selectedAnalysis.result?.message || "現在、特段の推奨事項はありませんでした。"}</p>
                    <p className="text-xs text-gray-400 mt-1">引き続き投稿の傾向をモニタリングします。</p>
                  </div>
                ) : (
                  <div className="grid gap-5">
                    {selectedAnalysis.result.recommendations.map((rec, idx) => (
                      <div key={idx} className="group bg-sage-50/40 hover:bg-sage-50/70 border border-sage-100 p-5 rounded-2xl transition-colors">
                        <div className="flex items-start gap-4 mb-3">
                          <div className="w-8 h-8 rounded-full bg-sage-100 flex items-center justify-center shrink-0 text-sage-600 mt-0.5">
                            <span className="font-bold text-sm">{idx + 1}</span>
                          </div>
                          <div className="flex-1">
                            <h5 className="font-bold text-sage-900 text-lg mb-2">{rec.title}</h5>

                            {/* Admin Reason */}
                            <div className="bg-white/80 p-3 rounded-lg border border-sage-100 mb-3">
                              <p className="text-[10px] font-bold text-sage-600 mb-1 flex items-center gap-1">
                                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                                管理者向け：分析背景
                              </p>
                              <p className="text-sm text-slate-700 leading-relaxed">{rec.reason}</p>
                            </div>

                            {/* Survey Description for Respondents */}
                            {rec.survey_description && (
                              <div className="bg-gradient-to-br from-sage-50 to-white p-3 rounded-lg border border-sage-200 mb-3">
                                <p className="text-[10px] font-bold text-sage-700 mb-1 flex items-center gap-1">
                                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                                  </svg>
                                  回答者向け：フォーム説明文
                                </p>
                                <p className="text-sm text-sage-800 leading-relaxed font-medium">{rec.survey_description}</p>
                              </div>
                            )}

                            {rec.suggested_questions && rec.suggested_questions.length > 0 && (
                              <div className="bg-white rounded-xl p-4 border border-sage-100 shadow-sm mb-4">
                                <p className="text-xs font-bold text-sage-600 mb-2 flex items-center gap-1">
                                  <MessageSquare className="w-3 h-3" /> 具体的な質問案
                                </p>
                                <ul className="space-y-2">
                                  {rec.suggested_questions.map((q, qIdx) => (
                                    <li key={qIdx} className="text-sm text-gray-600 flex items-start gap-2">
                                      <span className="text-sage-400 mt-1">•</span>
                                      {q}
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}

                            {/* Form Creation Button */}
                            {isAdmin && (
                              <button
                                onClick={() => handleCreateForm(rec)}
                                className="w-full mt-3 px-4 py-2.5 bg-gradient-to-r from-sage-600 to-sage-500 hover:from-sage-700 hover:to-sage-600 text-white rounded-xl text-sm font-bold shadow-md hover:shadow-lg transition-all flex items-center justify-center gap-2"
                              >
                                <Sparkles className="w-4 h-4" />
                                この提案でフォームを作成
                              </button>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {isAdmin && (
                <div className="mt-8 pt-6 border-t border-sage-100 flex items-center justify-between bg-sage-50/30 -mx-6 -mb-6 p-6">
                  <p className="text-xs text-sage-700 max-w-[60%]">
                    ※ 「公開」に設定すると、一般メンバーもこの分析レポート（推奨テーマと質問案）を閲覧できるようになります。
                  </p>
                  <button
                    onClick={() => toggleVisibility(selectedAnalysis)}
                    className={`px-5 py-2.5 rounded-xl text-sm font-bold transition-all shadow-sm hover:shadow-md flex items-center gap-2 ${selectedAnalysis.is_published ? 'bg-white border border-green-200 text-green-600 hover:bg-green-50' : 'bg-sage-600 text-white hover:bg-sage-700 hover:scale-105'}`}
                  >
                    {selectedAnalysis.is_published ? (
                      <>
                        <CheckCircle2 className="w-4 h-4" /> 公開中 (非公開にする)
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-4 h-4" /> メンバーに公開する
                      </>
                    )}
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// PostNode Component - Recursive rendering for threaded replies
function PostNode({
  post,
  index,
  user,
  onLike,
  onRefresh,
  depth = 0
}: {
  post: CasualPost;
  index: number;
  user: any;
  onLike: (id: number) => void;
  onRefresh: () => void;
  depth?: number;
}) {
  const [isReplying, setIsReplying] = useState(false);
  const [replyContent, setReplyContent] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [showReplies, setShowReplies] = useState(true);

  const isMyPost = post.user_name === user?.username;
  const hasReplies = post.children && post.children.length > 0;

  const handleReply = async () => {
    if (!replyContent.trim()) return;

    setSubmitting(true);
    try {
      await axios.post('/api/casual/posts', {
        content: replyContent,
        parent_id: post.id
      });
      setReplyContent('');
      setIsReplying(false);
      setShowReplies(true);
      onRefresh();
    } catch (e) {
      alert('返信に失敗しました');
    } finally {
      setSubmitting(false);
    }
  };

  const indent = Math.min(depth * 24, 96);

  return (
    <div
      className="animate-in fade-in slide-in-from-bottom-3 duration-300"
      style={{
        animationDelay: `${index * 30}ms`,
        marginLeft: `${indent}px`
      }}
    >
      {/* Bulletin Board Note Style */}
      <div className={`relative bg-white p-5 rounded-lg border-2 ${isMyPost ? 'border-amber-300' : 'border-amber-200'} shadow-md hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1 mb-3`}>
        {/* Decorative Pin */}
        {depth === 0 && (
          <div className="absolute -top-3 left-6">
            <div className="w-6 h-6 bg-red-400 rounded-full shadow-lg border-2 border-red-500/50 flex items-center justify-center">
              <div className="w-2 h-2 bg-red-600 rounded-full"></div>
            </div>
          </div>
        )}

        {/* Post Header */}
        <div className="flex items-center justify-between mb-3 pt-2">
          <div className="flex items-center gap-2">
            <div className={`${isMyPost ? 'bg-amber-100 text-amber-700' : 'bg-gray-100 text-gray-600'} p-2 rounded-full shadow-sm`}>
              <User className="h-4 w-4" />
            </div>
            <div>
              <span className="font-bold text-sm text-slate-800">{post.user_name}</span>
              <span className="text-xs text-slate-500 ml-2">
                {format(new Date(post.created_at), 'M月d日 H:mm', { locale: ja })}
              </span>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => onLike(post.id)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold transition-all shadow-sm hover:shadow-md ${post.is_liked_by_me ? 'bg-pink-100 text-pink-600 ring-2 ring-pink-200' : 'bg-white/80 text-gray-500 hover:bg-pink-50 hover:text-pink-500'}`}
            >
              <Heart className={`w-4 h-4 ${post.is_liked_by_me ? 'fill-current' : ''}`} />
              <span>{post.likes_count > 0 ? post.likes_count : ''}</span>
            </button>

            <button
              onClick={() => setIsReplying(!isReplying)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold bg-white/80 text-gray-500 hover:bg-sage-50 hover:text-sage-600 transition-all shadow-sm hover:shadow-md"
            >
              <Reply className="w-4 h-4" />
              返信
            </button>
          </div>
        </div>

        {/* Post Content */}
        <div className="text-sm text-slate-700 leading-relaxed markdown-body pl-1 bg-white/40 p-3 rounded border border-white/60">
          <ReactMarkdown remarkPlugins={[remarkGfm, remarkBreaks]}>
            {post.content}
          </ReactMarkdown>
        </div>

        {/* Reply Form */}
        {isReplying && (
          <div className="mt-4 pt-4 border-t border-slate-200/50 animate-in slide-in-from-top-2">
            <RichTextEditor
              content={replyContent}
              onChange={setReplyContent}
              placeholder="返信内容を入力..."
              className="min-h-[80px] mb-2"
              minHeight="80px"
            />
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setIsReplying(false)}
                className="text-xs text-slate-500 hover:text-slate-700 px-3 py-1.5"
              >
                キャンセル
              </button>
              <button
                onClick={handleReply}
                disabled={submitting || !replyContent.trim()}
                className="btn-primary px-4 py-1.5 text-xs disabled:opacity-50"
              >
                {submitting ? '送信中...' : '返信する'}
              </button>
            </div>
          </div>
        )}

        {/* Decorative Tape Effect */}
        {depth === 0 && (
          <div className="absolute -bottom-1 right-8 w-16 h-3 bg-amber-100/60 border-t border-b border-amber-200/40 transform rotate-2 opacity-50"></div>
        )}
      </div>

      {/* Replies */}
      {hasReplies && (
        <div className="mt-2 ml-6">
          {!showReplies ? (
            <button
              onClick={() => setShowReplies(true)}
              className="flex items-center gap-2 text-xs font-bold text-sage-primary hover:text-sage-dark transition-colors mb-2"
            >
              <ChevronDown className="h-3 w-3" />
              <span>{post.children!.length}件の返信を表示</span>
            </button>
          ) : (
            <>
              <button
                onClick={() => setShowReplies(false)}
                className="flex items-center gap-2 text-xs text-slate-400 hover:text-slate-600 mb-2"
              >
                <ChevronUp className="h-3 w-3" />
                返信を閉じる
              </button>
              {post.children!.map((child, idx) => (
                <PostNode
                  key={child.id}
                  post={child}
                  index={idx}
                  user={user}
                  onLike={onLike}
                  onRefresh={onRefresh}
                  depth={depth + 1}
                />
              ))}
            </>
          )}
        </div>
      )}
    </div>
  );
}
