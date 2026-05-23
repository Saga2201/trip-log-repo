import React, { useState, useEffect } from 'react'
import { BarChart2 } from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid
} from 'recharts'
import { getInsights } from '../api'
import { KpiCard } from '../components/KpiCard'

const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

function monthlyRevenue(trips) {
  const year = new Date().getFullYear().toString()
  const map = {}
  MONTHS.forEach((m, i) => { map[`${year}-${String(i+1).padStart(2,'0')}`] = 0 })
  trips.forEach(t => {
    const k = (t.date || '').slice(0, 7)
    if (k in map) map[k] += t.total_booking || 0
  })
  return MONTHS.map((label, i) => ({
    month: label,
    revenue: map[`${year}-${String(i+1).padStart(2,'0')}`],
  }))
}

function vehicleSummary(trips) {
  const map = {}
  trips.forEach(t => {
    const v = t.vehicle_number || '—'
    if (!map[v]) map[v] = { trips: 0, earnings: 0 }
    map[v].trips += 1
    map[v].earnings += t.total_booking || 0
  })
  return Object.entries(map)
    .sort((a, b) => b[1].earnings - a[1].earnings)
    .slice(0, 10)
}

function stateSummary(trips) {
  const map = {}
  trips.forEach(t => {
    const s = t.state || 'Unknown'
    map[s] = (map[s] || 0) + 1
  })
  return Object.entries(map).sort((a, b) => b[1] - a[1]).slice(0, 8)
}

function fmt(n) {
  return `₹${Number(n || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`
}

const customTooltip = ({ active, payload, label }) => {
  if (active && payload?.length) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg px-3 py-2 shadow text-xs">
        <div className="font-bold text-navy">{label}</div>
        <div className="text-gray-600">{fmt(payload[0].value)}</div>
      </div>
    )
  }
  return null
}

export default function InsightsPage() {
  const [trips, setTrips] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getInsights()
      .then(setTrips)
      .catch(() => setTrips([]))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return <div className="flex items-center justify-center h-full text-gray-400 text-sm">Loading insights…</div>
  }

  const totalRevenue    = trips.reduce((s, t) => s + (t.total_booking || 0), 0)
  const totalPending    = trips.reduce((s, t) => s + (t.pending || 0), 0)
  const totalCommission = trips.reduce((s, t) => s + (t.commission || 0), 0)
  const avgBooking      = trips.length ? totalRevenue / trips.length : 0

  const monthly = monthlyRevenue(trips)
  const vehicles = vehicleSummary(trips)
  const states = stateSummary(trips)
  const pendingTrips = [...trips].filter(t => t.pending > 0).sort((a, b) => b.pending - a.pending).slice(0, 10)
  const maxStateCount = states.length ? states[0][1] : 1

  return (
    <div className="p-3 sm:p-6 flex flex-col gap-4 sm:gap-6">
      <div className="flex items-center gap-3">
        <BarChart2 size={24} className="text-navy" />
        <h1 className="text-lg sm:text-xl font-bold text-navy">Business Insights</h1>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 sm:gap-4">
        <KpiCard title="Total Revenue"    value={fmt(totalRevenue)}       accent="#1e3a5f" />
        <KpiCard title="Total Pending"    value={fmt(totalPending)}       accent="#e53935" />
        <KpiCard title="Total Trips"      value={trips.length.toString()} accent="#f57c00" />
        <KpiCard title="Avg. Booking"     value={fmt(avgBooking)}         accent="#2e7d32" />
        <KpiCard title="Total Commission" value={fmt(totalCommission)}    accent="#7b1fa2" className="col-span-2 sm:col-span-1" />
      </div>

      {/* Monthly chart + Pending list */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        <div className="lg:col-span-3 bg-white rounded-xl shadow-sm border border-gray-200 p-4 sm:p-5">
          <p className="text-xs font-bold text-navy uppercase tracking-wide mb-4">Monthly Revenue</p>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={monthly} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f4f8" />
              <XAxis dataKey="month" tick={{ fontSize: 10, fill: '#888' }} axisLine={false} tickLine={false} />
              <YAxis
                tick={{ fontSize: 10, fill: '#888' }}
                axisLine={false}
                tickLine={false}
                width={48}
                tickFormatter={v => v >= 1000 ? `₹${(v/1000).toFixed(0)}k` : `₹${v}`}
              />
              <Tooltip content={customTooltip} />
              <Bar dataKey="revenue" fill="#1e3a5f" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="lg:col-span-2 bg-white rounded-xl shadow-sm border border-gray-200 p-4 sm:p-5">
          <p className="text-xs font-bold text-red-600 uppercase tracking-wide mb-4">Pending Payments</p>
          {pendingTrips.length === 0 ? (
            <p className="text-xs text-gray-400 mt-4">All trips are fully paid</p>
          ) : (
            <div className="space-y-2">
              {pendingTrips.map(t => (
                <div key={t.id} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                  <div className="min-w-0 flex-1 mr-3">
                    <div className="text-xs font-bold text-gray-800 truncate">{t.vehicle_number}</div>
                    <div className="text-[10px] text-gray-400 truncate">{t.loading_address} → {t.unloading_address} · {t.date}</div>
                  </div>
                  <span className="text-xs font-bold text-red-600 flex-shrink-0">{fmt(t.pending)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Vehicle table + State bars */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 sm:p-5">
          <p className="text-xs font-bold text-navy uppercase tracking-wide mb-4">Vehicle-wise Summary</p>
          <div className="overflow-x-auto">
            <table className="w-full text-sm min-w-[240px]">
              <thead>
                <tr className="border-b border-gray-100">
                  <th className="text-left text-xs text-gray-400 font-semibold pb-2">Vehicle</th>
                  <th className="text-center text-xs text-gray-400 font-semibold pb-2">Trips</th>
                  <th className="text-right text-xs text-gray-400 font-semibold pb-2">Earnings</th>
                </tr>
              </thead>
              <tbody>
                {vehicles.map(([v, d]) => (
                  <tr key={v} className="border-b border-gray-50 last:border-0">
                    <td className="py-2 text-xs font-bold text-navy">{v}</td>
                    <td className="py-2 text-xs text-center text-gray-600">{d.trips}</td>
                    <td className="py-2 text-xs text-right font-semibold text-gray-700">{fmt(d.earnings)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 sm:p-5">
          <p className="text-xs font-bold text-navy uppercase tracking-wide mb-4">State-wise Trip Count</p>
          <div className="space-y-3">
            {states.map(([state, count]) => (
              <div key={state}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-semibold text-gray-700">{state}</span>
                  <span className="text-xs text-gray-400">{count} trips</span>
                </div>
                <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-navy rounded-full transition-all"
                    style={{ width: `${Math.round((count / maxStateCount) * 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
