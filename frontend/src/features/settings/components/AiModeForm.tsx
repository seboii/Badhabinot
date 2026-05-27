import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useQuery } from '@tanstack/react-query'
import { CheckCircle2, WifiOff, Loader2, RefreshCw, Brain } from 'lucide-react'
import { userApi } from '@/api/user'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useLanguage } from '@/i18n/language-provider'
import type { SettingsResponse, ModelMode } from '@/types/user'

const BADHABINOT_MODEL = 'badhabinot:latest'

const schema = z.object({
  model_mode: z.enum(['API', 'LOCAL'] as const),
  local_model_name: z.string().min(1).max(100),
  ollama_base_url: z.string().url().max(255),
})

type FormValues = z.infer<typeof schema>

export function AiModeForm({
  settings,
  isSaving,
  onSubmit,
}: {
  settings: SettingsResponse
  isSaving: boolean
  onSubmit: (values: Pick<FormValues, 'model_mode' | 'local_model_name' | 'ollama_base_url'>) => void
}) {
  const { isTurkish } = useLanguage()
  const [testTriggered, setTestTriggered] = useState(false)

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { isDirty },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      model_mode: settings.model_mode,
      local_model_name: BADHABINOT_MODEL,
      ollama_base_url: settings.ollama_base_url || 'http://host.docker.internal:11434',
    },
  })

  const modelMode = watch('model_mode')

  const ollamaHealthQuery = useQuery({
    queryKey: ['ollama-health'],
    queryFn: userApi.ollamaHealth,
    enabled: testTriggered,
    retry: false,
    staleTime: 0,
  })

  function handleTestConnection() {
    setTestTriggered(true)
    void ollamaHealthQuery.refetch()
  }

  const health = ollamaHealthQuery.data
  const isModelInstalled = health?.model_installed ?? false

  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>{isTurkish ? 'AI modu' : 'AI mode'}</CardTitle>
          <CardDescription className="mt-2">
            {isTurkish
              ? 'Bulut API veya kendi Badhabinot AI modeliniz arasında geçiş yapın.'
              : 'Switch between Cloud API and your own Badhabinot AI model.'}
          </CardDescription>
        </div>
      </CardHeader>
      <CardContent>
        <form className="grid gap-4 md:grid-cols-2" onSubmit={handleSubmit((v) => onSubmit(v))}>
          {/* Mode selector */}
          <div className="md:col-span-2 grid grid-cols-2 gap-3">
            {(['API', 'LOCAL'] as ModelMode[]).map((mode) => (
              <button
                key={mode}
                type="button"
                onClick={() => setValue('model_mode', mode, { shouldDirty: true })}
                className={[
                  'rounded-[20px] border p-4 text-left transition-all',
                  modelMode === mode
                    ? 'border-[var(--primary)] bg-[rgba(var(--primary-rgb),0.08)]'
                    : 'border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] hover:border-[var(--line-muted)]',
                ].join(' ')}
              >
                <p className="text-sm font-semibold text-white">
                  {mode === 'API'
                    ? isTurkish ? 'Bulut API' : 'Cloud API'
                    : isTurkish ? 'Yerel AI' : 'Local AI'}
                </p>
                <p className="mt-1 text-xs text-[var(--text-muted)]">
                  {mode === 'API'
                    ? isTurkish ? 'OpenAI uyumlu uzak servis' : 'OpenAI-compatible remote service'
                    : isTurkish ? 'Badhabinot AI — internet bağlantısı gerekmez' : 'Badhabinot AI — no internet required'}
                </p>
              </button>
            ))}
          </div>

          {/* Local mode: fixed Badhabinot AI card */}
          {modelMode === 'LOCAL' && (
            <>
              {/* Model info */}
              <div className="md:col-span-2 flex items-center gap-4 rounded-[20px] border border-[var(--primary)] bg-[rgba(var(--primary-rgb),0.06)] p-4">
                <div className="flex size-10 shrink-0 items-center justify-center rounded-2xl bg-[rgba(var(--primary-rgb),0.15)]">
                  <Brain className="size-5 text-[var(--primary)]" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-white">Badhabinot AI</p>
                  <p className="text-xs text-[var(--text-muted)]">
                    {isTurkish
                      ? 'Qwen 2.5 7B tabanlı, davranış analizi için ince ayarlı'
                      : 'Qwen 2.5 7B base, fine-tuned for behavior analysis'}
                  </p>
                </div>
              </div>

              {/* Ollama URL */}
              <div className="md:col-span-2">
                <label className="flex flex-col gap-2">
                  <span className="text-sm font-medium text-white">
                    {isTurkish ? 'Ollama sunucu adresi' : 'Ollama base URL'}
                  </span>
                  <input
                    className="h-12 rounded-2xl border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] px-4 text-sm text-white outline-none focus:border-[var(--primary)]"
                    {...register('ollama_base_url')}
                    placeholder="http://host.docker.internal:11434"
                  />
                </label>
              </div>

              {/* Connection test */}
              <div className="md:col-span-2 rounded-[20px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4">
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <p className="text-sm font-semibold text-white">
                      {isTurkish ? 'Bağlantı testi' : 'Connection test'}
                    </p>
                    {!testTriggered && (
                      <p className="mt-1 text-xs text-[var(--text-muted)]">
                        {isTurkish ? 'Kaydetmeden önce test et.' : 'Test before saving.'}
                      </p>
                    )}
                    {ollamaHealthQuery.isLoading && (
                      <p className="mt-1 flex items-center gap-1 text-xs text-[var(--text-muted)]">
                        <Loader2 className="h-3 w-3 animate-spin" />
                        {isTurkish ? 'Test ediliyor...' : 'Testing...'}
                      </p>
                    )}
                    {health && !ollamaHealthQuery.isLoading && (
                      <div className="mt-2 space-y-1">
                        {health.provider_status === 'reachable' ? (
                          <p className="flex items-center gap-1 text-xs text-[var(--success,#4caf50)]">
                            <CheckCircle2 className="h-3 w-3" />
                            {isTurkish ? 'Ollama erişilebilir' : 'Ollama reachable'}
                          </p>
                        ) : (
                          <p className="flex items-center gap-1 text-xs text-[var(--danger)]">
                            <WifiOff className="h-3 w-3" />
                            {isTurkish ? 'Ollama erişilemiyor' : 'Ollama unreachable'}
                            {health.reason && ` — ${health.reason}`}
                          </p>
                        )}
                        {health.provider_status === 'reachable' && (
                          <p className="text-xs text-[var(--text-muted)]">
                            {isModelInstalled
                              ? isTurkish ? 'Badhabinot AI kurulu ✓' : 'Badhabinot AI installed ✓'
                              : isTurkish
                                ? 'Model henüz kurulmadı — Docker yeniden başlatın'
                                : 'Model not installed yet — restart Docker'}
                          </p>
                        )}
                      </div>
                    )}
                    {ollamaHealthQuery.isError && !ollamaHealthQuery.isLoading && (
                      <p className="mt-1 flex items-center gap-1 text-xs text-[var(--danger)]">
                        <WifiOff className="h-3 w-3" />
                        {isTurkish ? 'Bağlantı hatası' : 'Connection error'}
                      </p>
                    )}
                  </div>
                  <Button
                    type="button"
                    variant="ghost"
                    onClick={handleTestConnection}
                    loading={ollamaHealthQuery.isLoading}
                  >
                    <RefreshCw className="mr-2 h-4 w-4" />
                    {isTurkish ? 'Test et' : 'Test'}
                  </Button>
                </div>
              </div>
            </>
          )}

          <input type="hidden" {...register('model_mode')} />
          <input type="hidden" {...register('local_model_name')} />

          <div className="flex justify-end md:col-span-2">
            <Button type="submit" loading={isSaving} disabled={!isDirty}>
              {isTurkish ? 'AI modunu kaydet' : 'Save AI mode'}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}
