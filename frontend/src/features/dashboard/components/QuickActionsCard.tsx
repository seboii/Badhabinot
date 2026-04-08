import { BellRing, Coffee, GlassWater } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useLanguage } from '@/i18n/language-provider'

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
  const { isTurkish } = useLanguage()

  return (
    <Card className="h-full">
      <CardHeader>
        <div>
          <CardTitle>{isTurkish ? 'Hizli islemler' : 'Quick actions'}</CardTitle>
          <CardDescription className="mt-2">
            {isTurkish
              ? 'Su kaydini manuel ekle veya arka ucun kullandigi hatirlatici akisinin aynisini tetikle.'
              : 'Manually log hydration or trigger the same reminder flow used by the backend.'}
          </CardDescription>
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
          {isTurkish ? '250 ml su kaydet' : 'Log 250 ml water'}
        </Button>
        <Button
          variant="secondary"
          className="justify-start rounded-[24px]"
          iconLeft={<BellRing className="size-4" />}
          loading={pendingAction === 'water_reminder'}
          onClick={onWaterReminder}
        >
          {isTurkish ? 'Su hatirlaticisi tetikle' : 'Trigger water reminder'}
        </Button>
        <Button
          variant="secondary"
          className="justify-start rounded-[24px]"
          iconLeft={<Coffee className="size-4" />}
          loading={pendingAction === 'break'}
          onClick={onBreakReminder}
        >
          {isTurkish ? 'Mola hatirlaticisi tetikle' : 'Trigger break reminder'}
        </Button>
      </CardContent>
    </Card>
  )
}
