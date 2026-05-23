import React from 'react'

export function KpiCard({ title, value, accent, className = '' }) {
  return (
    <div
      className={`bg-white rounded-lg p-4 flex-1 min-w-[160px] shadow-sm ${className}`}
      style={{ borderLeft: `4px solid ${accent}` }}
    >
      <p className="text-[10px] uppercase tracking-wide text-gray-400 font-semibold">{title}</p>
      <p className="text-2xl font-bold mt-1" style={{ color: accent }}>{value}</p>
    </div>
  )
}
