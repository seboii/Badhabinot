import type { AnalyzeFrameResponse } from '@/types/monitoring'
import { useLanguage } from '@/i18n/language-provider'

type VisionOverlayPanelProps = {
  analysis: AnalyzeFrameResponse | null
  visible: boolean
}

/**
 * Absolutely-positioned overlay that renders the server-side annotated frame
 * (annotated_frame_base64) on top of the live <video> element.
 * Mount this as a sibling of <video> inside a relative-positioned container.
 */
export function VisionOverlayPanel({ analysis, visible }: VisionOverlayPanelProps) {
  const { isTurkish } = useLanguage()

  if (!visible) {
    return null
  }

  const auth = analysis?.face_auth

  return (
    <div className="pointer-events-none absolute inset-0 z-10">
      {/* Annotated frame — cv2-rendered overlay from vision-service */}
      {analysis?.annotated_frame_base64 ? (
        <img
          src={`data:image/jpeg;base64,${analysis.annotated_frame_base64}`}
          alt={isTurkish ? 'Aciklamali kare' : 'Annotated frame'}
          className="h-full w-full object-cover"
          aria-hidden="true"
        />
      ) : null}

      {/* Face auth status badge — top-right corner */}
      {auth ? (
        <div className="absolute right-3 top-3">
          <span
            className={`rounded-md px-2 py-1 text-xs font-semibold text-white backdrop-blur-sm ${
              !auth.enabled
                ? 'bg-[rgba(100,100,100,0.82)]'
                : auth.authenticated
                  ? 'bg-[rgba(34,197,94,0.82)]'
                  : 'bg-[rgba(239,68,68,0.82)]'
            }`}
          >
            {!auth.enabled
              ? isTurkish ? 'Yüz profili yok' : 'No face profile'
              : auth.authenticated
                ? `${isTurkish ? 'Doğrulandı' : 'Verified'} ${Math.round(auth.confidence * 100)}%`
                : `${isTurkish ? 'Eşleşmedi' : 'No match'} ${Math.round(auth.confidence * 100)}%`}
          </span>
        </div>
      ) : null}

      {/* Event badge strip along the bottom */}
      {analysis?.vision_behavior_events && analysis.vision_behavior_events.length > 0 ? (
        <div className="absolute inset-x-0 bottom-0 flex flex-wrap items-end gap-1.5 p-3">
          {analysis.vision_behavior_events.map((evt, idx) => {
            const bg =
              evt.severity === 'high'
                ? 'bg-[rgba(239,68,68,0.82)]'
                : evt.severity === 'medium'
                  ? 'bg-[rgba(251,146,60,0.82)]'
                  : 'bg-[rgba(96,165,250,0.82)]'
            return (
              <span
                key={idx}
                className={`rounded-md px-2 py-0.5 text-xs font-semibold text-white backdrop-blur-sm ${bg}`}
              >
                {evt.event_type.replace(/_/g, ' ')}
              </span>
            )
          })}
        </div>
      ) : null}
    </div>
  )
}
