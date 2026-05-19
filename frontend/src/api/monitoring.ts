import { apiClient } from '@/api/client'
import { useAuthStore } from '@/store/auth-store'
import { env } from '@/lib/env'
import type {
  ActivityItemResponse,
  AnalyzeFrameRequest,
  AnalyzeFrameResponse,
  BehaviorEventResponse,
  ChatRequest,
  ChatHistoryResponse,
  ChatResponse,
  ChatStreamDoneEvent,
  DashboardResponse,
  DailyReportResponse,
  FaceRegisterRequest,
  FaceRegisterResponse,
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
    const response = await apiClient.post<AnalyzeFrameResponse>('/api/v1/monitoring/analyze', payload, {
      timeout: 35_000,
    })
    return response.data
  },

  async getDashboard() {
    const response = await apiClient.get<DashboardResponse>('/api/v1/monitoring/dashboard')
    return response.data
  },

  async getActivities(page = 0, size = 15) {
    const response = await apiClient.get<ActivityItemResponse[]>('/api/v1/monitoring/activities', {
      params: { page, size },
    })
    return response.data
  },

  async getEvents(page = 0, size = 15) {
    const response = await apiClient.get<BehaviorEventResponse[]>('/api/v1/monitoring/events', {
      params: { page, size },
    })
    return response.data
  },

  async getWeeklyTrend(from?: string) {
    const response = await apiClient.get<WeeklyTrendResponse>('/api/v1/monitoring/history/weekly', {
      params: from ? { from } : undefined,
    })
    return response.data
  },

  async getDailyReport(date?: string) {
    const response = await apiClient.get<DailyReportResponse>('/api/v1/monitoring/reports/daily', {
      params: date ? { date } : undefined,
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

  async chat(payload: ChatRequest) {
    const response = await apiClient.post<ChatResponse>('/api/v1/monitoring/chat', payload)
    return response.data
  },

  async chatStream(
    payload: ChatRequest,
    onToken: (token: string) => void,
    onDone: (result: ChatStreamDoneEvent) => void,
    signal: AbortSignal,
  ): Promise<void> {
    const accessToken = useAuthStore.getState().session?.access_token
    const base = env.apiBaseUrl || ''

    const response = await fetch(`${base}/api/v1/monitoring/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'text/event-stream',
        ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      },
      body: JSON.stringify(payload),
      signal,
    })

    if (!response.ok) {
      throw new Error(`SSE request failed with status ${response.status}`)
    }
    if (!response.body) {
      throw new Error('SSE response has no body')
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let receivedDone = false

    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })

        // Process complete SSE events separated by double newline.
        let eventEnd: number
        while ((eventEnd = buffer.indexOf('\n\n')) !== -1) {
          const eventBlock = buffer.slice(0, eventEnd)
          buffer = buffer.slice(eventEnd + 2)

          for (const line of eventBlock.split('\n')) {
            if (!line.startsWith('data: ')) continue

            let parsed: Record<string, unknown>
            try {
              parsed = JSON.parse(line.slice(6)) as Record<string, unknown>
            } catch {
              continue
            }

            if (parsed.done === true) {
              receivedDone = true
              onDone({
                conversationId: parsed.conversationId as string,
                groundedFacts: Array.isArray(parsed.groundedFacts)
                  ? (parsed.groundedFacts as string[])
                  : [],
                followUpSuggestions: Array.isArray(parsed.followUpSuggestions)
                  ? (parsed.followUpSuggestions as string[])
                  : [],
              })
            } else if (typeof parsed.token === 'string') {
              onToken(parsed.token)
            }
          }
        }
      }
    } finally {
      reader.cancel()
    }

    if (!receivedDone && !signal.aborted) {
      throw new Error('SSE stream ended without a done event')
    }
  },

  async getChatHistory(conversationId?: string | null, limit = 40) {
    const response = await apiClient.get<ChatHistoryResponse>('/api/v1/monitoring/chat/history', {
      params: {
        ...(conversationId ? { conversation_id: conversationId } : {}),
        limit,
      },
    })
    return response.data
  },

  async registerFace(payload: FaceRegisterRequest) {
    const response = await apiClient.post<FaceRegisterResponse>('/api/v1/monitoring/face/register', payload, {
      timeout: 20_000,
    })
    return response.data
  },

  async faceStatus() {
    const response = await apiClient.get<FaceRegisterResponse>('/api/v1/monitoring/face/status')
    return response.data
  },

  async deleteFaceProfile() {
    await apiClient.delete('/api/v1/monitoring/face')
  },
}
