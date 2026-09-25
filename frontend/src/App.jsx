import React, { useState } from 'react'
import { Routes, Route } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import TripsPage from './pages/TripsPage'
import InsightsPage from './pages/InsightsPage'
import InvoicesPage from './pages/InvoicesPage'
import TripModal from './components/TripModal'
import InvoiceModal from './components/InvoiceModal'

export default function App() {
  const [modal, setModal] = useState({ open: false, tripId: null })
  const [refreshKey, setRefreshKey] = useState(0)
  const [invModal, setInvModal] = useState({ open: false, invoiceId: null })
  const [invRefreshKey, setInvRefreshKey] = useState(0)

  const openNew = () => setModal({ open: true, tripId: null })
  const openEdit = (id) => setModal({ open: true, tripId: id })
  const closeModal = () => setModal({ open: false, tripId: null })
  const onSaved = () => {
    closeModal()
    setRefreshKey(k => k + 1)
  }

  const openNewInvoice = () => setInvModal({ open: true, invoiceId: null })
  const openEditInvoice = (id) => setInvModal({ open: true, invoiceId: id })
  const closeInvModal = () => setInvModal({ open: false, invoiceId: null })
  const onInvSaved = () => { closeInvModal(); setInvRefreshKey(k => k + 1) }

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar onNewTrip={openNew} />
      {/* pt-14 = space for mobile top bar; pb-16 = space for mobile bottom nav */}
      <main className="flex-1 overflow-auto bg-page pt-14 md:pt-0 pb-16 md:pb-0">
        <Routes>
          <Route
            path="/"
            element={<TripsPage onEditTrip={openEdit} refreshKey={refreshKey} />}
          />
          <Route path="/insights" element={<InsightsPage />} />
          <Route path="/invoices" element={<InvoicesPage onNewInvoice={openNewInvoice} onEditInvoice={openEditInvoice} refreshKey={invRefreshKey} />} />
        </Routes>
      </main>

      <TripModal
        open={modal.open}
        tripId={modal.tripId}
        onClose={closeModal}
        onSaved={onSaved}
      />

      <InvoiceModal open={invModal.open} invoiceId={invModal.invoiceId} onClose={closeInvModal} onSaved={onInvSaved} />
    </div>
  )
}
