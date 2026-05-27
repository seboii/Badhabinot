import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import { Preferences } from '@capacitor/preferences'
import { Capacitor } from '@capacitor/core'
import type { TokenResponse } from '@/types/auth'

type AuthState = {
  session: TokenResponse | null
  has_hydrated: boolean
  setSession: (session: TokenResponse) => void
  clearSession: () => void
  markHydrated: () => void
}

// Capacitor Preferences uses Android Keystore on native and localStorage on web.
// This single adapter works on both platforms.
const preferencesStorage = {
  getItem: async (name: string): Promise<string | null> => {
    const { value } = await Preferences.get({ key: name })
    return value
  },
  setItem: async (name: string, value: string): Promise<void> => {
    await Preferences.set({ key: name, value })
  },
  removeItem: async (name: string): Promise<void> => {
    await Preferences.remove({ key: name })
  },
}

// On web without Capacitor, Preferences.get/.set fall back to localStorage anyway.
// Using a single storage adapter keeps the code path identical across platforms.
const storage = Capacitor.isNativePlatform()
  ? createJSONStorage(() => preferencesStorage)
  : createJSONStorage(() => localStorage)

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      session: null,
      has_hydrated: false,
      setSession: (session) => set({ session }),
      clearSession: () => set({ session: null }),
      markHydrated: () => set({ has_hydrated: true }),
    }),
    {
      name: 'badhabinot-auth',
      storage,
      partialize: (state) => ({ session: state.session }),
      onRehydrateStorage: () => (state) => {
        state?.markHydrated()
      },
    },
  ),
)
