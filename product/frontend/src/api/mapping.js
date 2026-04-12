import api from './client'

export async function getAutoMapping(sessionId) {
  const { data } = await api.post('/mapping/auto', { session_id: sessionId })
  return data  // AutoMappingResponse
}

export async function confirmMapping(sessionId, mapping) {
  const { data } = await api.post('/mapping/confirm', {
    session_id: sessionId,
    mapping,
  })
  return data  // ConfirmMappingResponse
}
