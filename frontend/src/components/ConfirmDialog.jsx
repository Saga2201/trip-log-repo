import React from 'react'

const COLOR_MAP = {
  red:    'bg-red-500 hover:bg-red-600',
  green:  'bg-green-600 hover:bg-green-700',
  yellow: 'bg-yellow-500 hover:bg-yellow-600',
  navy:   'bg-navy hover:bg-navy-light',
}

export function ConfirmDialog({ open, onConfirm, onCancel, message, confirmLabel = 'Delete', confirmColor = 'red' }) {
  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={onCancel} />
      <div className="relative bg-white rounded-xl shadow-xl p-6 w-full max-w-sm mx-4">
        <p className="text-gray-700 text-sm leading-relaxed mb-6">
          {message ?? 'Are you sure? This action cannot be undone.'}
        </p>
        <div className="flex justify-end gap-3">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-sm font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className={`px-4 py-2 text-sm font-medium text-white rounded-lg transition-colors ${COLOR_MAP[confirmColor] || COLOR_MAP.red}`}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}
