import { create } from 'zustand'
import type { UserContextResponse } from '@/types/user'

type UserState = {
  profile: UserContextResponse | null
  setProfile: (profile: UserContextResponse) => void
  clearUser: () => void
}

export const useUserStore = create<UserState>()((set) => ({
  profile: null,
  setProfile: (profile) => set({ profile }),
  clearUser: () => set({ profile: null }),
}))
