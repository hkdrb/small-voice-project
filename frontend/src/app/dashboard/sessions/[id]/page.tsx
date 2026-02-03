'use client';

import { useEffect, useState, useMemo } from 'react';
import { useParams, useRouter } from 'next/navigation';
import axios from 'axios';
import dynamic from 'next/dynamic';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkBreaks from 'remark-breaks';
// import Tabs from '@/components/ui/Tabs';
import CommentTree from '@/components/dashboard/CommentTree';
import { SessionDetail } from '@/types/dashboard';
import { Map as MapIcon, FileText, MessageCircle, ArrowLeft, Sparkles } from 'lucide-react';
import Link from 'next/link';
import RichTextEditor from '@/components/ui/RichTextEditor';

// Dynamic import for Plotly
const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

// Define simple user type for local use or import shared
interface User {
  id: number;
  role: string;
  org_role?: string;
}

const COLOR_PALETTE = [
  '#FF6B6B', // Coral Red
  '#4ECDC4', // Medium Turquoise
  '#45B7D1', // Sky Blue
  '#FFA07A', // Light Salmon
  '#98D8C8', // Pale Green
  '#F06292', // Pink
  '#AED581', // Light Green
  '#7986CB', // Indigo
  '#9575CD', // Purple
  '#4DB6AC', // Teal
  '#FFD54F', // Amber
  '#4DD0E1', // Cyan
  '#BA68C8', // Lavender
  '#E57373', // Red Light
];

// Helper to wrap text for Plotly tooltips
const wrapText = (text: string, maxLen: number = 30) => {
  if (!text) return '';
  // Split by existing newlines first
  const paragraphs = text.split('\n');

  return paragraphs.map(p => {
    if (p.length <= maxLen) return p;
    const regex = new RegExp(`.{1,${maxLen}}`, 'g');
    return p.match(regex)?.join('<br>') || p;
  }).join('<br>');
};

export default function SessionDetailPage() {
  const params = useParams();
  const id = params?.id;
  const router = useRouter();

  const [data, setData] = useState<SessionDetail | null>(null);
  const [loading, setLoading] = useState(true);

  const [user, setUser] = useState<User | null>(null);
  const [isUpdating, setIsUpdating] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Memoize color mapping
  const categoryColorMap = useMemo(() => {
    if (!data?.results) return new Map<string, string>();

    const uniqueCategories = Array.from(new Set(data.results.map(r => r.sub_topic))).sort();
    const map = new Map<string, string>();

    uniqueCategories.forEach((category, index) => {
      map.set(category, COLOR_PALETTE[index % COLOR_PALETTE.length]);
    });

    return map;
  }, [data]);

  useEffect(() => {
    if (!id) return;

    const fetchDetail = async () => {
      try {
        // 1. Fetch User (for permissions)
        try {
          const userRes = await axios.get('/api/auth/me', { withCredentials: true });
          setUser(userRes.data);
        } catch (e: any) {
          if (e.response && e.response.status === 401) {
            router.push('/login');
            return;
          }
          setUser(null);
        }

        // 2. Fetch Data
        const res = await axios.get(`/api/dashboard/sessions/${id}`, { withCredentials: true });
        setData(res.data);
      } catch (error: any) {
        // Handle Unauthorized Access (Redirect)
        if (error.response && error.response.status === 401) {
          router.push('/login');
          return;
        }

        console.error("Failed to fetch session detail", error);
        // router.push('/dashboard');
      } finally {
        setLoading(false);
      }
    };
    fetchDetail();
  }, [id, router]);

  const handlePublishToggle = async () => {
    if (!data) return;
    const action = data.is_published ? "非公開" : "公開";
    if (!confirm(`このレポートを${action}にしますか？`)) return;
    setIsUpdating(true);
    try {
      const newState = !data.is_published;
      await axios.put(`/api/dashboard/sessions/${id}/publish`, {
        is_published: newState
      }, { withCredentials: true });

      setData({ ...data, is_published: newState });
    } catch (error) {
      alert("更新に失敗しました");
    } finally {
      setIsUpdating(false);
    }
  };

  // Create Post State
  const [isCreatingPost, setIsCreatingPost] = useState(false);
  const [postContent, setPostContent] = useState('');
  const [isAnonymous, setIsAnonymous] = useState(false);

  const handleCreatePost = async () => {
    if (!postContent.trim() || !data) return;
    try {
      await axios.post(`/api/dashboard/sessions/${id}/comments`, {
        content: postContent,
        is_anonymous: isAnonymous
      }, { withCredentials: true });

      // Reset & Reload
      setPostContent('');
      setIsCreatingPost(false);
      setIsAnonymous(false);

      // Reload comments (fetch detail again)
      const res = await axios.get(`/api/dashboard/sessions/${id}`, { withCredentials: true });
      setData(res.data);

    } catch (error) {
      alert("投稿に失敗しました");
    }
  };

  const handleDelete = async () => {
    if (!confirm("本当に削除しますか？この操作は取り消せません。")) return;
    setIsUpdating(true);
    try {
      await axios.delete(`/api/dashboard/sessions/${id}`, { withCredentials: true });
      router.push('/dashboard');
    } catch (error) {
      alert("削除に失敗しました");
      setIsUpdating(false);
    }
  };

  const handleRunCommentAnalysis = async () => {
    if (!data) return;
    setIsAnalyzing(true);
    setIsUpdating(true); // Disable other interactions
    try {
      await axios.post(`/api/dashboard/sessions/${id}/analyze-comments`, {}, { withCredentials: true });
      // Reload Data
      const res = await axios.get(`/api/dashboard/sessions/${id}`, { withCredentials: true });
      setData(res.data);
      alert("分析が完了しました");
    } catch (error) {
      alert("分析の実行に失敗しました（コメントが存在しない可能性があります）");
    } finally {
      setIsUpdating(false);
      setIsAnalyzing(false);
    }
  };

  const handleToggleCommentAnalysisPublish = async () => {
    if (!data) return;
    const action = data.is_comment_analysis_published ? "非公開" : "公開";
    if (!confirm(`みんなの提案分析結果を${action}にしますか？`)) return;
    setIsUpdating(true);
    try {
      const newState = !data.is_comment_analysis_published;
      await axios.put(`/api/dashboard/sessions/${id}/publish-comments`, {
        is_published: newState
      }, { withCredentials: true });

      setData({ ...data, is_comment_analysis_published: newState });
    } catch (error) {
      alert("更新に失敗しました");
    } finally {
      setIsUpdating(false);
    }
  };

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

  if (!data) return <div className="p-8 text-center text-slate-500">データが見つかりません</div>;

  // Check Permissions
  const isAdmin = user?.role === 'admin' || user?.role === 'system_admin' || user?.org_role === 'admin';

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <header className="h-16 flex items-center justify-between px-6 border-b border-white/40 shrink-0 bg-white/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="flex items-center">
          <Link href="/dashboard" className="mr-4 text-slate-400 hover:text-sage-dark transition-colors">
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-lg font-bold text-sage-dark">{data.title}</h1>
              <span className={`px-2 py-0.5 rounded text-xs font-bold ${data.is_published ? 'bg-green-100 text-green-700' : 'bg-slate-100 text-slate-500'}`}>
                {data.is_published ? '公開中' : '下書き'}
              </span>
            </div>
            <div className="flex items-center gap-3 text-xs text-slate-500">
              <p>テーマ: {data.theme}</p>
              <span>•</span>
              <p>{new Date(data.created_at).toLocaleDateString('ja-JP')} 作成</p>
            </div>
          </div>
        </div>

        {/* Admin Actions */}
        {isAdmin && (
          <div className="flex items-center gap-2">
            <button
              onClick={handlePublishToggle}
              disabled={isUpdating}
              className={`px-3 py-1.5 rounded-lg text-sm font-bold transition-all ${data.is_published ? 'bg-slate-200 text-slate-600 hover:bg-slate-300' : 'bg-green-500 text-white hover:bg-green-600'}`}
            >
              {data.is_published ? '🔒 非公開にする' : '🟢 公開する'}
            </button>
            <button
              onClick={handleDelete}
              disabled={isUpdating}
              className="px-3 py-1.5 rounded-lg text-sm font-bold bg-red-100 text-red-600 hover:bg-red-200"
            >
              🗑️ 削除
            </button>
          </div>
        )}
      </header>

      <div className="flex-1 overflow-y-auto p-6 space-y-8 pb-32">

        {/* 1. Meaning Map */}
        <section className="glass-card p-4 h-[600px] relative">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-sage-dark pl-2 border-l-4 border-sage-primary">1. クラスタリング</h3>
          </div>
          <div className="w-full h-full pb-8 flex flex-col">
            <div className="flex-1 min-h-0">
              <Plot
                data={[
                  {
                    x: data.results.map(r => r.x),
                    y: data.results.map(r => r.y),
                    text: data.results.map(r => {
                      return `<b>${r.sub_topic}</b><br>${wrapText(r.original_text, 30)}`;
                    }),
                    mode: 'markers',
                    type: 'scatter',
                    marker: {
                      // Topic Mode (Categorical)
                      size: 12,
                      color: data.results.map(r => {
                        // 特異点（Small Voices）を赤色で強調
                        if (r.is_noise || r.cluster_id === -1 || r.sub_topic.includes("特異点")) {
                          return '#EF4444';
                        }
                        return categoryColorMap.get(r.sub_topic) || '#ccc';
                      }),
                      line: {
                        width: 1.5,
                        color: 'white'
                      },
                      opacity: 0.8,
                      symbol: 'circle'
                    },
                    hoverinfo: 'text',
                    hovertemplate: '%{text}<extra></extra>'
                  }
                ]}
                layout={{
                  autosize: true,
                  hovermode: 'closest',
                  margin: { l: 20, r: 20, t: 20, b: 20 },
                  xaxis: {
                    showgrid: true,
                    gridcolor: 'rgba(200,200,200,0.2)',
                    zeroline: false,
                    showticklabels: false
                  },
                  yaxis: {
                    showgrid: true,
                    gridcolor: 'rgba(200,200,200,0.2)',
                    zeroline: false,
                    showticklabels: false
                  },
                  paper_bgcolor: 'rgba(0,0,0,0)',
                  plot_bgcolor: 'rgba(255,255,255,0.3)', // Slight background for contrast
                  showlegend: false,
                  dragmode: 'zoom',
                  hoverlabel: {
                    bgcolor: 'rgba(255, 255, 255, 0.95)',
                    bordercolor: '#e2e8f0',
                    font: { family: 'sans-serif', size: 14, color: '#334155' },
                    align: 'left'
                  }
                }}
                style={{ width: '100%', height: '100%' }}
                useResizeHandler
                config={{
                  displayModeBar: true,
                  displaylogo: false,
                  modeBarButtonsToRemove: ['select2d', 'lasso2d', 'toggleSpikelines'],
                  scrollZoom: true,
                }}
              />
            </div>
          </div>
          {/* Legend */}
          <div className="mt-4 flex flex-wrap gap-3 px-4 justify-center">
            {Array.from(categoryColorMap.entries()).filter(([cat]) => !cat.includes("特異点")).map(([category, color]) => (
              <div key={category} className="flex items-center gap-1.5 bg-white/60 px-2 py-1 rounded-md text-xs border border-white/40 shadow-sm max-w-[150px]">
                <span className="w-3 h-3 rounded-full shrink-0" style={{ backgroundColor: color }}></span>
                <span className="text-slate-600 font-medium truncate" title={category}>
                  {category}
                </span>
              </div>
            ))}
            {/* 特異点の凡例を常に追加（データが存在する場合） */}
            {data.results.some(r => r.is_noise || r.cluster_id === -1 || r.sub_topic.includes("特異点")) && (
              <div className="flex items-center gap-1.5 bg-white/60 px-2 py-1 rounded-md text-xs border border-white/40 shadow-sm max-w-[150px]">
                <span className="w-3 h-3 rounded-full shrink-0" style={{ backgroundColor: '#EF4444' }}></span>
                <span className="text-slate-600 font-medium truncate">特異点 (Small Voices)</span>
              </div>
            )}
          </div>
        </section>

        {/* 2. Analysis Report -> Critical Issues Definition */}
        <section className="glass-card p-6">
          <div className="mb-4 border-b border-gray-100 pb-2 flex justify-between items-center">
            <h3 className="text-sm font-bold text-sage-dark pl-2 border-l-4 border-sage-primary flex items-center gap-2">
              <FileText className="h-4 w-4" /> 2. 課題リスト
            </h3>
            <span className="text-xs text-slate-400">データから特定された解決すべき課題</span>
          </div>
          <div className="bg-white/40 rounded-xl p-6">
            {(() => {
              if (!data.report_content) {
                return (
                  <p className="text-slate-400 text-center py-10">
                    レポートはまだ作成されていません。
                  </p>
                );
              }

              let issues = [];
              let parseFailed = false;
              try {
                // Try parsing JSON
                const parsed = JSON.parse(data.report_content);
                if (Array.isArray(parsed)) {
                  issues = parsed;
                }
              } catch (e) {
                console.error("JSON parse error:", e);
                // Fallback: If content looks like empty array, treat as such
                if (data.report_content.trim() === '[]') {
                  issues = [];
                } else {
                  parseFailed = true;
                }
              }

              if (issues.length > 0) {
                // Render Issue Cards
                return (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {issues.map((issue: any, idx: number) => (
                      <div key={idx} className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow">
                        <h4 className="font-bold text-sage-dark mb-3 text-sm flex items-start gap-2">
                          <span className="text-amber-500 mt-0.5">⚠️</span>
                          {issue.title}
                        </h4>
                        <p className="text-xs text-slate-600 leading-relaxed">
                          {issue.description}
                        </p>
                        <div className="mt-3 flex gap-2">
                          {issue.urgency === 'high' && <span className="bg-red-100 text-red-700 text-[10px] px-2 py-0.5 rounded font-bold">緊急: 高</span>}
                          {issue.category && <span className="bg-slate-100 text-slate-600 text-[10px] px-2 py-0.5 rounded">{issue.category}</span>}
                        </div>
                      </div>
                    ))}
                  </div>
                );
              } else if (!parseFailed && issues.length === 0) {
                // Parsed to empty array
                return (
                  <div className="text-center py-10 text-slate-500">
                    <p>顕著な課題は検出されませんでした。</p>
                  </div>
                );
              } else {
                // Render Markdown (Legacy or Fallback)
                return (
                  <div className="prose-analysis max-w-none">
                    {/* @ts-ignore */}
                    <ReactMarkdown remarkPlugins={[remarkGfm, remarkBreaks]}>{data.report_content}</ReactMarkdown>
                  </div>
                );
              }
            })()}
          </div>
        </section>

        {/* 3. Everyone's Suggestions Analysis */}
        <section className="glass-card p-6">
          <div className="flex items-center justify-between mb-4 border-b border-gray-100 pb-2">
            <div className="flex items-center gap-3">
              <h3 className="text-sm font-bold text-sage-dark pl-2 border-l-4 border-sage-primary flex items-center gap-2">
                <Sparkles className="h-4 w-4" /> 3. みんなの提案分析
              </h3>
              {isAdmin && (
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${data.is_comment_analysis_published ? 'bg-green-100 text-green-700' : 'bg-slate-100 text-slate-500'}`}>
                  {data.is_comment_analysis_published ? '公開中' : '下書き'}
                </span>
              )}
            </div>
            {isAdmin && (
              <div className="flex items-center gap-2">
                <button
                  onClick={handleToggleCommentAnalysisPublish}
                  disabled={isUpdating}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${data.is_comment_analysis_published ? 'bg-slate-200 text-slate-600 hover:bg-slate-300' : 'bg-green-500 text-white hover:bg-green-600'}`}
                >
                  {data.is_comment_analysis_published ? '🔒 非公開' : '🟢 公開'}
                </button>
                <button
                  onClick={handleRunCommentAnalysis}
                  disabled={isUpdating || isAnalyzing}
                  className="btn-primary px-3 py-1.5 text-xs flex items-center gap-1"
                >
                  {isAnalyzing ? (
                    <>
                      <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white"></div>
                      分析中...
                    </>
                  ) : (
                    <>
                      <Sparkles className="h-3 w-3" />
                      {data.comment_analysis ? '再分析を実行' : '分析を実行'}
                    </>
                  )}
                </button>
              </div>
            )}
          </div>

          <div className="bg-white/40 rounded-xl p-6">
            {(() => {
              if (!data.comment_analysis) {
                return (
                  <p className="text-slate-400 text-center py-10">
                    {isAdmin
                      ? "まだ分析結果がありません。「分析を実行」ボタンを押して分析を開始してください。"
                      : "このセクションの分析結果はまだありません。"}
                  </p>
                );
              }

              let analysisData = null;
              try {
                analysisData = JSON.parse(data.comment_analysis);
              } catch (e) {
                // Fallback for markdown
              }

              if (analysisData && analysisData.overall_summary) {
                // Render New UI
                return (
                  <div className="space-y-8">
                    {/* Summary */}
                    <div className="bg-gradient-to-r from-sage-50 to-white p-4 rounded-xl border border-sage-100">
                      <h4 className="text-sm font-bold text-sage-800 mb-2 flex items-center gap-2">
                        <span className="text-xl">📊</span> 全体要約
                      </h4>
                      <p className="text-sm text-sage-700 leading-relaxed">
                        {analysisData.overall_summary}
                      </p>
                    </div>

                    {/* Trends */}
                    <div>
                      <h4 className="text-sm font-bold text-slate-700 mb-3 flex items-center gap-2">
                        <span className="text-xl">📈</span> 主要なトレンド
                      </h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {analysisData.key_trends.map((trend: any, idx: number) => (
                          <div key={idx} className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm relative overflow-hidden group hover:shadow-md transition-all">
                            <div className={`absolute top-0 right-0 w-16 h-16 bg-gradient-to-bl opacity-10 rounded-bl-3xl transition-transform group-hover:scale-110 
                              ${trend.count_inference === 'High' ? 'from-red-500 to-transparent' :
                                trend.count_inference === 'Medium' ? 'from-orange-500 to-transparent' : 'from-blue-500 to-transparent'}`}
                            />
                            <div className="relative z-10">
                              <h5 className="font-bold text-slate-800 mb-1 flex items-center gap-2">
                                {trend.title}
                                {trend.count_inference === 'High' && <span className="text-[10px] bg-red-100 text-red-600 px-1.5 py-0.5 rounded-full">High</span>}
                              </h5>
                              <p className="text-xs text-slate-600 leading-relaxed">
                                {trend.description}
                              </p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Ideas */}
                    <div>
                      <h4 className="text-sm font-bold text-slate-700 mb-3 flex items-center gap-2">
                        <span className="text-xl">💡</span> 注目すべきアイデア
                      </h4>
                      <div className="space-y-3">
                        {analysisData.notable_ideas.map((idea: any, idx: number) => (
                          <div key={idx} className="bg-amber-50/50 p-4 rounded-xl border border-amber-100/50 flex gap-4">
                            <div className="shrink-0 mt-1">
                              <div className="w-8 h-8 bg-amber-100 rounded-full flex items-center justify-center text-amber-600">
                                <Sparkles className="w-4 h-4" />
                              </div>
                            </div>
                            <div>
                              <h5 className="font-bold text-slate-800 text-sm mb-1">{idea.title}</h5>
                              <p className="text-xs text-slate-600 mb-2">{idea.description}</p>
                              <div className="flex items-center gap-1.5 text-[10px] text-amber-700 font-medium bg-amber-100/50 px-2 py-1 rounded w-fit">
                                <span>🚀 期待される効果:</span>
                                <span>{idea.expected_impact}</span>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                );
              }

              // Fallback to Markdown
              return (
                <div className="prose-analysis max-w-none">
                  {/* @ts-ignore */}
                  <ReactMarkdown remarkPlugins={[remarkGfm, remarkBreaks]}>{data.comment_analysis}</ReactMarkdown>
                </div>
              );
            })()}
          </div>
        </section>

        {/* 4. Comments Chat */}
        <section className="glass-card p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-sm font-bold text-sage-dark pl-2 border-l-4 border-sage-primary">4. みんなの提案チャット</h3>
            <button
              onClick={() => setIsCreatingPost(!isCreatingPost)}
              className="btn-primary px-4 py-2 text-sm flex items-center gap-2"
            >
              <MessageCircle className="h-4 w-4" />
              新規投稿
            </button>
          </div>

          {/* New Post Form */}
          {isCreatingPost && (
            <div className="mb-8 p-4 bg-sage-50 rounded-xl animate-in slide-in-from-top-2 border border-sage-200">
              <h4 className="font-bold text-sage-800 mb-2">新規投稿を作成</h4>
              <RichTextEditor
                content={postContent}
                onChange={(content) => setPostContent(content)}
                placeholder="提案やコメントを入力してください..."
                className="mb-3 min-h-[150px]"
                minHeight="150px"
              />
              <div className="flex items-center justify-between">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={isAnonymous}
                    onChange={(e) => setIsAnonymous(e.target.checked)}
                    className="w-4 h-4 text-sage-600 rounded"
                  />
                  <span className="text-sm text-gray-600">匿名で投稿</span>
                </label>
                <div className="flex gap-2">
                  <button
                    onClick={() => setIsCreatingPost(false)}
                    className="px-4 py-2 text-sm text-gray-500 hover:text-gray-700"
                  >
                    キャンセル
                  </button>
                  <button
                    onClick={handleCreatePost}
                    disabled={!postContent.trim()}
                    className="btn-primary px-4 py-2 text-sm"
                  >
                    投稿する
                  </button>
                </div>
              </div>
            </div>
          )}

          <CommentTree
            comments={data.comments}
            sessionId={data.id}
            currentUserId={user?.id}
            onRefresh={() => {
              // Re-fetch data
              axios.get(`/api/dashboard/sessions/${id}`, { withCredentials: true })
                .then(res => setData(res.data));
            }}
          />
        </section>
      </div>
    </div>
  );
}
