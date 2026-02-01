export interface AnalysisResultItem {
  sub_topic: string;
  // sentiment removed
  summary: string;
  original_text: string;
  x: number;
  y: number;
  small_voice_score?: number; // NEW
}

export interface CommentItem {
  id: number;
  content: string;
  user_id: number;
  user_name: string;
  is_anonymous: boolean;
  created_at: string;
  likes_count: number;
  parent_id: number | null;
  children?: CommentItem[]; // For frontend tree structure
  liked_by_current_user?: boolean; // Optional if we track this
}

export interface SessionDetail {
  id: number;
  title: string;
  theme: string;
  created_at: string;
  is_published: boolean;
  report_content: string | null;
  results: AnalysisResultItem[];
  comments: CommentItem[];
  comment_analysis?: string; // If available in API
  is_comment_analysis_published?: boolean;
}

export interface SurveySummary {
  id: number;
  title: string;
  uuid: string;
  is_active: boolean;
  approval_status: string;
  rejection_reason?: string;
  description?: string;
  created_by?: number;
}
