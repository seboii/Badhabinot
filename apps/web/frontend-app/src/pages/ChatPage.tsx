import { useState, type FormEvent } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { MessageSquare, Send } from 'lucide-react'
import { toast } from 'sonner'
import { monitoringApi } from '@/api/monitoring'
import { toErrorMessage } from '@/api/client'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { EmptyState } from '@/components/ui/empty-state'
import { Button } from '@/components/ui/button'
import { LoadingCard } from '@/components/ui/loading-state'
import { formatRelativeTime } from '@/lib/format'
import type { ChatMessageResponse } from '@/types/monitoring'

const starters = [
  'Did I sit with bad posture a lot today?',
  'Did I drink enough water today?',
  'When did the system detect risky behavior?',
]

export function ChatPage() {
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [draft, setDraft] = useState('')
  const [messages, setMessages] = useState<ChatMessageResponse[]>([])
  const [groundedFacts, setGroundedFacts] = useState<string[]>([])
  const [followUps, setFollowUps] = useState<string[]>(starters)

  const reportQuery = useQuery({
    queryKey: ['daily-report-chat-preview'],
    queryFn: () => monitoringApi.getDailyReport(),
  })

  const chatMutation = useMutation({
    mutationFn: (message: string) =>
      monitoringApi.chat({
        conversation_id: conversationId,
        message,
      }),
    onSuccess(response) {
      setConversationId(response.conversation_id)
      setMessages(response.recent_messages)
      setGroundedFacts(response.grounded_facts)
      setFollowUps(response.follow_up_suggestions.length > 0 ? response.follow_up_suggestions : starters)
      setDraft('')
    },
    onError(error) {
      toast.error(toErrorMessage(error, 'Unable to send the grounded chat request.'))
    },
  })

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    const trimmed = draft.trim()
    if (!trimmed) {
      return
    }
    chatMutation.mutate(trimmed)
  }

  if (reportQuery.isLoading || !reportQuery.data) {
    return <LoadingCard message="Loading grounded behavior context" />
  }

  return (
    <div className="grid gap-4 xl:grid-cols-[minmax(0,1.2fr)_minmax(340px,0.8fr)]">
      <Card className="min-h-[620px]">
        <CardHeader>
          <div>
            <CardTitle>Behavior chat</CardTitle>
            <CardDescription className="mt-2">
              Ask about tracked posture, hydration, reminders, and smoking-like cues. The answer is grounded in your stored monitoring data.
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent className="flex h-[calc(100%-5.5rem)] flex-col gap-4">
          <div className="flex-1 space-y-3 overflow-y-auto rounded-[24px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4">
            {messages.length === 0 ? (
              <EmptyState
                icon={MessageSquare}
                title="No conversation yet"
                description="Start with one of the suggested questions or type a new one about your tracked behavior."
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
                  <p className="text-sm leading-6">{message.content}</p>
                  <p className="mt-2 text-xs opacity-70">{formatRelativeTime(message.created_at)}</p>
                </div>
              ))
            )}
          </div>

          <form className="space-y-3" onSubmit={handleSubmit}>
            <textarea
              className="min-h-[112px] w-full rounded-[24px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] px-4 py-3 text-sm text-white outline-none focus:border-[var(--primary)]"
              placeholder="Ask about posture trends, hydration, reminders, or risky behavior timings."
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
            />
            <div className="flex justify-end">
              <Button type="submit" loading={chatMutation.isPending} iconLeft={<Send className="size-4" />}>
                Send question
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      <div className="space-y-4">
        <Card>
          <CardHeader>
            <div>
              <CardTitle>Grounded facts</CardTitle>
              <CardDescription className="mt-2">Facts pulled directly from the current report context used for the latest answer.</CardDescription>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            {groundedFacts.length === 0 ? (
              <p className="text-sm text-[var(--text-muted)]">{reportQuery.data.summary}</p>
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
              <CardTitle>Suggested questions</CardTitle>
              <CardDescription className="mt-2">These stay grounded to the same report and event history used by the backend chat endpoint.</CardDescription>
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
