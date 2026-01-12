"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import axios from "axios";
import { ArrowLeft, Plus, Trash2, Check, Loader2 } from "lucide-react";

interface QuestionInput {
  text: string;
  is_required: boolean;
}

export default function NewSurveyPage() {
  const router = useRouter();
  const [step, setStep] = useState<"input" | "confirm">("input");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [questions, setQuestions] = useState<QuestionInput[]>([{ text: "", is_required: true }]);
  const [loading, setLoading] = useState(false);

  // Check Auth on Mount
  useEffect(() => {
    axios.get("/api/auth/me", { withCredentials: true })
      .catch((e) => {
        if (e.response && e.response.status === 401) {
          router.push("/login");
        }
      });
  }, [router]);

  const addQuestion = () => {
    if (questions.length >= 10) return;
    setQuestions([...questions, { text: "", is_required: true }]);
  };

  const removeQuestion = (index: number) => {
    if (questions.length <= 1) return;
    const newQs = [...questions];
    newQs.splice(index, 1);
    setQuestions(newQs);
  };

  const updateQuestion = (index: number, field: keyof QuestionInput, value: any) => {
    const newQs = [...questions];
    newQs[index] = { ...newQs[index], [field]: value };
    setQuestions(newQs);
  };

  const handleConfirm = () => {
    if (!title.trim()) {
      alert("タイトルを入力してください");
      return;
    }
    setStep("confirm");
  };

  const handleSubmit = async () => {
    setLoading(true);
    try {
      // Filter empty questions if needed, or validate
      const validQuestions = questions.map((q, idx) => ({
        text: q.text,
        is_required: q.is_required,
        order: idx
      })).filter(q => q.text.trim() !== "");

      await axios.post("/api/surveys/", {
        title,
        description,
        questions: validQuestions
      }, { withCredentials: true });

      router.push("/dashboard/surveys");
    } catch (error) {
      console.error("Failed to create survey", error);
      alert("作成に失敗しました");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-50">
      <header className="bg-white border-b border-slate-200 h-16 flex items-center px-8 gap-4 sticky top-0 z-10">
        <Link href="/dashboard/surveys" className="p-2 hover:bg-slate-100 rounded-full text-slate-500">
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <h1 className="text-xl font-bold text-slate-800">新規フォーム作成</h1>
      </header>

      <div className="flex-1 overflow-auto p-8">
        <div className="max-w-3xl mx-auto glass-card">
          {step === "input" ? (
            <div className="space-y-8">
              <div>
                <label className="block text-sm font-bold text-sage-dark mb-2">タイトル <span className="text-red-500">*</span></label>
                <input
                  type="text"
                  className="w-full glass-input px-4 py-2"
                  placeholder="例: 第1回 意識調査"
                  value={title}
                  onChange={e => setTitle(e.target.value)}
                />
              </div>

              <div>
                <label className="block text-sm font-bold text-sage-dark mb-2">説明</label>
                <textarea
                  className="w-full glass-input px-4 py-2 h-24"
                  placeholder="アンケートの目的などを入力..."
                  value={description}
                  onChange={e => setDescription(e.target.value)}
                />
              </div>

              <div>
                <label className="block text-sm font-bold text-sage-dark mb-4">質問リスト</label>
                <div className="space-y-4">
                  {questions.map((q, idx) => (
                    <div key={idx} className="flex gap-4 items-start bg-slate-50/50 p-4 rounded-xl border border-slate-100">
                      <div className="flex-1">
                        <div className="flex justify-between mb-2">
                          <span className="text-xs font-bold text-slate-400">質問 {idx + 1}</span>
                          <label className="flex items-center gap-2 text-xs font-bold text-slate-500 cursor-pointer">
                            <input
                              type="checkbox"
                              checked={q.is_required}
                              onChange={e => updateQuestion(idx, 'is_required', e.target.checked)}
                              className="rounded text-sage-primary focus:ring-sage-primary"
                            />
                            必須
                          </label>
                        </div>
                        <input
                          type="text"
                          className="w-full glass-input px-3 py-2 text-sm"
                          placeholder="質問文を入力..."
                          value={q.text}
                          onChange={e => updateQuestion(idx, 'text', e.target.value)}
                        />
                      </div>
                      {questions.length > 1 && (
                        <button onClick={() => removeQuestion(idx)} className="mt-6 p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors">
                          <Trash2 className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                  ))}
                </div>

                <div className="mt-4">
                  <button onClick={addQuestion} className="flex items-center gap-2 text-sm font-bold text-sage-primary hover:bg-sage-light px-4 py-2 rounded-lg transition-colors">
                    <Plus className="h-4 w-4" />
                    質問を追加
                  </button>
                </div>
              </div>

              <div className="pt-4 flex justify-end">
                <button onClick={handleConfirm} className="btn-primary px-8 py-3">
                  確認画面へ進む
                </button>
              </div>
            </div>
          ) : (
            <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-300">
              <div className="text-center mb-8">
                <h2 className="text-2xl font-bold text-sage-dark mb-2">確認</h2>
                <p className="text-slate-500">以下の内容で作成しますか？</p>
              </div>

              <div className="bg-white p-6 rounded-xl border border-slate-100 shadow-sm">
                <h3 className="font-bold text-lg mb-2">{title}</h3>
                <p className="text-slate-600 whitespace-pre-wrap mb-6 text-sm">{description}</p>

                <div className="space-y-4">
                  {questions.filter(q => q.text.trim()).map((q, idx) => (
                    <div key={idx} className="flex gap-2 text-sm">
                      <span className="font-bold text-slate-400 w-6">{idx + 1}.</span>
                      <div className="flex-1">
                        <span className="text-slate-700">{q.text}</span>
                        {q.is_required && <span className="ml-2 text-xs text-red-500 bg-red-50 px-2 py-0.5 rounded-full font-bold">必須</span>}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex gap-4 justify-center">
                <button onClick={() => setStep("input")} className="px-6 py-3 font-bold text-slate-500 hover:bg-slate-100 rounded-xl transition-colors">
                  戻る
                </button>
                <button onClick={handleSubmit} disabled={loading} className="btn-primary px-8 py-3 flex items-center gap-2">
                  {loading ? <Loader2 className="animate-spin h-5 w-5" /> : <Check className="h-5 w-5" />}
                  作成する
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
