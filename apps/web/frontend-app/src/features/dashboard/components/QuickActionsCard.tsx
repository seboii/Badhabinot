import { BellRing, Coffee, GlassWater } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

type QuickActionsCardProps = {
  onLogWater: () => void
  onWaterReminder: () => void
  onBreakReminder: () => void
  pendingAction?: 'water' | 'water_reminder' | 'break'
}

export function QuickActionsCard({
  onLogWater,
  onWaterReminder,
  onBreakReminder,
  pendingAction,
}: QuickActionsCardProps) {
  return (
    <Card className="h-full">
      <CardHeader>
        <div>
          <CardTitle>Quick actions</CardTitle>
          <CardDescription className="mt-2">Manually log hydration or trigger the same reminder flow used by the backend.</CardDescription>
        </div>
      </CardHeader>
      <CardContent className="grid gap-3">
        <Button
          variant="secondary"
          className="justify-start rounded-[24px]"
          iconLeft={<GlassWater className="size-4" />}
          loading={pendingAction === 'water'}
          onClick={onLogWater}
        >
          Log 250 ml water
        </Button>
        <Button
          variant="secondary"
          className="justify-start rounded-[24px]"
          iconLeft={<BellRing className="size-4" />}
          loading={pendingAction === 'water_reminder'}
          onClick={onWaterReminder}
        >
          Trigger water reminder
        </Button>
        <Button
          variant="secondary"
          className="justify-start rounded-[24px]"
          iconLeft={<Coffee className="size-4" />}
          loading={pendingAction === 'break'}
          onClick={onBreakReminder}
        >
          Trigger break reminder
        </Button>
      </CardContent>
    </Card>
  )
}

