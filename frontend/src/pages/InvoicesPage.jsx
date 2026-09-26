import React, { useEffect, useMemo, useRef, useState } from 'react'
import { FileText, Search, X as XIcon, Edit2, Download, Trash2 } from 'lucide-react'
import { getInvoices, deleteInvoice, invoicePdfUrl, invoiceAllPdfsUrl } from '../api'
import { KpiCard } from '../components/KpiCard'
import { ConfirmDialog } from '../components/ConfirmDialog'

const fmt = (n) => `₹${Number(n || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`

export default function InvoicesPage({ onNewInvoice, onEditInvoice, refreshKey }) {
  const [invoices, setInvoices] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [confirm, setConfirm] = useState(null)
  const [downloadOpen, setDownloadOpen] = useState(null)  // { id, top, left, width } or null
  const dropdownRef = useRef(null)

  // Close dropdown on outside click, Escape, scroll, or resize
  useEffect(() => {
    if (!downloadOpen) return
    const onDocClick = (e) => {
      // If the click is on the dropdown itself, leave it open (link clicks are allowed).
      if (dropdownRef.current && dropdownRef.current.contains(e.target)) return
      // If the click is on the trigger button (data attr), it will toggle itself.
      if (e.target.closest('[data-download-trigger]')) return
      setDownloadOpen(null)
    }
    const onKey = (e) => { if (e.key === 'Escape') setDownloadOpen(null) }
    const onScrollOrResize = () => setDownloadOpen(null)
    document.addEventListener('mousedown', onDocClick)
    document.addEventListener('keydown', onKey)
    window.addEventListener('scroll', onScrollOrResize, true)  // capture scroll on any ancestor
    window.addEventListener('resize', onScrollOrResize)
    return () => {
      document.removeEventListener('mousedown', onDocClick)
      document.removeEventListener('keydown', onKey)
      window.removeEventListener('scroll', onScrollOrResize, true)
      window.removeEventListener('resize', onScrollOrResize)
    }
  }, [downloadOpen])

  const toggleDownload = (id, e) => {
    if (downloadOpen && downloadOpen.id === id) { setDownloadOpen(null); return }
    const r = e.currentTarget.getBoundingClientRect()
    setDownloadOpen({ id, top: r.bottom + 4, left: Math.max(8, r.right - 180), width: 180 })
  }

  const load = () => {
    setLoading(true)
    getInvoices().then(setInvoices).catch(() => setInvoices([])).finally(() => setLoading(false))
  }
  useEffect(() => { load() }, [refreshKey])

  const filtered = useMemo(() => {
    const q = search.toLowerCase().trim()
    if (!q) return invoices
    return invoices.filter(i =>
      i.serial_number?.toLowerCase().includes(q) ||
      i.vehicle_number?.toLowerCase().includes(q) ||
      i.consignor_name?.toLowerCase().includes(q) ||
      i.consignee_name?.toLowerCase().includes(q) ||
      i.from_location?.toLowerCase().includes(q) ||
      i.to_location?.toLowerCase().includes(q)
    )
  }, [invoices, search])

  const monthKey = new Date().toISOString().slice(0, 7)
  const thisMonth = invoices.filter(i => (i.date || '').startsWith(monthKey)).length
  const totalBilled = invoices.reduce((s, i) => s + (i.pb_amount_total || 0), 0)
  const latestSerial = invoices[0]?.serial_number || '—'

  const handleConfirm = async () => {
    if (!confirm) return
    try { await deleteInvoice(confirm.id) } catch { /* ignore */ }
    setConfirm(null); load()
  }

  return (
    <div className="p-3 sm:p-6 flex flex-col gap-4 sm:gap-5 min-h-full">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <FileText size={24} className="text-navy" />
          <h1 className="text-lg sm:text-xl font-bold text-navy">Invoices</h1>
        </div>
        <button
          onClick={onNewInvoice}
          className="bg-navy text-white font-semibold px-4 py-2 rounded-lg text-sm flex items-center gap-2 hover:bg-navy-light"
        >
          + New Invoice
        </button>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
        <KpiCard title="Total Invoices" value={invoices.length.toString()} accent="#1e3a5f" />
        <KpiCard title="This Month" value={thisMonth.toString()} accent="#f57c00" />
        <KpiCard title="Total Billed" value={fmt(totalBilled)} accent="#2e7d32" />
        <KpiCard title="Latest Serial" value={latestSerial} accent="#7b1fa2" />
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="flex items-center gap-2 px-3 sm:px-4 py-3 border-b border-gray-100">
          <div className="relative flex-1">
            <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
            <input
              type="text"
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search serial, vehicle, party, route…"
              className="w-full pl-8 pr-7 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-navy bg-white"
            />
            {search && (
              <button onClick={() => setSearch('')} className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-700">
                <XIcon size={13} />
              </button>
            )}
          </div>
        </div>

        {loading ? (
          <div className="py-16 text-center text-gray-400 text-sm">Loading invoices…</div>
        ) : filtered.length === 0 ? (
          <div className="py-16 text-center text-gray-400 text-sm">
            {search ? 'No invoices match your search.' : 'No invoices yet. Click "New Invoice" to create your first one.'}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200 text-xs font-bold text-gray-500 uppercase">
                  <th className="text-left px-4 py-3">Serial #</th>
                  <th className="text-left px-4 py-3">Date</th>
                  <th className="text-left px-4 py-3">Vehicle</th>
                  <th className="text-left px-4 py-3">Consignor → Consignee</th>
                  <th className="text-left px-4 py-3">Route</th>
                  <th className="text-right px-4 py-3">Freight</th>
                  <th className="text-left px-4 py-3">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((i, idx) => (
                  <tr key={i.id} className={`border-b border-gray-100 hover:bg-blue-50 ${idx % 2 === 1 ? 'bg-gray-50/30' : ''}`}>
                    <td className="px-4 py-3 font-bold text-navy whitespace-nowrap">{i.serial_number}</td>
                    <td className="px-4 py-3 text-gray-700 whitespace-nowrap">{i.date}</td>
                    <td className="px-4 py-3 font-mono font-bold text-navy whitespace-nowrap">{i.vehicle_number}</td>
                    <td className="px-4 py-3 text-gray-700">{[i.consignor_name, i.consignee_name].filter(Boolean).join(' → ') || '—'}</td>
                    <td className="px-4 py-3 text-gray-500">{[i.from_location, i.to_location].filter(Boolean).join(' → ') || '—'}</td>
                    <td className="px-4 py-3 text-right font-semibold">{fmt(i.pb_amount_total)}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1">
                        <button title="View / Edit" onClick={() => onEditInvoice(i.id)} className="p-1.5 rounded hover:bg-blue-100 text-blue-600">
                          <Edit2 size={15} />
                        </button>
                        <button
                          data-download-trigger
                          title="Download PDFs"
                          onClick={(e) => toggleDownload(i.id, e)}
                          className="p-1.5 rounded hover:bg-green-100 text-green-600"
                        >
                          <Download size={15} />
                        </button>
                        <button title="Delete" onClick={() => setConfirm({ id: i.id, serial: i.serial_number })} className="p-1.5 rounded hover:bg-red-100 text-red-500">
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
      </div>

      {downloadOpen && (
        <div
          ref={dropdownRef}
          style={{ position: 'fixed', top: downloadOpen.top, left: downloadOpen.left, width: downloadOpen.width, zIndex: 50 }}
          className="bg-white border border-gray-200 rounded-lg shadow-lg text-xs"
        >
          <a href={invoicePdfUrl(downloadOpen.id, 'lr')} target="_blank" rel="noopener noreferrer" onClick={() => setDownloadOpen(null)} className="block px-3 py-2 hover:bg-gray-50">Download LR</a>
          <a href={invoicePdfUrl(downloadOpen.id, 'party_bill')} target="_blank" rel="noopener noreferrer" onClick={() => setDownloadOpen(null)} className="block px-3 py-2 hover:bg-gray-50">Download Party Bill</a>
          <a href={invoicePdfUrl(downloadOpen.id, 'driver_bill')} target="_blank" rel="noopener noreferrer" onClick={() => setDownloadOpen(null)} className="block px-3 py-2 hover:bg-gray-50">Download Driver Bill</a>
          <a href={invoiceAllPdfsUrl(downloadOpen.id)} target="_blank" rel="noopener noreferrer" onClick={() => setDownloadOpen(null)} className="block px-3 py-2 hover:bg-gray-50 border-t border-gray-100 font-semibold">All 3 (ZIP)</a>
        </div>
      )}

      <ConfirmDialog
        open={!!confirm}
        message={confirm ? `Permanently delete invoice ${confirm.serial}? This cannot be undone.` : ''}
        confirmLabel="Delete"
        confirmColor="red"
        onCancel={() => setConfirm(null)}
        onConfirm={handleConfirm}
      />
    </div>
  )
}
