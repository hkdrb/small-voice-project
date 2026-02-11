'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';
import { Plus, Trash2, Edit, Check, Eye, EyeOff, BarChart2, Save, X, FileDown } from 'lucide-react';
import { SurveySummary } from '@/types/dashboard';
import { Tooltip } from '@/components/ui/Tooltip';
import SurveyChat from './SurveyChat';

interface QuestionDraft {
  id?: number;
  text: string;
  is_required: boolean;
  order: number;
}

interface User {
  id: number;
  role: string;
  org_role?: string;
}

export default function SurveyManager({ user: propUser }: { user?: User }) {
  const [surveys, setSurveys] = useState<SurveySummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState<'list' | 'create' | 'edit'>('list');
  const [user, setUser] = useState<User | null>(propUser || null);

  // Form State
  const [editingSurveyId, setEditingSurveyId] = useState<number | null>(null);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [questions, setQuestions] = useState<QuestionDraft[]>([{ text: '', is_required: false, order: 1 }]);
  const [pendingComment, setPendingComment] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchSurveys();
    if (!user) fetchUser();
  }, [propUser]);

  const fetchUser = async () => {
    try {
      const res = await axios.get('/api/auth/me', { withCredentials: true });
      setUser(res.data);
    } catch (e) {
      console.error("Failed to fetch user", e);
    }
  };

  const fetchSurveys = async () => {
    try {
      const res = await axios.get('/api/dashboard/surveys', { withCredentials: true });
      setSurveys(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleEditStart = async (survey: SurveySummary) => {
    try {
      setLoading(true);
      // Fetch full survey detail (with questions)
      const res = await axios.get(`/api/surveys/${survey.id}`, { withCredentials: true });
      const fullSurvey = res.data;

      setEditingSurveyId(survey.id);
      setTitle(fullSurvey.title);
      setDescription(fullSurvey.description || '');
      setQuestions(fullSurvey.questions.length > 0 ? fullSurvey.questions : [{ text: '', is_required: false, order: 1 }]);
      setView('edit');
    } catch (e) {
      alert("フォームの取得に失敗しました");
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!title.trim()) return alert("タイトルを入力してください");
    if (questions.some(q => !q.text.trim())) return alert("すべての質問内容を入力してください");

    // 一般ユーザー（申請者）の場合は確認ダイアログを表示
    if (!isAdmin) {
      const actionText = view === 'edit' ? "再申請" : "申請";
      if (!confirm(`この内容で${actionText}しますか？`)) return;
    }

    setSubmitting(true);
    try {
      const payload = { title, description, questions };
      if (view === 'edit' && editingSurveyId) {
        await axios.put(`/api/surveys/${editingSurveyId}`, payload, { withCredentials: true });
        alert("送信しました");
      } else {
        const res = await axios.post('/api/surveys', payload, { withCredentials: true });

        // 申請時のドラフトコメントがあれば送信
        if (pendingComment.trim()) {
          try {
            await axios.post(`/api/surveys/${res.data.id}/comments`, { content: pendingComment }, { withCredentials: true });
          } catch (ignore) {
            console.error("Initial comment failed", ignore);
          }
        }

        if (isAdmin) {
          alert("フォーム作成をしました");
        } else {
          alert("フォーム申請をしました");
        }
        // 新規作成後は編集画面（チャット画面）に遷移
        setEditingSurveyId(res.data.id);
        setView('edit');
      }

      // 管理者の場合は一覧に戻る
      if (isAdmin) {
        resetForm();
      }
      // 申請者の場合は編集画面（チャット画面）に留まるため resetForm しない

      fetchSurveys();
    } catch (e) {
      console.error(e);
      alert("保存に失敗しました");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("本当にこのフォームを削除しますか？\n(この操作は取り消せません)")) return;
    try {
      await axios.delete(`/api/surveys/${id}`, { withCredentials: true });
      fetchSurveys();
    } catch (e) {
      alert("削除に失敗しました");
    }
  };

  const handleToggleActive = async (id: number, currentStatus: boolean) => {
    const action = currentStatus ? "非公開" : "公開";
    if (!confirm(`このフォームを${action}にしますか？`)) return;
    try {
      await axios.patch(`/api/surveys/${id}/toggle`, {}, { withCredentials: true });
      fetchSurveys();
    } catch (e) {
      alert("切り替えに失敗しました");
    }
  };

  const handleApprove = async (id: number) => {
    if (!confirm("この申請を承認しますか？\n(ステータスは「停止中」となり、管理者が公開できるようになります)")) return;
    try {
      await axios.put(`/api/surveys/${id}/approve`, {}, { withCredentials: true });
      fetchSurveys();
    } catch (e) {
      alert("承認に失敗しました");
    }
  };

  const handleReject = async (id: number) => {
    if (!confirm("この申請を却下しますか？\n(却下されたフォームは申請者に表示され、修正後に再申請が可能になります)")) return;
    try {
      await axios.put(`/api/surveys/${id}/reject`, {}, { withCredentials: true });
      fetchSurveys();
    } catch (e) {
      alert("却下に失敗しました");
    }
  };

  const handleDownloadCSV = async (id: number, title: string) => {
    try {
      const response = await axios.get(`/api/surveys/${id}/responses/csv`, {
        withCredentials: true,
        responseType: 'blob'
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      // フォーマット: survey_export_タイトル_日時.csv
      const dateStr = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
      // タイトルからファイル名に使えない文字を除去
      const safeTitle = title.replace(/[\\/:*?"<>|]/g, '_');
      link.setAttribute('download', `survey_${safeTitle}_${dateStr}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      alert("CSVのダウンロードに失敗しました");
    }
  };

  const resetForm = () => {
    setView('list');
    setTitle('');
    setDescription('');
    setQuestions([{ text: '', is_required: false, order: 1 }]);
    setPendingComment('');
    setEditingSurveyId(null);
  };

  const isAdmin = user?.role === 'system_admin' || user?.org_role === 'admin' || user?.role === 'admin';

  const handleAddQuestion = () => {
    setQuestions([...questions, { text: '', is_required: false, order: questions.length + 1 }]);
  };

  const handleRemoveQuestion = (index: number) => {
    const newQuestions = questions.filter((_, i) => i !== index);
    setQuestions(newQuestions.map((q, i) => ({ ...q, order: i + 1 })));
  };

  const handleQuestionChange = (index: number, field: keyof QuestionDraft, value: any) => {
    const newQuestions = [...questions];
    newQuestions[index] = { ...newQuestions[index], [field]: value };
    setQuestions(newQuestions);
  };



  if (loading) return <div className="text-center py-10">読み込み中...</div>;

  return (
    <div className="space-y-6">
      {view === 'list' ? (
        <div className="animate-in fade-in slide-in-from-bottom-2">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-lg font-bold text-sage-dark pl-2 border-l-4 border-sage-primary">
              {isAdmin ? "フォーム作成・管理" : "フォーム申請"}
            </h3>
            <button
              onClick={() => setView('create')}
              className="btn-primary px-4 py-2 text-sm flex items-center gap-2"
            >
              <Plus className="h-4 w-4" />
              {isAdmin ? "新規作成" : "作成申請"}
            </button>
          </div>

          <div className="grid gap-4">
            {surveys.length === 0 && <p className="text-slate-400 text-center py-8">管理中のフォームがありません。</p>}

            {surveys.filter(s => isAdmin || !s.is_active).map(survey => {
              const canEdit = isAdmin || (survey.created_by === user?.id && ['pending', 'rejected'].includes(survey.approval_status));

              return (
                <div key={survey.id} className="glass-card p-4 group hover:shadow-md transition-all">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        {survey.is_active ? (
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-green-100 text-green-700 uppercase tracking-wider">
                            公開中
                          </span>
                        ) : survey.approval_status === 'pending' ? (
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-700 uppercase tracking-wider">
                            申請中
                          </span>
                        ) : survey.approval_status === 'approved' ? (
                          isAdmin ? (
                            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-500 uppercase tracking-wider">
                              停止中
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-100 text-blue-700 uppercase tracking-wider">
                              承認済み
                            </span>
                          )
                        ) : survey.approval_status === 'rejected' ? (
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-red-100 text-red-700 uppercase tracking-wider">
                            却下
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-500 uppercase tracking-wider">
                            停止中
                          </span>
                        )}
                        <h4 className="font-bold text-slate-700">{survey.title}</h4>
                      </div>

                    </div>

                    <div className="flex items-center gap-1 opacity-80 group-hover:opacity-100 transition-opacity">


                      {canEdit && (
                        <>
                          <Tooltip text="編集">
                            <button onClick={() => handleEditStart(survey)} className="p-2 hover:bg-sage-50 rounded-lg text-slate-400 hover:text-orange-600 transition-colors">
                              <Edit className="h-4 w-4" />
                            </button>
                          </Tooltip>
                          <Tooltip text="削除">
                            <button onClick={() => handleDelete(survey.id)} className="p-2 hover:bg-red-50 rounded-lg text-slate-400 hover:text-red-500 transition-colors">
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </Tooltip>
                        </>
                      )}

                      {isAdmin && (
                        <>
                          {/* CSVダウンロードボタン */}
                          <Tooltip text="CSVダウンロード">
                            <button
                              onClick={() => handleDownloadCSV(survey.id, survey.title)}
                              className="p-2 hover:bg-sage-50 rounded-lg text-slate-400 hover:text-green-600 transition-colors"
                            >
                              <FileDown className="h-4 w-4" />
                            </button>
                          </Tooltip>

                          {/* 承認済み（公開中 or 停止中）の場合は公開・非公開のトグルを表示 */}
                          {survey.approval_status === 'approved' && (
                            <Tooltip text={survey.is_active ? "公開停止" : "公開する"}>
                              <button onClick={() => handleToggleActive(survey.id, survey.is_active)} className="p-2 hover:bg-sage-50 rounded-lg text-slate-400 hover:text-sage-600 transition-colors">
                                {survey.is_active ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                              </button>
                            </Tooltip>
                          )}

                          {/* 申請中の場合は承認・却下ボタンを表示 */}
                          {survey.approval_status === 'pending' && (
                            <>
                              <Tooltip text="承認（停止中に変更）">
                                <button onClick={() => handleApprove(survey.id)} className="p-2 hover:bg-green-50 rounded-lg text-slate-400 hover:text-green-600 transition-colors">
                                  <Check className="h-4 w-4" />
                                </button>
                              </Tooltip>
                              <Tooltip text="却下">
                                <button onClick={() => handleReject(survey.id)} className="p-2 hover:bg-red-50 rounded-lg text-slate-400 hover:text-red-500 transition-colors">
                                  <X className="h-4 w-4" />
                                </button>
                              </Tooltip>
                            </>
                          )}
                        </>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ) : (
        <div className="animate-in zoom-in-95 duration-200">
          <div className="flex justify-between items-center mb-6 border-b border-gray-200/50 pb-4">
            <h3 className="text-lg font-bold text-sage-dark">
              {view === 'edit' ? (isAdmin ? 'フォームを編集' : '申請を編集') : (isAdmin ? '新しいフォームを作成' : 'フォーム作成申請')}
            </h3>
            <button onClick={resetForm} className="text-slate-400 hover:text-slate-600">
              <X className="h-5 w-5" />
            </button>
          </div>

          <div className="space-y-6 max-w-3xl mx-auto">
            <div className="glass-card p-6">
              <label className="block text-sm font-bold text-gray-700 mb-2">タイトル <span className="text-red-500">*</span></label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="glass-input w-full p-2 mb-4"
                placeholder="例: 社員満足度調査"
              />

              <label className="block text-sm font-bold text-gray-700 mb-2">説明</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="glass-input w-full p-2 h-24 resize-none"
                placeholder="フォームの説明を入力..."
              />
            </div>

            <div className="space-y-4">
              <h4 className="font-bold text-slate-600 mb-2">質問リスト</h4>
              {questions.map((q, idx) => (
                <div key={idx} className="glass-card p-4 flex gap-4 items-start">
                  <span className="bg-sage-100 text-sage-700 font-bold w-6 h-6 flex items-center justify-center rounded-full text-xs mt-2">
                    {idx + 1}
                  </span>
                  <div className="flex-1">
                    <input
                      type="text"
                      value={q.text}
                      onChange={(e) => handleQuestionChange(idx, 'text', e.target.value)}
                      className="glass-input w-full p-2 mb-2"
                      placeholder="質問内容"
                    />
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        id={`req_${idx}`}
                        checked={q.is_required}
                        onChange={(e) => handleQuestionChange(idx, 'is_required', e.target.checked)}
                        className="mr-2"
                      />
                      <label htmlFor={`req_${idx}`} className="text-sm text-slate-600 select-none">必須項目にする</label>
                    </div>
                  </div>
                  {questions.length > 1 && (
                    <Tooltip text="質問を削除">
                      <button onClick={() => handleRemoveQuestion(idx)} className="text-slate-400 hover:text-red-500 p-2">
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </Tooltip>
                  )}
                </div>
              ))}

              <button onClick={handleAddQuestion} className="w-full py-3 border-2 border-dashed border-sage-300 text-sage-600 rounded-xl hover:bg-sage-50 font-bold transition-colors flex items-center justify-center gap-2">
                <Plus className="h-4 w-4" />
                質問を追加
              </button>
            </div>

            {view === 'edit' && editingSurveyId && (() => {
              const currentSurvey = surveys.find(s => s.id === editingSurveyId);
              // チャットは申請中または却下時のみ表示（公開中・停止中は非表示）
              if (currentSurvey && ['pending', 'rejected'].includes(currentSurvey.approval_status)) {
                return (
                  <div className="pt-8 mt-8 border-t border-slate-200">
                    <SurveyChat surveyId={editingSurveyId} currentUser={user} />
                  </div>
                );
              }
              return null;
            })()}

            {view === 'create' && (
              <div className="pt-8 mt-8 border-t border-slate-200">
                {isAdmin ? (
                  <div className="flex flex-col h-[150px] border border-sage-200 rounded-xl bg-slate-50 overflow-hidden opacity-70">
                    <div className="bg-sage-50 px-4 py-3 border-b border-sage-100 flex items-center justify-between">
                      <h4 className="font-bold text-sage-700 flex items-center gap-2">
                        申請に関するチャット
                      </h4>
                    </div>
                    <div className="flex-1 flex items-center justify-center text-slate-400 text-sm">
                      （管理者のため、申請時のチャット入力は不要です）
                    </div>
                  </div>
                ) : (
                  <SurveyChat
                    surveyId={null}
                    currentUser={user}
                    isDraft={true}
                    draftText={pendingComment}
                    onDraftChange={setPendingComment}
                  />
                )}
              </div>
            )}

            <div className="pt-4 flex justify-end gap-4">
              <button onClick={resetForm} className="px-6 py-2 text-slate-500 hover:bg-slate-100 rounded-lg">戻る</button>
              <button onClick={handleSave} disabled={submitting} className="btn-primary px-8 py-2 flex items-center gap-2">
                {submitting ? '保存中...' : (
                  <>
                    <Save className="h-4 w-4" />
                    {view === 'edit' ? '変更を保存' : (isAdmin ? '保存' : '申請を送信')}
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
