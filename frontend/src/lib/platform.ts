import { Capacitor } from '@capacitor/core'

export const platform = {
  /** True when running inside a Capacitor native container (Android / iOS). */
  isNative: Capacitor.isNativePlatform(),
  /** True when running in a normal browser. */
  isWeb: !Capacitor.isNativePlatform(),
  /** 'android' | 'ios' | 'web' */
  name: Capacitor.getPlatform() as 'android' | 'ios' | 'web',
}
