export type Sensitivity = 'LOW' | 'MEDIUM' | 'HIGH'
export type ModelMode = 'LOCAL' | 'API'

export type ConsentResponse = {
  privacy_policy_accepted: boolean
  camera_monitoring_accepted: boolean
  remote_inference_accepted: boolean
  accepted_at: string | null
  updated_at: string
}

export type SettingsResponse = {
  sensitivity: Sensitivity
  water_goal_ml: number
  water_interval_min: number
  exercise_interval_min: number
  quiet_hours_enabled: boolean
  quiet_hours_start: string
  quiet_hours_end: string
  model_mode: ModelMode
  notifications_enabled: boolean
  updated_at: string
}

export type UserContextResponse = {
  user_id: string
  email: string
  display_name: string
  timezone: string
  locale: string
  settings: SettingsResponse
  consents: ConsentResponse
}

export type UserProfileResponse = {
  user_id: string
  email: string
  display_name: string
  timezone: string
  locale: string
  updated_at: string
}

export type UpdateProfileRequest = {
  display_name: string
  timezone: string
  locale: string
}

export type UpdateSettingsRequest = {
  sensitivity: Sensitivity
  water_goal_ml: number
  water_interval_min: number
  exercise_interval_min: number
  quiet_hours_enabled: boolean
  quiet_hours_start: string
  quiet_hours_end: string
  model_mode: ModelMode
  notifications_enabled: boolean
}

export type UpdateConsentsRequest = {
  privacy_policy_accepted: boolean
  camera_monitoring_accepted: boolean
  remote_inference_accepted: boolean
}

