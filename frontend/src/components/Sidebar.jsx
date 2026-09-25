import React from 'react'
import { NavLink } from 'react-router-dom'
import { Truck, List, PlusCircle, BarChart2, Download, FileText } from 'lucide-react'
import { exportExcel } from '../api'

export default function Sidebar({ onNewTrip }) {
  const navActive =
    'flex items-center gap-3 px-4 py-3 text-sm font-medium text-white bg-[#2d5a8e] border-l-4 border-[#4fc3f7] transition-colors'
  const navInactive =
    'flex items-center gap-3 px-4 py-3 text-sm font-medium text-blue-100 hover:bg-[#2d5a8e] hover:text-white transition-colors border-l-4 border-transparent'

  const mobileNavActive   = 'flex flex-col items-center gap-0.5 flex-1 py-2 text-[#4fc3f7] text-[10px] font-semibold'
  const mobileNavInactive = 'flex flex-col items-center gap-0.5 flex-1 py-2 text-blue-200 text-[10px] font-medium'

  return (
    <>
      {/* ── Desktop sidebar (hidden on mobile) ── */}
      <aside className="hidden md:flex w-[220px] bg-navy min-h-screen flex-col flex-shrink-0">
        {/* Header */}
        <div className="flex items-center gap-3 px-5 py-5 border-b border-navy-dark">
          <Truck className="text-[#4fc3f7]" size={24} />
          <span className="text-white text-lg font-bold tracking-wide">JB Transport</span>
        </div>

        {/* Nav */}
        <nav className="flex flex-col mt-3 flex-1">
          <NavLink to="/" end className={({ isActive }) => (isActive ? navActive : navInactive)}>
            <List size={18} />
            All Trips
          </NavLink>

          <button onClick={onNewTrip} className={navInactive + ' w-full text-left'}>
            <PlusCircle size={18} />
            New Trip
          </button>

          <NavLink to="/insights" className={({ isActive }) => (isActive ? navActive : navInactive)}>
            <BarChart2 size={18} />
            Insights
          </NavLink>

          <NavLink to="/invoices" className={({ isActive }) => (isActive ? navActive : navInactive)}>
            <FileText size={18} />
            Invoices
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

      {/* ── Mobile top bar ── */}
      <header className="md:hidden fixed top-0 left-0 right-0 z-40 bg-navy flex items-center justify-between px-4 py-3 shadow-lg">
        <div className="flex items-center gap-2">
          <Truck className="text-[#4fc3f7]" size={20} />
          <span className="text-white text-base font-bold tracking-wide">JB Transport</span>
        </div>
        <button
          onClick={onNewTrip}
          className="flex items-center gap-1.5 bg-[#4fc3f7] text-navy text-xs font-bold px-3 py-1.5 rounded-lg"
        >
          <PlusCircle size={15} />
          New Trip
        </button>
      </header>

      {/* ── Mobile bottom nav ── */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 z-40 bg-navy border-t border-[#2d5a8e] flex">
        <NavLink to="/" end className={({ isActive }) => (isActive ? mobileNavActive : mobileNavInactive)}>
          <List size={20} />
          Trips
        </NavLink>

        <button onClick={onNewTrip} className={mobileNavInactive + ' border-0 bg-transparent cursor-pointer'}>
          <PlusCircle size={20} />
          New Trip
        </button>

        <NavLink to="/insights" className={({ isActive }) => (isActive ? mobileNavActive : mobileNavInactive)}>
          <BarChart2 size={20} />
          Insights
        </NavLink>

        <NavLink to="/invoices" className={({ isActive }) => (isActive ? mobileNavActive : mobileNavInactive)}>
          <FileText size={20} />
          Invoices
        </NavLink>

        <button onClick={exportExcel} className={mobileNavInactive + ' border-0 bg-transparent cursor-pointer'}>
          <Download size={20} />
          Export
        </button>
      </nav>
    </>
  )
}