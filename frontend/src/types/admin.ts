export type AdminUserSummary = {
  id: string
  email: string
  display_name: string | null
  role: string
  status: string
  created_at: string
  last_login_at: string | null
}

export type AdminUserListResponse = {
  items: AdminUserSummary[]
  total: number
  page: number
  size: number
}

export type AdminUserDetail = {
  id: string
  email: string
  role: string
  status: string
  created_at: string
  last_login_at: string | null
  profile: {
    display_name: string
    timezone: string
    locale: string
  } | null
  settings: {
    sensitivity: string
    model_mode: string
    local_model_name: string
    ollama_base_url: string
    chat_persona: string
    water_goal_ml: number
    water_interval_min: number
    exercise_interval_min: number
    notifications_enabled: boolean
  } | null
  consents: {
    privacy_policy_accepted: boolean
    camera_monitoring_accepted: boolean
    remote_inference_accepted: boolean
  } | null
  stats: {
    sessions: number
    analyses: number
    events: number
    reports: number
    chat_messages: number
  }
  face: {
    enrolled: boolean
    frames_enrolled: number
  }
}

export type AdminReportSummary = {
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
  generated_at: string
}

export type AdminUserAiSettingsRequest = {
  model_mode: 'API' | 'LOCAL'
  local_model_name?: string
  ollama_base_url?: string
  chat_persona?: 'GENERAL_CHAT' | 'BEHAVIOR_COACH' | 'CUSTOM'
}

export type AdminStats = {
  total_users: number
  admin_count: number
  total_sessions: number
  total_analyses: number
  total_reports: number
  total_events: number
}
