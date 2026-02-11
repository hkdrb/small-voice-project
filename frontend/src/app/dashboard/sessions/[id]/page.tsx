'use client';

import { useEffect, useState, useMemo, useRef } from 'react';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import axios from 'axios';
import dynamic from 'next/dynamic';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkBreaks from 'remark-breaks';
// import Tabs from '@/components/ui/Tabs';
import CommentTree from '@/components/dashboard/CommentTree';
import { SessionDetail } from '@/types/dashboard';
import { Map as MapIcon, FileText, MessageCircle, ArrowLeft, Sparkles, Users, ChevronDown, User as UserIcon, CheckCircle, ListTodo, Lightbulb } from 'lucide-react';
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
  const searchParams = useSearchParams();
  const targetTitle = searchParams.get('title');

  const [data, setData] = useState<SessionDetail | null>(null);
  const [loading, setLoading] = useState(true);

  const [user, setUser] = useState<User | null>(null);
  const [isUpdating, setIsUpdating] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Active Issue/Thread State
  const [activeIssue, setActiveIssue] = useState<any>(null);
  const [activeThreadRootId, setActiveThreadRootId] = useState<number | null>(null);

  // Auto-open issue from query param
  useEffect(() => {
    if (data && targetTitle && !activeIssue) {
      let issues = [];
      try {
        const parsed = JSON.parse(data.report_content);
        if (Array.isArray(parsed)) issues = parsed;
      } catch (e) { }

      const tTitle = targetTitle as string;
      const found = issues.find((i: any) => i.title === tTitle);
      if (found) {
        setActiveIssue(found);
      }
    }
  }, [data, targetTitle, activeIssue]);

  // State for linking Issue List with Clustering Map
  const [selectedIssueTopics, setSelectedIssueTopics] = useState<string[]>([]);
  // State for Accordion Expansion (One can be open at a time)
  const [expandedIssueIndex, setExpandedIssueIndex] = useState<number | null>(null);

  // Layout state for Plotly to handle zoom/reset
  const [plotLayout, setPlotLayout] = useState<any>({
    autosize: true,
    hovermode: 'closest',
    margin: { l: 20, r: 20, t: 20, b: 20 },
    xaxis: { showgrid: true, gridcolor: 'rgba(200,200,200,0.2)', zeroline: false, showticklabels: false },
    yaxis: { showgrid: true, gridcolor: 'rgba(200,200,200,0.2)', zeroline: false, showticklabels: false },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(255,255,255,0.3)',
    showlegend: false,
    dragmode: 'zoom',
    hoverlabel: {
      bgcolor: 'rgba(255, 255, 255, 0.95)',
      bordercolor: '#e2e8f0',
      font: { family: 'sans-serif', size: 12, color: '#334155' },
      align: 'left'
    }
  });

  // State for highlighting specific text from Small Voice links
  const [highlightedText, setHighlightedText] = useState<string | null>(null);

  // Ref for auto-scrolling to map
  const mapSectionRef = useRef<HTMLElement>(null);

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

  // Force resize event for Plotly when activeIssue changes (layout transition)
  useEffect(() => {
    // Trigger reset immediately and frequently during the transition
    window.dispatchEvent(new Event('resize'));

    const timers = [
      setTimeout(() => window.dispatchEvent(new Event('resize')), 10),
      setTimeout(() => window.dispatchEvent(new Event('resize')), 50),
      setTimeout(() => window.dispatchEvent(new Event('resize')), 100), // End of animation
    ];

    return () => timers.forEach(t => clearTimeout(t));
  }, [activeIssue]);

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
    if (!postContent.trim() || !data || !activeIssue) return;

    try {
      let rootId = activeThreadRootId;

      // 1. Prepare Root if needed
      if (!rootId) {
        // Create System Root (Hidden)
        const systemContent = `System Root for Issue: ${activeIssue.title}\n\n<!-- issue:${activeIssue.title} --> <!-- system_root -->`;

        const rootRes = await axios.post(`/api/dashboard/sessions/${id}/comments`, {
          content: systemContent,
          is_anonymous: false // System
        }, { withCredentials: true });

        rootId = rootRes.data.id;
      }

      // 2. Create User Comment (Child of Root)
      await axios.post(`/api/dashboard/sessions/${id}/comments`, {
        content: postContent,
        is_anonymous: isAnonymous,
        parent_id: rootId
      }, { withCredentials: true });

      // Reset & Reload
      setPostContent('');
      setIsCreatingPost(false);
      setIsAnonymous(false);

      // Reload comments (fetch detail again)
      const res = await axios.get(`/api/dashboard/sessions/${id}`, { withCredentials: true });
      setData(res.data);

    } catch (error) {
      console.error("Failed to create post", error);
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



  const handleIssueClick = (issue: any, index: number) => {
    // 1. Toggle Expansion
    const isClearing = expandedIssueIndex === index;
    if (isClearing) {
      setExpandedIssueIndex(null);
      setSelectedIssueTopics([]); // Also clear map selection
      setHighlightedText(null);
      return;
    } else {
      setExpandedIssueIndex(index);
      setHighlightedText(null);
    }

    // 2. Map Selection Logic
    // Extract related topics from issue
    // Keep compatibility with both 'category' (string) and 'related_topics' (array)
    let topics: string[] = [];
    if (issue.related_topics && Array.isArray(issue.related_topics)) {
      topics = issue.related_topics;
    } else if (issue.category) {
      topics = [issue.category];
    }

    setSelectedIssueTopics(topics);
  };


  const chatInputRef = useRef<HTMLDivElement>(null);
  const [threadAnalysisResults, setThreadAnalysisResults] = useState<Record<string, any>>({});

  useEffect(() => {
    if (data?.comment_analysis) {
      try {
        const parsed = JSON.parse(data.comment_analysis);
        if (parsed.threads) {
          setThreadAnalysisResults(parsed.threads);
        }
      } catch (e) {
        console.error("Failed to parse comment analysis", e);
      }
    }
  }, [data]);

  // Logic to find linked thread
  useEffect(() => {
    if (!activeIssue || !data?.comments) {
      setActiveThreadRootId(null);
      return;
    }

    // Match by hidden tag OR legacy visible tag
    const hiddenTag = `<!-- issue:${activeIssue.title} -->`;
    const legacyPattern = `【議題: ${activeIssue.title}`;

    const found = data.comments.find(c =>
      !c.parent_id && (c.content.includes(hiddenTag) || c.content.includes(legacyPattern))
    );

    if (found) {
      setActiveThreadRootId(found.id);
      setIsCreatingPost(false);
    } else {
      setActiveThreadRootId(null);
      setPostContent(''); // Clear content, don't pre-fill visible text
      setIsCreatingPost(true);
    }
  }, [activeIssue, data?.comments]);

  const handleDiscuss = (issue: any) => {
    setActiveIssue((prev: any) => (prev?.title === issue.title ? null : issue));
    // We rely on useEffect to handle thread switching/creation logic
  };

  const handleCloseRightPanel = () => {
    setActiveIssue(null);
    setIsCreatingPost(false);
  };

  const handleAnalyzeThread = async (rootCommentId: number) => {
    setIsAnalyzing(true);
    try {
      const res = await axios.post(`/api/dashboard/sessions/${id}/analyze-thread`, {
        parent_comment_id: rootCommentId
      }, { withCredentials: true });

      // Update local state
      const newResult = res.data.result;
      setThreadAnalysisResults(prev => ({
        ...prev,
        [rootCommentId]: newResult
      }));

      alert("分析が完了しました");
    } catch (e) {
      console.error(e);
      alert("分析に失敗しました");
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Filter comments for the active thread
  // Filter comments for the active thread
  // Return separate root and descendants to render "Flat" thread style
  const { root: activeThreadRoot, descendants: activeThreadDescendants } = useMemo(() => {
    if (!data?.comments || !activeThreadRootId) return { root: null, descendants: [] };

    const root = data.comments.find(c => c.id === activeThreadRootId);
    if (!root) return { root: null, descendants: [] };

    const descendants: any[] = [];
    const stack = [root.id];
    while (stack.length > 0) {
      const currentId = stack.pop();
      const children = data.comments.filter(c => c.parent_id === currentId);
      descendants.push(...children);
      stack.push(...children.map(c => c.id));
    }

    return { root, descendants };
  }, [data?.comments, activeThreadRootId]);

  // Current analysis result
  const currentAnalysis = activeThreadRootId && threadAnalysisResults[activeThreadRootId.toString()];

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
    <div className="h-full flex flex-col bg-slate-50">
      {/* Header */}
      <header className="h-16 flex items-center justify-between px-6 border-b border-white/40 shrink-0 bg-white/50 backdrop-blur-sm sticky top-0 z-20">
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

      {/* Main Content - Dynamic Layout */}
      <div className="flex-1 overflow-hidden relative flex">

        {/* Left Column: Input (Map & Issues) */}
        <div className={`
          h-full overflow-y-auto p-6 space-y-6 custom-scrollbar transition-all ${activeIssue ? 'duration-100' : 'duration-0'} ease-[cubic-bezier(0.23,1,0.32,1)]
          ${activeIssue ? 'w-[60%] border-r border-slate-200/60' : 'w-full'}
        `}>

          {/* 1. Meaning Map */}
          <section ref={mapSectionRef} className="glass-card p-4 h-[500px] relative">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-bold text-sage-dark pl-2 border-l-4 border-sage-primary">1. クラスタリング</h3>
              {selectedIssueTopics.length > 0 && (
                <button
                  onClick={() => setSelectedIssueTopics([])}
                  className="text-xs bg-slate-200 text-slate-600 px-2 py-1 rounded hover:bg-slate-300 transition-colors"
                >
                  絞り込みを解除
                </button>
              )}
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
                        size: data.results.map(r => {
                          const isTopicSelected = selectedIssueTopics.some(t => r.sub_topic.includes(t)) ||
                            (r.cluster_id === -1 && selectedIssueTopics.some(t => t.includes('Small Voice')));

                          if (highlightedText && r.original_text.includes(highlightedText)) {
                            return 18;
                          }
                          return isTopicSelected ? 14 : 10;
                        }),
                        color: data.results.map(r => {
                          if (r.is_noise || r.cluster_id === -1) {
                            if (selectedIssueTopics.length > 0 && !selectedIssueTopics.some(t => r.sub_topic.includes(t)) && !selectedIssueTopics.some(t => t.includes('Small Voice'))) {
                              return 'rgba(239, 68, 68, 0.2)';
                            }
                            return '#EF4444';
                          }

                          const color = categoryColorMap.get(r.sub_topic) || '#ccc';

                          if (selectedIssueTopics.length > 0) {
                            if (!selectedIssueTopics.includes(r.sub_topic)) {
                              return 'rgba(200,200,200, 0.2)';
                            }
                          }
                          return color;
                        }),
                        line: {
                          width: data.results.map(r => {
                            const isTopicSelected = selectedIssueTopics.some(t => r.sub_topic.includes(t)) ||
                              (r.cluster_id === -1 && selectedIssueTopics.some(t => t.includes('Small Voice')));

                            if (highlightedText && r.original_text.includes(highlightedText)) {
                              return 3;
                            }
                            return isTopicSelected ? 2 : 1;
                          }),
                          color: data.results.map(r => {
                            if (highlightedText && r.original_text.includes(highlightedText)) {
                              return '#1e293b';
                            }
                            return 'white';
                          })
                        },
                        opacity: 0.8,
                        symbol: 'circle'
                      },
                      hoverinfo: 'text',
                      hovertemplate: '%{text}<extra></extra>'
                    }
                  ]}
                  layout={plotLayout}
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
            <div className="absolute bottom-2 left-4 right-4 flex overflow-x-auto gap-2 py-1 scrollbar-hide">
              {Array.from(categoryColorMap.entries()).slice(0, 5).map(([category, color]) => (
                <div key={category} className="flex items-center gap-1 bg-white/80 px-1.5 py-0.5 rounded text-[10px] whitespace-nowrap border border-slate-100 shadow-sm">
                  <span className="w-2 h-2 rounded-full" style={{ backgroundColor: color }}></span>
                  <span className="text-slate-600 font-medium truncate max-w-[80px]">{category}</span>
                </div>
              ))}
            </div>
          </section>

          {/* 2. Issue List */}
          <section className="glass-card p-6">
            <div className="mb-4 border-b border-gray-100 pb-2 flex justify-between items-center">
              <h3 className="text-sm font-bold text-sage-dark pl-2 border-l-4 border-sage-primary flex items-center gap-2">
                <FileText className="h-4 w-4" /> 2. 課題リスト
              </h3>
              <span className="text-xs text-slate-400">クリックして詳細と関連マップを表示</span>
            </div>

            <div className="space-y-4">
              {(() => {
                if (!data.report_content) {
                  return <p className="text-slate-400 text-center py-10">レポートはまだ作成されていません。</p>;
                }

                let issues = [];
                try {
                  const parsed = JSON.parse(data.report_content);
                  if (Array.isArray(parsed)) issues = parsed;
                } catch (e) {
                  if (data.report_content.trim() === '[]') issues = [];
                }

                if (issues.length > 0) {
                  return issues.map((issue: any, idx: number) => {
                    let topics: string[] = [];
                    if (issue.related_topics && Array.isArray(issue.related_topics)) topics = issue.related_topics;
                    else if (issue.category) topics = [issue.category];

                    const isActive = activeIssue?.title === issue.title;
                    const isExpanded = idx === expandedIssueIndex || isActive;
                    const isSmallVoice = issue.source_type === 'small_voice' || topics.some(t => t.includes('Small Voice'));

                    return (
                      <div
                        key={idx}
                        onClick={() => handleIssueClick(issue, idx)}
                        className={`bg-white rounded-xl border transition-all cursor-pointer overflow-hidden
                            ${isActive ? 'ring-2 ring-sage-primary shadow-lg border-sage-300' : isExpanded ? 'ring-1 ring-sage-200 shadow-md' : 'border-slate-200 shadow-sm hover:shadow-md hover:border-sage-300'}
                        `}
                      >
                        <div className="p-4 flex items-center justify-between group">
                          <h4 className={`font-bold text-sm flex items-start gap-2 ${isExpanded || isActive ? 'text-sage-700' : 'text-slate-700'}`}>
                            {isSmallVoice ? (
                              <Sparkles className="h-5 w-5 text-amber-500 mt-0.5 shrink-0" />
                            ) : (
                              <Users className="h-5 w-5 text-sage-500 mt-0.5 shrink-0" />
                            )}
                            <span>{issue.title}</span>
                          </h4>
                          <div className={`transition-transform duration-300 ${isExpanded ? 'rotate-180' : ''}`}>
                            <ChevronDown className="h-4 w-4 text-slate-400" />
                          </div>
                        </div>

                        {/* Expandable Content */}
                        <div className={`transition-all duration-300 ease-in-out border-t border-slate-100 bg-slate-50/50
                            ${isExpanded ? 'max-h-[800px] opacity-100 p-4' : 'max-h-0 opacity-0 p-0 overflow-hidden'}
                        `}>
                          {isSmallVoice ? (
                            <div className="space-y-2">
                              {(() => {
                                const content = issue.insight || issue.description || '';
                                const lines = content.split('\n');
                                return lines.map((line: string, lIdx: number) => {
                                  // Detect bullet points (e.g., "- ", "• ", "1. ")
                                  const bulletMatch = line.match(/^(\s*[-•*]|\s*\d+\.)\s*(.*)/);
                                  if (bulletMatch) {
                                    const text = bulletMatch[2];
                                    return (
                                      <div key={lIdx} className="pl-2 flex items-start gap-2 group/item">
                                        <button
                                          onClick={(e) => {
                                            e.stopPropagation();
                                            setHighlightedText(text);
                                            mapSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
                                          }}
                                          className={`text-xs text-left leading-normal py-0.5 hover:text-amber-600 hover:underline transition-colors ${highlightedText === text ? 'text-amber-700 font-bold underline' : 'text-slate-600'}`}
                                        >
                                          {text}
                                        </button>
                                      </div>
                                    );
                                  }
                                  return (
                                    <p key={lIdx} className="text-xs text-slate-600 leading-relaxed whitespace-pre-wrap">
                                      {line}
                                    </p>
                                  );
                                });
                              })()}
                            </div>
                          ) : (
                            <p className="text-xs text-slate-600 leading-relaxed whitespace-pre-wrap">
                              {issue.insight || issue.description}
                            </p>
                          )}

                          <div className="mt-4 pt-3 border-t border-slate-200/60 flex flex-wrap justify-between items-center gap-3">
                            <div className="flex gap-2 flex-wrap flex-1 min-w-0">
                              {topics.map((t, i) => (
                                <span key={i} className="bg-sage-100 text-sage-700 text-[10px] px-2 py-0.5 rounded flex items-center gap-1">
                                  <span className="w-1.5 h-1.5 rounded-full bg-sage-500"></span>
                                  {t}
                                </span>
                              ))}
                            </div>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDiscuss(issue);
                              }}
                              className={`btn-primary px-3 py-1.5 text-xs flex items-center gap-1.5 shadow-sm hover:shadow-md transition-all shrink-0 ml-auto ${isActive ? 'bg-sage-600 ring-2 ring-offset-1 ring-sage-400' : ''}`}
                            >
                              <MessageCircle className="w-3 h-3" />
                              {isActive ? '議論中' : '議論する'}
                            </button>
                          </div>
                        </div>
                      </div>
                    );
                  });
                } else {
                  return <div className="text-center py-10 text-slate-500"><p>顕著な課題は検出されませんでした。</p></div>
                }
              })()}
            </div>
          </section>
        </div>

        {/* Right Column: Dynamic Panel (Chat & Thread Analysis) */}
        <div className={`
          h-full bg-white border-l border-slate-200 
          transition-all ${activeIssue ? 'duration-100' : 'duration-0'} ease-[cubic-bezier(0.23,1,0.32,1)] origin-right flex flex-col
          ${activeIssue ? 'w-[40%] opacity-100 shadow-xl' : 'w-0 opacity-0 overflow-hidden'}
        `}>
          {/* Important: Use min-w to prevent content squashing during transition */}
          <div className="flex-1 flex flex-col min-w-[400px] h-full overflow-hidden">

            {/* Panel Header (Fixed at top) */}
            <div className="shrink-0 bg-white/95 z-20 px-6 py-4 border-b border-slate-100 shadow-sm flex items-center justify-between">
              <div className="min-w-0 flex-1">
                <span className="text-[10px] bg-sage-100 text-sage-600 px-2 py-0.5 rounded font-bold mb-1 inline-block">議論中の課題</span>
                <h3 className="text-sm font-bold text-sage-800 line-clamp-1" title={activeIssue?.title}>{activeIssue?.title}</h3>
              </div>
              <button
                onClick={handleCloseRightPanel}
                className="group flex items-center gap-1.5 px-3 py-1.5 bg-slate-50 hover:bg-slate-100 text-slate-500 hover:text-slate-700 rounded-full transition-all border border-slate-200/60 shadow-sm shrink-0 ml-4"
                title="スレッドを閉じる"
              >
                <div className="flex items-center justify-center bg-white rounded-full w-5 h-5 shadow-sm border border-slate-100 group-hover:scale-110 transition-transform">
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="translate-x-[1px]">
                    <polyline points="9 18 15 12 9 6" />
                  </svg>
                </div>
                <span className="text-xs font-bold mr-1">閉じる</span>
              </button>
            </div>

            {/* Scrollable Content Area */}
            <div className="flex-1 overflow-y-auto scrollbar-thin">
              {/* Thread Analysis Area (Top) */}
              <div className="px-6 py-4 bg-amber-50/50 border-b border-amber-100">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-xs font-bold text-amber-800 flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5" />
                    AIファシリテーターの整理と提案
                  </h4>
                  {activeThreadRootId && (user?.role === 'system_admin' || user?.org_role === 'admin') && (
                    <button
                      onClick={() => handleAnalyzeThread(activeThreadRootId!)}
                      disabled={isAnalyzing}
                      className="text-[10px] bg-white border border-amber-200 text-amber-700 px-2 py-1 rounded shadow-sm hover:bg-amber-50 transition-all flex items-center gap-1 disabled:opacity-50"
                    >
                      {isAnalyzing ? <div className="animate-spin h-3 w-3 border-b-2 border-amber-600 rounded-full"></div> : <span className="text-xs">↻</span>}
                      更新
                    </button>
                  )}
                </div>

                {currentAnalysis ? (
                  <div className="space-y-4">
                    {/* Next Actions (Directly displayed) */}
                    {currentAnalysis.next_steps?.length > 0 && (
                      <div className="bg-white rounded-lg border border-amber-100 shadow-sm overflow-hidden">
                        <div className="divide-y divide-amber-50/50">
                          {Array.isArray(currentAnalysis.next_steps) ? (
                            currentAnalysis.next_steps.map((step: any, i: number) => {
                              const isObject = typeof step === 'object' && step !== null && 'title' in step;
                              const title = isObject ? step.title : step;
                              const detail = isObject ? step.detail : null;

                              return (
                                <details key={i} className="group open:bg-amber-50/30 transition-colors">
                                  <summary className="px-4 py-3 cursor-pointer flex items-start gap-2 list-none outline-none">
                                    <CheckCircle className="w-4 h-4 text-sage-500 shrink-0 mt-0.5" />
                                    <span className="text-xs text-slate-700 font-bold leading-relaxed flex-1">{title}</span>
                                    {detail && (
                                      <ChevronDown className="w-4 h-4 text-amber-400 group-open:rotate-180 transition-transform shrink-0" />
                                    )}
                                  </summary>
                                  {detail && (
                                    <div className="px-4 pb-3 pl-10 text-xs text-slate-600 leading-relaxed">
                                      {detail}
                                    </div>
                                  )}
                                </details>
                              );
                            })
                          ) : (
                            // Fallback for legacy string next_steps
                            <p className="p-4 text-xs text-slate-700 leading-relaxed whitespace-pre-wrap">{currentAnalysis.next_steps}</p>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-3 bg-white/50 rounded-lg border border-dashed border-amber-200">
                    <p className="text-xs text-slate-400 mb-2">まだ分析結果がありません</p>

                    {/* Admin View */}
                    {(user?.role === 'system_admin' || user?.org_role === 'admin') ? (
                      <>
                        {activeThreadRootId ? (
                          <button
                            onClick={() => handleAnalyzeThread(activeThreadRootId!)}
                            disabled={isAnalyzing}
                            className="text-[10px] text-amber-600 hover:text-amber-800 underline disabled:opacity-50"
                          >
                            分析を実行する
                          </button>
                        ) : (
                          <p className="text-[10px] text-slate-400">スレッドが作成されると分析を実行できます</p>
                        )}
                      </>
                    ) : (
                      /* Member View */
                      <p className="text-[10px] text-slate-400">
                        {!activeThreadRootId
                          ? "スレッドが作成され、分析が実行されるとここに表示されます"
                          : "分析がされるまでお待ちください"}
                      </p>
                    )}
                  </div>
                )}
              </div>

              {/* Main Comment Area */}
              <div className="p-6">


                {activeThreadRootId && activeThreadRoot ? (
                  <>
                    {/* Root Comment Display (Thread Starter) - ONLY if NOT System Root */}
                    {/* System Root is hidden, and its children (user comments) are rendered by CommentTree */}
                    {!activeThreadRoot.content.includes('<!-- system_root -->') && (
                      <div className="mb-6 pb-6 border-b border-slate-200">
                        <div className="flex items-center gap-2 mb-3">
                          <span className="bg-sage-100 text-sage-700 p-2 rounded-full">
                            <UserIcon className="h-5 w-5" />
                          </span>
                          <div>
                            <div className="font-bold text-slate-800 text-sm">{activeThreadRoot.user_name || '名無し'}</div>
                            <div className="text-xs text-slate-400">
                              {new Date(activeThreadRoot.created_at).toLocaleString('ja-JP')}
                            </div>
                          </div>
                        </div>
                        <div className="text-sm text-slate-700 markdown-body bg-white p-4 rounded-xl border border-sage-200 shadow-sm">
                          <ReactMarkdown remarkPlugins={[remarkGfm, remarkBreaks]}>
                            {activeThreadRoot.content.replace(/<!-- issue:.*? -->/g, '')}
                          </ReactMarkdown>
                        </div>
                      </div>
                    )}

                    <h4 className="font-bold text-slate-400 text-xs mb-4 flex items-center gap-2">
                      <span>コメント ({activeThreadDescendants.length})</span>
                      <div className="h-[1px] flex-1 bg-slate-200"></div>
                    </h4>

                    <CommentTree
                      comments={activeThreadDescendants}
                      sessionId={data.id}
                      currentUserId={user?.id}
                      onRefresh={() => {
                        axios.get(`/api/dashboard/sessions/${id}`, { withCredentials: true })
                          .then(res => setData(res.data));
                      }}
                      analysisResults={{}}
                      isAdmin={user?.role === 'system_admin' || user?.org_role === 'admin'}
                      onQuote={(text) => {
                        setPostContent((prev: string) => prev ? `${prev}\n${text}\n` : `${text}\n`);
                      }}
                    />
                  </>
                ) : (
                  <div className="text-center text-slate-400 py-10">
                    <div className="mb-2 text-4xl">💬</div>
                    <p>まだコメントはありません</p>
                    <p className="text-xs mt-1">最初のコメントを投稿して議論を始めましょう</p>
                  </div>
                )}
              </div>
            </div>

            {/* Persistent Input Footer (Always Visible) */}
            <div className="shrink-0 bg-white border-t border-slate-200 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)] z-10 p-4">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-bold text-sage-800 text-xs flex items-center gap-1.5">
                  <MessageCircle className="w-3.5 h-3.5" />
                  コメントを投稿
                </h4>
              </div>
              <RichTextEditor
                content={postContent}
                onChange={(content) => setPostContent(content)}
                placeholder="コメントを入力... (Shift+Enterで改行)"
                className="mb-3 min-h-[80px]"
                minHeight="80px"
              />
              <div className="flex items-center justify-between">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={isAnonymous}
                    onChange={(e) => setIsAnonymous(e.target.checked)}
                    className="w-4 h-4 text-sage-600 rounded"
                  />
                  <span className="text-xs text-gray-600">匿名で投稿</span>
                </label>
                <button
                  onClick={async () => {
                    if (!postContent.trim()) return;

                    try {
                      if (activeThreadRootId) {
                        await axios.post(`/api/dashboard/sessions/${data.id}/comments`, {
                          content: postContent,
                          is_anonymous: isAnonymous,
                          parent_id: activeThreadRootId
                        }, { withCredentials: true });
                      } else {
                        // Create New Thread (System Root + Comment)
                        await handleCreatePost();
                        return;
                      }

                      setPostContent('');
                      setIsAnonymous(false);

                      // Refresh
                      const res = await axios.get(`/api/dashboard/sessions/${id}`, { withCredentials: true });
                      setData(res.data);

                    } catch (e) {
                      console.error("Failed to post comment", e);
                      alert("投稿に失敗しました");
                    }
                  }}
                  disabled={!postContent.trim()}
                  className="btn-primary px-4 py-1.5 text-xs shadow-md"
                >
                  送信
                </button>
              </div>
            </div>

          </div>
        </div>
      </div>
    </div>
  );
}


