import { useEffect, useRef, useState } from 'react'

// ── MediaPipe CDN paths (must match installed package version) ────────────────
const WASM_CDN = 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.35/wasm'
const FACE_MODEL =
  'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task'
const HAND_MODEL =
  'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task'

// Module-level cache — models load once for the entire session.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
let _modelsCache: any | null = null
// eslint-disable-next-line @typescript-eslint/no-explicit-any
let _loadPromise: Promise<any> | null = null

// eslint-disable-next-line @typescript-eslint/no-explicit-any
async function ensureModels(): Promise<any> {
  if (_modelsCache) return _modelsCache
  if (_loadPromise) return _loadPromise

  _loadPromise = (async () => {
    const { FaceLandmarker, HandLandmarker, FilesetResolver, DrawingUtils } =
      await import('@mediapipe/tasks-vision')

    const vision = await FilesetResolver.forVisionTasks(WASM_CDN)

    const [faceLandmarker, handLandmarker] = await Promise.all([
      FaceLandmarker.createFromOptions(vision, {
        baseOptions: { modelAssetPath: FACE_MODEL, delegate: 'GPU' },
        runningMode: 'VIDEO',
        numFaces: 1,
        outputFaceBlendshapes: false,
        outputFacialTransformationMatrixes: false,
      }),
      HandLandmarker.createFromOptions(vision, {
        baseOptions: { modelAssetPath: HAND_MODEL, delegate: 'GPU' },
        runningMode: 'VIDEO',
        numHands: 2,
      }),
    ])

    _modelsCache = { FaceLandmarker, HandLandmarker, DrawingUtils, faceLandmarker, handLandmarker }
    return _modelsCache
  })()

  return _loadPromise
}

export type MediaPipeLiveState = {
  ready: boolean
  loading: boolean
  error: string | null
}

/**
 * Runs MediaPipe FaceLandmarker + HandLandmarker in the browser at ~30 fps,
 * drawing results directly onto canvasRef. No server round-trip.
 *
 * @param videoRef - the live <video> element
 * @param canvasRef - a <canvas> absolutely positioned over the video
 * @param active - enable/disable the loop (false = canvas cleared)
 */
export function useMediaPipeLive(
  videoRef: React.RefObject<HTMLVideoElement | null>,
  canvasRef: React.RefObject<HTMLCanvasElement | null>,
  active: boolean,
): MediaPipeLiveState {
  const [state, setState] = useState<MediaPipeLiveState>({
    ready: false,
    loading: false,
    error: null,
  })

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const modelsRef = useRef<any>(null)
  const rafRef = useRef<number>(0)
  const activeRef = useRef(active)
  activeRef.current = active

  // Load models once when first activated
  useEffect(() => {
    if (!active) return

    let cancelled = false
    setState(s => ({ ...s, loading: true, error: null }))

    ensureModels()
      .then(models => {
        if (cancelled) return
        modelsRef.current = models
        setState({ ready: true, loading: false, error: null })
      })
      .catch((err: unknown) => {
        if (cancelled) return
        console.error('[MediaPipe] failed to load models:', err)
        setState({ ready: false, loading: false, error: String(err) })
      })

    return () => {
      cancelled = true
    }
  }, [active])

  // rAF detection + drawing loop
  useEffect(() => {
    if (!state.ready) return

    const models = modelsRef.current!

    // Cache DrawingUtils per canvas context to avoid re-allocating every frame
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    let du: any = null
    let lastCtx: CanvasRenderingContext2D | null = null

    function loop() {
      const video = videoRef.current
      const canvas = canvasRef.current

      if (!activeRef.current) {
        if (canvas) {
          const ctx = canvas.getContext('2d')
          ctx?.clearRect(0, 0, canvas.width, canvas.height)
        }
        // Don't schedule next frame — restarted by the effect when active flips.
        return
      }

      rafRef.current = requestAnimationFrame(loop)

      if (!video || video.readyState < 2 || video.videoWidth === 0 || !canvas) return

      // Keep canvas pixel dimensions in sync with the video
      if (canvas.width !== video.videoWidth || canvas.height !== video.videoHeight) {
        canvas.width = video.videoWidth
        canvas.height = video.videoHeight
        du = null // invalidate cached DrawingUtils after resize
      }

      const ctx = canvas.getContext('2d')
      if (!ctx) return

      ctx.clearRect(0, 0, canvas.width, canvas.height)

      // Re-create DrawingUtils only when the context object changes
      if (ctx !== lastCtx) {
        du = new models.DrawingUtils(ctx)
        lastCtx = ctx
      }

      const now = performance.now()

      try {
        const faceResult = models.faceLandmarker.detectForVideo(video, now)
        const handResult = models.handLandmarker.detectForVideo(video, now)

        // ── Face mesh ───────────────────────────────────────────────────────
        for (const landmarks of faceResult.faceLandmarks ?? []) {
          // Thin tessellation grid
          du.drawConnectors(landmarks, models.FaceLandmarker.FACE_LANDMARKS_TESSELATION, {
            color: 'rgba(0,220,120,0.10)',
            lineWidth: 0.8,
          })
          // Face oval — brighter
          du.drawConnectors(landmarks, models.FaceLandmarker.FACE_LANDMARKS_FACE_OVAL, {
            color: 'rgba(0,220,120,0.55)',
            lineWidth: 1.5,
          })
          // Eyes
          du.drawConnectors(landmarks, models.FaceLandmarker.FACE_LANDMARKS_LEFT_EYE, {
            color: 'rgba(80,180,255,0.80)',
            lineWidth: 1.5,
          })
          du.drawConnectors(landmarks, models.FaceLandmarker.FACE_LANDMARKS_RIGHT_EYE, {
            color: 'rgba(80,180,255,0.80)',
            lineWidth: 1.5,
          })
          du.drawConnectors(landmarks, models.FaceLandmarker.FACE_LANDMARKS_LEFT_EYEBROW, {
            color: 'rgba(80,180,255,0.55)',
            lineWidth: 1,
          })
          du.drawConnectors(landmarks, models.FaceLandmarker.FACE_LANDMARKS_RIGHT_EYEBROW, {
            color: 'rgba(80,180,255,0.55)',
            lineWidth: 1,
          })
          // Irises
          du.drawConnectors(landmarks, models.FaceLandmarker.FACE_LANDMARKS_LEFT_IRIS, {
            color: 'rgba(255,220,50,0.80)',
            lineWidth: 1.5,
          })
          du.drawConnectors(landmarks, models.FaceLandmarker.FACE_LANDMARKS_RIGHT_IRIS, {
            color: 'rgba(255,220,50,0.80)',
            lineWidth: 1.5,
          })
          // Lips
          du.drawConnectors(landmarks, models.FaceLandmarker.FACE_LANDMARKS_LIPS, {
            color: 'rgba(80,120,255,0.75)',
            lineWidth: 1.5,
          })
        }

        // ── Hand skeleton ───────────────────────────────────────────────────
        for (const landmarks of handResult.landmarks ?? []) {
          du.drawConnectors(landmarks, models.HandLandmarker.HAND_CONNECTIONS, {
            color: 'rgba(0,220,255,0.75)',
            lineWidth: 2,
          })
          du.drawLandmarks(landmarks, {
            color: 'rgba(0,255,200,0.90)',
            lineWidth: 1,
            radius: 3,
          })
        }
      } catch {
        // Detection errors (e.g. during model warm-up) are non-fatal — skip frame
      }
    }

    rafRef.current = requestAnimationFrame(loop)

    return () => {
      cancelAnimationFrame(rafRef.current)
      const canvas = canvasRef.current
      if (canvas) {
        const ctx = canvas.getContext('2d')
        ctx?.clearRect(0, 0, canvas.width, canvas.height)
      }
    }
  }, [state.ready, canvasRef, videoRef])

  return state
}
