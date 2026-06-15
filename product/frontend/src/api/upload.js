import api from './client'

export async function uploadFile(file) {
  const form = new FormData()
  form.append('file', file)
  const { data } = await api.post('/upload', form)
  return data  // UploadResponse
}

export async function uploadBigQuery(tablePath) {
  const { data } = await api.post('/upload/bigquery', {
    table_path: tablePath,
  })
  return data  // UploadResponse
}
