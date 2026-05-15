import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useQuery } from '@tanstack/react-query'
import { CheckCircle2, WifiOff, Loader2, RefreshCw } from 'lucide-react'
import { userApi } from '@/api/user'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useLanguage } from '@/i18n/language-provider'
import type { SettingsResponse, ModelMode } from '@/types/user'

const RECOMMENDED_MODELS = [
  { id: 'llama3.2:3b', label: 'Llama 3.2 3B', note: 'Fast, low memory' },
  { id: 'llama3.1:8b', label: 'Llama 3.1 8B', note: 'Balanced' },
  { id: 'mistral:7b', label: 'Mistral 7B', note: 'Strong reasoning' },
  { id: 'gemma3:4b', label: 'Gemma 3 4B', note: 'Lightweight' },
  { id: 'phi4-mini:3.8b', label: 'Phi-4 Mini 3.8B', note: 'Efficient' },
]

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
    formState: { isDirty, errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      model_mode: settings.model_mode,
      local_model_name: settings.local_model_name || 'llama3.2:3b',
      ollama_base_url: settings.ollama_base_url || 'http://localhost:11434',
    },
  })

  const modelMode = watch('model_mode')
  const localModelName = watch('local_model_name')

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
  const installedModels = health?.installed_models ?? []

  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>{isTurkish ? 'AI modu' : 'AI mode'}</CardTitle>
          <CardDescription className="mt-2">
            {isTurkish
              ? 'Bulut API veya yerel Ollama modeli arasinda geçis yap. Yerel mod API anahtarı gerektirmez.'
              : 'Switch between Cloud API and a local Ollama model. Local mode requires no API key.'}
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
                    : isTurkish ? 'Yerel AI (Ollama)' : 'Local AI (Ollama)'}
                </p>
                <p className="mt-1 text-xs text-[var(--text-muted)]">
                  {mode === 'API'
                    ? isTurkish ? 'OpenAI uyumlu uzak servis' : 'OpenAI-compatible remote service'
                    : isTurkish ? 'Yerel makine, internet baglantisi yok' : 'Local machine, no internet required'}
                </p>
              </button>
            ))}
          </div>

          {/* Local mode settings */}
          {modelMode === 'LOCAL' && (
            <>
              <div className="md:col-span-2">
                <label className="flex flex-col gap-2">
                  <span className="text-sm font-medium text-white">
                    {isTurkish ? 'Ollama sunucu adresi' : 'Ollama base URL'}
                  </span>
                  <input
                    className="h-12 rounded-2xl border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] px-4 text-sm text-white outline-none focus:border-[var(--primary)]"
                    {...register('ollama_base_url')}
                    placeholder="http://localhost:11434"
                  />
                  {errors.ollama_base_url && (
                    <span className="text-xs text-[var(--danger)]">{errors.ollama_base_url.message}</span>
                  )}
                </label>
              </div>

              {/* Model list */}
              <div className="md:col-span-2">
                <p className="mb-3 text-sm font-medium text-white">
                  {isTurkish ? 'Onerililen modeller' : 'Recommended models'}
                </p>
                <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                  {RECOMMENDED_MODELS.map((m) => {
                    const installed = installedModels.some((name) => name.startsWith(m.id.split(':')[0]))
                    const selected = localModelName === m.id
                    return (
                      <button
                        key={m.id}
                        type="button"
                        onClick={() => setValue('local_model_name', m.id, { shouldDirty: true })}
                        className={[
                          'flex items-center justify-between rounded-[16px] border px-4 py-3 text-left transition-all',
                          selected
                            ? 'border-[var(--primary)] bg-[rgba(var(--primary-rgb),0.08)]'
                            : 'border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] hover:border-[var(--line-muted)]',
                        ].join(' ')}
                      >
                        <div>
                          <p className="text-sm font-medium text-white">{m.label}</p>
                          <p className="text-xs text-[var(--text-muted)]">{m.note}</p>
                        </div>
                        {testTriggered && !ollamaHealthQuery.isLoading && (
                          installed ? (
                            <CheckCircle2 className="h-4 w-4 shrink-0 text-[var(--success,#4caf50)]" />
                          ) : (
                            <span className="text-xs text-[var(--text-muted)]">
                              {isTurkish ? 'kurulu degil' : 'not installed'}
                            </span>
                          )
                        )}
                      </button>
                    )
                  })}
                </div>

                {/* Custom model input */}
                <label className="mt-3 flex flex-col gap-2">
                  <span className="text-xs text-[var(--text-muted)]">
                    {isTurkish ? 'veya özel model adı girin' : 'or enter a custom model name'}
                  </span>
                  <input
                    className="h-10 rounded-2xl border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] px-4 text-sm text-white outline-none focus:border-[var(--primary)]"
                    {...register('local_model_name')}
                    placeholder="e.g. llama3.2:3b"
                  />
                  {errors.local_model_name && (
                    <span className="text-xs text-[var(--danger)]">{errors.local_model_name.message}</span>
                  )}
                </label>
              </div>

              {/* Connection test */}
              <div className="md:col-span-2 rounded-[20px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4">
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <p className="text-sm font-semibold text-white">
                      {isTurkish ? 'Ollama baglantı testi' : 'Ollama connection test'}
                    </p>
                    {!testTriggered && (
                      <p className="mt-1 text-xs text-[var(--text-muted)]">
                        {isTurkish ? 'Kaydetmeden once test et.' : 'Test before saving.'}
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
                              ? isTurkish ? `${health.model} kurulu` : `${health.model} is installed`
                              : isTurkish
                                ? `${health.model} kurulu değil — \`ollama pull ${health.model}\` komutunu çalıştırın`
                                : `${health.model} not installed — run \`ollama pull ${health.model}\``}
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
