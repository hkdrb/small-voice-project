import pandas as pd
import random
import os
import shutil
from datetime import datetime, timedelta
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- Configuration ---
NUM_ROWS = 1000
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs", "test_data")

# --- Utility Functions ---
def generate_random_date():
    start_date = datetime.now() - timedelta(days=90)
    random_days = random.randint(0, 90)
    random_seconds = random.randint(0, 86400)
    dt = start_date + timedelta(days=random_days, seconds=random_seconds)
    return dt.strftime("%Y/%m/%d %H:%M")

def generate_combinatorial_sentence(parts):
    """
    parts: list of lists
    """
    sentence = ""
    for part_list in parts:
        if not part_list: continue
        fragment = random.choice(part_list)
        if fragment:
            sentence += fragment
    return sentence

# =============================================================================
# 1. 今月の業務振り返り (KPT)
# =============================================================================

# Keep: 良かったこと、継続したいこと
KEEP_INTROS = [
    "今月は、", "振り返ると、", "特に良かったのは、", "成果として、", 
    "継続したいこととして、", "うまくいったのは、", "チームで、", "個人的には、",
    "", "", ""
]

KEEP_SUBJECTS = [
    "新しい技術スタックの導入が", "チーム内のコミュニケーションが", "コードレビューのプロセスが",
    "ペアプログラミングの実施が", "定期的な1on1が", "スプリント計画の精度が",
    "自動テストの拡充が", "ドキュメント整備が", "リファクタリングの時間確保が",
    "非同期コミュニケーションの活用が", "技術的負債の返済が", "新メンバーのオンボーディングが",
    "デプロイの自動化が", "モニタリング体制の強化が", "セキュリティ対策の見直しが"
]

KEEP_OUTCOMES = [
    "スムーズに進んだ", "チームの生産性向上に繋がった", "品質が大きく改善された",
    "メンバーのモチベーションが上がった", "予想以上の成果を出せた", "障害が減少した",
    "開発速度が向上した", "属人化が解消された", "知見が共有された",
    "心理的安全性が高まった", "技術力の底上げになった", "顧客満足度が向上した"
]

KEEP_CLOSINGS = [
    "ので、来月も継続したい。", "ため、定着させていきたい。", "ので、さらに強化したい。",
    "ため、他のチームにも展開したい。", "ので、習慣化していきたい。", "。",
    "ため、今後も大切にしたい。", "ので、ベストプラクティスとして確立したい。"
]

# Problem: 困ったこと、改善したいこと
PROBLEM_INTROS = [
    "一方で、", "課題として、", "改善が必要なのは、", "困ったこととして、",
    "ボトルネックになったのは、", "非効率だと感じたのは、", "問題だったのは、",
    "", "", ""
]

PROBLEM_SUBJECTS = [
    "仕様変更への対応が", "レビュー待ち時間が", "会議の時間が", "技術的負債が",
    "テスト環境の不安定さが", "情報共有の不足が", "優先順位の変更が",
    "開発環境のセットアップが", "依存関係の管理が", "デプロイプロセスが",
    "ドキュメントの古さが", "コミュニケーションコストが", "割り込みタスクが",
    "見積もりの精度が", "他部署との連携が"
]

PROBLEM_ISSUES = [
    "予想以上に時間を取られた", "進行の妨げになった", "ストレスの原因になった",
    "品質低下を招いた", "手戻りが発生した", "チームの士気を下げた",
    "納期遅延の原因になった", "属人化を招いた", "混乱を生んだ",
    "効率を大きく下げた", "技術的な課題を残した", "顧客への影響があった"
]

PROBLEM_CLOSINGS = [
    "ので、改善策を検討したい。", "ため、来月は対策を講じたい。", "ので、根本的な解決が必要。",
    "ため、チームで議論したい。", "ので、プロセスの見直しが必要。", "。",
    "ため、優先的に取り組みたい。", "ので、仕組みを変えたい。"
]

# Try: 挑戦したいこと、新しく取り組みたいこと
TRY_INTROS = [
    "来月は、", "次のスプリントでは、", "挑戦したいこととして、", "新しく取り組みたいのは、",
    "試してみたいのは、", "改善のために、", "個人的に、", "チームとして、",
    "", "", ""
]

TRY_ACTIONS = [
    "新しいフレームワークの検証を", "ペアプログラミングの頻度を増やすことを",
    "自動テストのカバレッジ向上を", "技術ブログの執筆を", "OSSへのコントリビューションを",
    "新しい開発ツールの導入を", "コードレビューの質向上を", "リファクタリング週間の設定を",
    "社内勉強会の開催を", "モブプログラミングの実施を", "CI/CDパイプラインの改善を",
    "パフォーマンスチューニングを", "セキュリティ監査の実施を", "アーキテクチャの見直しを",
    "ドキュメント自動生成の導入を"
]

TRY_GOALS = [
    "進めたい", "実現したい", "挑戦したい", "取り組みたい", "試してみたい",
    "導入したい", "強化したい", "推進したい", "実践したい", "開始したい"
]

TRY_CLOSINGS = [
    "と考えている。", "と思っている。", "。", "と計画している。",
    "と決意している。", "つもりだ。", "予定だ。", "と目標にしている。"
]

# =============================================================================
# 2. 部会について
# =============================================================================

BUKAI_INTROS = [
    "今月の部会では、", "部会で印象に残ったのは、", "部会について、", "部会の内容は、",
    "今回の部会は、", "", "", ""
]

BUKAI_TOPICS = [
    "新プロジェクトの方針説明が", "技術選定の議論が", "組織変更のアナウンスが",
    "四半期の振り返りが", "新しい評価制度の説明が", "技術トレンドの共有が",
    "セキュリティインシデントの報告が", "開発プロセス改善の提案が",
    "他チームの成功事例の共有が", "新メンバーの紹介が", "予算計画の説明が",
    "顧客フィードバックの共有が", "技術的負債の現状報告が", "今後のロードマップの発表が"
]

BUKAI_IMPRESSIONS = [
    "非常に有益だった", "参考になった", "興味深かった", "刺激を受けた",
    "理解が深まった", "視野が広がった", "モチベーションが上がった",
    "共感できた", "新しい気づきがあった", "勉強になった", "考えさせられた"
]

BUKAI_REQUESTS = [
    "。今後も定期的に開催してほしい。", "。もう少し詳しく聞きたかった。",
    "。質疑応答の時間をもっと取ってほしい。", "。資料を事前共有してほしい。",
    "。もっと頻繁に開催してほしい。", "。", "。他部署の事例ももっと聞きたい。",
    "。ワークショップ形式も取り入れてほしい。", "。オンライン参加の環境を改善してほしい。"
]

# =============================================================================
# 3. サービス精神について
# =============================================================================

# Q1: サービス精神のイメージ (組み合わせ可能な要素に分解)
SERVICE_SPIRIT_PREFIXES = [
    "", "", "", "", "",  # 50% no prefix
    "私が考えるサービス精神とは、", "サービス精神とは、", "具体的には、",
    "日常業務で言えば、", "チームにおいては、", "顧客対応では、",
    "プロフェッショナルとして、", "組織の一員として、"
]

SERVICE_SPIRIT_CORE_CONCEPTS = [
    "相手の立場に立って考え、期待を超える価値を提供すること",
    "困っている人を見かけたら、自分から声をかけて手を差し伸べること",
    "顧客だけでなく、同僚やチームメンバーにも気配りをすること",
    "相手が求めていることを先回りして察知し、行動すること",
    "感謝の気持ちを忘れず、常に謙虚な姿勢で接すること",
    "自分の役割を超えて、チーム全体の成功のために動くこと",
    "相手の成功を自分のことのように喜び、サポートすること",
    "小さな気配りや心遣いを大切にすること",
    "相手の話をよく聞き、真摯に向き合うこと",
    "プロフェッショナルとして、最高の品質を提供すること",
    "困難な状況でも笑顔を絶やさず、前向きに対応すること",
    "相手の時間を尊重し、効率的にコミュニケーションすること",
    "自分の知識や経験を惜しみなく共有すること",
    "相手の成長を支援し、一緒に成長していくこと",
    "細部にまでこだわり、丁寧な仕事をすること",
    "相手の不安や悩みに寄り添い、解決策を一緒に考えること",
    "約束を守り、信頼関係を築くこと",
    "相手の立場や状況を理解し、柔軟に対応すること",
    "感謝を言葉で伝え、相手の貢献を認めること",
    "チーム全体の雰囲気を良くするために、積極的にコミュニケーションを取ること",
    "相手の期待を理解し、それを超える成果を出すこと",
    "困っている人に気づき、自然に手を差し伸べること",
    "相手の視点で物事を考え、最適な解決策を提案すること",
    "誠実に向き合い、信頼される存在になること",
    "相手の成功を心から喜び、共に成長を目指すこと",
    "細やかな配慮を忘れず、心地よい環境を作ること",
    "相手の話に耳を傾け、理解しようと努めること",
    "常に最善を尽くし、妥協しない姿勢を持つこと",
    "ポジティブな態度で接し、周囲を明るくすること",
    "相手の時間を大切にし、無駄を省くこと",
    "自分の経験を共有し、他者の成長を支援すること",
    "相手と共に成長し、互いに高め合うこと",
    "品質にこだわり、満足度の高い成果を提供すること",
    "相手の課題を自分事として捉え、解決に尽力すること",
    "信頼を築き、長期的な関係を構築すること",
    "状況に応じて柔軟に対応し、最適な方法を選ぶこと",
    "感謝の気持ちを表現し、良好な関係を維持すること",
    "チームの一体感を高め、協力し合える環境を作ること",
    "相手のニーズを深く理解し、的確に応えること",
    "率先して行動し、周囲の模範となること"
]

SERVICE_SPIRIT_SUFFIXES = [
    "", "", "", "", "",  # 50% no suffix
    "だと思います。", "が重要だと考えます。", "を心がけています。",
    "が基本だと思います。", "を実践したいです。", "が大切だと感じます。",
    "を意識しています。", "が本質だと思います。"
]

def get_service_spirit_concept_comment():
    """Generate service spirit concept comment with variations"""
    prefix = random.choice(SERVICE_SPIRIT_PREFIXES)
    core = random.choice(SERVICE_SPIRIT_CORE_CONCEPTS)
    suffix = random.choice(SERVICE_SPIRIT_SUFFIXES)
    return f"{prefix}{core}{suffix}"

# Q2: サービス精神を広めるための取り組み (組み合わせ可能な要素に分解)
SERVICE_INITIATIVE_PREFIXES = [
    "", "", "", "", "",  # 50% no prefix
    "サービス精神を広めるには、", "組織全体に浸透させるために、", "文化として定着させるには、",
    "実践を促進するために、", "具体的な施策として、", "効果的な方法として、"
]

SERVICE_INITIATIVE_CORE_IDEAS = [
    "サービス精神を体現した行動を評価制度に組み込み、表彰する仕組みを作る",
    "具体的な事例を社内で共有し、ベストプラクティスとして可視化する",
    "1on1や定期的なフィードバックの場で、サービス精神について対話する",
    "新入社員研修でサービス精神の重要性を伝え、文化として根付かせる",
    "リーダー層が率先してサービス精神を実践し、ロールモデルとなる",
    "サービス精神に関するワークショップや勉強会を定期的に開催する",
    "感謝を伝え合う文化を作るため、Thanksカードやピアボーナス制度を導入する",
    "顧客の声を社内で共有し、サービス精神の重要性を実感できるようにする",
    "チームビルディング活動を通じて、相互理解と信頼関係を深める",
    "サービス精神を行動指針やバリューに明文化し、全員で共有する",
    "失敗を責めず、挑戦を称賛する文化を作り、心理的安全性を高める",
    "他部署との交流機会を増やし、組織全体でサービス精神を共有する",
    "日々のコミュニケーションで「ありがとう」を言う習慣を定着させる",
    "サービス精神を発揮した人をMVPとして表彰する制度を作る",
    "顧客満足度やNPSを全員で共有し、サービス精神の成果を可視化する",
    "メンター制度を充実させ、先輩が後輩にサービス精神を伝える仕組みを作る",
    "社内アンケートでサービス精神の浸透度を測定し、改善サイクルを回す",
    "サービス精神に関する書籍や記事を社内で共有し、学びの機会を提供する",
    "困っている人を助けた事例を社内報で紹介し、文化として定着させる",
    "サービス精神を評価軸の一つとし、昇進や昇給の判断材料にする",
    "サービス精神を発揮した行動を朝会で共有し、認知度を高める",
    "サービス精神に関する目標を個人の目標設定に組み込む",
    "サービス精神を測定する指標を設定し、定量的に評価する",
    "サービス精神を発揮するための時間を業務時間内に確保する",
    "サービス精神に関する社内コンテストを開催し、優秀事例を表彰する",
    "サービス精神を発揮した人に特別なバッジや称号を付与する",
    "サービス精神を社外にも発信し、企業ブランドとして確立する",
    "サービス精神を発揮するための予算を確保し、自由に使えるようにする",
    "サービス精神を発揮した行動を定期的にレビューし、改善点を見つける",
    "サービス精神を発揮するための相談窓口を設置する",
    "サービス精神を発揮した行動を社内SNSでシェアし、拡散する",
    "サービス精神を発揮するためのツールやリソースを提供する",
    "サービス精神を発揮した行動を年次報告書にも掲載する",
    "サービス精神を発揮するための研修プログラムを開発する",
    "サービス精神を発揮した人を経営層が直接表彰する機会を設ける",
    "サービス精神を部署ごとに具体化し、それぞれの業務に合わせた定義を作る",
    "サービス精神を発揮する際の判断基準を明確にし、迷わず行動できるようにする",
    "サービス精神を継続的に学び、進化させる仕組みを作る",
    "サービス精神を発揮した結果を数値で可視化し、効果を実感できるようにする",
    "サービス精神を発揮するための環境整備(時間、リソース)を行う"
]

SERVICE_INITIATIVE_SUFFIXES = [
    "", "", "", "", "",  # 50% no suffix
    "ことが重要だと思います。", "ことを提案します。", "べきだと考えます。",
    "ことが効果的です。", "ことから始めたいです。", "ことが必要です。",
    "ことを推奨します。", "ことが有効だと思います。"
]

def get_service_spirit_initiative_comment():
    """Generate service spirit initiative comment with variations"""
    prefix = random.choice(SERVICE_INITIATIVE_PREFIXES)
    core = random.choice(SERVICE_INITIATIVE_CORE_IDEAS)
    suffix = random.choice(SERVICE_INITIATIVE_SUFFIXES)
    return f"{prefix}{core}{suffix}"

# =============================================================================
# 4. 組織・開発体制について
# =============================================================================

# Q1: 社内の課題 (組み合わせ可能な要素に分解)
ORG_ISSUES_PREFIXES = [
    "", "", "", "", "",  # 50% no prefix
    "現在の課題として、", "改善が必要なのは、", "問題だと感じているのは、",
    "組織として、", "率直に言うと、", "最大の課題は、", "懸念しているのは、"
]

ORG_ISSUES_CORE = [
    "部署間の連携が不足しており、情報のサイロ化が起きている",
    "意思決定のスピードが遅く、市場の変化に追いつけていない",
    "リソース配分が最適化されておらず、一部のチームに負荷が集中している",
    "情報の透明性が低く、経営層の意図が現場に伝わっていない",
    "評価制度が不明瞭で、何を頑張れば評価されるのかわからない",
    "キャリアパスが見えづらく、将来の成長イメージが持てない",
    "技術的な挑戦が評価されず、保守的な判断が優先される傾向がある",
    "新しいアイデアを提案しても、実現までのハードルが高い",
    "会議が多すぎて、開発に集中できる時間が確保できない",
    "ドキュメントや知識が属人化しており、引き継ぎが困難",
    "組織の目標と個人の目標が紐づいておらず、方向性が不明確",
    "人材育成の仕組みが不十分で、成長機会が限られている",
    "リモートワークとオフィスワークの格差があり、不公平感がある",
    "他部署との調整に時間がかかり、プロジェクトが遅延しがち",
    "失敗を許容する文化が弱く、チャレンジしづらい雰囲気がある",
    "コミュニケーションツールが多すぎて、情報が分散している",
    "組織の変化が速すぎて、現場がついていけていない",
    "経営層と現場の距離が遠く、意見が届きにくい",
    "評価のフィードバックが不十分で、成長につながっていない",
    "チーム間の競争が激しく、協力体制が築けていない",
    "業務の優先順位が頻繁に変わり、計画が立てにくい",
    "技術的な意思決定が遅く、競合に後れを取っている",
    "組織の文化が明文化されておらず、浸透していない",
    "新しいメンバーが定着しにくい環境になっている",
    "ワークライフバランスが取りにくく、離職率が高い",
    "イノベーションを生み出す仕組みが不足している",
    "部署ごとの目標が対立し、全体最適が図れていない",
    "情報共有の仕組みが整っておらず、同じ質問が繰り返される",
    "組織の意思決定プロセスが不透明で、納得感が低い",
    "キャリア支援の制度が不十分で、自己成長に頼っている"
]

ORG_ISSUES_SUFFIXES = [
    "", "", "", "", "",  # 50% no suffix
    "点です。", "ことが課題です。", "状況です。", "と感じています。",
    "ことが問題です。", "と思います。", "ことが懸念されます。"
]

def get_org_issue_comment():
    """Generate organization issue comment with variations"""
    prefix = random.choice(ORG_ISSUES_PREFIXES)
    core = random.choice(ORG_ISSUES_CORE)
    suffix = random.choice(ORG_ISSUES_SUFFIXES)
    return f"{prefix}{core}{suffix}"

# Q2: 開発体制についての意見 (組み合わせ可能な要素に分解)
DEV_STRUCTURE_PREFIXES = [
    "", "", "", "", "",  # 50% no prefix
    "開発体制については、", "現在の体制は、", "率直に言うと、", "個人的には、",
    "チーム構成について、", "開発フローについて、", "技術面では、"
]

DEV_STRUCTURE_CORE = [
    "チームの役割分担が明確で、責任範囲がはっきりしているのは良いが、柔軟性に欠ける面もある",
    "コードレビューのプロセスは機能しているが、レビュー待ち時間が長くボトルネックになっている",
    "スプリント計画は丁寧だが、計画に時間をかけすぎて開発時間が圧迫されている",
    "品質管理の仕組みはしっかりしているが、手動テストが多く効率が悪い",
    "使用ツールは充実しているが、ツールが多すぎて使いこなせていない",
    "チーム間の連携が弱く、重複した作業が発生している",
    "技術選定の自由度が低く、新しい技術を試しづらい",
    "デプロイフローは自動化されているが、本番環境への反映が慎重すぎて遅い",
    "ドキュメントの整備は進んでいるが、更新が追いついておらず古い情報が残っている",
    "リリースサイクルが長く、フィードバックを得るまでに時間がかかる",
    "テスト環境が本番と乖離しており、環境起因のバグが多い",
    "オンコール体制が整っているが、負担が特定のメンバーに偏っている",
    "技術的負債の返済時間が確保されておらず、負債が蓄積している",
    "新メンバーのオンボーディングプロセスが整備されているが、実践的な内容が不足している",
    "アジャイル開発を導入しているが、形骸化しており本質的な価値を得られていない",
    "CI/CDパイプラインは整っているが、ビルド時間が長く待ち時間が発生している",
    "モニタリングツールは導入されているが、アラートが多すぎて重要な通知を見逃す",
    "セキュリティ対策は実施されているが、開発速度を犠牲にしている面がある",
    "ペアプログラミングは推奨されているが、時間的余裕がなく実施できていない",
    "技術的な議論の場はあるが、意思決定までに時間がかかりすぎる",
    "開発環境は整っているが、ローカル環境のセットアップが複雑で時間がかかる",
    "コードの品質は高いが、過度な完璧主義でリリースが遅れがち",
    "チームの自律性は高いが、全体の方向性が揃っていない",
    "技術スタックは統一されているが、柔軟性に欠け新しい挑戦がしにくい",
    "開発プロセスは確立されているが、硬直的で改善提案が通りにくい",
    "リファクタリングの重要性は認識されているが、実際には後回しにされがち",
    "テストカバレッジは高いが、テストの保守コストが増大している",
    "ドキュメントは充実しているが、実際のコードと乖離している箇所がある",
    "技術的な知見は豊富だが、共有の仕組みが不十分で属人化している",
    "開発ツールは最新だが、学習コストが高く生産性向上に時間がかかる"
]

DEV_STRUCTURE_SUFFIXES = [
    "", "", "", "", "",  # 50% no suffix
    "と感じています。", "と思います。", "状況です。", "のが現状です。",
    "と考えています。", "印象です。", "と評価しています。"
]

def get_dev_structure_comment():
    """Generate dev structure comment with variations"""
    prefix = random.choice(DEV_STRUCTURE_PREFIXES)
    core = random.choice(DEV_STRUCTURE_CORE)
    suffix = random.choice(DEV_STRUCTURE_SUFFIXES)
    return f"{prefix}{core}{suffix}"

# =============================================================================
# 5. 1on1・ユニット活動
# =============================================================================

# Q1: 1on1の実施方法について (組み合わせ可能な要素に分解)
ONEONONE_CURRENT_PREFIXES = [
    "", "", "", "", "",  # 50% no prefix
    "現状の1on1は、", "1on1について、", "率直に言うと、", "個人的には、",
    "今の1on1は、", "1on1の運用は、"
]

ONEONONE_CURRENT_CORE = [
    "話しやすい雰囲気で、率直に意見を言える点は良い",
    "定期的に実施されており、継続的な対話ができている",
    "上長が真摯に話を聞いてくれるので、安心して相談できる",
    "キャリアの相談ができる貴重な機会になっている",
    "頻度が適切で、タイミングよく悩みを相談できる",
    "時間が短く、深い話ができないことが多い",
    "業務の進捗確認に終始してしまい、本質的な対話ができていない",
    "頻度が低く、相談したいタイミングで実施されないことがある",
    "形式的になっており、表面的な会話で終わってしまう",
    "上長が忙しそうで、本音を話しづらい雰囲気がある",
    "評価面談と混同されており、率直に話しづらい",
    "アジェンダが不明確で、何を話せばいいかわからない",
    "フィードバックが一方的で、対話になっていない",
    "プライベートな話題が多く、仕事の相談がしづらい",
    "内容が記録されず、次回に活かされていない",
    "時間が確保されているが、内容が薄く有意義に感じられない",
    "上長の都合でキャンセルされることが多く、優先度が低いと感じる",
    "話したいことを事前に準備する時間がなく、場当たり的になる",
    "上長が一方的にアドバイスするだけで、自分の意見を聞いてもらえない",
    "成長支援というより、問題点の指摘に終始している",
    "心理的安全性が低く、本当の悩みを打ち明けられない",
    "時間が長すぎて、何を話せばいいか困ることがある",
    "上長との相性が合わず、有意義な時間にならない",
    "具体的なアクションにつながらず、話して終わりになっている",
    "他のメンバーとの1on1の質に差があり、不公平感がある",
    "オンラインでの実施が多く、対面での深い対話ができていない",
    "業務時間外に設定されることがあり、負担に感じる",
    "上長が話を遮ることが多く、最後まで話せない",
    "同じ話題が繰り返され、新しい気づきが得られない",
    "上長の経験に基づくアドバイスが、自分の状況に合わないことがある"
]

ONEONONE_CURRENT_SUFFIXES = [
    "", "", "", "", "",  # 50% no suffix
    "と感じています。", "と思います。", "状況です。", "のが現状です。",
    "と評価しています。", "印象です。", "と考えています。"
]

def get_oneonone_current_comment():
    """Generate 1on1 current status comment with variations"""
    prefix = random.choice(ONEONONE_CURRENT_PREFIXES)
    core = random.choice(ONEONONE_CURRENT_CORE)
    suffix = random.choice(ONEONONE_CURRENT_SUFFIXES)
    return f"{prefix}{core}{suffix}"

# Q2: 1on1の改善案 (組み合わせ可能な要素に分解)
ONEONONE_IMPROVEMENT_PREFIXES = [
    "", "", "", "", "",  # 50% no prefix
    "改善案として、", "より有意義にするために、", "提案としては、", "個人的には、",
    "もっと良くするために、", "具体的には、", "効果的な方法として、"
]

ONEONONE_IMPROVEMENT_CORE = [
    "話すトピックを事前に共有し、準備してから臨めるようにする",
    "時間を延長し、じっくり対話できる時間を確保する",
    "評価とは切り離し、成長支援のための場であることを明確にする",
    "上長からのフィードバックだけでなく、双方向の対話を重視する",
    "キャリアプランを一緒に考える時間を設ける",
    "頻度を増やし、タイムリーに相談できるようにする",
    "1on1の目的を再確認し、形式的にならないようにする",
    "話した内容を記録し、次回に振り返れるようにする",
    "業務の進捗確認は別の場で行い、1on1は対話に集中する",
    "上長へのリクエストを事前に伝えられる仕組みを作る",
    "心理的安全性を高めるため、評価に影響しないことを明言する",
    "1on1のガイドラインを作成し、質を均一化する",
    "外部のコーチやメンターとの1on1も選択肢に加える",
    "オンラインとオフラインを選べるようにし、話しやすい環境を提供する",
    "1on1の満足度を定期的に測定し、改善サイクルを回す",
    "具体的なアクションアイテムを設定し、次回にフォローアップする",
    "上長以外のメンバーとの1on1も実施し、多様な視点を得る",
    "1on1の時間を業務時間内に確保し、優先度を高める",
    "上長が傾聴のスキルを学ぶ研修を実施する",
    "1on1の内容をテンプレート化し、話すべきトピックを明確にする",
    "成功事例や失敗事例を共有し、学びの機会にする",
    "1on1の効果を測定し、ROIを可視化する",
    "1on1の場所を工夫し、リラックスして話せる環境を作る",
    "1on1の後に振り返りの時間を設け、気づきを整理する",
    "1on1の内容を匿名でフィードバックできる仕組みを作る",
    "1on1で話した内容を人事にも共有し(本人の同意のもと)、組織改善に活用する",
    "1on1のキャンセルを極力避け、定期的に実施する文化を作る",
    "1on1の日程を柔軟に調整できるようにし、参加しやすくする",
    "1on1の内容を本人が主導で決められるようにする",
    "1on1で業務以外の話題も取り上げ、信頼関係を深める"
]

ONEONONE_IMPROVEMENT_SUFFIXES = [
    "", "", "", "", "",  # 50% no suffix
    "ことが重要だと思います。", "ことを提案します。", "べきだと考えます。",
    "ことが効果的です。", "ことから始めたいです。", "ことが必要です。",
    "ことを推奨します。", "ことが有効だと思います。"
]

def get_oneonone_improvement_comment():
    """Generate 1on1 improvement comment with variations"""
    prefix = random.choice(ONEONONE_IMPROVEMENT_PREFIXES)
    core = random.choice(ONEONONE_IMPROVEMENT_CORE)
    suffix = random.choice(ONEONONE_IMPROVEMENT_SUFFIXES)
    return f"{prefix}{core}{suffix}"

# Q3: ユニット活動への期待 (組み合わせ可能な要素に分解)
UNIT_ACTIVITY_PREFIXES = [
    "", "", "", "", "",  # 50% no prefix
    "ユニット活動には、", "横断組織に期待するのは、", "ユニット活動を通じて、",
    "個人的には、", "ユニット活動で、", "具体的には、"
]

UNIT_ACTIVITY_CORE = [
    "他部署のメンバーと交流し、視野を広げる機会を得たい",
    "技術スタックや知見を共有し、組織全体のレベルアップに繋げたい",
    "部署を超えた課題解決に取り組み、組織の壁を取り払いたい",
    "新しいスキルを学ぶ機会を提供してほしい",
    "イノベーションを生み出すための実験的な取り組みをしたい",
    "普段関わらないメンバーとのネットワークを構築したい",
    "組織全体の目標達成に貢献できる活動をしたい",
    "自分の専門外の領域に挑戦する機会を得たい",
    "ベストプラクティスを共有し、組織全体の効率を上げたい",
    "若手とベテランが交流し、知識の伝承を促進したい",
    "社内の課題を発見し、改善提案をする場にしたい",
    "技術的な議論を深め、エンジニアリングカルチャーを醸成したい",
    "キャリアの選択肢を広げるための情報を得たい",
    "組織の方向性を理解し、自分の役割を再確認したい",
    "楽しみながら学べる、活気のある活動にしたい",
    "部署間の情報格差を解消し、全体最適を図りたい",
    "新しい技術やツールを試す実験の場として活用したい",
    "他部署の業務を理解し、協力しやすい関係を築きたい",
    "組織の文化を共創し、一体感を高めたい",
    "自分の強みを活かし、組織に貢献できる機会を得たい",
    "多様な視点を学び、視野を広げたい",
    "組織の課題を可視化し、解決策を提案したい",
    "クロスファンクショナルなプロジェクトに参加したい",
    "組織の未来を一緒に考える場にしたい",
    "自分の成長を加速させる学びの機会を得たい",
    "組織の変革を推進する一員になりたい",
    "他部署のメンバーから刺激を受け、モチベーションを高めたい",
    "組織の強みと弱みを理解し、改善に貢献したい",
    "新しい挑戦を後押ししてもらえる環境を作りたい",
    "組織全体のビジョンを共有し、方向性を揃えたい"
]

UNIT_ACTIVITY_SUFFIXES = [
    "", "", "", "", "",  # 50% no suffix
    "と考えています。", "と思います。", "と期待しています。", "と希望します。",
    "ことを求めます。", "ことを期待します。", "と願っています。"
]

def get_unit_activity_comment():
    """Generate unit activity expectation comment with variations"""
    prefix = random.choice(UNIT_ACTIVITY_PREFIXES)
    core = random.choice(UNIT_ACTIVITY_CORE)
    suffix = random.choice(UNIT_ACTIVITY_SUFFIXES)
    return f"{prefix}{core}{suffix}"

# =============================================================================
# Small Voices & Dense Clusters
# =============================================================================

SMALL_VOICES = {
    "kpt": [
        "【Keep】上司のパワハラが減ったこと。【Problem】まだ完全になくなっていない。【Try】外部の相談窓口を利用する。",
        "【Keep】残業が減った。【Problem】持ち帰り仕事が増えている。【Try】労働時間の実態調査を提案する。",
        "【Keep】特になし。【Problem】評価が不透明で納得できない。【Try】評価基準の開示を求める。",
        "【Keep】リモートワークが認められた。【Problem】監視ツールの導入が不快。【Try】信頼に基づく働き方への転換を求める。"
    ],
    "bukai": [
        "部会で報告された売上数字が、実際の現場感覚と大きく乖離している。数字の根拠を明確にしてほしい。",
        "重要な意思決定が既に決まった後に報告されるだけで、現場の意見が反映されていない。",
        "部会の内容が形式的で、本質的な議論がされていない。もっとオープンな対話の場にしてほしい。",
        "一部の役員の発言が威圧的で、質問しづらい雰囲気がある。心理的安全性を確保してほしい。"
    ],
    "service_spirit_concept": [
        "サービス精神とは、顧客や同僚を尊重し、誠実に向き合うこと。しかし、現状は形だけのサービスになっていないか懸念している。",
        "サービス精神を強調するあまり、過度な負担や無理な要求を正当化する口実にされていないか心配。",
        "サービス精神は大切だが、まずは従業員が健康で働ける環境を整えることが先決だと思う。",
        "顧客へのサービス精神は重要だが、社内の人間関係においても同様に尊重し合う文化が必要。"
    ],
    "service_spirit_initiative": [
        "サービス精神を評価する前に、ハラスメントや不当な扱いをなくす取り組みを優先すべき。",
        "サービス精神を強要するのではなく、自然に発揮できる環境を整えることが重要。",
        "サービス精神の名のもとに、サービス残業や無償労働が美化されないよう注意が必要。",
        "サービス精神を広めるには、まず経営層が従業員に対してサービス精神を示すべき。"
    ],
    "org_issue": [
        "組織の最大の課題は、意見を言っても変わらないという諦めの空気が蔓延していること。",
        "情報の透明性が低く、重要な決定が密室で行われている。もっとオープンにすべき。",
        "評価制度が不公平で、成果よりも上司との関係性が重視されている。",
        "ハラスメントの相談窓口が機能しておらず、被害者が泣き寝入りしている現状がある。"
    ],
    "dev_structure": [
        "開発体制は表面上は整っているが、実際には属人化が激しく、特定の人に依存している。",
        "品質管理と言いながら、実際には納期優先でテストが疎かにされている。",
        "技術的負債が膨大に蓄積しているのに、返済の時間が全く確保されていない。",
        "セキュリティ対策が不十分で、重大なインシデントが起きるリスクがある。"
    ],
    "oneonone_current": [
        "1on1が評価のための情報収集の場になっており、本音を話せない。",
        "上長が一方的に話すだけで、こちらの話を聞いてくれない。",
        "1on1で相談した内容が、他のメンバーに漏れていた。守秘義務を徹底してほしい。",
        "1on1の時間が業務の進捗確認だけで終わり、キャリアの相談ができない。"
    ],
    "oneonone_improvement": [
        "1on1を評価と完全に切り離し、安心して話せる環境を作る。",
        "上長以外のメンターやコーチとも話せる選択肢を提供する。",
        "1on1の内容が評価に影響しないことを明文化し、周知する。",
        "守秘義務を徹底し、信頼関係を築ける仕組みを作る。"
    ],
    "unit_activity": [
        "ユニット活動が形骸化しており、参加する意義を感じられない。目的を明確にしてほしい。",
        "ユニット活動への参加が強制的で、業務の負担になっている。任意参加にすべき。",
        "ユニット活動の成果が評価されず、ボランティア扱いされている。",
        "ユニット活動で得た知見が組織に還元されず、活動が無駄になっている。"
    ]
}

DENSE_CLUSTERS = {
    "kpt_keep": [
        {"topic": "技術的成果", "templates": [
            "【Keep】新しいフレームワークの導入がスムーズに進んだ。【Problem】ドキュメントが不足している。【Try】ドキュメント整備を進める。",
            "【Keep】自動テストの拡充で品質が向上した。【Problem】テスト実行時間が長い。【Try】並列実行を導入する。",
            "【Keep】リファクタリングで保守性が改善した。【Problem】まだ技術的負債が残っている。【Try】継続的にリファクタリングする。",
            "【Keep】CI/CDパイプラインの改善でデプロイが高速化した。【Problem】たまに失敗する。【Try】安定性を向上させる。",
            "【Keep】コードレビューの質が向上した。【Problem】レビュー待ち時間が長い。【Try】レビュアーを増やす。"
        ]},
        {"topic": "チームワーク", "templates": [
            "【Keep】ペアプログラミングで知見が共有された。【Problem】時間がかかる。【Try】効率的な進め方を模索する。",
            "【Keep】定期的な1on1でコミュニケーションが改善した。【Problem】頻度が少ない。【Try】隔週から毎週に増やす。",
            "【Keep】チーム内の心理的安全性が高まった。【Problem】他チームとの連携が弱い。【Try】部署横断の交流会を開催する。",
            "【Keep】スプリントレトロスペクティブで改善が進んだ。【Problem】実行に移せていない項目がある。【Try】アクションアイテムを明確にする。",
            "【Keep】新メンバーのオンボーディングがスムーズだった。【Problem】ドキュメントが古い。【Try】ドキュメントを更新する。"
        ]},
        {"topic": "プロセス改善", "templates": [
            "【Keep】スプリント計画の精度が向上した。【Problem】見積もりが甘い。【Try】過去データを分析する。",
            "【Keep】デイリースタンドアップが効率化された。【Problem】時間が長い。【Try】15分以内に制限する。",
            "【Keep】ドキュメント整備が進んだ。【Problem】更新が追いついていない。【Try】定期的な見直しを行う。",
            "【Keep】非同期コミュニケーションが定着した。【Problem】情報が分散している。【Try】情報を一元化する。",
            "【Keep】技術的負債の返済が進んだ。【Problem】まだ多く残っている。【Try】返済時間を確保する。"
        ]}
    ],
    "kpt_problem": [
        {"topic": "時間管理", "templates": [
            "【Keep】チームの雰囲気が良い。【Problem】会議が多すぎて開発時間が足りない。【Try】会議を削減する。",
            "【Keep】コミュニケーションが活発。【Problem】割り込みが多い。【Try】集中時間を設ける。",
            "【Keep】情報共有が進んだ。【Problem】情報過多で重要な情報が埋もれる。【Try】情報を整理する。",
            "【Keep】柔軟な働き方ができる。【Problem】オンオフの切り替えが難しい。【Try】勤務時間を明確にする。",
            "【Keep】リモートワークが定着した。【Problem】コミュニケーションコストが増えた。【Try】ツールを改善する。"
        ]},
        {"topic": "技術的課題", "templates": [
            "【Keep】新機能のリリースが順調。【Problem】技術的負債が増えている。【Try】リファクタリング時間を確保する。",
            "【Keep】開発速度が向上した。【Problem】品質が低下している。【Try】テストを強化する。",
            "【Keep】デプロイが自動化された。【Problem】本番環境でのバグが多い。【Try】ステージング環境を改善する。",
            "【Keep】新しい技術を導入できた。【Problem】学習コストが高い。【Try】勉強会を開催する。",
            "【Keep】モニタリングが充実した。【Problem】アラートが多すぎる。【Try】閾値を見直す。"
        ]},
        {"topic": "組織的課題", "templates": [
            "【Keep】チーム内の連携は良好。【Problem】他部署との連携が弱い。【Try】定期的な情報共有会を開催する。",
            "【Keep】技術的な挑戦ができる。【Problem】評価されにくい。【Try】評価基準を見直す。",
            "【Keep】自由な雰囲気がある。【Problem】方向性が不明確。【Try】ビジョンを明確にする。",
            "【Keep】新しいアイデアを出しやすい。【Problem】実現までのハードルが高い。【Try】意思決定を迅速化する。",
            "【Keep】フラットな組織。【Problem】責任の所在が不明確。【Try】役割を明確にする。"
        ]}
    ],
    "kpt_try": [
        {"topic": "技術的挑戦", "templates": [
            "【Keep】安定した開発ができている。【Problem】新しい技術に触れる機会が少ない。【Try】新技術の検証時間を確保する。",
            "【Keep】既存システムの保守は順調。【Problem】モダンな技術スタックに移行できていない。【Try】段階的なマイグレーションを計画する。",
            "【Keep】チームの技術力は高い。【Problem】最新トレンドに追いついていない。【Try】技術ブログや勉強会に参加する。",
            "【Keep】品質は維持できている。【Problem】開発効率が悪い。【Try】開発ツールを見直す。",
            "【Keep】セキュリティ意識は高い。【Problem】自動化が不十分。【Try】セキュリティスキャンを導入する。"
        ]},
        {"topic": "スキルアップ", "templates": [
            "【Keep】業務はこなせている。【Problem】成長実感が薄い。【Try】新しいスキルを学ぶ時間を確保する。",
            "【Keep】チーム内で知見共有ができている。【Problem】外部の知見に触れる機会が少ない。【Try】カンファレンスに参加する。",
            "【Keep】OJTで学べている。【Problem】体系的な学習ができていない。【Try】オンライン学習サービスを活用する。",
            "【Keep】先輩からのフィードバックがある。【Problem】自分の強みがわからない。【Try】360度フィードバックを受ける。",
            "【Keep】実務で経験を積めている。【Problem】資格取得の時間がない。【Try】資格取得支援制度を活用する。"
        ]},
        {"topic": "チーム改善", "templates": [
            "【Keep】チームの雰囲気は良い。【Problem】もっと活性化したい。【Try】チームビルディング活動を企画する。",
            "【Keep】コミュニケーションは取れている。【Problem】深い議論ができていない。【Try】技術的な議論の場を設ける。",
            "【Keep】協力体制はある。【Problem】もっと効率化したい。【Try】ペアプログラミングを増やす。",
            "【Keep】情報共有はできている。【Problem】ドキュメントが不足。【Try】ドキュメント作成を習慣化する。",
            "【Keep】定期的な振り返りをしている。【Problem】改善が進まない。【Try】アクションアイテムを明確にする。"
        ]}
    ]
}

def get_small_voice_comment(category="kpt"):
    """Returns a specific outlier comment."""
    cat = category if category in SMALL_VOICES else "kpt"
    return random.choice(SMALL_VOICES[cat])

def get_dense_cluster_comment(category="kpt_keep"):
    """Returns a comment from a specific topic cluster."""
    cat = category if category in DENSE_CLUSTERS else "kpt_keep"
    cluster = random.choice(DENSE_CLUSTERS[cat])
    return random.choice(cluster["templates"])

def generate_mixed_comments_list(count, category, generator_func):
    """
    Generates a list of UNIQUE comments with balanced cluster distribution:
    - 5% Small Voice (Outliers)
    - 80% Dense Clusters (BALANCED)
    - 15% General Noise
    """
    n_small_voices = max(int(count * 0.05), 1)
    n_dense_clusters = int(count * 0.80)
    n_general = count - n_small_voices - n_dense_clusters
    
    comments = []
    seen = set()
    
    # 1. ADD SMALL VOICES
    cat = category if category in SMALL_VOICES else list(SMALL_VOICES.keys())[0]
    available_small_voices = SMALL_VOICES[cat].copy()
    random.shuffle(available_small_voices)
    
    for i in range(min(n_small_voices, len(available_small_voices))):
        comment = available_small_voices[i]
        if comment not in seen:
            comments.append(comment)
            seen.add(comment)
    
    # 2. ADD DENSE CLUSTERS - WITH BALANCED DISTRIBUTION
    cat = category if category in DENSE_CLUSTERS else list(DENSE_CLUSTERS.keys())[0]
    if cat in DENSE_CLUSTERS:
        available_clusters = DENSE_CLUSTERS[cat]
        
        if available_clusters:
            num_clusters = len(available_clusters)
            comments_per_cluster = n_dense_clusters // num_clusters
            remainder = n_dense_clusters % num_clusters
            
            cluster_assignments = []
            for i, cluster in enumerate(available_clusters):
                cluster_count = comments_per_cluster + (1 if i < remainder else 0)
                cluster_assignments.extend([cluster] * cluster_count)
            
            random.shuffle(cluster_assignments)
            
            cluster_template_indices = {i: list(range(len(cluster["templates"]))) for i, cluster in enumerate(available_clusters)}
            for cluster_idx, cluster in enumerate(available_clusters):
                random.shuffle(cluster_template_indices[cluster_idx])
            
            for cluster in cluster_assignments[:n_dense_clusters]:
                cluster_idx = available_clusters.index(cluster)
                templates = cluster["templates"]
                
                max_attempts = 50
                for attempt in range(max_attempts):
                    if cluster_template_indices[cluster_idx]:
                        template_idx = cluster_template_indices[cluster_idx].pop(0)
                        comment = templates[template_idx]
                        
                        if not cluster_template_indices[cluster_idx]:
                            cluster_template_indices[cluster_idx] = list(range(len(templates)))
                            random.shuffle(cluster_template_indices[cluster_idx])
                    else:
                        comment = random.choice(templates)
                    
                    if comment in seen:
                        continue
                    
                    if comment not in seen:
                        comments.append(comment)
                        seen.add(comment)
                        break
                else:
                    for _ in range(20):
                        comment = generator_func()
                        if comment not in seen:
                            comments.append(comment)
                            seen.add(comment)
                            break
    
    # 3. ADD GENERAL NOISE
    attempts = 0
    max_attempts = n_general * 10
    while len(comments) < count and attempts < max_attempts:
        comment = generator_func()
        if comment not in seen:
            comments.append(comment)
            seen.add(comment)
        attempts += 1
    
    # Fill remaining
    fill_attempts = 0
    max_fill_attempts = 1000
    while len(comments) < count and fill_attempts < max_fill_attempts:
        comment = generator_func()
        if comment not in seen:
            comments.append(comment)
            seen.add(comment)
        fill_attempts += 1
    
    while len(comments) < count:
        comments.append(generator_func())
    
    random.shuffle(comments)
    return comments[:count]

# =============================================================================
# Generator Functions
# =============================================================================

def get_kpt_keep_comment():
    parts = [KEEP_INTROS, KEEP_SUBJECTS, KEEP_OUTCOMES, KEEP_CLOSINGS]
    return generate_combinatorial_sentence(parts)

def get_kpt_problem_comment():
    parts = [PROBLEM_INTROS, PROBLEM_SUBJECTS, PROBLEM_ISSUES, PROBLEM_CLOSINGS]
    return generate_combinatorial_sentence(parts)

def get_kpt_try_comment():
    parts = [TRY_INTROS, TRY_ACTIONS, TRY_GOALS, TRY_CLOSINGS]
    return generate_combinatorial_sentence(parts)


def get_bukai_comment():
    parts = [BUKAI_INTROS, BUKAI_TOPICS, BUKAI_IMPRESSIONS, BUKAI_REQUESTS]
    return generate_combinatorial_sentence(parts)

# =============================================================================
# CSV Generation
# =============================================================================

def generate_csv_files():
    # 1. KPT
    print("Generating KPT data...")
    keep_comments = generate_mixed_comments_list(NUM_ROWS, "kpt_keep", get_kpt_keep_comment)
    problem_comments = generate_mixed_comments_list(NUM_ROWS, "kpt_problem", get_kpt_problem_comment)
    try_comments = generate_mixed_comments_list(NUM_ROWS, "kpt_try", get_kpt_try_comment)
    
    kpt_data = []
    for i in range(NUM_ROWS):
        kpt_data.append({
            "日時": generate_random_date(),
            "【Keep】今月の業務で「良かったこと」や「今後も継続したいこと」": keep_comments[i],
            "【Problem】業務で「困ったこと」や「改善したいこと」": problem_comments[i],
            "【Try】来月「挑戦したいこと」や「新しく取り組みたいこと」": try_comments[i]
        })
    pd.DataFrame(kpt_data).to_csv(os.path.join(OUTPUT_DIR, "kpt.csv"), index=False, encoding="utf-8-sig")
    
    # 2. 部会
    print("Generating Bukai data...")
    bukai_comments = generate_mixed_comments_list(NUM_ROWS, "bukai", get_bukai_comment)
    
    bukai_data = []
    for i in range(NUM_ROWS):
        bukai_data.append({
            "日時": generate_random_date(),
            "今月の部会の感想": bukai_comments[i]
        })
    pd.DataFrame(bukai_data).to_csv(os.path.join(OUTPUT_DIR, "bukai.csv"), index=False, encoding="utf-8-sig")
    
    # 3. サービス精神
    print("Generating Service Spirit data...")
    concept_comments = generate_mixed_comments_list(NUM_ROWS, "service_spirit_concept", get_service_spirit_concept_comment)
    initiative_comments = generate_mixed_comments_list(NUM_ROWS, "service_spirit_initiative", get_service_spirit_initiative_comment)
    
    service_data = []
    for i in range(NUM_ROWS):
        service_data.append({
            "日時": generate_random_date(),
            "「サービス精神」という言葉から、どのような行動や考え方を思い浮かべますか?": concept_comments[i],
            "サービス精神を社内で広めていくために、どのような取り組みが必要だと思いますか?": initiative_comments[i]
        })
    pd.DataFrame(service_data).to_csv(os.path.join(OUTPUT_DIR, "service_spirit.csv"), index=False, encoding="utf-8-sig")
    
    # 4. 組織・開発体制
    print("Generating Organization data...")
    org_issue_comments = generate_mixed_comments_list(NUM_ROWS, "org_issue", get_org_issue_comment)
    dev_structure_comments = generate_mixed_comments_list(NUM_ROWS, "dev_structure", get_dev_structure_comment)
    
    org_data = []
    for i in range(NUM_ROWS):
        org_data.append({
            "日時": generate_random_date(),
            "現在の「社内の課題」は何だと思いますか?": org_issue_comments[i],
            "現在の「開発体制」について、率直にどう思われますか?": dev_structure_comments[i]
        })
    pd.DataFrame(org_data).to_csv(os.path.join(OUTPUT_DIR, "organization.csv"), index=False, encoding="utf-8-sig")
    
    # 5. 1on1・ユニット活動
    print("Generating 1on1 & Unit Activity data...")
    oneonone_current_comments = generate_mixed_comments_list(NUM_ROWS, "oneonone_current", get_oneonone_current_comment)
    oneonone_improvement_comments = generate_mixed_comments_list(NUM_ROWS, "oneonone_improvement", get_oneonone_improvement_comment)
    unit_activity_comments = generate_mixed_comments_list(NUM_ROWS, "unit_activity", get_unit_activity_comment)
    
    oneonone_data = []
    for i in range(NUM_ROWS):
        oneonone_data.append({
            "日時": generate_random_date(),
            "現状の「1on1」の実施方法についてどう思われますか?": oneonone_current_comments[i],
            "1on1をより有意義にするために、どのように改善すると良いと思いますか?": oneonone_improvement_comments[i],
            "「ユニット活動(横断組織)」に対し、何を求めますか?": unit_activity_comments[i]
        })
    pd.DataFrame(oneonone_data).to_csv(os.path.join(OUTPUT_DIR, "oneonone_unit.csv"), index=False, encoding="utf-8-sig")
    
    print(f"✅ Generated data: All files have {NUM_ROWS} rows.")

# --- Main ---
if __name__ == "__main__":
    print("🚀 Starting new forms test data generation...")
    
    generate_csv_files()
    
    print("\n✨ Data generation completed!")
    print(f"Files created in: {OUTPUT_DIR}")
    print("- kpt.csv")
    print("- bukai.csv")
    print("- service_spirit.csv")
    print("- organization.csv")
    print("- oneonone_unit.csv")
