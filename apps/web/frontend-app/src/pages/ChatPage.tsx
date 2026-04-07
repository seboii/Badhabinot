import { useEffect, useMemo, useRef, useState, type FormEvent } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { AlertTriangle, MessageSquare, RefreshCcw, Send, Sparkles } from 'lucide-react'
import { toast } from 'sonner'
import { monitoringApi } from '@/api/monitoring'
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
  const historyContainerRef = useRef<HTMLDivElement | null>(null)

  const reportQuery = useQuery({
    queryKey: ['daily-report-chat-preview'],
    queryFn: () => monitoringApi.getDailyReport(),
  })

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

  const chatMutation = useMutation({
    mutationFn: (payload: { message: string; optimisticId: string }) =>
      monitoringApi.chat({
        conversation_id: conversationId,
        message: payload.message,
      }),
    onSuccess(response) {
      setConversationId(response.conversation_id)
      storeConversationId(response.conversation_id)
      setMessages(response.recent_messages)
      setGroundedFacts(response.grounded_facts)
      setFollowUps(response.follow_up_suggestions.length > 0 ? response.follow_up_suggestions : starters)
      setSendError(null)
      setLastFailedMessage(null)
    },
    onError(error, payload) {
      setMessages((previous) => previous.filter((message) => message.message_id !== payload.optimisticId))
      setDraft((previous) => (previous.length > 0 ? previous : payload.message))
      setLastFailedMessage(payload.message)
      setSendError(
        toErrorMessage(
          error,
          isTurkish ? 'Veriye dayali sohbet istegi gonderilemedi.' : 'Unable to send the grounded chat request.',
        ),
      )
      toast.error(
        toErrorMessage(
          error,
          isTurkish ? 'Veriye dayali sohbet istegi gonderilemedi.' : 'Unable to send the grounded chat request.',
        ),
      )
    },
  })

  const sendMessage = (message: string) => {
    const trimmed = message.trim()
    if (!trimmed || chatMutation.isPending) {
      return
    }
    setDraft('')
    setSendError(null)

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
    chatMutation.mutate({ message: trimmed, optimisticId })
  }

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    sendMessage(draft)
  }

  const resetConversation = () => {
    setConversationId(null)
    setMessages([])
    setGroundedFacts([])
    setFollowUps(starters)
    setSendError(null)
    setLastFailedMessage(null)
    setDraft('')
    storeConversationId(null)
    initialConversationIdRef.current = null
  }

  if (historyQuery.isLoading && messages.length === 0) {
    return (
      <LoadingCard message={isTurkish ? 'Sohbet gecmisi yukleniyor' : 'Loading grounded chat history'} />
    )
  }

  return (
    <div className="grid gap-4 xl:grid-cols-[minmax(0,1.2fr)_minmax(340px,0.8fr)]">
      <Card className="min-h-[620px]">
        <CardHeader>
          <div className="flex items-start justify-between gap-3">
            <div>
              <CardTitle>{isTurkish ? 'Davranis sohbeti' : 'Behavior chat'}</CardTitle>
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
              disabled={chatMutation.isPending}
            >
              {isTurkish ? 'Yeni sohbet' : 'New chat'}
            </Button>
          </div>
        </CardHeader>
        <CardContent className="flex h-[calc(100%-5.5rem)] flex-col gap-4">
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
            {messages.length === 0 ? (
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
            {chatMutation.isPending ? (
              <div className="flex items-center gap-2 rounded-[16px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] px-3 py-2 text-xs text-[var(--text-muted)]">
                <Sparkles className="size-3.5 animate-pulse" />
                {isTurkish
                  ? 'Asistan kayitli davranis verilerini analiz ediyor...'
                  : 'Assistant is analyzing your stored behavior data...'}
              </div>
            ) : null}
          </div>

          {sendError ? (
            <div className="rounded-[20px] border border-[rgba(239,68,68,0.4)] bg-[rgba(239,68,68,0.08)] p-3 text-sm text-[var(--text-muted)]">
              <p>{sendError}</p>
              <div className="mt-3 flex justify-end gap-2">
                {lastFailedMessage ? (
                  <Button
                    type="button"
                    variant="ghost"
                    iconLeft={<RefreshCcw className="size-4" />}
                    onClick={() => sendMessage(lastFailedMessage)}
                  >
                    {isTurkish ? 'Son soruyu tekrar gonder' : 'Retry last question'}
                  </Button>
                ) : null}
              </div>
            </div>
          ) : null}

          <form className="space-y-3" onSubmit={handleSubmit}>
            <textarea
              className="min-h-[112px] w-full rounded-[24px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] px-4 py-3 text-sm text-white outline-none focus:border-[var(--primary)]"
              placeholder={
                isTurkish
                  ? 'Durus, su, hatirlatici, sigara-benzeri olaylar veya gunluk trend hakkinda sor.'
                  : 'Ask about posture, hydration, reminders, smoking-like cues, or your daily trend.'
              }
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              disabled={chatMutation.isPending}
            />
            <div className="flex justify-end">
              <Button type="submit" loading={chatMutation.isPending} iconLeft={<Send className="size-4" />}>
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
                className="w-full rounded-[20px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] px-4 py-3 text-left text-sm text-[var(--text-muted)] transition hover:border-[var(--primary)] hover:text-white"
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
