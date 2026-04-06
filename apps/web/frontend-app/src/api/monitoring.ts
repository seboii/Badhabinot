import { apiClient } from '@/api/client'
import type {
  ActivityItemResponse,
  AnalyzeFrameRequest,
  AnalyzeFrameResponse,
  DashboardResponse,
  HydrationLogRequest,
  HydrationLogResponse,
  ReminderTriggerRequest,
  SessionStartRequest,
  SessionStartResponse,
  SessionStopResponse,
  WeeklyTrendResponse,
} from '@/types/monitoring'

export const monitoringApi = {
  async startSession(payload: SessionStartRequest) {
    const response = await apiClient.post<SessionStartResponse>('/api/v1/monitoring/sessions/start', payload)
    return response.data
  },

  async stopSession(sessionId: string) {
    const response = await apiClient.post<SessionStopResponse>(`/api/v1/monitoring/sessions/${sessionId}/stop`)
    return response.data
  },

  async analyze(payload: AnalyzeFrameRequest) {
    const response = await apiClient.post<AnalyzeFrameResponse>('/api/v1/monitoring/analyze', payload)
    return response.data
  },

  async getDashboard() {
    const response = await apiClient.get<DashboardResponse>('/api/v1/monitoring/dashboard')
    return response.data
  },

  async getActivities(limit = 10) {
    const response = await apiClient.get<ActivityItemResponse[]>('/api/v1/monitoring/activities', {
      params: { limit },
    })
    return response.data
  },

  async getWeeklyTrend(from?: string) {
    const response = await apiClient.get<WeeklyTrendResponse>('/api/v1/monitoring/history/weekly', {
      params: from ? { from } : undefined,
    })
    return response.data
  },

  async logHydration(payload: HydrationLogRequest) {
    const response = await apiClient.post<HydrationLogResponse>('/api/v1/monitoring/hydration/log', payload)
    return response.data
  },

  async triggerReminder(payload: ReminderTriggerRequest) {
    const response = await apiClient.post<ActivityItemResponse>('/api/v1/monitoring/reminders/trigger', payload)
    return response.data
  },
}

