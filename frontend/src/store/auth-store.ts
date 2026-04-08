import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { TokenResponse } from '@/types/auth'

type AuthState = {
  session: TokenResponse | null
  has_hydrated: boolean
  setSession: (session: TokenResponse) => void
  clearSession: () => void
  markHydrated: () => void
}

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
      partialize: (state) => ({ session: state.session }),
      onRehydrateStorage: () => (state) => {
        state?.markHydrated()
      },
    },
  ),
)

