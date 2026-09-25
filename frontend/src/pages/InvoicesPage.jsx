import React from 'react'
import { FileText } from 'lucide-react'

export default function InvoicesPage({ onNewInvoice }) {
  return (
    <div className="p-6">
      <div className="flex items-center gap-3">
        <FileText size={24} className="text-navy" />
        <h1 className="text-lg sm:text-xl font-bold text-navy">Invoices</h1>
      </div>
      <p className="mt-4 text-sm text-gray-500">Invoice list coming up in Task 10.</p>
    </div>
  )
}
