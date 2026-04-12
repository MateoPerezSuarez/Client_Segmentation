import api from './client'

export async function cleanData(sessionId, opts = {}) {
  const { data } = await api.post('/clean', {
    session_id: sessionId,
    remove_nulls: opts.removeNulls ?? true,
    remove_negatives: opts.removeNegatives ?? true,
    remove_duplicates: opts.removeDuplicates ?? true,
  })
  return data  // CleanResponse
}
