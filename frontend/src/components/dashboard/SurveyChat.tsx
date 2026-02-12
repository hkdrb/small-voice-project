'use client';

import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Send } from 'lucide-react';

interface Comment {
  id: number;
  content: string;
  user_id: number;
  username: string;
  created_at: string;
}

interface User {
  id: number;
  role: string;
  org_role?: string;
  email?: string;
}

interface SurveyChatProps {
  surveyId: number | null;
  currentUser: User | null;
  isDraft?: boolean;
  draftText?: string;
  onDraftChange?: (text: string) => void;
}

export default function SurveyChat({ surveyId, currentUser, isDraft = false, draftText = '', onDraftChange }: SurveyChatProps) {
  const [comments, setComments] = useState<Comment[]>([]);
  const [newMessage, setNewMessage] = useState(draftText);
  const [loading, setLoading] = useState(!isDraft); // Draft mode doesn't need loading
  const [submitting, setSubmitting] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const fetchComments = async () => {
    if (isDraft || !surveyId) return;
    try {
      const res = await axios.get(`/api/surveys/${surveyId}/comments`, { withCredentials: true });
      setComments(res.data);
      setLoading(false);
    } catch (e) {
      console.error("Failed to fetch comments", e);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchComments();
  }, [surveyId, isDraft]);

  // Sync internal state with prop if controlled
  useEffect(() => {
    if (isDraft && draftText !== undefined) {
      setNewMessage(draftText);
    }
  }, [draftText, isDraft]);

  useEffect(() => {
    if (!isDraft) {
      scrollToBottom();
    }
  }, [comments, isDraft]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const handleSend = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!newMessage.trim()) return;

    if (isDraft) return; // Draft mode handles input via onChange, no send action

    setSubmitting(true);
    try {
      const res = await axios.post(`/api/surveys/${surveyId}/comments`,
        { content: newMessage },
        { withCredentials: true }
      );
      setComments([...comments, res.data]);
      setNewMessage('');
    } catch (e) {
      alert("メッセージの送信に失敗しました");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <div className="text-center py-4 text-slate-400">読み込み中...</div>;

  return (
    <div className="flex flex-col h-[300px] md:h-[400px] border border-sage-200 rounded-xl bg-white/50 overflow-hidden">
      <div className="bg-sage-50 px-4 py-3 border-b border-sage-100 flex items-center justify-between">
        <h4 className="font-bold text-sage-700 flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-sage-500 animate-pulse"></span>
          申請に関するチャット
        </h4>
        <span className="text-xs text-sage-500">管理者と直接やり取りできます</span>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {comments.length === 0 && (
          <div className="text-center text-slate-400 py-8 text-sm">
            {isDraft ? (
              <span className="opacity-70">
                まだ申請は送信されていません。<br />
                補足事項やメッセージがあれば下に入力してください。<br />
                申請と同時に管理者へ送信されます。
              </span>
            ) : (
              <>
                メッセージはまだありません。<br />
                ここでのやり取りは管理者と申請者のみが閲覧できます。
              </>
            )}
          </div>
        )}

        {comments.map((comment) => {
          const isMe = currentUser?.id === comment.user_id;
          return (
            <div key={comment.id} className={`flex ${isMe ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm shadow-sm ${isMe
                ? 'bg-sage-600 text-white rounded-tr-none'
                : 'bg-white text-slate-700 border border-slate-100 rounded-tl-none'
                }`}>
                <div className={`text-xs mb-1 opacity-70 ${isMe ? 'text-sage-100' : 'text-slate-400'}`}>
                  {comment.username} • {new Date(comment.created_at).toLocaleString('ja-JP')}
                </div>
                <div className="whitespace-pre-wrap">{comment.content}</div>
              </div>
            </div>
          );
        })}
        <div ref={messagesEndRef} />
      </div>

      <div className="p-3 bg-white border-t border-sage-100">
        <form onSubmit={handleSend} className="flex gap-2">
          <input
            type="text"
            value={newMessage}
            onChange={(e) => {
              setNewMessage(e.target.value);
              if (isDraft && onDraftChange) onDraftChange(e.target.value);
            }}
            placeholder={isDraft ? "申請に合わせて送るメッセージを入力（任意）" : "メッセージを入力..."}
            className="flex-1 glass-input px-4 py-2 text-sm"
            disabled={submitting}
          />
          {!isDraft && (
            <button
              type="submit"
              disabled={submitting || !newMessage.trim()}
              className="btn-primary px-4 py-2 flex items-center justify-center rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send className="h-4 w-4" />
            </button>
          )}
        </form>
      </div>
    </div>
  );
}
