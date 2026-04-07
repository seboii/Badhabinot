export type ActivityItemResponse = {
  id: string
  activity_type: string
  category: 'ALERT' | 'REMINDER' | 'MANUAL' | 'SYSTEM'
  title: string
  message: string
  confidence: number | null
  occurred_at: string
}

export type AnalyzeFrameRequest = {
  session_id: string
  frame_id: string
  captured_at: string
  image_base64: string
  image_content_type: string
}

export type AnalyzeFrameResponse = {
  analysis_id: string
  session_id: string
  frame_id: string
  subject_present: boolean
  posture_state: string
  behavior_type: string
  confidence: number
  processed_at: string
  summary: string
  recommendation: string
  events: BehaviorEventResponse[]
  generated_reminders: ReminderEventResponse[]
  processing: {
    frame_width: number
    frame_height: number
    brightness_mean: number
    edge_density: number
    focus_score: number
    posture_risk_score: number
    vision_latency_ms: number
    ai_latency_ms: number
    scores: Record<string, number>
  }
  model: {
    provider: string
    name: string
    mode: string
  }
}

export type BehaviorEventResponse = {
  event_id: string
  analysis_id: string
  session_id: string | null
  event_type: string
  detector: string
  confidence: number
  severity: 'low' | 'medium' | 'high'
  interpretation: string
  recommendation_hint: string
  evidence: Record<string, unknown>
  occurred_at: string
}

export type ReminderEventResponse = {
  reminder_id: string
  session_id: string | null
  reminder_type: string
  source: string
  severity: 'low' | 'medium' | 'high'
  message: string
  trigger_reason: string
  metadata: Record<string, unknown>
  occurred_at: string
}

export type SessionStartRequest = {
  client_surface: string
  device_type: string
}

export type SessionStartResponse = {
  session_id: string
  status: string
  started_at: string
}

export type SessionStopResponse = {
  session_id: string
  status: string
  ended_at: string
}

export type DashboardResponse = {
  monitoring_active: boolean
  active_session_id: string | null
  model_mode: string
  privacy_mode: string
  analysis_enabled: boolean
  streak_days: number
  alert_count_today: number
  reminder_count_today: number
  water_progress_ml: number
  water_goal_ml: number
  latest_activity: ActivityItemResponse | null
  recent_activities: ActivityItemResponse[]
  generated_at: string
}

export type HydrationLogRequest = {
  amount_ml: number
  source: string
  session_id?: string
  occurred_at?: string
}

export type HydrationLogResponse = {
  hydration_log_id: string
  amount_ml: number
  source: string
  occurred_at: string
}

export type ReminderTriggerRequest = {
  reminder_type: string
  message?: string
  session_id?: string
  occurred_at?: string
}

export type WeeklyTrendPointResponse = {
  day: string
  alert_count: number
  reminder_count: number
  hydration_count: number
}

export type WeeklyTrendResponse = {
  from: string
  to: string
  points: WeeklyTrendPointResponse[]
}

export type DailyReportResponse = {
  report_id: string
  report_date: string
  analyses_completed: number
  posture_alert_count: number
  hand_movement_count: number
  smoking_like_count: number
  reminder_count: number
  hydration_progress_ml: number
  water_goal_ml: number
  poor_posture_ratio: number
  summary: string
  recommendations: string[]
  key_behavior_events: BehaviorEventResponse[]
  reminders: ReminderEventResponse[]
  timeline: ActivityItemResponse[]
  generated_at: string
}

export type ChatRequest = {
  conversation_id?: string | null
  message: string
}

export type ChatMessageResponse = {
  message_id: string
  conversation_id: string
  role: 'user' | 'assistant'
  content: string
  created_at: string
  metadata: Record<string, unknown>
}

export type ChatResponse = {
  conversation_id: string
  message_id: string
  answer: string
  grounded_facts: string[]
  follow_up_suggestions: string[]
  recent_messages: ChatMessageResponse[]
  model: {
    provider: string
    name: string
    mode: string
  }
}

export type ChatHistoryResponse = {
  conversation_id: string | null
  recent_messages: ChatMessageResponse[]
}
