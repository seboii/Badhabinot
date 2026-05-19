import type { ErrorInfo, ReactNode } from 'react'
import { Component } from 'react'
import { AlertTriangle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'

type Props = {
  children: ReactNode
  fallback?: ReactNode
}

type State = {
  hasError: boolean
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(): State {
    return { hasError: true }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('[ErrorBoundary] Uncaught error:', error, info.componentStack)
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <div className="flex min-h-[280px] items-center justify-center p-6">
          <Card className="w-full max-w-md">
            <CardContent className="flex flex-col items-center gap-4 p-8 text-center">
              <div className="flex size-14 items-center justify-center rounded-2xl bg-[rgba(244,63,94,0.12)]">
                <AlertTriangle className="size-6 text-[var(--danger)]" />
              </div>
              <div>
                <p className="text-base font-semibold text-[var(--text-strong)]">Bir şeyler ters gitti</p>
                <p className="mt-1 text-sm text-[var(--text-muted)]">
                  Bu bölüm yüklenirken beklenmedik bir hata oluştu.
                </p>
              </div>
              <Button variant="secondary" onClick={() => window.location.reload()}>
                Sayfayı Yenile
              </Button>
            </CardContent>
          </Card>
        </div>
      )
    }

    return this.props.children
  }
}
