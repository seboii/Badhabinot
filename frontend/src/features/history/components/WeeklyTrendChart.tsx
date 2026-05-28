import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useBreakpoint } from '@/hooks/use-breakpoint'
import { useLanguage } from '@/i18n/language-provider'
import type { WeeklyTrendPointResponse } from '@/types/monitoring'

export function WeeklyTrendChart({ points }: { points: WeeklyTrendPointResponse[] }) {
  const { isTurkish } = useLanguage()
  const { isMobile } = useBreakpoint()

  const chartData = points.map((point) => ({
    day: point.day.slice(5),
    alerts: point.alert_count,
    reminders: point.reminder_count,
    hydration: point.hydration_count,
  }))

  const tickFontSize = isMobile ? 10 : 12
  const barRadius = isMobile ? [4, 4, 0, 0] : [8, 8, 0, 0]

  return (
    <Card className="h-full">
      <CardHeader>
        <div>
          <CardTitle>{isTurkish ? 'Haftalik trend' : 'Weekly trend'}</CardTitle>
          <CardDescription className="mt-2">
            {isTurkish
              ? 'Secilen yedi gunluk pencere icin toplu uyari, hatirlatici ve su kayitlari.'
              : 'Aggregated alerts, reminders, and hydration logs for the selected seven-day window.'}
          </CardDescription>
        </div>
      </CardHeader>
      <CardContent className="h-[200px] sm:h-[260px] lg:h-[320px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 10, right: 8, left: isMobile ? -28 : -20, bottom: 0 }}>
            <CartesianGrid stroke="var(--line-soft)" vertical={false} />
            <XAxis
              dataKey="day"
              tick={{ fill: 'var(--text-muted)', fontSize: tickFontSize }}
              axisLine={false}
              tickLine={false}
              interval={isMobile ? 'preserveStartEnd' : 0}
            />
            <YAxis
              tick={{ fill: 'var(--text-soft)', fontSize: tickFontSize }}
              axisLine={false}
              tickLine={false}
              allowDecimals={false}
              width={isMobile ? 28 : 40}
            />
            <Tooltip
              contentStyle={{
                background: 'var(--surface-strong)',
                border: '1px solid var(--line-soft)',
                borderRadius: 16,
                color: 'var(--text-strong)',
                fontSize: isMobile ? 12 : 14,
              }}
            />
            <Legend wrapperStyle={{ fontSize: isMobile ? 10 : 12 }} />
            <Bar dataKey="alerts" name={isTurkish ? 'Uyarilar' : 'Alerts'} fill="var(--danger)" radius={barRadius as [number, number, number, number]} isAnimationActive={!isMobile} />
            <Bar dataKey="reminders" name={isTurkish ? 'Hatirlaticilar' : 'Reminders'} fill="var(--primary)" radius={barRadius as [number, number, number, number]} isAnimationActive={!isMobile} />
            <Bar dataKey="hydration" name={isTurkish ? 'Su kayitlari' : 'Hydration'} fill="var(--info)" radius={barRadius as [number, number, number, number]} isAnimationActive={!isMobile} />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
