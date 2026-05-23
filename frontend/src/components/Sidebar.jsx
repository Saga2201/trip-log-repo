import React from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { Truck, List, PlusCircle, BarChart2, Download } from 'lucide-react'
import { exportExcel } from '../api'

export default function Sidebar({ onNewTrip }) {
  const navBase =
    'flex items-center gap-3 px-4 py-3 text-sm font-medium text-blue-100 hover:bg-navy-light hover:text-white transition-colors rounded-none cursor-pointer'
  const navActive =
    'flex items-center gap-3 px-4 py-3 text-sm font-medium text-white bg-[#2d5a8e] border-l-4 border-[#4fc3f7] transition-colors'
  const navInactive =
    'flex items-center gap-3 px-4 py-3 text-sm font-medium text-blue-100 hover:bg-[#2d5a8e] hover:text-white transition-colors border-l-4 border-transparent'

  return (
    <aside className="w-[220px] bg-navy min-h-screen flex flex-col flex-shrink-0">
      {/* Header */}
      <div className="flex items-center gap-3 px-5 py-5 border-b border-navy-dark">
        <Truck className="text-[#4fc3f7]" size={24} />
        <span className="text-white text-lg font-bold tracking-wide">JB Transport</span>
      </div>

      {/* Nav */}
      <nav className="flex flex-col mt-3 flex-1">
        <NavLink
          to="/"
          end
          className={({ isActive }) => (isActive ? navActive : navInactive)}
        >
          <List size={18} />
          All Trips
        </NavLink>

        <button
          onClick={onNewTrip}
          className={navInactive + ' w-full text-left'}
        >
          <PlusCircle size={18} />
          New Trip
        </button>

        <NavLink
          to="/insights"
          className={({ isActive }) => (isActive ? navActive : navInactive)}
        >
          <BarChart2 size={18} />
          Insights
        </NavLink>
      </nav>

      {/* Footer */}
      <div className="px-4 py-5 border-t border-navy-dark">
        <button
          onClick={exportExcel}
          className="flex items-center gap-2 w-full px-3 py-2 rounded text-sm text-blue-100 hover:bg-[#2d5a8e] hover:text-white transition-colors"
        >
          <Download size={16} />
          Export to Excel
        </button>
      </div>
    </aside>
  )
}
