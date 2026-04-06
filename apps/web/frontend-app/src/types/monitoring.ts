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
  processing: {
    frame_width?: number
    frame_height?: number
    brightness_mean?: number
    edge_density?: number
    vision_latency_ms?: number
    ai_latency_ms?: number
    scores?: Record<string, number>
  }
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

