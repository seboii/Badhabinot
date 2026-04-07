import { useEffect, useRef, useState } from 'react'
import { useLanguage } from '@/i18n/language-provider'

export type CameraPermissionState = 'idle' | 'requesting' | 'granted' | 'denied' | 'unsupported' | 'error'

type CapturedFrame = {
  image_base64: string
  image_content_type: string
}

const LOCALHOST_HOSTS = new Set(['localhost', '127.0.0.1', '[::1]'])

export function useCamera() {
  const { isTurkish } = useLanguage()
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const [permissionState, setPermissionState] = useState<CameraPermissionState>('idle')
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [streamReady, setStreamReady] = useState(false)

  const attachStream = async (stream: MediaStream) => {
    const video = videoRef.current
    if (!video) {
      setPermissionState('error')
      setErrorMessage(
        isTurkish
          ? 'Kamera onizleme ogesi hazir degil. Lutfen tekrar dene.'
          : 'Camera preview element is not ready. Please retry.',
      )
      return false
    }

    video.srcObject = stream
    video.autoplay = true
    video.muted = true
    video.playsInline = true

    try {
      await video.play()
      setStreamReady(true)
      return true
    } catch (error) {
      setStreamReady(false)
      setPermissionState('error')
      setErrorMessage(error instanceof Error ? error.message : isTurkish ? 'Kamera onizlemesi oynatilamadi.' : 'Unable to play camera preview.')
      return false
    }
  }

  const stopCamera = () => {
    streamRef.current?.getTracks().forEach((track) => {
      track.onended = null
      track.stop()
    })
    streamRef.current = null
    setStreamReady(false)

    if (videoRef.current) {
      videoRef.current.pause()
      videoRef.current.srcObject = null
    }
  }

  const requestCamera = async () => {
    if (!window.isSecureContext && !LOCALHOST_HOSTS.has(window.location.hostname)) {
      setPermissionState('unsupported')
      setErrorMessage(isTurkish ? 'Kamera erisimi HTTPS veya localhost gerektirir.' : 'Camera access requires HTTPS or localhost.')
      return false
    }

    if (!navigator.mediaDevices?.getUserMedia) {
      setPermissionState('unsupported')
      setErrorMessage(isTurkish ? 'Bu tarayici kamera erisimini desteklemiyor.' : 'This browser does not support camera access.')
      return false
    }

    stopCamera()
    setPermissionState('requesting')
    setErrorMessage(null)

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: 'user',
          width: { ideal: 1280 },
          height: { ideal: 720 },
        },
        audio: false,
      })

      stream.getTracks().forEach((track) => {
        track.onended = () => {
          setStreamReady(false)
          setErrorMessage(
            isTurkish
              ? 'Kamera akisi sonlandi. Izlemeye devam etmek icin kamera erisimi ver.'
              : 'Camera stream ended. Grant camera access to continue monitoring.',
          )
        }
      })

      streamRef.current = stream
      const attached = await attachStream(stream)
      if (!attached) {
        stopCamera()
        return false
      }

      setPermissionState('granted')
      return true
    } catch (error) {
      setStreamReady(false)

      if (error instanceof DOMException && (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError')) {
        setPermissionState('denied')
        setErrorMessage(isTurkish ? 'Kamera izni reddedildi.' : 'Camera permission was denied.')
        return false
      }

      if (error instanceof DOMException && error.name === 'NotFoundError') {
        setPermissionState('error')
        setErrorMessage(isTurkish ? 'Kamera cihazi bulunamadi.' : 'No camera device was found.')
        return false
      }

      setPermissionState('error')
      setErrorMessage(error instanceof Error ? error.message : isTurkish ? 'Kameraya erisim saglanamadi.' : 'Unable to access camera.')
      return false
    }
  }

  const captureFrame = (): CapturedFrame | null => {
    const video = videoRef.current
    const hasLiveTrack = streamRef.current?.getVideoTracks().some((track) => track.readyState === 'live')

    if (!video || !streamReady || !hasLiveTrack || video.videoWidth === 0 || video.videoHeight === 0) {
      return null
    }

    const canvas = document.createElement('canvas')
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight

    const context = canvas.getContext('2d')
    if (!context) {
      return null
    }

    context.drawImage(video, 0, 0, canvas.width, canvas.height)
    const dataUrl = canvas.toDataURL('image/jpeg', 0.86)
    const imageBase64 = dataUrl.split(',')[1]

    if (!imageBase64) {
      return null
    }

    return {
      image_base64: imageBase64,
      image_content_type: 'image/jpeg',
    }
  }

  useEffect(() => () => stopCamera(), [])

  return {
    videoRef,
    permissionState,
    errorMessage,
    streamReady,
    requestCamera,
    stopCamera,
    captureFrame,
  }
}
