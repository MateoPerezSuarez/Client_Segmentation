import api from './client'

export async function previewKScores(sessionId, kMin, kMax) {
  const { data } = await api.post('/segment/rfm-kmeans/preview', {
    session_id: sessionId,
    k_min: kMin,
    k_max: kMax,
  })
  return data.k_scores  // { ks, wcss, silhouette, davies_bouldin, calinski_harabasz, combined }
}

export async function runSegmentation(method, sessionId, config = {}) {
  const endpoints = {
    rfm_quintiles: '/segment/rfm-quintiles',
    rfm_kmeans: '/segment/rfm-kmeans',
    abc: '/segment/abc',
    lrfms: '/segment/lrfms',
  }
  const { data } = await api.post(endpoints[method], {
    session_id: sessionId,
    ...config,
  })
  return data  // SegmentationResponse
}

export function getDownloadUrl(sessionId, token) {
  return `/segment/download/${sessionId}/${token}`
}

export async function getDashboardData(sessionId, token) {
  const { data } = await api.get(`/segment/dashboard/${sessionId}/${token}`)
  return data
}

export async function renameSegments(sessionId, token, renames) {
  const { data } = await api.post(`/segment/rename/${sessionId}/${token}`, renames)
  return data
}
