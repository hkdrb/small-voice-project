import Image from 'next/image';
import Link from 'next/link';
import { Github, Play, ExternalLink, User, Shield, Users, Server, Database, Brain, Globe, Lock, Download, Info, CheckCircle2 } from 'lucide-react';
import { CopyButton } from '@/components/CopyButton';

export default function LandingPage() {
  const users = [
    { role: 'システム管理者', name: 'システム管理者1', email: 'system@example.com', pass: 'SystemAdmin1234!', org: '-' },
    { role: 'システム管理者', name: 'システム管理者2', email: 'system2@example.com', pass: 'SystemAdmin1234!', org: '-' },
    { role: 'システム管理者', name: 'システム管理者3', email: 'system3@example.com', pass: 'SystemAdmin1234!', org: '-' },
    { role: 'システム管理者', name: 'システム管理者4', email: 'system4@example.com', pass: 'SystemAdmin1234!', org: '-' },
    { role: 'システム管理者', name: 'システム管理者5', email: 'system5@example.com', pass: 'SystemAdmin1234!', org: '-' },
    { role: '組織管理者', name: '組織管理者 (全兼務)', email: 'admin@example.com', pass: 'OrgAdmin1234!', org: '株式会社サンプル, サンプル部署, サンプル案件1, サンプル案件2' },
    { role: '組織管理者', name: '管理者1 (兼務)', email: 'admin1@example.com', pass: 'OrgAdmin1234!', org: '株式会社サンプル, サンプル部署, サンプル案件1, サンプル案件2' },
    { role: '組織管理者', name: '管理者2 (案件1責任者)', email: 'admin2@example.com', pass: 'OrgAdmin1234!', org: '株式会社サンプル, サンプル部署, サンプル案件1' },
    { role: '組織管理者', name: '管理者3 (案件2責任者)', email: 'admin3@example.com', pass: 'OrgAdmin1234!', org: '株式会社サンプル, サンプル部署, サンプル案件2' },
    { role: '組織管理者', name: '管理者4 (兼務)', email: 'admin4@example.com', pass: 'OrgAdmin1234!', org: '株式会社サンプル, サンプル部署, サンプル案件1, サンプル案件2' },
    { role: '組織管理者', name: '管理者5 (兼務)', email: 'admin5@example.com', pass: 'OrgAdmin1234!', org: '株式会社サンプル, サンプル部署, サンプル案件1, サンプル案件2' },
    { role: '組織管理者', name: '管理者6 (兼務)', email: 'admin6@example.com', pass: 'OrgAdmin1234!', org: '株式会社サンプル, サンプル部署, サンプル案件1, サンプル案件2' },
    { role: '一般ユーザー', name: 'ユーザー1', email: 'user1@example.com', pass: 'GeneralUser1234!', org: '株式会社サンプル, サンプル部署, サンプル案件1, サンプル案件2' },
    { role: '一般ユーザー', name: 'ユーザー2', email: 'user2@example.com', pass: 'GeneralUser1234!', org: '株式会社サンプル, サンプル部署, サンプル案件1, サンプル案件2' },
    { role: '一般ユーザー', name: 'ユーザー3', email: 'user3@example.com', pass: 'GeneralUser1234!', org: '株式会社サンプル, サンプル部署, サンプル案件1' },
    { role: '一般ユーザー', name: 'ユーザー4', email: 'user4@example.com', pass: 'GeneralUser1234!', org: '株式会社サンプル, サンプル部署, サンプル案件1' },
    { role: '一般ユーザー', name: 'ユーザー5', email: 'user5@example.com', pass: 'GeneralUser1234!', org: '株式会社サンプル, サンプル部署, サンプル案件1' },
    { role: '一般ユーザー', name: 'ユーザー6', email: 'user6@example.com', pass: 'GeneralUser1234!', org: '株式会社サンプル, サンプル部署, サンプル案件1' },
    { role: '一般ユーザー', name: 'ユーザー7', email: 'user7@example.com', pass: 'GeneralUser1234!', org: '株式会社サンプル, サンプル部署, サンプル案件2' },
    { role: '一般ユーザー', name: 'ユーザー8', email: 'user8@example.com', pass: 'GeneralUser1234!', org: '株式会社サンプル, サンプル部署, サンプル案件2' },
    { role: '一般ユーザー', name: 'ユーザー9', email: 'user9@example.com', pass: 'GeneralUser1234!', org: '株式会社サンプル, サンプル部署, サンプル案件2' },
    { role: '一般ユーザー', name: 'ユーザー10', email: 'user10@example.com', pass: 'GeneralUser1234!', org: '株式会社サンプル, サンプル部署, サンプル案件2' },
  ];

  return (
    <div className="min-h-dvh bg-sage-50 text-slate-800 font-sans selection:bg-sage-200 selection:text-sage-900">

      {/* Hero Section */}
      <header className="relative overflow-hidden bg-gradient-to-br from-sage-100 to-white py-20 px-4 sm:px-6 lg:px-8 shadow-sm">
        <div className="max-w-4xl mx-auto text-center relative z-10">
          <div className="inline-block px-4 py-1.5 mb-6 text-xs font-semibold tracking-wider text-sage-800 uppercase bg-sage-200/50 rounded-full border border-sage-300/50 backdrop-blur-sm">
            Project Introduction
          </div>
          <h1 className="text-4xl sm:text-5xl md:text-7xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-sage-800 to-sage-600 mb-6 tracking-tight drop-shadow-sm">
            Small Voice <span className="text-3xl sm:text-4xl align-top">🍃</span>
          </h1>
          <p className="text-lg sm:text-xl md:text-2xl text-slate-600 max-w-4xl mx-auto mb-10 leading-relaxed font-light px-4">
            組織内の「小さな声」を聴き、課題解決を促進する<br className="hidden md:inline" />AI搭載型ブロードリスニングシステム
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Link
              href="/login"
              target="_blank"
              rel="noopener noreferrer"
              className="px-8 py-4 bg-sage-600 hover:bg-sage-700 text-white font-bold rounded-xl shadow-lg hover:shadow-xl transition-all transform hover:-translate-y-1 flex items-center gap-2 group"
            >
              <ExternalLink className="w-5 h-5 group-hover:rotate-45 transition-transform" />
              システムにログイン / 利用開始
            </Link>
            <a
              href="https://github.com/small-voice/small-voice-project"
              target="_blank"
              rel="noopener noreferrer"
              className="px-8 py-4 bg-white hover:bg-gray-50 text-slate-700 font-bold rounded-xl shadow-md hover:shadow-lg border border-gray-200 transition-all transform hover:-translate-y-1 flex items-center gap-2"
            >
              <Github className="w-5 h-5" />
              GitHubを見る
            </a>
          </div>
        </div>

        {/* Background decorative elements */}
        <div className="absolute top-0 left-0 w-full h-full overflow-hidden -z-0 pointer-events-none">
          <div className="absolute -top-[10%] -left-[10%] w-[40%] h-[40%] bg-sage-200/30 rounded-full blur-3xl opacity-60 animate-pulse"></div>
          <div className="absolute top-[20%] -right-[5%] w-[30%] h-[30%] bg-orange-100/40 rounded-full blur-3xl opacity-60 delay-700 animate-pulse"></div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-12 sm:px-6 lg:px-8 space-y-16">

        {/* Environment Info */}
        <section className="bg-white/60 backdrop-blur-md rounded-2xl p-5 sm:p-8 border border-white/50 shadow-sm hover:shadow-md transition-shadow">
          <h2 className="text-2xl font-bold flex items-center gap-3 mb-6 text-sage-900 border-b border-sage-200 pb-2">
            <Globe className="w-6 h-6 text-sage-600" />
            🔗 デモ公開URL
          </h2>
          <div className="space-y-4">
            <div>
              <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Login URL</label>
              <div className="mt-1 font-mono text-base sm:text-lg text-sage-700 selection:bg-sage-200">
                <a
                  href="https://small-voice.xyz/login"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:underline flex items-center gap-2 break-all sm:break-normal"
                >
                  https://small-voice.xyz/login
                  <ExternalLink className="w-4 h-4 shrink-0" />
                </a>
              </div>
            </div>

            <div className="bg-orange-50/50 p-4 rounded-xl border border-orange-100/50">
              <div className="flex items-center gap-2 mb-2">
                <Lock className="w-4 h-4 text-orange-400" />
                <span className="text-xs font-bold text-orange-400 uppercase tracking-wider">Basic Auth Credentials</span>
              </div>
              <div className="grid grid-cols-[80px_1fr_auto] gap-2 font-mono text-sm text-slate-600 items-center">
                <span className="text-slate-400">User:</span>
                <span className="font-bold select-all">smallvoice</span>
                <CopyButton text="smallvoice" className="ml-2" />
                <span className="text-slate-400">Pass:</span>
                <span className="font-bold select-all">R3HCydsK</span>
                <CopyButton text="R3HCydsK" className="ml-2" />
              </div>
            </div>
            <div className="text-sm text-slate-500 leading-relaxed bg-slate-50 p-4 rounded-xl border border-slate-100 italic">
              ※ 本番環境はBasic認証によって保護されています。アクセス時に上記のIDとパスワードを入力してください。
            </div>
          </div>
        </section>

        {/* About Small Voice */}
        <section className="bg-white/60 backdrop-blur-md rounded-2xl p-5 sm:p-8 border border-white/50 shadow-sm hover:shadow-md transition-shadow">
          <h2 className="text-2xl font-bold flex items-center gap-3 mb-6 text-sage-900 border-b border-sage-200 pb-2">
            <Info className="w-6 h-6 text-sage-600" />
            Small Voiceについて
          </h2>
          <div className="space-y-8">
            <div>
              <h3 className="text-xl font-bold text-sage-800 mb-3 flex items-center gap-2">
                <span className="text-2xl">🔍</span> ブロードリスニングとは
              </h3>
              <p className="text-slate-600 leading-relaxed">
                「ブロードリスニング」とは、一方的な情報発信である「ブロードキャスト」と対をなす概念です。個々の異なる意見を収集・分析することで、組織や社会全体の傾向、あるいは感覚的には捉えきれていない不可視の課題を俯瞰的に把握することのできる手法です。
              </p>

              <p className="text-slate-600 leading-relaxed mt-4">
                ブロードキャストによって生じがちな情報の偏りを是正し、統計的な分析によって浮き彫りになった課題に対し、対話を通じて異なる意見の架け橋を見出したり、意思決定の質を高めたりすることを目的としています。
              </p>

              <div className="mt-8 max-w-2xl mx-auto rounded-2xl overflow-hidden shadow-lg border border-sage-200 bg-white p-2">
                <Image
                  src="/images/broad-listening-concept.png"
                  alt="ブロードリスニングのコンセプト（ブロードキャストとの比較）"
                  width={800}
                  height={533}
                  className="w-full h-auto rounded-xl"
                />
                <p className="text-center text-xs text-slate-400 mt-2 italic">
                  図：ブロードキャストからブロードリスニングの時代へ
                </p>
              </div>
            </div>

            <div>
              <h3 className="text-xl font-bold text-sage-800 mb-3 flex items-center gap-2">
                <span className="text-2xl">💡</span> Small Voice（外れ値）の救い上げ
              </h3>
              <p className="text-slate-600 leading-relaxed">
                さらに本システムでは、統計的な分析の過程で切り捨てられがちな「少数の意見（Small Voice）」を、組織の重要な兆しとして扱います。大多数の声に埋もれた外れ値を独立したトピックとして抽出・保持することで、潜在的なリスクや革新的なアイデアを確実に対話のテーブルへと導きます。
              </p>
            </div>

            <div>
              <h3 className="text-xl font-bold text-sage-800 mb-6 flex items-center gap-2">
                <span className="text-2xl">🚀</span> 主な機能
              </h3>
              <div className="space-y-8">

                {/* Feature 1 */}
                <div className="bg-white p-4 sm:p-6 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow">
                  <div className="flex items-start gap-0 sm:gap-4">
                    <div className="hidden sm:block bg-sage-100 p-3 rounded-xl text-sage-600 shrink-0">
                      <Database className="w-8 h-8" />
                    </div>
                    <div>
                      <h4 className="text-xl font-bold text-sage-900 mb-3">多様なデータ収集方法</h4>
                      <div className="space-y-3">
                        <p className="text-slate-600 leading-relaxed">
                          管理者によるフォーム作成・管理に加えて、さまざまな方法でデータ収集が可能です。
                        </p>
                        <ul className="space-y-4 mt-4">
                          <li className="flex items-start gap-3 text-sm text-slate-600">
                            <CheckCircle2 className="w-5 h-5 text-sage-500 mt-0.5 shrink-0" />
                            <span>
                              <span className="font-bold text-sage-800 block mb-1">雑談掲示板からのフォーム作成</span>
                              メンバーが日常的に投稿した声をAI分析し、フォーム作成のベースとなるテーマを自動抽出。分析結果から直接フォームを作成できます。
                            </span>
                          </li>
                          <li className="flex items-start gap-3 text-sm text-slate-600">
                            <CheckCircle2 className="w-5 h-5 text-sage-500 mt-0.5 shrink-0" />
                            <span>
                              <span className="font-bold text-sage-800 block mb-1">メンバーからのフォーム申請</span>
                              メンバーが自発的に問いたい内容をフォームにし、管理者へ承認申請できるボトムアップ設計。
                            </span>
                          </li>
                          <li className="flex items-start gap-3 text-sm text-slate-600">
                            <CheckCircle2 className="w-5 h-5 text-sage-500 mt-0.5 shrink-0" />
                            <span>
                              <span className="font-bold text-sage-800 block mb-1">外部フォームのインポート</span>
                              Googleフォームなどの外部アンケートの結果を、CSVインポートで一括取り込みすることも可能です。
                            </span>
                          </li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Feature 2 */}
                <div className="bg-white p-4 sm:p-6 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow">
                  <div className="flex items-start gap-0 sm:gap-4">
                    <div className="hidden sm:block bg-sage-100 p-3 rounded-xl text-sage-600 shrink-0">
                      <Brain className="w-8 h-8" />
                    </div>
                    <div>
                      <h4 className="text-xl font-bold text-sage-900 mb-3">シームレスな広聴と対話空間の設計</h4>
                      <div className="space-y-3">
                        <p className="text-slate-600 leading-relaxed">
                          収集した声を収集しただけで終わらせず、解決まで一気通貫で繋げるシームレスなブロードリスニングを実現します。
                        </p>
                        <ul className="space-y-4 mt-4">
                          <li className="flex items-start gap-3 text-sm text-slate-600">
                            <CheckCircle2 className="w-5 h-5 text-sage-500 mt-0.5 shrink-0" />
                            <span>
                              <span className="font-bold text-sage-800 block mb-1">クラスタリング</span>
                              収集された多種多様な意見をAIが各カテゴリに分類・構造化。
                            </span>
                          </li>
                          <li className="flex items-start gap-3 text-sm text-slate-600">
                            <CheckCircle2 className="w-5 h-5 text-sage-500 mt-0.5 shrink-0" />
                            <span>
                              <span className="font-bold text-sage-800 block mb-1">課題リスト</span>
                              クラスタリング結果に基づき、取り組むべき課題を抽出・リスト化。
                            </span>
                          </li>
                          <li className="flex items-start gap-3 text-sm text-slate-600">
                            <CheckCircle2 className="w-5 h-5 text-sage-500 mt-0.5 shrink-0" />
                            <span>
                              <span className="font-bold text-sage-800 block mb-1">課題ごとの議論チャット</span>
                              各課題に専用のチャット空間を生成し、具体的な対話を促進。
                            </span>
                          </li>
                          <li className="flex items-start gap-3 text-sm text-slate-600">
                            <CheckCircle2 className="w-5 h-5 text-sage-500 mt-0.5 shrink-0" />
                            <span>
                              <span className="font-bold text-sage-800 block mb-1">AIファシリテーター</span>
                              各チャットの対話をAIが中立的なファシリテーターとして分析し、合意形成をサポートします。
                            </span>
                          </li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Feature 3 */}
                <div className="bg-white p-4 sm:p-6 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow">
                  <div className="flex items-start gap-0 sm:gap-4">
                    <div className="hidden sm:block bg-sage-100 p-3 rounded-xl text-sage-600 shrink-0">
                      <Server className="w-8 h-8" />
                    </div>
                    <div>
                      <h4 className="text-xl font-bold text-sage-900 mb-3">柔軟な組織管理（マルチテナント構成）</h4>
                      <div className="space-y-3">
                        <ul className="space-y-4 mt-4">
                          <li className="flex items-start gap-3 text-sm text-slate-600">
                            <CheckCircle2 className="w-5 h-5 text-sage-500 mt-0.5 shrink-0" />
                            <span>
                              <span className="font-bold text-sage-800 block mb-1">多重所属に対応</span>
                              システム内のユーザーは複数の組織（部署や案件）に同時に属することが可能。
                            </span>
                          </li>
                          <li className="flex items-start gap-3 text-sm text-slate-600">
                            <CheckCircle2 className="w-5 h-5 text-sage-500 mt-0.5 shrink-0" />
                            <span>
                              <span className="font-bold text-sage-800 block mb-1">実態に即した管理</span>
                              部署単位だけでなく、参画案件やプロジェクト単位での柔軟な管理・運用を実現します。
                            </span>
                          </li>
                          <li className="flex items-start gap-3 text-sm text-slate-600">
                            <CheckCircle2 className="w-5 h-5 text-sage-500 mt-0.5 shrink-0" />
                            <span>
                              <span className="font-bold text-sage-800 block mb-1">セキュアな分離</span>
                              データは組織ごとに論理的に分離され、安心して利用できます。
                            </span>
                          </li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Feature 4 */}
                <div className="bg-white p-4 sm:p-6 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow">
                  <div className="flex items-start gap-0 sm:gap-4">
                    <div className="hidden sm:block bg-sage-100 p-3 rounded-xl text-sage-600 shrink-0">
                      <Shield className="w-8 h-8" />
                    </div>
                    <div>
                      <h4 className="text-xl font-bold text-sage-900 mb-3">3つの権限設計</h4>
                      <p className="text-slate-600 leading-relaxed mb-4">
                        本システムでは以下の3つの役割（ロール）を提供し、スムーズな運用をサポートします。
                      </p>
                      <div className="grid sm:grid-cols-3 gap-4">
                        <div className="bg-purple-50 p-4 rounded-xl border border-purple-100">
                          <h5 className="font-bold text-purple-900 mb-1 flex items-center gap-2">
                            <Shield className="w-4 h-4" /> システム管理者
                          </h5>
                          <p className="text-xs text-purple-800/80 leading-relaxed">
                            システム全体の統括。組織の作成や全ユーザーの管理権限を持ちます。
                          </p>
                        </div>
                        <div className="bg-blue-50 p-4 rounded-xl border border-blue-100">
                          <h5 className="font-bold text-blue-900 mb-1 flex items-center gap-2">
                            <Users className="w-4 h-4" /> 組織管理者
                          </h5>
                          <p className="text-xs text-blue-800/80 leading-relaxed">
                            所属する組織内におけるフォーム作成や管理、分析の実行や分析結果の管理を行います。
                          </p>
                        </div>
                        <div className="bg-green-50 p-4 rounded-xl border border-green-100">
                          <h5 className="font-bold text-green-900 mb-1 flex items-center gap-2">
                            <User className="w-4 h-4" /> 一般ユーザー
                          </h5>
                          <p className="text-xs text-green-800/80 leading-relaxed">
                            フォームへの回答や申請、分析結果の閲覧、議論への参加が可能です。
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

              </div>
            </div>
          </div>
        </section>



        {/* Demo Video Placeholder */}
        <section>
          <h2 className="text-2xl font-bold flex items-center gap-3 mb-6 text-sage-900 border-b border-sage-200 pb-2">
            <Play className="w-6 h-6 text-sage-600" />
            🎬 デモ動画
          </h2>
          <div className="aspect-video w-full bg-slate-100 rounded-2xl border-2 border-dashed border-slate-300 flex items-center justify-center text-slate-400">
            <div className="text-center">
              <Play className="w-12 h-12 mx-auto mb-2 opacity-50" />
              <p className="font-medium">Coming Soon...</p>
              <p className="text-sm">デモ動画は後ほど公開予定です</p>
            </div>
          </div>
        </section>

        {/* Test Users Table */}
        <section>
          <div className="flex flex-col md:flex-row md:items-center justify-between mb-6 border-b border-sage-200 pb-2">
            <h2 className="text-2xl font-bold flex items-center gap-3 text-sage-900">
              <User className="w-6 h-6 text-sage-600" />
              👤 デモ用ユーザー
            </h2>
          </div>

          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left text-slate-600">
                <thead className="text-xs text-slate-500 uppercase bg-slate-50 border-b border-slate-200">
                  <tr>
                    <th className="px-3 sm:px-6 py-4 font-bold">表示名</th>
                    <th className="px-3 sm:px-6 py-4 font-bold">メールアドレス</th>
                    <th className="px-3 sm:px-6 py-4 font-bold">パスワード(初期)</th>
                    <th className="px-3 sm:px-6 py-4 font-bold whitespace-nowrap">権限種別</th>
                    <th className="px-3 sm:px-6 py-4 font-bold w-1/3">所属組織</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {users.map((user, index) => (
                    <tr key={index} className="hover:bg-slate-50 transition-colors">
                      <td className="px-3 sm:px-6 py-4 font-medium text-slate-800 whitespace-nowrap">{user.name}</td>
                      <td className="px-3 sm:px-6 py-4 font-mono select-all text-sage-700">
                        <div className="flex items-center gap-2">
                          <span>{user.email}</span>
                          <CopyButton text={user.email} />
                        </div>
                      </td>
                      <td className="px-3 sm:px-6 py-4 font-mono select-all text-slate-500">
                        <div className="flex items-center gap-2">
                          <span>{user.pass}</span>
                          <CopyButton text={user.pass} />
                        </div>
                      </td>
                      <td className="px-3 sm:px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium 
                          ${user.role.includes('システム') ? 'bg-purple-100 text-purple-800' :
                            user.role.includes('組織') ? 'bg-blue-100 text-blue-800' :
                              'bg-green-100 text-green-800'}`}>
                          {user.role}
                        </span>
                      </td>
                      <td className="px-3 sm:px-6 py-4 text-xs text-slate-500">{user.org}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>

        {/* Test Data Downloads */}
        <section>
          <h2 className="text-2xl font-bold flex items-center gap-3 mb-6 text-sage-900 border-b border-sage-200 pb-2">
            <Database className="w-6 h-6 text-sage-600" />
            👤 テスト用レポートデータ
          </h2>
          <div className="bg-slate-50 rounded-2xl p-5 sm:p-8 border border-slate-200 text-center">
            <p className="text-slate-600 mb-6">
              分析機能お試し用に、ダミーデータのセットを用意しました。<br />
              ダウンロードしてCSVインポート機能から取り込むことで、すぐに分析を試すことができます。
            </p>
            <a
              href="/downloads/sample_data.zip"
              download
              className="inline-flex items-center gap-3 px-8 py-4 bg-sage-600 hover:bg-sage-700 text-white font-bold rounded-xl shadow-lg hover:shadow-xl transition-all transform hover:-translate-y-1 group"
            >
              <Download className="w-5 h-5 group-hover:animate-bounce" />
              テストデータ一括ダウンロード (ZIP)
            </a>
          </div>
        </section>

        {/* Demo Video Placeholder */}


        {/* Supplementary Info */}
        <section>
          <h2 className="text-2xl font-bold flex items-center gap-3 mb-6 text-sage-900 border-b border-sage-200 pb-2">
            <Info className="w-6 h-6 text-sage-600" />
            📌 補足事項
          </h2>
          <div className="bg-white p-5 sm:p-8 rounded-2xl border border-slate-200 shadow-sm">
            <ul className="space-y-4 text-slate-600 leading-relaxed list-inside">
              <li className="flex gap-3">
                <span className="text-sage-500 font-bold shrink-0">•</span>
                <span>デモ公開URLのログイン画面より、こちらに記載のデモ用ユーザーでログインし、自由に操作いただいて問題ありません。</span>
              </li>
              <li className="flex gap-3">
                <span className="text-sage-500 font-bold shrink-0">•</span>
                <span>テスト用レポートデータも自由に使い、レポート分析を試してみてください。</span>
              </li>
              <li className="flex gap-3">
                <span className="text-sage-500 font-bold shrink-0">•</span>
                <span>本システムはAIエージェント「Antigravity」を活用したバイブコーディングにより、そのほとんどを開発しました。</span>
              </li>
            </ul>
          </div>
        </section>

      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 py-8 mt-12 text-center text-slate-400 text-sm">
        <p>© 2026 Small Voice Project.</p>
        <p className="mt-2 text-xs">Created for Hackathon Submission</p>
      </footer>
    </div >
  );
}
