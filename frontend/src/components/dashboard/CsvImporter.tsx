'use client';

import { useState } from 'react';
import axios from 'axios';
import { Upload, FileText, CheckCircle, AlertTriangle } from 'lucide-react';

export default function CsvImporter() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string[][]>([]); // Simple preview
  const [headers, setHeaders] = useState<string[]>([]);
  const [selectedHeaders, setSelectedHeaders] = useState<Set<string>>(new Set());
  const [uploading, setUploading] = useState(false);
  const [success, setSuccess] = useState(false);

  // Form
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const f = e.target.files[0];
      setFile(f);
      setTitle(f.name.replace('.csv', ''));
      setDescription(`Imported from ${f.name}`);

      // Simple preview parsing
      const reader = new FileReader();
      reader.onload = (evt) => {
        const text = evt.target?.result as string;
        const lines = text.split('\n').filter(l => l.trim()).slice(0, 6);
        const rows = lines.map(line => line.split(',')); // Naive CSV split
        if (rows.length > 0) {
          const detectedHeaders = rows[0];
          setHeaders(detectedHeaders);
          setSelectedHeaders(new Set(detectedHeaders)); // Default all selected
          setPreview(rows.slice(1));
        }
      };
      reader.readAsText(f);
    }
  };

  const toggleHeader = (header: string) => {
    const newSelected = new Set(selectedHeaders);
    if (newSelected.has(header)) {
      newSelected.delete(header);
    } else {
      newSelected.add(header);
    }
    setSelectedHeaders(newSelected);
  };

  const handleUpload = async () => {
    if (!file) return;
    if (selectedHeaders.size === 0) {
      alert("少なくとも1つの列を選択してください。");
      return;
    }

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title);
    formData.append('description', description);
    formData.append('selected_columns', Array.from(selectedHeaders).join(','));

    try {
      await axios.post('/api/surveys/import', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        withCredentials: true
      });
      setSuccess(true);
      // Reset after 3 secs
      setTimeout(() => {
        setSuccess(false);
        setFile(null);
        setPreview([]);
        setTitle('');
        setSelectedHeaders(new Set());
      }, 3000);
    } catch (e) {
      console.error(e);
      alert("インポートに失敗しました。CSV形式を確認してください。");
    } finally {
      setUploading(false);
    }
  };



  if (success) {
    return (
      <div className="max-w-xl mx-auto glass-card p-6 md:p-12 text-center animate-in zoom-in-95">
        <div className="w-16 h-16 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto mb-4">
          <CheckCircle className="h-8 w-8" />
        </div>
        <h2 className="text-xl font-bold text-sage-dark mb-2">インポート完了！</h2>
        <p className="text-slate-500">フォーム一覧に新しいデータが追加されました。</p>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto glass-card p-4 md:p-8 animate-in fade-in slide-in-from-bottom-2">
      <div className="text-center mb-8">
        <div className="w-16 h-16 bg-sage-100 text-sage-600 rounded-full flex items-center justify-center mx-auto mb-4">
          <Upload className="h-8 w-8" />
        </div>
        <h2 className="text-xl md:text-2xl font-bold text-sage-dark">CSVデータをインポート</h2>
        <p className="text-slate-500">外部フォームのアンケート結果などを取り込んで分析できます</p>
      </div>

      <div className="space-y-6">
        {/* File Input */}
        <div className="border-2 border-dashed border-sage-300 rounded-xl p-8 text-center hover:bg-sage-50 transition-colors relative cursor-pointer">
          <input type="file" accept=".csv" onChange={handleFileChange} className="absolute inset-0 w-full h-full opacity-0 cursor-pointer" />
          {file ? (
            <div className="flex flex-col items-center">
              <FileText className="h-10 w-10 text-sage-primary mb-2" />
              <p className="font-bold text-slate-700">{file.name}</p>
              <p className="text-xs text-slate-400">{(file.size / 1024).toFixed(1)} KB</p>
            </div>
          ) : (
            <div className="flex flex-col items-center text-slate-400">
              <Upload className="h-8 w-8 mb-2" />
              <p className="font-bold">クリックしてCSVファイルを選択</p>
              <p className="text-xs">またはファイルをドロップ</p>
            </div>
          )}
        </div>

        {/* Settings */}
        {file && (
          <div className="space-y-4 animate-in fade-in">
            <div>
              <label className="block text-sm font-bold text-gray-700 mb-2">フォームタイトル</label>
              <input type="text" value={title} onChange={(e) => setTitle(e.target.value)} className="glass-input w-full p-2 text-base" />
            </div>

            <div>
              <label className="block text-sm font-bold text-gray-700 mb-2">プレビュー (最初の5行)</label>
              <div className="overflow-x-auto border border-gray-200 rounded-lg">
                <table className="w-full text-sm text-left whitespace-nowrap">
                  <thead className="bg-sage-50 text-sage-700 text-xs uppercase">
                    <tr>
                      {headers.map((h, i) => (
                        <th key={i} className="px-4 py-2 border-b">
                          <label className="flex items-center gap-2 cursor-pointer hover:text-sage-700">
                            <input
                              type="checkbox"
                              checked={selectedHeaders.has(h)}
                              onChange={() => toggleHeader(h)}
                              className="rounded text-sage-600 focus:ring-sage-500 w-4 h-4 cursor-pointer"
                            />
                            {h}
                          </label>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {preview.map((row, i) => (
                      <tr key={i} className="border-b last:border-0 hover:bg-gray-50">
                        {row.map((c, j) => <td key={j} className="px-4 py-2 text-slate-600 truncate max-w-xs">{c}</td>)}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 flex gap-3 text-amber-700 text-sm">
              <AlertTriangle className="h-5 w-5 shrink-0" />
              <div>
                <p className="font-bold">注意</p>
                <p>1行目を「質問文」、2行目以降を「回答」として取り込みます。チェックを入れた列のみがインポートされます。</p>
              </div>
            </div>

            <button
              onClick={handleUpload}
              disabled={uploading}
              className="w-full btn-primary py-3 font-bold"
            >
              {uploading ? 'アップロード中...' : 'インポートを実行'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
