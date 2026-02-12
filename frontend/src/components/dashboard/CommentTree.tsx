
import React, { useState } from 'react';
import { CommentItem } from '@/types/dashboard';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkBreaks from 'remark-breaks';
import { MessageCircle, Heart, Reply, Edit2, ChevronDown, ChevronUp, User, Sparkles, Bot } from 'lucide-react';
import RichTextEditor from '@/components/ui/RichTextEditor';

import axios from 'axios';

interface CommentTreeProps {
  comments: CommentItem[];
  currentUserId?: number;
  sessionId: number;
  onRefresh?: () => void;
  analysisResults?: Record<string, any>; // parent_id -> result
  onAnalyzeThread?: (rootCommentId: number) => Promise<void>;
  isAnalyzing?: boolean;
  isAdmin?: boolean;
  onQuote?: (text: string) => void;
  rootCid?: number;
}

export default function CommentTree({
  comments,
  currentUserId,
  sessionId,
  onRefresh,
  analysisResults = {},
  onAnalyzeThread,
  isAnalyzing = false,
  isAdmin = false,
  onQuote,
  rootCid = -1
}: CommentTreeProps) {
  // Build tree logic
  const buildTree = (items: CommentItem[]): CommentItem[] => {
    const map = new Map<number, CommentItem>();
    const roots: CommentItem[] = [];

    // Deep copy to avoid mutating props directly if they are reused
    const params = items.map(i => ({ ...i, children: [] }));

    params.forEach(item => {
      map.set(item.id, item);
    });

    params.forEach(item => {
      if (item.parent_id && map.has(item.parent_id)) {
        map.get(item.parent_id)!.children!.push(item);
      } else {
        // If rootCid is specified, only take that as root
        if (rootCid !== -1) {
          if (item.id === rootCid) roots.push(item);
        } else {
          roots.push(item);
        }
      }
    });

    // Sort: Roots desc by date, Children asc by date
    roots.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());

    const sortChildren = (nodes: CommentItem[]) => {
      nodes.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
      nodes.forEach(n => {
        if (n.children && n.children.length > 0) sortChildren(n.children);
      });
    };
    sortChildren(roots);

    return roots;
  };

  const tree = buildTree(comments);

  return (
    <div className="space-y-4">
      {tree.map(node => (
        <CommentNode
          key={node.id}
          node={node}
          currentUserId={currentUserId}
          depth={0}
          sessionId={sessionId}
          onRefresh={onRefresh}
          analysisResult={analysisResults[node.id.toString()]}
          onAnalyzeThread={onAnalyzeThread}
          isAnalyzingGlobal={isAnalyzing}
          isAdmin={isAdmin}
          onQuote={onQuote}
        />
      ))}
      {tree.length === 0 && <p className="text-slate-400 text-sm">まだコメントはありません。</p>}
    </div>
  );
}

function CommentNode({
  node,
  currentUserId,
  depth,
  sessionId,
  onRefresh,
  defaultExpanded = false,
  analysisResult,
  onAnalyzeThread,
  isAnalyzingGlobal,
  isAdmin,
  onQuote
}: {
  node: CommentItem,
  currentUserId?: number,
  depth: number,
  sessionId: number,
  onRefresh?: () => void,
  defaultExpanded?: boolean,
  analysisResult?: any,
  onAnalyzeThread?: (id: number) => Promise<void>,
  isAnalyzingGlobal?: boolean,
  isAdmin?: boolean,
  onQuote?: (text: string) => void
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState('');
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);
  const [isReplying, setIsReplying] = useState(false);
  const [replyContent, setReplyContent] = useState('');
  const [isAnonymous, setIsAnonymous] = useState(false);

  // Analysis UI State
  const [showAnalysis, setShowAnalysis] = useState(!!analysisResult);

  // Auto-expand if it's a system root to show children immediately
  const isSystemRoot = node.content.includes('<!-- system_root -->');
  if (isSystemRoot && !isExpanded) {
    setIsExpanded(true);
  }

  // Helper to count all descendants
  const countDescendants = (item: CommentItem): number => {
    let count = 0;
    if (item.children) {
      count += item.children.length;
      item.children.forEach(child => {
        count += countDescendants(child);
      });
    }
    return count;
  };

  const totalDescendants = countDescendants(node);

  // Handlers (Real Logic)
  const handleLike = async () => {
    try {
      await axios.post(`/api/dashboard/comments/${node.id}/like`, {}, { withCredentials: true });
      if (onRefresh) onRefresh();
    } catch (e) {
      console.error("Failed to like", e);
    }
  };

  const handleEditSubmit = async () => {
    if (!editContent.trim()) return;
    try {
      await axios.put(`/api/dashboard/comments/${node.id}`, {
        content: editContent,
      }, { withCredentials: true });

      setIsEditing(false);
      setEditContent('');
      if (onRefresh) onRefresh();
    } catch (e) {
      console.error("Failed to update comment", e);
      alert("更新に失敗しました");
    }
  };

  const startEditing = () => {
    setEditContent(node.content);
    setIsEditing(true);
    setIsReplying(false); // Close reply if open
  };

  const handleReplySubmit = async () => {
    if (!replyContent.trim()) return;
    try {
      await axios.post(`/api/dashboard/sessions/${sessionId}/comments`, {
        content: replyContent,
        is_anonymous: isAnonymous,
        parent_id: node.id
      }, { withCredentials: true });

      setReplyContent('');
      setIsReplying(false);
      setIsAnonymous(false);
      setIsExpanded(true); // Open to see new reply
      if (onRefresh) onRefresh();

    } catch (e) {
      console.error("Failed to reply", e);
      alert("返信に失敗しました");
    }
  };

  const handleRunAnalysis = async () => {
    if (onAnalyzeThread) {
      setShowAnalysis(true); // Ensure expanded
      await onAnalyzeThread(node.id);
    }
  };

  const indent = Math.min(depth * 20, 100); // Cap indent
  const isOwner = currentUserId === node.user_id;

  return (
    <div className={`mb-3 animate-in fade-in duration-300 ${isSystemRoot ? 'm-0' : ''}`} style={{ marginLeft: isSystemRoot ? '0px' : `${indent}px` }}>
      {!isSystemRoot && (
        <div className={`
          relative p-4 rounded-xl border-l-4 
          ${depth === 0 ? 'bg-white/60 border-sage-primary shadow-sm' : 'bg-white/40 border-slate-300'}
        `}>
          {/* Header */}
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <span className="bg-sage-100 text-sage-700 p-1.5 rounded-full">
                <User className="h-4 w-4" />
              </span>
              <span className="font-bold text-sm text-slate-700 animate-in fade-in">{node.user_name}</span>
              <span className="text-xs text-slate-400">
                {new Date(node.created_at).toLocaleString('ja-JP', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>
            <div className="flex items-center gap-1">
              {isOwner && !isEditing && (
                <button
                  onClick={startEditing}
                  className="text-slate-400 hover:text-sage-primary p-1 rounded hover:bg-sage-50 transition-colors mr-1"
                  title="編集"
                >
                  <Edit2 className="h-4 w-4" />
                </button>
              )}
              <button onClick={handleLike} className="flex items-center gap-1 text-slate-400 hover:text-red-500 transition-colors bg-transparent px-2 py-1 rounded hover:bg-red-50 text-xs">
                <Heart className="h-4 w-4" />
                <span>{node.likes_count}</span>
              </button>
              <button
                onClick={() => setIsReplying(!isReplying)}
                className="text-slate-400 hover:text-sage-primary p-1 rounded hover:bg-sage-50 transition-colors"
                title="返信"
              >
                <Reply className="h-4 w-4" />
              </button>
              {onQuote && (
                <button
                  onClick={() => {
                    const quoteText = `> @${node.user_name || '名無し'}: ${node.content.split('\n')[0]}`;
                    onQuote(quoteText);
                  }}
                  className="text-slate-400 hover:text-sage-primary p-1 rounded hover:bg-sage-50 transition-colors"
                  title="引用"
                >
                  <MessageCircle className="h-4 w-4" />
                </button>
              )}
              {/* Thread Analysis Button (Root Only & Admin Only/or visible to all?) -> Visible to all but restricted execution maybe? Assuming Visible for now */}
              {depth === 0 && onAnalyzeThread && (
                <button
                  onClick={() => setShowAnalysis(!showAnalysis)}
                  className={`ml-1 p-1 rounded transition-colors ${analysisResult ? 'text-amber-500 bg-amber-50 hover:bg-amber-100' : 'text-slate-400 hover:text-sage-primary hover:bg-sage-50'}`}
                  title="議論の分析（AI）"
                >
                  <Bot className="h-4 w-4" />
                </button>
              )}
            </div>
          </div>

          {/* Content */}
          {isEditing ? (
            <div className="animate-in fade-in">
              <RichTextEditor
                content={editContent}
                onChange={setEditContent}
                placeholder="コメントを編集..."
                className="mb-2 min-h-[100px]"
                minHeight="100px"
              />
              <div className="flex justify-end gap-2">
                <button onClick={() => setIsEditing(false)} className="text-xs text-slate-500 hover:text-slate-700 px-3 py-1.5">キャンセル</button>
                <button onClick={handleEditSubmit} className="btn-primary px-3 py-1.5 text-xs">保存</button>
              </div>
            </div>
          ) : (
            <div className="text-sm text-slate-700 markdown-body">
              <ReactMarkdown remarkPlugins={[remarkGfm, remarkBreaks]}>
                {node.content.replace(/<!-- issue:.*? -->/g, '')}
              </ReactMarkdown>
            </div>
          )}

          {/* Thread Analysis Result (Root Only) */}
          {depth === 0 && showAnalysis && (
            <div className="mt-4 pt-3 border-t border-slate-200/50 animate-in fade-in">
              {!analysisResult ? (
                <div className="text-center py-4 bg-slate-50/50 rounded-lg">
                  <p className="text-xs text-slate-500 mb-2">このスレッドの議論をAIが要約・分析します。</p>
                  <button
                    onClick={handleRunAnalysis}
                    disabled={isAnalyzingGlobal}
                    className="btn-primary px-3 py-1.5 text-xs flex items-center justify-center gap-2 mx-auto disabled:opacity-50"
                  >
                    {isAnalyzingGlobal ? <div className="animate-spin h-3 w-3 border-b-2 border-white rounded-full"></div> : <Sparkles className="h-3 w-3" />}
                    分析を実行
                  </button>
                </div>
              ) : (
                <div className="bg-gradient-to-br from-amber-50 to-white rounded-lg p-3 border border-amber-100 shadow-sm text-xs">
                  {/* Summary */}
                  <div className="mb-3">
                    <h5 className="font-bold text-amber-800 mb-1 flex items-center gap-1.5">
                      <span className="bg-amber-100 p-0.5 rounded text-amber-600">📝</span>
                      議論の要約
                    </h5>
                    <p className="text-slate-700 leading-relaxed pl-6">{analysisResult.summary}</p>
                  </div>

                  {/* Points */}
                  {analysisResult.points && analysisResult.points.length > 0 && (
                    <div className="mb-3">
                      <h5 className="font-bold text-amber-800 mb-1 flex items-center gap-1.5">
                        <span className="bg-amber-100 p-0.5 rounded text-amber-600">📌</span>
                        主な論点
                      </h5>
                      <ul className="list-disc list-inside text-slate-700 pl-6 space-y-0.5">
                        {analysisResult.points.map((p: string, i: number) => (
                          <li key={i}>{p}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Conclusion */}
                  {analysisResult.conclusion && (
                    <div>
                      <h5 className="font-bold text-amber-800 mb-1 flex items-center gap-1.5">
                        <span className="bg-amber-100 p-0.5 rounded text-amber-600">🏁</span>
                        結論・ネクストアクション
                      </h5>
                      <p className="text-slate-700 leading-relaxed pl-6">{analysisResult.conclusion}</p>
                    </div>
                  )}

                  {/* Re-analyze button */}
                  {isAdmin && (
                    <div className="mt-3 text-right">
                      <button
                        onClick={handleRunAnalysis}
                        disabled={isAnalyzingGlobal}
                        className="text-[10px] text-slate-400 hover:text-amber-600 underline"
                      >
                        再分析を実行
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Reply Form */}
          {isReplying && !isEditing && (
            // ... (Same Reply Form as before)
            <div className="mt-3 pt-3 border-t border-slate-200/50 animate-in slide-in-from-top-1">
              <RichTextEditor
                content={replyContent}
                onChange={(content) => setReplyContent(content)}
                placeholder="返信内容を入力..."
                className="mb-2 min-h-[100px]"
                minHeight="100px"
              // autoFocus is not directly supported by this wrapper yet, but that's fine for now
              />
              <div className="flex justify-between items-center">
                <label className="flex items-center gap-1 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={isAnonymous}
                    onChange={(e) => setIsAnonymous(e.target.checked)}
                    className="w-3 h-3 text-sage-600 rounded"
                  />
                  <span className="text-xs text-gray-500">匿名</span>
                </label>
                <div className="flex justify-end gap-2">
                  <button onClick={() => setIsReplying(false)} className="text-xs text-slate-500 hover:text-slate-700 px-3 py-1.5">キャンセル</button>
                  <button onClick={handleReplySubmit} disabled={!replyContent} className="btn-primary px-3 py-1.5 text-xs">返信</button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Children (Replies) - Existing code ... */}
      {node.children && node.children.length > 0 && (
        <div className="mt-2">
          {!isExpanded && (
            <button
              onClick={() => setIsExpanded(true)}
              className="flex items-center gap-2 text-xs font-bold text-sage-primary hover:text-sage-dark ml-2 mb-2 transition-colors"
            >
              <div className="w-6 h-[1px] bg-sage-primary/50"></div>
              <span>返信 {totalDescendants}件を表示</span>
              <ChevronDown className="h-3 w-3" />
            </button>
          )}

          {isExpanded && (
            <div className="relative">
              {!isSystemRoot && (
                <button
                  onClick={() => setIsExpanded(false)}
                  className="absolute -top-8 right-0 text-xs text-slate-400 hover:text-slate-600 flex items-center gap-1"
                >
                  <ChevronUp className="h-3 w-3" />
                  閉じる
                </button>
              )}
              {node.children.map(child => (
                <CommentNode
                  key={child.id}
                  node={child}
                  currentUserId={currentUserId}
                  depth={isSystemRoot ? depth : depth + 1}
                  sessionId={sessionId}
                  onRefresh={onRefresh}
                  defaultExpanded={true}
                  onQuote={onQuote}
                // Do not pass analysis props to children, only root matters for this design
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
