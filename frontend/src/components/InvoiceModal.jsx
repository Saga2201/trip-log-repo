import React from 'react'

export default function InvoiceModal({ open, invoiceId, onClose, onSaved }) {
  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white rounded-2xl p-6 max-w-md">
        <div className="text-lg font-bold text-navy mb-2">Invoice Form (stub)</div>
        <div className="text-sm text-gray-500 mb-4">
          {invoiceId ? `Editing invoice #${invoiceId}` : 'New invoice'} — form UI arrives in Task 11.
        </div>
        <div className="flex justify-end gap-2">
          <button onClick={onClose} className="px-4 py-2 rounded-lg text-sm bg-gray-200">Close</button>
          <button onClick={onSaved} className="px-4 py-2 rounded-lg text-sm bg-navy text-white">Simulate Save</button>
        </div>
      </div>
    </div>
  )
}
