// loan-ui/src/services/api.jsx
import axios from 'axios'

const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
export const api = axios.create({ baseURL })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// ---- Auth
export async function login(email, password){
  const { data } = await api.post('/api/v1/auth/login', { email, password })
  return data
}
export async function register(payload){
  const { data } = await api.post('/api/v1/auth/register', payload)
  return data
}

// ---- Applicants
export async function createApplicant(payload){
  const { data } = await api.post('/api/v1/applicants', payload)
  return data
}
export async function listApplicants({ limit = 100, offset = 0 } = {}, signal){
  const { data } = await api.get('/api/v1/applicants', { params: { limit, offset }, signal })
  return data
}
export async function deleteApplicant(id){
  // Admin only
  await api.delete(`/api/v1/applicants/${id}`)
  return { ok: true }
}

// ---- Loans
export async function createLoan(payload, key){
  const { data } = await api.post(
    '/api/v1/loans',
    payload,
    { headers: { 'Idempotency-Key': key || crypto.randomUUID() } }
  )
  return data
}
export async function getLoan(id){
  const { data } = await api.get(`/api/v1/loans/${id}`)
  return data
}

// ---- Dashboard metrics (JSON)
export async function getMetrics(){
  // NOTE: Use /stats (JSON), not /metrics (Prometheus text)
  const { data } = await api.get('/api/v1/stats')
  return data
}



// // loan-ui/src/services/api.jsx
// import axios from 'axios'
// const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
// export const api = axios.create({ baseURL })

// api.interceptors.request.use((config) => {
//   const token = localStorage.getItem('token')
//   if (token) config.headers.Authorization = `Bearer ${token}`
//   return config
// })

// export async function login(email, password){
//   const { data } = await api.post('/api/v1/auth/login', { email, password })
//   return data
// }
// export async function register(payload){
//   const { data } = await api.post('/api/v1/auth/register', payload)
//   return data
// }
// export async function createApplicant(payload){
//   const { data } = await api.post('/api/v1/applicants', payload)
//   return data
// }
// export async function createLoan(payload, key){
//   const { data } = await api.post('/api/v1/loans', payload, { headers: { 'Idempotency-Key': key || crypto.randomUUID() }})
//   return data
// }
// export async function getLoan(id){
//   const { data } = await api.get(`/api/v1/loans/${id}`)
//   return data
// }
// export async function getMetrics(){
//   const { data } = await api.get('/api/v1/metrics')
//   return data
// }

// export async function listApplicants({ limit = 100, offset = 0 } = {}) {
//   const { data } = await api.get('/api/v1/applicants', { params: { limit, offset } })
//   return Array.isArray(data) ? data : []
// }

// export async function deleteApplicant(id) {
//   await api.delete(`/api/v1/applicants/${id}`)
// }