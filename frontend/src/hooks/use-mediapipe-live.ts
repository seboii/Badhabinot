import { useEffect, useRef, useState } from 'react'
import { platform } from '@/lib/platform'

// ─────────────────────────────────────────────────────────────────────────────
// MediaPipe — CDN paths (must match installed package version)
// ─────────────────────────────────────────────────────────────────────────────
const MP_WASM_CDN = 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.35/wasm'
const FACE_MODEL =
  'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task'
const HAND_MODEL =
  'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task'

// Module-level caches — loaded once per browser session
// eslint-disable-next-line @typescript-eslint/no-explicit-any
let _mpCache: any | null = null
// eslint-disable-next-line @typescript-eslint/no-explicit-any
let _mpPromise: Promise<any> | null = null

// eslint-disable-next-line @typescript-eslint/no-explicit-any
async function ensureMediaPipe(): Promise<any> {
  if (_mpCache) return _mpCache
  if (_mpPromise) return _mpPromise

  _mpPromise = (async () => {
    const { FaceLandmarker, HandLandmarker, FilesetResolver, DrawingUtils } =
      await import('@mediapipe/tasks-vision')
    const vision = await FilesetResolver.forVisionTasks(MP_WASM_CDN)
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
    _mpCache = { FaceLandmarker, HandLandmarker, DrawingUtils, faceLandmarker, handLandmarker }
    return _mpCache
  })()

  return _mpPromise
}

// ─────────────────────────────────────────────────────────────────────────────
// YOLOv8n-pose — ONNX Runtime Web inference
// ─────────────────────────────────────────────────────────────────────────────

/** WASM path for onnxruntime-web (CDN, matches installed 1.25.1) */
const ORT_WASM_CDN = 'https://cdn.jsdelivr.net/npm/onnxruntime-web@1.25.1/dist/'
const YOLO_MODEL_PATH = '/models/yolov8n-pose.onnx'
const YOLO_INPUT_SIZE = 640

// eslint-disable-next-line @typescript-eslint/no-explicit-any
let _ortSession: any | null = null
// eslint-disable-next-line @typescript-eslint/no-explicit-any
let _ortPromise: Promise<any> | null = null

// eslint-disable-next-line @typescript-eslint/no-explicit-any
async function ensureOrtSession(): Promise<any> {
  if (_ortSession) return _ortSession
  if (_ortPromise) return _ortPromise

  _ortPromise = (async () => {
    const ort = await import('onnxruntime-web')
    ort.env.wasm.wasmPaths = ORT_WASM_CDN
    const session = await ort.InferenceSession.create(YOLO_MODEL_PATH, {
      executionProviders: ['webgl', 'wasm'],
      graphOptimizationLevel: 'all',
    })
    _ortSession = { ort, session }
    return _ortSession
  })()

  return _ortPromise
}

// COCO 17 keypoint colors
const KP_COLORS = [
  '#FF6B6B', // 0  nose
  '#FF9FF3', '#FF9FF3', // 1,2  eyes
  '#FECA57', '#FECA57', // 3,4  ears
  '#48DBFB', '#54A0FF', // 5,6  shoulders
  '#1DD1A1', '#10AC84', // 7,8  elbows
  '#FFEAA7', '#F9CA24', // 9,10 wrists
  '#A29BFE', '#6C5CE7', // 11,12 hips
  '#FD79A8', '#E84393', // 13,14 knees
  '#FDCB6E', '#E17055', // 15,16 ankles
]

// COCO skeleton pairs (keypoint index pairs to connect with a line)
const SKELETON_PAIRS: [number, number][] = [
  [0, 1], [0, 2],   // nose → eyes
  [1, 3], [2, 4],   // eyes → ears
  [5, 6],           // left shoulder ↔ right shoulder
  [5, 7], [7, 9],   // left arm
  [6, 8], [8, 10],  // right arm
  [5, 11], [6, 12], // torso sides
  [11, 12],         // left hip ↔ right hip
  [11, 13], [13, 15], // left leg
  [12, 14], [14, 16], // right leg
]

// Skeleton line colors grouped by body region
const SKELETON_COLORS: Record<string, string> = {
  '0,1': 'rgba(255,200,100,0.75)',
  '0,2': 'rgba(255,200,100,0.75)',
  '1,3': 'rgba(255,200,100,0.75)',
  '2,4': 'rgba(255,200,100,0.75)',
  '5,6': 'rgba(72,219,251,0.80)',
  '5,7': 'rgba(29,209,161,0.80)',
  '7,9': 'rgba(29,209,161,0.80)',
  '6,8': 'rgba(84,160,255,0.80)',
  '8,10': 'rgba(84,160,255,0.80)',
  '5,11': 'rgba(162,155,254,0.70)',
  '6,12': 'rgba(162,155,254,0.70)',
  '11,12': 'rgba(162,155,254,0.70)',
  '11,13': 'rgba(253,121,168,0.80)',
  '13,15': 'rgba(253,121,168,0.80)',
  '12,14': 'rgba(108,92,231,0.80)',
  '14,16': 'rgba(108,92,231,0.80)',
}

type PoseKeypoint = { x: number; y: number; conf: number; visible: boolean }

/** Resize video frame to 640×640 and return NCHW Float32Array (RGB, 0-1) */
function preprocessVideoFrame(
  video: HTMLVideoElement,
  size: number,
  offscreen: HTMLCanvasElement,
): Float32Array {
  const ctx = offscreen.getContext('2d')!
  ctx.drawImage(video, 0, 0, size, size)
  const { data } = ctx.getImageData(0, 0, size, size)
  const pixels = size * size
  const out = new Float32Array(3 * pixels)
  for (let i = 0; i < pixels; i++) {
    out[i]           = data[i * 4]     / 255  // R
    out[pixels + i]  = data[i * 4 + 1] / 255  // G
    out[pixels * 2 + i] = data[i * 4 + 2] / 255  // B
  }
  return out
}

/**
 * Decode YOLOv8 pose output [1, 56, 8400].
 * Returns keypoints for the highest-confidence detection.
 * Coordinates are scaled to the original video dimensions.
 */
function decodePose(
  output: Float32Array,
  videoW: number,
  videoH: number,
  confThresh = 0.35,
  kpConfThresh = 0.5,
): PoseKeypoint[] {
  const N = 8400 // number of anchor proposals
  const scaleX = videoW / YOLO_INPUT_SIZE
  const scaleY = videoH / YOLO_INPUT_SIZE

  // Find proposal with highest object confidence
  let bestConf = confThresh
  let bestIdx = -1
  for (let j = 0; j < N; j++) {
    const conf = output[4 * N + j]
    if (conf > bestConf) {
      bestConf = conf
      bestIdx = j
    }
  }
  if (bestIdx === -1) return []

  // Extract all 17 keypoints for the best detection
  const kps: PoseKeypoint[] = []
  for (let k = 0; k < 17; k++) {
    const base = (5 + k * 3) * N
    const x    = output[base          + bestIdx] * scaleX
    const y    = output[base + N      + bestIdx] * scaleY
    const conf = output[base + N * 2  + bestIdx]
    kps.push({ x, y, conf, visible: conf >= kpConfThresh })
  }
  return kps
}

/** Draw skeleton lines then keypoint dots for one detected person */
function drawPose(
  ctx: CanvasRenderingContext2D,
  kps: PoseKeypoint[],
): void {
  if (!kps.length) return

  ctx.save()
  ctx.lineWidth = 2.5
  ctx.lineCap = 'round'

  // Lines first (drawn under dots)
  for (const [a, b] of SKELETON_PAIRS) {
    const ka = kps[a], kb = kps[b]
    if (!ka?.visible || !kb?.visible) continue
    ctx.strokeStyle = SKELETON_COLORS[`${a},${b}`] ?? 'rgba(255,255,255,0.60)'
    ctx.beginPath()
    ctx.moveTo(ka.x, ka.y)
    ctx.lineTo(kb.x, kb.y)
    ctx.stroke()
  }

  // Keypoint dots
  for (let i = 0; i < kps.length; i++) {
    const kp = kps[i]
    if (!kp.visible) continue
    const color = KP_COLORS[i] ?? '#FFFFFF'
    ctx.fillStyle = color
    ctx.beginPath()
    ctx.arc(kp.x, kp.y, 5, 0, Math.PI * 2)
    ctx.fill()
    // Crisp white outline
    ctx.strokeStyle = 'rgba(255,255,255,0.85)'
    ctx.lineWidth = 1.5
    ctx.stroke()
    ctx.lineWidth = 2.5 // restore for next iteration
  }

  ctx.restore()
}

// ─────────────────────────────────────────────────────────────────────────────
// Hook
// ─────────────────────────────────────────────────────────────────────────────

export type MediaPipeLiveState = {
  ready: boolean
  loading: boolean
  error: string | null
}

/**
 * Runs MediaPipe (face mesh + hands) at ~30 fps AND YOLOv8n-pose at ~10 fps
 * in the browser, drawing all results onto canvasRef. No server round-trip.
 *
 * @param videoRef  – live <video> element
 * @param canvasRef – transparent <canvas> absolutely positioned over the video
 * @param active    – enable / disable (canvas is cleared when false)
 */
export function useMediaPipeLive(
  videoRef: React.RefObject<HTMLVideoElement | null>,
  canvasRef: React.RefObject<HTMLCanvasElement | null>,
  active: boolean,
): MediaPipeLiveState {
  // MediaPipe + ONNX are browser-only; disable on native (constant — safe to gate effects)
  const effectiveActive = active && !platform.isNative

  const [state, setState] = useState<MediaPipeLiveState>({
    ready: false,
    loading: false,
    error: null,
  })

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const mpRef  = useRef<any>(null)
  const rafRef = useRef<number>(0)

  // Latest YOLO pose result — shared between async inference and rAF draw
  const poseRef = useRef<PoseKeypoint[]>([])

  // ── Load MediaPipe models ─────────────────────────────────────────────────
  useEffect(() => {
    if (!effectiveActive) return
    let cancelled = false
    setState(s => ({ ...s, loading: true, error: null }))

    ensureMediaPipe()
      .then(mp => {
        if (cancelled) return
        mpRef.current = mp
        setState({ ready: true, loading: false, error: null })
      })
      .catch((err: unknown) => {
        if (cancelled) return
        console.error('[MediaPipe] failed to load models:', err)
        setState({ ready: false, loading: false, error: String(err) })
      })

    return () => { cancelled = true }
  }, [effectiveActive])

  // ── Load ONNX session (YOLOv8 pose) — independent of MediaPipe ───────────
  useEffect(() => {
    if (!effectiveActive) return
    ensureOrtSession().catch((err: unknown) =>
      console.error('[YOLOPose] ONNX session failed:', err),
    )
  }, [effectiveActive])

  // ── YOLO inference loop — async, ~10 fps max ──────────────────────────────
  useEffect(() => {
    if (!state.ready || !effectiveActive) return

    // Offscreen canvas reused across inference calls to avoid GC pressure
    const offscreen = document.createElement('canvas')
    offscreen.width = YOLO_INPUT_SIZE
    offscreen.height = YOLO_INPUT_SIZE

    let inferring = false

    const id = window.setInterval(async () => {
      if (inferring) return
      const video = videoRef.current
      if (!video || video.readyState < 2 || video.videoWidth === 0) return

      // Grab session — might still be loading
      const ortCtx = _ortSession
      if (!ortCtx) return

      inferring = true
      try {
        const { ort, session } = ortCtx
        const inputData = preprocessVideoFrame(video, YOLO_INPUT_SIZE, offscreen)
        const tensor = new ort.Tensor('float32', inputData, [1, 3, YOLO_INPUT_SIZE, YOLO_INPUT_SIZE])
        const feeds: Record<string, unknown> = {}
        // YOLOv8 ONNX input name is always "images"
        feeds['images'] = tensor
        const results = await session.run(feeds)
        // Output tensor name from YOLOv8 ONNX export is "output0"
        const outputTensor = results['output0']
        if (outputTensor) {
          poseRef.current = decodePose(
            outputTensor.data as Float32Array,
            video.videoWidth,
            video.videoHeight,
          )
        }
      } catch (err) {
        console.warn('[YOLOPose] inference error:', err)
        poseRef.current = []
      } finally {
        inferring = false
      }
    }, 100) // 10 fps cap

    return () => window.clearInterval(id)
  }, [state.ready, effectiveActive, videoRef])

  // ── rAF drawing loop — MediaPipe + YOLO pose drawn together ──────────────
  useEffect(() => {
    if (!state.ready || !effectiveActive) return

    const mp = mpRef.current!

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    let du: any = null
    let lastCtx: CanvasRenderingContext2D | null = null

    function loop() {
      rafRef.current = requestAnimationFrame(loop)

      const video  = videoRef.current
      const canvas = canvasRef.current
      if (!video || video.readyState < 2 || video.videoWidth === 0 || !canvas) return

      if (canvas.width !== video.videoWidth || canvas.height !== video.videoHeight) {
        canvas.width  = video.videoWidth
        canvas.height = video.videoHeight
        du = null
      }

      const ctx = canvas.getContext('2d')
      if (!ctx) return
      ctx.clearRect(0, 0, canvas.width, canvas.height)

      if (ctx !== lastCtx) {
        du = new mp.DrawingUtils(ctx)
        lastCtx = ctx
      }

      const now = performance.now()

      try {
        // ── MediaPipe: face mesh ──────────────────────────────────────────
        const faceResult = mp.faceLandmarker.detectForVideo(video, now)
        for (const landmarks of faceResult.faceLandmarks ?? []) {
          du.drawConnectors(landmarks, mp.FaceLandmarker.FACE_LANDMARKS_TESSELATION, {
            color: 'rgba(0,220,120,0.10)', lineWidth: 0.8,
          })
          du.drawConnectors(landmarks, mp.FaceLandmarker.FACE_LANDMARKS_FACE_OVAL, {
            color: 'rgba(0,220,120,0.55)', lineWidth: 1.5,
          })
          du.drawConnectors(landmarks, mp.FaceLandmarker.FACE_LANDMARKS_LEFT_EYE, {
            color: 'rgba(80,180,255,0.80)', lineWidth: 1.5,
          })
          du.drawConnectors(landmarks, mp.FaceLandmarker.FACE_LANDMARKS_RIGHT_EYE, {
            color: 'rgba(80,180,255,0.80)', lineWidth: 1.5,
          })
          du.drawConnectors(landmarks, mp.FaceLandmarker.FACE_LANDMARKS_LEFT_EYEBROW, {
            color: 'rgba(80,180,255,0.55)', lineWidth: 1,
          })
          du.drawConnectors(landmarks, mp.FaceLandmarker.FACE_LANDMARKS_RIGHT_EYEBROW, {
            color: 'rgba(80,180,255,0.55)', lineWidth: 1,
          })
          du.drawConnectors(landmarks, mp.FaceLandmarker.FACE_LANDMARKS_LEFT_IRIS, {
            color: 'rgba(255,220,50,0.80)', lineWidth: 1.5,
          })
          du.drawConnectors(landmarks, mp.FaceLandmarker.FACE_LANDMARKS_RIGHT_IRIS, {
            color: 'rgba(255,220,50,0.80)', lineWidth: 1.5,
          })
          du.drawConnectors(landmarks, mp.FaceLandmarker.FACE_LANDMARKS_LIPS, {
            color: 'rgba(80,120,255,0.75)', lineWidth: 1.5,
          })
        }

        // ── MediaPipe: hand skeleton ──────────────────────────────────────
        const handResult = mp.handLandmarker.detectForVideo(video, now)
        for (const landmarks of handResult.landmarks ?? []) {
          du.drawConnectors(landmarks, mp.HandLandmarker.HAND_CONNECTIONS, {
            color: 'rgba(0,220,255,0.75)', lineWidth: 2,
          })
          du.drawLandmarks(landmarks, {
            color: 'rgba(0,255,200,0.90)', lineWidth: 1, radius: 3,
          })
        }
      } catch {
        // MediaPipe detection errors during warm-up — skip frame silently
      }

      // ── YOLOv8 pose — drawn from last async result (always current frame) ─
      drawPose(ctx, poseRef.current)
    }

    rafRef.current = requestAnimationFrame(loop)

    return () => {
      cancelAnimationFrame(rafRef.current)
      const canvas = canvasRef.current
      if (canvas) {
        canvas.getContext('2d')?.clearRect(0, 0, canvas.width, canvas.height)
      }
    }
  }, [state.ready, effectiveActive, canvasRef, videoRef])

  return state
}
