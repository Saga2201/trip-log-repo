import axios from 'axios'

export const api = axios.create({ baseURL: '/api' })

export const getTrips = () => api.get('/trips').then(r => r.data)
export const createTrip = (data) => api.post('/trips', data).then(r => r.data)
export const updateTrip = (id, data) => api.put(`/trips/${id}`, data).then(r => r.data)
export const deleteTrip = (id) => api.delete(`/trips/${id}`).then(r => r.data)
export const getLocations = () => api.get('/locations').then(r => r.data)
export const getInsights = () => api.get('/insights').then(r => r.data)

export const uploadImage = (tripId, n, file) => {
  const fd = new FormData()
  fd.append('file', file)
  return api.post(`/trips/${tripId}/images/${n}`, fd).then(r => r.data)
}

export const deleteImage = (tripId, n) =>
  api.delete(`/trips/${tripId}/images/${n}`).then(r => r.data)

export const markComplete = (id) => api.patch(`/trips/${id}/complete`).then(r => r.data)
export const markReopen   = (id) => api.patch(`/trips/${id}/reopen`).then(r => r.data)

export const exportExcel = () => window.open('/api/export')

// ── Invoices ─────────────────────────────────────────────────────
export const getInvoices          = ()             => api.get('/invoices').then(r => r.data)
export const getInvoice           = (id)           => api.get(`/invoices/${id}`).then(r => r.data)
export const createInvoice        = (data)         => api.post('/invoices', data).then(r => r.data)
export const updateInvoice        = (id, data)     => api.put(`/invoices/${id}`, data).then(r => r.data)
export const deleteInvoice        = (id)           => api.delete(`/invoices/${id}`).then(r => r.data)
export const nextSerial           = (date)         => api.get('/invoices/next-serial', { params: { date } }).then(r => r.data.serial)
export const invoicePdfUrl        = (id, kind)     => `/api/invoices/${id}/pdf/${kind}`
export const invoiceAllPdfsUrl    = (id)           => `/api/invoices/${id}/pdf/all`
