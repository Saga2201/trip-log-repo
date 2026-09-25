import React, { useState } from 'react'
import { Routes, Route } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import TripsPage from './pages/TripsPage'
import InsightsPage from './pages/InsightsPage'
import TripModal from './components/TripModal'

export default function App() {
  const [modal, setModal] = useState({ open: false, tripId: null })
  const [refreshKey, setRefreshKey] = useState(0)

  const openNew = () => setModal({ open: true, tripId: null })
  const openEdit = (id) => setModal({ open: true, tripId: id })
  const closeModal = () => setModal({ open: false, tripId: null })
  const onSaved = () => {
    closeModal()
    setRefreshKey(k => k + 1)
  }

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
        </Routes>
      </main>

      <TripModal
        open={modal.open}
        tripId={modal.tripId}
        onClose={closeModal}
        onSaved={onSaved}
      />
    </div>
  )
}
