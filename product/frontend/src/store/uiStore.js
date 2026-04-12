import { create } from 'zustand'

export const useUiStore = create((set) => ({
  language: 'en',   // 'en' | 'es'
  toggleLanguage: () => set((s) => ({ language: s.language === 'en' ? 'es' : 'en' })),
}))
