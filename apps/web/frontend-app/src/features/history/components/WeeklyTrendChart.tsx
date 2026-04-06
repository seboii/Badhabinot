import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import type { WeeklyTrendPointResponse } from '@/types/monitoring'

export function WeeklyTrendChart({ points }: { points: WeeklyTrendPointResponse[] }) {
  const chartData = points.map((point) => ({
    day: point.day.slice(5),
    Alerts: point.alert_count,
    Reminders: point.reminder_count,
    Hydration: point.hydration_count,
  }))

  return (
    <Card className="h-full">
      <CardHeader>
        <div>
          <CardTitle>Weekly trend</CardTitle>
          <CardDescription className="mt-2">Aggregated alerts, reminders, and hydration logs for the selected seven-day window.</CardDescription>
        </div>
      </CardHeader>
      <CardContent className="h-[320px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 10, right: 8, left: -20, bottom: 0 }}>
            <CartesianGrid stroke="var(--line-soft)" vertical={false} />
            <XAxis dataKey="day" tick={{ fill: 'var(--text-muted)', fontSize: 12 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: 'var(--text-soft)', fontSize: 12 }} axisLine={false} tickLine={false} allowDecimals={false} />
            <Tooltip
              contentStyle={{
                background: 'var(--surface-strong)',
                border: '1px solid var(--line-soft)',
                borderRadius: 16,
                color: 'var(--text-strong)',
              }}
            />
            <Legend />
            <Bar dataKey="Alerts" fill="var(--danger)" radius={[8, 8, 0, 0]} />
            <Bar dataKey="Reminders" fill="var(--primary)" radius={[8, 8, 0, 0]} />
            <Bar dataKey="Hydration" fill="var(--info)" radius={[8, 8, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
