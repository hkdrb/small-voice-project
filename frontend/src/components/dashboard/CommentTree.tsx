'use client';

import React, { useState } from 'react';
import { CommentItem } from '@/types/dashboard';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkBreaks from 'remark-breaks';
import { MessageCircle, Heart, Reply, Edit2, ChevronDown, ChevronUp, User } from 'lucide-react';
import RichTextEditor from '@/components/ui/RichTextEditor';

import axios from 'axios';

interface CommentTreeProps {
  comments: CommentItem[];
  currentUserId?: number;
  sessionId: number;
  onRefresh?: () => void;
}

export default function CommentTree({ comments, currentUserId, sessionId, onRefresh }: CommentTreeProps) {
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
        roots.push(item);
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
        />
      ))}
      {tree.length === 0 && <p className="text-slate-400 text-sm">まだコメントはありません。</p>}
    </div>
  );
}

function CommentNode({ node, currentUserId, depth, sessionId, onRefresh, defaultExpanded = false }: {
  node: CommentItem,
  currentUserId?: number,
  depth: number,
  sessionId: number,
  onRefresh?: () => void,
  defaultExpanded?: boolean
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState('');
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);
  const [isReplying, setIsReplying] = useState(false);
  const [replyContent, setReplyContent] = useState('');
  const [isAnonymous, setIsAnonymous] = useState(false);

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

  const indent = Math.min(depth * 20, 100); // Cap indent
  const isOwner = currentUserId === node.user_id;

  return (
    <div className="mb-3 animate-in fade-in duration-300" style={{ marginLeft: `${indent}px` }}>
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
            <button onClick={() => setIsReplying(!isReplying)} className="text-slate-400 hover:text-sage-primary p-1 rounded hover:bg-sage-50 transition-colors">
              <Reply className="h-4 w-4" />
            </button>
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
            <ReactMarkdown remarkPlugins={[remarkGfm, remarkBreaks]}>{node.content}</ReactMarkdown>
          </div>
        )}

        {/* Reply Form */}
        {isReplying && !isEditing && (
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

      {/* Children (Replies) */}
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
              <button
                onClick={() => setIsExpanded(false)}
                className="absolute -top-8 right-0 text-xs text-slate-400 hover:text-slate-600 flex items-center gap-1"
              >
                <ChevronUp className="h-3 w-3" />
                閉じる
              </button>
              {node.children.map(child => (
                <CommentNode
                  key={child.id}
                  node={child}
                  currentUserId={currentUserId}
                  depth={depth + 1}
                  sessionId={sessionId}
                  onRefresh={onRefresh}
                  defaultExpanded={true}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
