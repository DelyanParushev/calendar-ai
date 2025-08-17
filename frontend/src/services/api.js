import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000',
})

export async function parseText(text) {
  const { data } = await api.post('/parse', { text })
  return data // { title, start, end }
}

export async function createEvent(payload) {
  const { data } = await api.post('/events', payload)
  return data // saved event
}

export async function listEvents() {
  const { data } = await api.get('/events')
  return data // array of events
}

export default api