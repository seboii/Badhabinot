import { useState } from 'react'
import { format } from 'date-fns'
import { useQuery } from '@tanstack/react-query'
import { BellRing, ClipboardList, Droplets, ShieldAlert } from 'lucide-react'
import { monitoringApi } from '@/api/monitoring'
import { ActivityFeedCard } from '@/features/dashboard/components/ActivityFeedCard'
import { BehaviorEventListCard } from '@/features/history/components/BehaviorEventListCard'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { LoadingCard } from '@/components/ui/loading-state'
import { formatMilliliters, toPercent } from '@/lib/format'

function ReportMetric({
  label,
  value,
  detail,
  icon: Icon,
}: {
  label: string
  value: string
  detail: string
  icon: typeof ClipboardList
}) {
  return (
    <Card>
      <CardContent className="p-5">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-sm font-medium text-[var(--text-muted)]">{label}</p>
            <p className="mt-4 text-3xl font-extrabold tracking-tight text-white">{value}</p>
            <p className="mt-3 text-sm text-[var(--text-muted)]">{detail}</p>
          </div>
          <div className="flex size-12 items-center justify-center rounded-2xl bg-[rgba(255,255,255,0.06)]">
            <Icon className="size-5 text-white" />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export function ReportsPage() {
  const [selectedDate, setSelectedDate] = useState(format(new Date(), 'yyyy-MM-dd'))

  const reportQuery = useQuery({
    queryKey: ['daily-report', selectedDate],
    queryFn: () => monitoringApi.getDailyReport(selectedDate),
  })

  if (reportQuery.isLoading || !reportQuery.data) {
    return <LoadingCard message="Generating daily report" />
  }

  const report = reportQuery.data

  return (
    <div className="space-y-6">
      <Card>
        <CardContent className="flex flex-col gap-4 p-5 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-sm font-medium text-[var(--text-muted)]">Daily report</p>
            <p className="mt-2 text-xl font-bold text-white">End-of-day behavior summary</p>
            <p className="mt-2 text-sm text-[var(--text-muted)]">
              This report is generated from stored behavior events, reminders, hydration logs, and analysis sessions.
            </p>
          </div>
          <div className="w-full max-w-xs">
            <Input label="Report date" type="date" value={selectedDate} onChange={(event) => setSelectedDate(event.target.value)} />
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <ReportMetric
          label="Analyses"
          value={`${report.analyses_completed}`}
          detail="Processed frame analyses for the selected day."
          icon={ClipboardList}
        />
        <ReportMetric
          label="Posture alerts"
          value={`${report.posture_alert_count}`}
          detail={`Poor-posture share ${toPercent(report.poor_posture_ratio)}.`}
          icon={ShieldAlert}
        />
        <ReportMetric
          label="Reminders"
          value={`${report.reminder_count}`}
          detail="Automatic and manual reminders recorded in the backend."
          icon={BellRing}
        />
        <ReportMetric
          label="Hydration"
          value={formatMilliliters(report.hydration_progress_ml)}
          detail={`Target ${formatMilliliters(report.water_goal_ml)}.`}
          icon={Droplets}
        />
      </div>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.1fr)_minmax(360px,0.9fr)]">
        <Card>
          <CardHeader>
            <div>
              <div className="flex items-center gap-3">
                <CardTitle>Summary</CardTitle>
                <Badge variant="primary">{report.report_date}</Badge>
              </div>
              <CardDescription className="mt-2">Generated at {new Date(report.generated_at).toLocaleTimeString()}</CardDescription>
            </div>
          </CardHeader>
          <CardContent className="space-y-5">
            <div className="rounded-[24px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-5">
              <p className="text-sm leading-7 text-white">{report.summary}</p>
            </div>
            <div className="space-y-3">
              <p className="text-sm font-semibold text-white">Recommendations</p>
              {report.recommendations.map((recommendation) => (
                <div
                  key={recommendation}
                  className="rounded-[20px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4 text-sm leading-6 text-[var(--text-muted)]"
                >
                  {recommendation}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
        <BehaviorEventListCard
          title="Key behavior events"
          description="Highest-signal behavior detections for the selected report date."
          events={report.key_behavior_events}
        />
      </div>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.05fr)_minmax(360px,0.95fr)]">
        <ActivityFeedCard
          title="Timeline"
          description="Combined reminders, alerts, and manual actions from the selected day."
          items={report.timeline}
        />
        <Card>
          <CardHeader>
            <div>
              <CardTitle>Reminder history</CardTitle>
              <CardDescription className="mt-2">Backend-generated reminder records used for coaching and reporting.</CardDescription>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            {report.reminders.length === 0 ? (
              <p className="text-sm text-[var(--text-muted)]">No reminders were generated for the selected date.</p>
            ) : (
              report.reminders.map((reminder) => (
                <div
                  key={reminder.reminder_id}
                  className="rounded-[20px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4"
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="text-sm font-semibold text-white">{reminder.reminder_type.replace(/_/g, ' ')}</p>
                    <Badge variant="info">{reminder.source}</Badge>
                  </div>
                  <p className="mt-2 text-sm leading-6 text-[var(--text-muted)]">{reminder.message}</p>
                  <p className="mt-2 text-xs text-[var(--text-soft)]">{reminder.trigger_reason}</p>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
