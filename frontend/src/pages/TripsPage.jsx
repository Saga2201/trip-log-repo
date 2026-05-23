import React, { useState, useEffect, useMemo } from 'react'
import { Search, Edit2, Trash2, Truck, X as XIcon, CheckCircle2, RotateCcw, Clock, CalendarDays, ListFilter } from 'lucide-react'
import { getTrips, deleteTrip, markComplete, markReopen } from '../api'
import { KpiCard } from '../components/KpiCard'
import { ConfirmDialog } from '../components/ConfirmDialog'

const TODAY = new Date().toISOString().slice(0, 10)

function statusBadge(status) {
  const map = {
    'Paid':    'bg-green-100 text-green-700 border-green-200',
    'Partial': 'bg-yellow-100 text-yellow-700 border-yellow-200',
    'Pending': 'bg-red-100 text-red-700 border-red-200',
  }
  return (
    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${map[status] || 'bg-gray-100 text-gray-600'}`}>
      {status}
    </span>
  )
}

function fmt(n) {
  return `₹${Number(n || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`
}

// Returns the value only if it contains meaningful text (not purely numeric)
function textLocation(val) {
  if (!val) return null
  const trimmed = String(val).trim()
  return /^\d+$/.test(trimmed) ? null : trimmed
}

function Tab({ active, onClick, children, count }) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 px-5 py-2.5 text-sm font-semibold border-b-2 transition-colors whitespace-nowrap ${
        active
          ? 'border-navy text-navy'
          : 'border-transparent text-gray-400 hover:text-gray-600 hover:border-gray-300'
      }`}
    >
      {children}
      {count !== undefined && (
        <span className={`text-xs px-1.5 py-0.5 rounded-full font-bold ${
          active ? 'bg-navy text-white' : 'bg-gray-200 text-gray-500'
        }`}>
          {count}
        </span>
      )}
    </button>
  )
}

export default function TripsPage({ onEditTrip, refreshKey }) {
  const [trips, setTrips] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [activeTab, setActiveTab] = useState('pending') // 'pending' | 'completed'
  const [confirm, setConfirm] = useState(null)          // { id, vehicle_number, action: 'delete'|'complete'|'reopen' }
  const [actionLoading, setActionLoading] = useState(null)
  const [dateFilter, setDateFilter] = useState(TODAY)   // '' = View All

  const load = () => {
    setLoading(true)
    getTrips()
      .then(setTrips)
      .catch(() => setTrips([]))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [refreshKey])

  // Split by tab
  const pendingTrips   = useMemo(() => trips.filter(t => !t.completed), [trips])
  const completedTrips = useMemo(() => trips.filter(t =>  t.completed), [trips])

  // Apply date filter (pending tab only)
  const tabTrips = useMemo(() => {
    const base = activeTab === 'pending' ? pendingTrips : completedTrips
    if (activeTab === 'pending' && dateFilter) {
      return base.filter(t => t.date === dateFilter)
    }
    return base
  }, [activeTab, pendingTrips, completedTrips, dateFilter])

  // Count for pending tab badge — total pending regardless of date
  const pendingCount = pendingTrips.length

  // Apply search filter on top
  const filtered = useMemo(() => {
    const q = search.toLowerCase().trim()
    if (!q) return tabTrips
    return tabTrips.filter(t =>
      t.vehicle_number?.toLowerCase().includes(q) ||
      t.loading_address?.toLowerCase().includes(q) ||
      t.unloading_address?.toLowerCase().includes(q) ||
      t.date?.includes(q) ||
      t.state?.toLowerCase().includes(q) ||
      t.city?.toLowerCase().includes(q)
    )
  }, [tabTrips, search])

  // KPIs always over all trips
  const totalRevenue    = trips.reduce((s, t) => s + (t.total_booking || 0), 0)
  const totalReceived   = trips.reduce((s, t) => s + (t.received    || 0), 0)
  const totalPending    = trips.reduce((s, t) => s + (t.pending     || 0), 0)
  const totalCommission = trips.reduce((s, t) => s + (t.commission  || 0), 0)

  const handleConfirm = async () => {
    if (!confirm) return
    setActionLoading(confirm.id)
    try {
      if (confirm.action === 'delete')   await deleteTrip(confirm.id)
      if (confirm.action === 'complete') await markComplete(confirm.id)
      if (confirm.action === 'reopen')   await markReopen(confirm.id)
      load()
    } catch { /* ignore */ }
    setConfirm(null)
    setActionLoading(null)
  }

  const emptyMsg = search
    ? 'No trips match your search.'
    : activeTab === 'pending' && dateFilter
      ? `No pending trips on ${dateFilter === TODAY ? 'today' : dateFilter}. Click "View All" to see all pending trips.`
      : activeTab === 'pending'
        ? 'No pending trips. All caught up!'
        : 'No completed trips yet.'

  return (
    <div className="p-6 flex flex-col gap-5 min-h-full">

      {/* Page title */}
      <div className="flex items-center gap-3">
        <Truck size={26} className="text-navy" />
        <h1 className="text-xl font-bold text-navy">All Trips</h1>
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        <KpiCard title="Total Trips"      value={trips.length.toString()} accent="#f57c00" />
        <KpiCard title="Total Revenue"    value={fmt(totalRevenue)}       accent="#1e3a5f" />
        <KpiCard title="Total Received"   value={fmt(totalReceived)}      accent="#2e7d32" />
        <KpiCard title="Total Pending"    value={fmt(totalPending)}       accent="#e53935" />
        <KpiCard title="Total Commission" value={fmt(totalCommission)}    accent="#7b1fa2" />
      </div>

      {/* Tabs + Search bar */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">

        {/* Tab bar */}
        <div className="flex items-center justify-between px-4 border-b border-gray-200 flex-wrap gap-y-2">
          <div className="flex">
            <Tab active={activeTab === 'pending'}   onClick={() => { setActiveTab('pending');   setSearch('') }} count={pendingCount}>
              <Clock size={14} />
              Pending Trips
            </Tab>
            <Tab active={activeTab === 'completed'} onClick={() => { setActiveTab('completed'); setSearch('') }} count={completedTrips.length}>
              <CheckCircle2 size={14} />
              Completed Trips
            </Tab>
          </div>

          {/* Controls row */}
          <div className="flex items-center gap-2 my-2 flex-wrap">

            {/* Date filter — pending tab only */}
            {activeTab === 'pending' && (
              <div className="flex items-center gap-1.5">
                <div className="relative">
                  <CalendarDays size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
                  <input
                    type="date"
                    value={dateFilter}
                    onChange={e => setDateFilter(e.target.value)}
                    className="pl-8 pr-2 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-navy bg-white cursor-pointer"
                  />
                </div>
                {dateFilter ? (
                  <button
                    onClick={() => setDateFilter('')}
                    className="flex items-center gap-1 px-2.5 py-1.5 text-xs font-semibold rounded-lg border border-gray-300 text-gray-600 hover:bg-gray-100 transition-colors whitespace-nowrap"
                    title="Show all pending trips"
                  >
                    <ListFilter size={12} />
                    View All
                  </button>
                ) : (
                  <button
                    onClick={() => setDateFilter(TODAY)}
                    className="flex items-center gap-1 px-2.5 py-1.5 text-xs font-semibold rounded-lg border border-navy text-navy hover:bg-blue-50 transition-colors whitespace-nowrap"
                    title="Filter by today"
                  >
                    <CalendarDays size={12} />
                    Today
                  </button>
                )}
              </div>
            )}

            {/* Search */}
            <div className={`relative w-60 ${search ? 'ring-2 ring-navy/20 rounded-lg' : ''}`}>
              <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
              <input
                type="text"
                value={search}
                onChange={e => setSearch(e.target.value)}
                placeholder="Search vehicle, route, city…"
                className="w-full pl-8 pr-7 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-navy bg-white"
              />
              {search && (
                <button onClick={() => setSearch('')} className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-700">
                  <XIcon size={13} />
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Table body */}
        {loading ? (
          <div className="flex items-center justify-center py-20 text-gray-400 text-sm">Loading trips…</div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-gray-400 gap-3">
            {activeTab === 'completed'
              ? <CheckCircle2 size={40} className="text-gray-200" />
              : <Truck size={40} className="text-gray-200" />
            }
            <span className="text-sm">{emptyMsg}</span>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  {['Date', 'Vehicle #', 'From → To', 'Material', 'Weight (T)', 'Booking', 'Party Rate', 'Commission', 'Received', 'Pending', 'Status', ''].map(h => (
                    <th key={h} className="text-left px-4 py-3 text-xs font-bold text-gray-500 uppercase tracking-wide whitespace-nowrap">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.map((t, i) => (
                  <tr
                    key={t.id}
                    className={`border-b border-gray-100 hover:bg-blue-50 cursor-pointer transition-colors ${i % 2 === 1 ? 'bg-gray-50/30' : ''} ${t.completed ? 'opacity-80' : ''}`}
                    onClick={() => onEditTrip(t.id)}
                  >
                    <td className="px-4 py-3 font-medium text-gray-700 whitespace-nowrap">{t.date}</td>
                    <td className="px-4 py-3 font-bold text-navy whitespace-nowrap">{t.vehicle_number}</td>
                    <td className="px-4 py-3 max-w-[260px]">
                      {/* From */}
                      <div className="flex items-start gap-1.5">
                        <span className="mt-0.5 flex-shrink-0 w-3.5 h-3.5 rounded-full bg-blue-100 border-2 border-blue-400 inline-block" />
                        <div>
                          <div className="text-xs text-gray-400 font-medium leading-none mb-0.5">FROM</div>
                          {textLocation(t.loading_address) ? (
                            <div className="text-sm font-semibold text-gray-700 truncate max-w-[200px]">
                              {textLocation(t.loading_address)}
                            </div>
                          ) : null}
                          {(t.city || t.state) ? (
                            <div className="text-xs text-gray-400 truncate">{[t.city, t.state].filter(Boolean).join(', ')}</div>
                          ) : !textLocation(t.loading_address) ? (
                            <div className="text-sm font-semibold text-gray-400">—</div>
                          ) : null}
                        </div>
                      </div>
                      {/* Divider */}
                      <div className="ml-[7px] my-0.5 h-3 w-px bg-gray-300" />
                      {/* To */}
                      <div className="flex items-start gap-1.5">
                        <span className="mt-0.5 flex-shrink-0 w-3.5 h-3.5 rounded-full bg-green-100 border-2 border-green-500 inline-block" />
                        <div>
                          <div className="text-xs text-gray-400 font-medium leading-none mb-0.5">TO</div>
                          {textLocation(t.unloading_address) ? (
                            <div className="text-sm font-semibold text-gray-700 truncate max-w-[200px]">
                              {textLocation(t.unloading_address)}
                            </div>
                          ) : (
                            <div className="text-sm font-semibold text-gray-400">—</div>
                          )}
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-gray-600 whitespace-nowrap">
                      {t.material || <span className="text-gray-300">—</span>}
                    </td>
                    <td className="px-4 py-3 text-gray-600 whitespace-nowrap">
                      {t.material_weight
                        ? `${(t.material_weight / 1000).toFixed(2)} T`
                        : <span className="text-gray-300">—</span>
                      }
                    </td>
                    <td className="px-4 py-3 font-medium text-gray-700 whitespace-nowrap">{fmt(t.total_booking)}</td>
                    <td className="px-4 py-3 font-medium text-gray-500 whitespace-nowrap">
                      {t.party_rate ? fmt(t.party_rate) : <span className="text-gray-300">—</span>}
                    </td>
                    <td className="px-4 py-3 font-semibold whitespace-nowrap" style={{ color: t.commission > 0 ? '#7b1fa2' : '#9e9e9e' }}>
                      {t.commission > 0 ? fmt(t.commission) : <span className="text-gray-300">—</span>}
                    </td>
                    <td className="px-4 py-3 font-medium text-green-700 whitespace-nowrap">{fmt(t.received)}</td>
                    <td className="px-4 py-3 font-medium text-red-600 whitespace-nowrap">{fmt(t.pending)}</td>
                    <td className="px-4 py-3">{statusBadge(t.status)}</td>
                    <td className="px-4 py-3" onClick={e => e.stopPropagation()}>
                      <div className="flex items-center gap-1">
                        {/* Complete / Reopen */}
                        {activeTab === 'pending' ? (
                          <button
                            onClick={() => setConfirm({ id: t.id, vehicle_number: t.vehicle_number, action: 'complete' })}
                            disabled={actionLoading === t.id}
                            className="p-1.5 rounded hover:bg-green-100 text-gray-400 hover:text-green-600 transition-colors"
                            title="Mark as Completed"
                          >
                            <CheckCircle2 size={16} />
                          </button>
                        ) : (
                          <button
                            onClick={() => setConfirm({ id: t.id, vehicle_number: t.vehicle_number, action: 'reopen' })}
                            disabled={actionLoading === t.id}
                            className="p-1.5 rounded hover:bg-yellow-100 text-gray-400 hover:text-yellow-600 transition-colors"
                            title="Move back to Pending"
                          >
                            <RotateCcw size={15} />
                          </button>
                        )}
                        {/* Edit */}
                        <button
                          onClick={() => onEditTrip(t.id)}
                          className="p-1.5 rounded hover:bg-blue-100 text-blue-600 transition-colors"
                          title="Edit"
                        >
                          <Edit2 size={15} />
                        </button>
                        {/* Delete */}
                        <button
                          onClick={() => setConfirm({ id: t.id, vehicle_number: t.vehicle_number, action: 'delete' })}
                          className="p-1.5 rounded hover:bg-red-100 text-red-500 transition-colors"
                          title="Delete"
                        >
                          <Trash2 size={15} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Footer row count */}
        {!loading && filtered.length > 0 && (
          <div className="px-4 py-2 border-t border-gray-100 bg-gray-50 text-xs text-gray-400">
            {search
              ? `Showing ${filtered.length} of ${tabTrips.length} trips`
              : `${filtered.length} trip${filtered.length !== 1 ? 's' : ''}`
            }
          </div>
        )}
      </div>

      <ConfirmDialog
        open={!!confirm}
        message={
          confirm?.action === 'delete'
            ? `Permanently delete trip for ${confirm.vehicle_number}? This cannot be undone.`
            : confirm?.action === 'complete'
            ? `Mark trip for ${confirm?.vehicle_number} as completed?`
            : `Move trip for ${confirm?.vehicle_number} back to Pending?`
        }
        confirmLabel={confirm?.action === 'delete' ? 'Delete' : confirm?.action === 'complete' ? 'Mark Completed' : 'Move to Pending'}
        confirmColor={confirm?.action === 'delete' ? 'red' : confirm?.action === 'complete' ? 'green' : 'yellow'}
        onCancel={() => setConfirm(null)}
        onConfirm={handleConfirm}
      />
    </div>
  )
}
