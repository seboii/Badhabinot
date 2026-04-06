import { useEffect, useRef, useState } from 'react'

export type CameraPermissionState = 'idle' | 'requesting' | 'granted' | 'denied' | 'unsupported' | 'error'

type CapturedFrame = {
  image_base64: string
  image_content_type: string
}

export function useCamera() {
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const [permissionState, setPermissionState] = useState<CameraPermissionState>('idle')
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [streamReady, setStreamReady] = useState(false)

  const attachStream = async (stream: MediaStream) => {
    if (!videoRef.current) {
      return
    }

    videoRef.current.srcObject = stream

    try {
      await videoRef.current.play()
      setStreamReady(true)
    } catch (error) {
      setPermissionState('error')
      setErrorMessage(error instanceof Error ? error.message : 'Unable to play camera preview.')
    }
  }

  const stopCamera = () => {
    streamRef.current?.getTracks().forEach((track) => track.stop())
    streamRef.current = null
    setStreamReady(false)

    if (videoRef.current) {
      videoRef.current.srcObject = null
    }
  }

  const requestCamera = async () => {
    if (!navigator.mediaDevices?.getUserMedia) {
      setPermissionState('unsupported')
      setErrorMessage('This browser does not support camera access.')
      return
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

      streamRef.current = stream
      setPermissionState('granted')
      await attachStream(stream)
    } catch (error) {
      setPermissionState('denied')
      setErrorMessage(error instanceof Error ? error.message : 'Camera permission was denied.')
    }
  }

  const captureFrame = (): CapturedFrame | null => {
    const video = videoRef.current
    if (!video || video.videoWidth === 0 || video.videoHeight === 0) {
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

