import { useEffect, useMemo, useRef, useState, type FormEvent } from 'react'
import { useQuery } from '@tanstack/react-query'
import { AlertTriangle, MessageSquare, RefreshCcw, Send, Sparkles, Cpu, Cloud } from 'lucide-react'
import { toast } from 'sonner'
import { monitoringApi } from '@/api/monitoring'
import { userApi } from '@/api/user'
import { toErrorMessage } from '@/api/client'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { EmptyState } from '@/components/ui/empty-state'
import { Button } from '@/components/ui/button'
import { LoadingCard } from '@/components/ui/loading-state'
import { useLanguage } from '@/i18n/language-provider'
import { formatRelativeTime } from '@/lib/format'
import type { ChatMessageResponse } from '@/types/monitoring'

const CHAT_CONVERSATION_STORAGE_KEY = 'badhabinot-chat-conversation-id'

function readStoredConversationId() {
  if (typeof window === 'undefined') {
    return null
  }
  const value = window.sessionStorage.getItem(CHAT_CONVERSATION_STORAGE_KEY)
  return value && value.length > 0 ? value : null
}

function storeConversationId(conversationId: string | null) {
  if (typeof window === 'undefined') {
    return
  }
  if (!conversationId) {
    window.sessionStorage.removeItem(CHAT_CONVERSATION_STORAGE_KEY)
    return
  }
  window.sessionStorage.setItem(CHAT_CONVERSATION_STORAGE_KEY, conversationId)
}

function groundedFactsFromMetadata(message: ChatMessageResponse | undefined) {
  if (!message || !message.metadata || typeof message.metadata !== 'object') {
    return []
  }
  const raw = (message.metadata as Record<string, unknown>).grounded_facts
  if (!Array.isArray(raw)) {
    return []
  }
  return raw.filter((item): item is string => typeof item === 'string' && item.trim().length > 0)
}

export function ChatPage() {
  const { language, isTurkish } = useLanguage()
  const starters = useMemo(
    () => [
      isTurkish ? 'Bugun cok kotu durusla mi oturdum?' : 'Did I sit with bad posture a lot today?',
      isTurkish ? 'Bugun yeterince su ictim mi?' : 'Did I drink enough water today?',
      isTurkish ? 'Bugunku trendim gecmise gore nasil?' : 'How does today compare with my recent trend?',
      isTurkish ? 'Bugun en cok hangi olay tekrarlandi?' : 'What happened most often today?',
    ],
    [isTurkish],
  )

  const initialConversationIdRef = useRef<string | null>(readStoredConversationId())
  const [conversationId, setConversationId] = useState<string | null>(initialConversationIdRef.current)
  const [draft, setDraft] = useState('')
  const [messages, setMessages] = useState<ChatMessageResponse[]>([])
  const [groundedFacts, setGroundedFacts] = useState<string[]>([])
  const [followUps, setFollowUps] = useState<string[]>(starters)
  const [sendError, setSendError] = useState<string | null>(null)
  const [lastFailedMessage, setLastFailedMessage] = useState<string | null>(null)
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingContent, setStreamingContent] = useState('')
  const historyContainerRef = useRef<HTMLDivElement | null>(null)
  const abortControllerRef = useRef<AbortController | null>(null)

  const reportQuery = useQuery({
    queryKey: ['daily-report-chat-preview'],
    queryFn: () => monitoringApi.getDailyReport(),
  })

  const settingsQuery = useQuery({
    queryKey: ['user-settings-chat'],
    queryFn: userApi.getSettings,
    staleTime: 60_000,
  })

  const modelMode = settingsQuery.data?.model_mode ?? 'API'
  const localModelName = settingsQuery.data?.local_model_name

  const historyQuery = useQuery({
    queryKey: ['chat-history-initial'],
    queryFn: () => monitoringApi.getChatHistory(initialConversationIdRef.current, 40),
    retry: 1,
  })

  useEffect(() => {
    if (!historyQuery.data) {
      return
    }
    setConversationId(historyQuery.data.conversation_id)
    storeConversationId(historyQuery.data.conversation_id)
    setMessages(historyQuery.data.recent_messages)
  }, [historyQuery.data])

  useEffect(() => {
    if (messages.length === 0) {
      setFollowUps(starters)
      setGroundedFacts([])
      return
    }

    const latestAssistant = [...messages].reverse().find((message) => message.role === 'assistant')
    const metadataFacts = groundedFactsFromMetadata(latestAssistant)
    if (metadataFacts.length > 0) {
      setGroundedFacts(metadataFacts)
    }
  }, [messages, starters])

  useEffect(() => {
    const container = historyContainerRef.current
    if (!container) {
      return
    }
    container.scrollTop = container.scrollHeight
  }, [messages.length])

  // Scroll during streaming as tokens arrive.
  useEffect(() => {
    const container = historyContainerRef.current
    if (!container || !isStreaming) {
      return
    }
    container.scrollTop = container.scrollHeight
  }, [streamingContent, isStreaming])

  const sendMessage = async (message: string) => {
    const trimmed = message.trim()
    if (!trimmed || isStreaming) {
      return
    }
    setDraft('')
    setSendError(null)
    setLastFailedMessage(null)

    const optimisticId = `temp-${Date.now()}`
    const optimisticMessage: ChatMessageResponse = {
      message_id: optimisticId,
      conversation_id: conversationId ?? optimisticId,
      role: 'user',
      content: trimmed,
      created_at: new Date().toISOString(),
      metadata: {},
    }
    setMessages((previous) => [...previous, optimisticMessage])
    setIsStreaming(true)

    const controller = new AbortController()
    abortControllerRef.current = controller

    let accumulated = ''
    let streamStarted = false

    try {
      await monitoringApi.chatStream(
        { conversation_id: conversationId, message: trimmed },
        (token) => {
          streamStarted = true
          accumulated += token
          setStreamingContent(accumulated)
        },
        (result) => {
          const assistantMsg: ChatMessageResponse = {
            message_id: `assistant-${Date.now()}`,
            conversation_id: result.conversationId,
            role: 'assistant',
            content: accumulated,
            created_at: new Date().toISOString(),
            metadata: {
              grounded_facts: result.groundedFacts,
            },
          }
          setStreamingContent('')
          setConversationId(result.conversationId)
          storeConversationId(result.conversationId)
          setMessages((previous) => [...previous, assistantMsg])
          setGroundedFacts(result.groundedFacts)
          setFollowUps(result.followUpSuggestions.length > 0 ? result.followUpSuggestions : starters)
          setSendError(null)
          setLastFailedMessage(null)
        },
        controller.signal,
      )
    } catch (error) {
      if (controller.signal.aborted) {
        setMessages((previous) => previous.filter((m) => m.message_id !== optimisticId))
        setStreamingContent('')
      } else if (!streamStarted) {
        // SSE failed before any token — fall back to non-streaming POST.
        setStreamingContent('')
        try {
          const response = await monitoringApi.chat({
            conversation_id: conversationId,
            message: trimmed,
          })
          setConversationId(response.conversation_id)
          storeConversationId(response.conversation_id)
          setMessages(response.recent_messages)
          setGroundedFacts(response.grounded_facts)
          setFollowUps(response.follow_up_suggestions.length > 0 ? response.follow_up_suggestions : starters)
          setSendError(null)
          setLastFailedMessage(null)
        } catch (fallbackError) {
          setMessages((previous) => previous.filter((m) => m.message_id !== optimisticId))
          setDraft((previous) => (previous.length > 0 ? previous : trimmed))
          setLastFailedMessage(trimmed)
          const errorMsg = toErrorMessage(
            fallbackError,
            isTurkish ? 'Veriye dayali sohbet istegi gonderilemedi.' : 'Unable to send the grounded chat request.',
          )
          setSendError(errorMsg)
          toast.error(errorMsg)
        }
      } else {
        // Mid-stream failure.
        setStreamingContent('')
        setMessages((previous) => previous.filter((m) => m.message_id !== optimisticId))
        setDraft((previous) => (previous.length > 0 ? previous : trimmed))
        setLastFailedMessage(trimmed)
        const errorMsg = toErrorMessage(
          error,
          isTurkish ? 'Veriye dayali sohbet istegi gonderilemedi.' : 'Unable to send the grounded chat request.',
        )
        setSendError(errorMsg)
        toast.error(errorMsg)
      }
    } finally {
      setIsStreaming(false)
      abortControllerRef.current = null
    }
  }

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    void sendMessage(draft)
  }

  const resetConversation = () => {
    abortControllerRef.current?.abort()
    setConversationId(null)
    setMessages([])
    setGroundedFacts([])
    setFollowUps(starters)
    setSendError(null)
    setLastFailedMessage(null)
    setDraft('')
    setStreamingContent('')
    storeConversationId(null)
    initialConversationIdRef.current = null
  }

  if (historyQuery.isLoading && messages.length === 0) {
    return (
      <LoadingCard message={isTurkish ? 'Sohbet gecmisi yukleniyor' : 'Loading grounded chat history'} />
    )
  }

  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(0,1.2fr)_minmax(300px,0.8fr)] xl:grid-cols-[minmax(0,1.2fr)_minmax(340px,0.8fr)]">
      <Card className="min-h-[480px] sm:min-h-[560px] lg:min-h-[620px]">
        <CardHeader>
          <div className="flex items-start justify-between gap-3">
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <CardTitle>{isTurkish ? 'Davranis sohbeti' : 'Behavior chat'}</CardTitle>
                {modelMode === 'LOCAL' ? (
                  <span className="inline-flex items-center gap-1 rounded-full border border-[rgba(139,92,246,0.4)] bg-[rgba(139,92,246,0.1)] px-2 py-0.5 text-xs text-purple-300">
                    <Cpu className="h-3 w-3" />
                    {localModelName ?? 'Local AI'}
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 rounded-full border border-[var(--line-soft)] bg-[rgba(255,255,255,0.04)] px-2 py-0.5 text-xs text-[var(--text-muted)]">
                    <Cloud className="h-3 w-3" />
                    Cloud API
                  </span>
                )}
              </div>
              <CardDescription className="mt-2">
                {isTurkish
                  ? 'Yanitlar sadece kendi kayitli davranis, rapor, hatirlatici ve seans verine dayanir.'
                  : 'Answers stay grounded in your own stored behavior events, reports, reminders, and sessions.'}
              </CardDescription>
            </div>
            <Button
              type="button"
              variant="ghost"
              iconLeft={<RefreshCcw className="size-4" />}
              onClick={resetConversation}
              disabled={isStreaming}
              className="shrink-0"
            >
              <span className="hidden sm:inline">{isTurkish ? 'Konusmayi Sifirla' : 'Reset'}</span>
            </Button>
          </div>
        </CardHeader>
        <CardContent className="flex flex-col gap-4" style={{ height: 'calc(100% - 5.5rem)' }}>
          {historyQuery.isError ? (
            <div className="rounded-[20px] border border-[rgba(245,158,11,0.4)] bg-[rgba(245,158,11,0.08)] p-3 text-sm text-[var(--text-muted)]">
              <div className="flex items-start gap-2">
                <AlertTriangle className="mt-0.5 size-4 text-amber-300" />
                <p>
                  {toErrorMessage(
                    historyQuery.error,
                    isTurkish
                      ? 'Sohbet gecmisi yuklenemedi. Yeni bir mesaj gonderebilirsin.'
                      : 'Failed to load chat history. You can still send a new message.',
                  )}
                </p>
              </div>
              <div className="mt-3 flex justify-end">
                <Button type="button" variant="ghost" onClick={() => historyQuery.refetch()}>
                  {isTurkish ? 'Tekrar dene' : 'Retry'}
                </Button>
              </div>
            </div>
          ) : null}

          <div
            ref={historyContainerRef}
            className="flex-1 space-y-3 overflow-y-auto rounded-[24px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4"
          >
            {messages.length === 0 && !isStreaming ? (
              <EmptyState
                icon={MessageSquare}
                title={isTurkish ? 'Henuz konusma yok' : 'No conversation yet'}
                description={
                  isTurkish
                    ? 'Onerilen sorulardan biriyle basla veya takip edilen davranislarla ilgili yeni bir soru yaz.'
                    : 'Start with one of the suggested questions or ask about your tracked behavior.'
                }
              />
            ) : (
              messages.map((message) => (
                <div
                  key={message.message_id}
                  className={`rounded-[20px] p-4 ${
                    message.role === 'assistant'
                      ? 'border border-[var(--line-soft)] bg-[rgba(255,255,255,0.04)]'
                      : 'ml-auto max-w-[80%] bg-[var(--primary-soft)] text-[var(--text-on-accent)]'
                  }`}
                >
                  <p className="whitespace-pre-wrap text-sm leading-6">{message.content}</p>
                  <p className="mt-2 text-xs opacity-70">{formatRelativeTime(message.created_at, language)}</p>
                </div>
              ))
            )}
            {isStreaming && streamingContent.length === 0 ? (
              <div className="flex items-center gap-2 rounded-[16px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] px-3 py-2 text-xs text-[var(--text-muted)]">
                <Sparkles className="size-3.5 animate-pulse" />
                {isTurkish
                  ? 'Asistan kayitli davranis verilerini analiz ediyor...'
                  : 'Assistant is analyzing your stored behavior data...'}
              </div>
            ) : null}
            {isStreaming && streamingContent.length > 0 ? (
              <div className="rounded-[20px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.04)] p-4">
                <p className="whitespace-pre-wrap text-sm leading-6">
                  {streamingContent}
                  <span className="animate-pulse text-[var(--primary)]">&#9611;</span>
                </p>
              </div>
            ) : null}
          </div>

          {sendError ? (
            <div className="rounded-[20px] border border-[rgba(239,68,68,0.4)] bg-[rgba(239,68,68,0.08)] p-3 text-sm text-[var(--text-muted)]">
              <p>{sendError}</p>
              {modelMode === 'LOCAL' && (sendError.toLowerCase().includes('timeout') || sendError.toLowerCase().includes('unreachable') || sendError.toLowerCase().includes('unavailable')) && (
                <div className="mt-2 rounded-[12px] border border-[rgba(139,92,246,0.3)] bg-[rgba(139,92,246,0.05)] p-3 text-xs">
                  <p className="font-medium text-purple-300">
                    {isTurkish ? 'Yerel AI (Ollama) erişilemiyor' : 'Local AI (Ollama) unreachable'}
                  </p>
                  <p className="mt-1 text-[var(--text-muted)]">
                    {isTurkish
                      ? `Ollama çalışıyor mu kontrol edin. Model yüklü değilse: ollama pull ${localModelName ?? 'llama3.2:3b'}`
                      : `Make sure Ollama is running. If the model is not installed: ollama pull ${localModelName ?? 'llama3.2:3b'}`}
                  </p>
                </div>
              )}
              <div className="mt-3 flex justify-end gap-2">
                {lastFailedMessage ? (
                  <Button
                    type="button"
                    variant="ghost"
                    iconLeft={<RefreshCcw className="size-4" />}
                    onClick={() => void sendMessage(lastFailedMessage)}
                  >
                    {isTurkish ? 'Son soruyu tekrar gonder' : 'Retry last question'}
                  </Button>
                ) : null}
              </div>
            </div>
          ) : null}

          <form className="space-y-3" onSubmit={handleSubmit}>
            <textarea
              className="min-h-[88px] w-full rounded-[20px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] px-4 py-3 text-sm text-white outline-none focus:border-[var(--primary)] sm:min-h-[112px] sm:rounded-[24px]"
              placeholder={
                isTurkish
                  ? 'Durus, su, hatirlatici, sigara-benzeri olaylar veya gunluk trend hakkinda sor.'
                  : 'Ask about posture, hydration, reminders, smoking-like cues, or your daily trend.'
              }
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              disabled={isStreaming}
            />
            <div className="flex justify-end">
              <Button type="submit" loading={isStreaming} iconLeft={<Send className="size-4" />} className="w-full sm:w-auto">
                {isTurkish ? 'Soruyu gonder' : 'Send question'}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      <div className="space-y-4">
        <Card>
          <CardHeader>
            <div>
              <CardTitle>{isTurkish ? 'Veriye dayali bilgiler' : 'Grounded facts'}</CardTitle>
              <CardDescription className="mt-2">
                {isTurkish
                  ? 'Son yanitta kullanilan kayitli veri noktalarindan secilen ozet bilgiler.'
                  : 'Selected grounded points taken from your stored data used in the latest answer.'}
              </CardDescription>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            {groundedFacts.length === 0 ? (
              <p className="text-sm text-[var(--text-muted)]">
                {reportQuery.data?.summary ??
                  (isTurkish
                    ? 'Sohbet baslatildiginda rapor ve olay verilerinden olusan bilgiler burada gorunur.'
                    : 'Grounded facts from report and event data will appear here after a response.')}
              </p>
            ) : (
              groundedFacts.map((fact) => (
                <div
                  key={fact}
                  className="rounded-[20px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4 text-sm leading-6 text-[var(--text-muted)]"
                >
                  {fact}
                </div>
              ))
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div>
              <CardTitle>{isTurkish ? 'Onerilen sorular' : 'Suggested questions'}</CardTitle>
              <CardDescription className="mt-2">
                {isTurkish
                  ? 'Sorular ayni kullaniciya ait rapor, olay, hatirlatici ve seans gecmisi ile sinirlandirilir.'
                  : 'Suggestions stay scoped to your own report, event, reminder, and session history.'}
              </CardDescription>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            {followUps.map((suggestion) => (
              <button
                key={suggestion}
                type="button"
                className="w-full rounded-[20px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] px-4 py-3 text-left text-sm text-[var(--text-muted)] transition hover:border-[var(--primary)] hover:text-white disabled:pointer-events-none disabled:opacity-50"
                disabled={isStreaming}
                onClick={() => setDraft(suggestion)}
              >
                {suggestion}
              </button>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
