import { create } from 'zustand'

export const useWizardStore = create((set) => ({
  step: 1,           // 1-6
  method: null,      // 'rfm_quintiles' | 'rfm_kmeans' | 'abc' | 'lrfms'

  // Step 2
  uploadResult: null,

  // Step 3
  autoMapping: null,
  confirmedMapping: null,
  treatNegativesAsReturns: false,

  // Step 4
  cleanResult: null,

  // Step 5
  methodConfig: {},

  // Step 6
  segmentResult: null,

  // Loading / error
  loading: false,
  error: null,

  // Actions
  setStep: (step) => set({ step }),
  nextStep: () => set((s) => ({ step: Math.min(s.step + 1, 6) })),

  // When going back from step N, clear everything produced by step N and later.
  // This forces each step to be re-run after any upstream change.
  prevStep: () => set((s) => {
    const next = Math.max(s.step - 1, 1)
    const clears = {
      // Back from Upload → clear upload data + all downstream
      2: { uploadResult: null, autoMapping: null, confirmedMapping: null,
           treatNegativesAsReturns: false, cleanResult: null, methodConfig: {}, segmentResult: null },
      // Back from Mapping → clear mapping data + all downstream
      3: { autoMapping: null, confirmedMapping: null, treatNegativesAsReturns: false,
           cleanResult: null, segmentResult: null },
      // Back from Clean → clear clean result + segment result
      4: { cleanResult: null, segmentResult: null },
      // Back from Configure → clear clean + segment so clean can be re-run freely
      5: { cleanResult: null, segmentResult: null },
      // Back from Results → clear segment result
      6: { segmentResult: null },
    }
    return { step: next, error: null, ...(clears[s.step] ?? {}) }
  }),

  setMethod: (method) => set({ method }),
  setUploadResult: (r) => set({ uploadResult: r }),
  setAutoMapping: (m) => set({ autoMapping: m }),
  setConfirmedMapping: (m) => set({ confirmedMapping: m }),
  setTreatNegativesAsReturns: (v) => set({ treatNegativesAsReturns: v }),
  setCleanResult: (r) => set({ cleanResult: r }),
  setMethodConfig: (cfg) => set({ methodConfig: cfg }),
  setSegmentResult: (r) => set({ segmentResult: r }),

  setLoading: (v) => set({ loading: v }),
  setError: (e) => set({ error: e }),

  reset: () => set({
    step: 1, method: null, uploadResult: null, autoMapping: null,
    confirmedMapping: null, treatNegativesAsReturns: false, cleanResult: null,
    methodConfig: {}, segmentResult: null, loading: false, error: null,
  }),
}))
