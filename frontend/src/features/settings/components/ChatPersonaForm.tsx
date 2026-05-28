import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { MessagesSquare, Activity, Wand2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useLanguage } from '@/i18n/language-provider'
import type { SettingsResponse, ChatPersona } from '@/types/user'

const schema = z.object({
  chat_persona: z.enum(['GENERAL_CHAT', 'BEHAVIOR_COACH', 'CUSTOM'] as const),
  custom_system_prompt: z.string().max(4000).nullable().optional(),
})

type FormValues = z.infer<typeof schema>

const PERSONAS: Array<{ id: ChatPersona; icon: typeof MessagesSquare }> = [
  { id: 'GENERAL_CHAT', icon: MessagesSquare },
  { id: 'BEHAVIOR_COACH', icon: Activity },
  { id: 'CUSTOM', icon: Wand2 },
]

const COPY: Record<ChatPersona, { tr: { title: string; description: string }; en: { title: string; description: string } }> = {
  GENERAL_CHAT: {
    tr: {
      title: 'Genel Sohbet',
      description: 'Normal bir yapay zeka gibi her konuda konuş. Veri yalnızca açıkça sorulduğunda eklenir.',
    },
    en: {
      title: 'General Chat',
      description: 'Talk like a normal AI on any topic. Monitoring data is only included when you ask for it.',
    },
  },
  BEHAVIOR_COACH: {
    tr: {
      title: 'Davranış Koçu',
      description: 'Her yanıt monitoring verisine bağlı: duruş, hidrasyon, hareket örüntüleri.',
    },
    en: {
      title: 'Behavior Coach',
      description: 'Every answer is grounded in monitoring data: posture, hydration, gesture patterns.',
    },
  },
  CUSTOM: {
    tr: {
      title: 'Özel Persona',
      description: 'Kendi system promptunu yaz — asistanın karakterini, tonunu, kurallarını belirle.',
    },
    en: {
      title: 'Custom Persona',
      description: 'Write your own system prompt — define the assistant\'s character, tone, and rules.',
    },
  },
}

export function ChatPersonaForm({
  settings,
  isSaving,
  onSubmit,
}: {
  settings: SettingsResponse
  isSaving: boolean
  onSubmit: (values: FormValues) => void
}) {
  const { isTurkish } = useLanguage()

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { isDirty },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      chat_persona: settings.chat_persona ?? 'GENERAL_CHAT',
      custom_system_prompt: settings.custom_system_prompt ?? '',
    },
  })

  const persona = watch('chat_persona')

  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>{isTurkish ? 'Sohbet Personası' : 'Chat Persona'}</CardTitle>
          <CardDescription className="mt-2">
            {isTurkish
              ? 'Asistanın seninle nasıl konuşacağını seç. İleride kendi konuşma verinden eğitebilirsin.'
              : 'Pick how the assistant talks to you. You can fine-tune from your own conversation data later.'}
          </CardDescription>
        </div>
      </CardHeader>
      <CardContent>
        <form className="grid gap-4" onSubmit={handleSubmit((v) => onSubmit(v))}>
          <div className="grid gap-3 md:grid-cols-3">
            {PERSONAS.map(({ id, icon: Icon }) => {
              const copy = COPY[id][isTurkish ? 'tr' : 'en']
              const active = persona === id
              return (
                <button
                  key={id}
                  type="button"
                  onClick={() => setValue('chat_persona', id, { shouldDirty: true })}
                  className={[
                    'rounded-[20px] border p-4 text-left transition-all',
                    active
                      ? 'border-[var(--primary)] bg-[rgba(var(--primary-rgb),0.08)]'
                      : 'border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] hover:border-[var(--line-muted)]',
                  ].join(' ')}
                >
                  <div className="flex items-center gap-2">
                    <div className="flex size-8 items-center justify-center rounded-xl bg-[rgba(var(--primary-rgb),0.15)]">
                      <Icon className="size-4 text-[var(--primary)]" />
                    </div>
                    <p className="text-sm font-semibold text-white">{copy.title}</p>
                  </div>
                  <p className="mt-2 text-xs text-[var(--text-muted)]">{copy.description}</p>
                </button>
              )
            })}
          </div>

          {persona === 'CUSTOM' && (
            <label className="flex flex-col gap-2">
              <span className="text-sm font-medium text-white">
                {isTurkish ? 'Kendi system promptun' : 'Your custom system prompt'}
              </span>
              <textarea
                rows={6}
                maxLength={4000}
                className="min-h-32 rounded-2xl border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] px-4 py-3 text-sm text-white outline-none focus:border-[var(--primary)]"
                placeholder={isTurkish
                  ? 'Örnek: Sen sabırlı bir mentor olarak davran. Kısa, somut adımlar öner...'
                  : 'Example: Act as a patient mentor. Offer concise, concrete next steps...'}
                {...register('custom_system_prompt')}
              />
              <span className="text-xs text-[var(--text-muted)]">
                {isTurkish
                  ? 'Maks 4000 karakter. İpucu: asistanın hangi konuda uzman olduğunu, hangi tondan konuşacağını ve yapmaması gerekenleri net yaz.'
                  : 'Max 4000 chars. Tip: define the assistant\'s expertise, tone, and forbidden actions clearly.'}
              </span>
            </label>
          )}

          <input type="hidden" {...register('chat_persona')} />

          <div className="flex justify-end">
            <Button type="submit" loading={isSaving} disabled={!isDirty}>
              {isTurkish ? 'Persona kaydet' : 'Save persona'}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}
