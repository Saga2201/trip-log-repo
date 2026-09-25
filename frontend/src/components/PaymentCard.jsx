import React, { useRef } from 'react'
import { Upload, X, Eye, RefreshCw } from 'lucide-react'

function imageUrl(path) {
  if (!path) return null
  const name = path.replace(/\\/g, '/').split('/').pop()
  return `/api/payment_images/${name}`
}

export default function PaymentCard({ label, n, amount, onAmountChange, onKeyDown, imgState, onFileSelect, onRemove }) {
  const fileRef = useRef(null)
  const { file, path, deleted } = imgState
  const displayPath = deleted ? null : (file ? URL.createObjectURL(file) : imageUrl(path))
  const hasImage = !!displayPath

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4 flex flex-col gap-3">
      <div className="text-xs font-bold text-navy uppercase tracking-wider">{label}</div>

      {/* Amount input */}
      <div className="relative">
        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm font-semibold">₹</span>
        <input
          type="number"
          min="0"
          step="1"
          value={amount}
          onChange={e => onAmountChange(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="0"
          className="w-full pl-7 pr-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-navy focus:border-transparent"
        />
      </div>

      {/* Image area */}
      <div className="mt-1">
        {hasImage ? (
          <div className="relative">
            <img
              src={displayPath}
              alt={`Payment ${n}`}
              className="w-full h-28 object-cover rounded-lg border border-gray-200"
            />
            <div className="absolute top-1.5 right-1.5 flex gap-1">
              <a
                href={displayPath}
                target="_blank"
                rel="noreferrer"
                className="bg-white/90 hover:bg-white rounded p-1 shadow text-gray-600 hover:text-navy transition-colors"
                title="View full size"
              >
                <Eye size={14} />
              </a>
              <button
                onClick={() => fileRef.current?.click()}
                className="bg-white/90 hover:bg-white rounded p-1 shadow text-gray-600 hover:text-navy transition-colors"
                title="Replace image"
              >
                <RefreshCw size={14} />
              </button>
              <button
                onClick={onRemove}
                className="bg-white/90 hover:bg-white rounded p-1 shadow text-red-500 hover:text-red-700 transition-colors"
                title="Remove image"
              >
                <X size={14} />
              </button>
            </div>
          </div>
        ) : (
          <button
            onClick={() => fileRef.current?.click()}
            className="w-full h-20 border-2 border-dashed border-gray-300 rounded-lg flex flex-col items-center justify-center gap-1 text-gray-400 hover:border-navy hover:text-navy transition-colors cursor-pointer bg-gray-50 hover:bg-blue-50"
          >
            <Upload size={18} />
            <span className="text-xs">Upload receipt</span>
          </button>
        )}
        <input
          ref={fileRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={e => {
            const f = e.target.files?.[0]
            if (f) onFileSelect(f)
            e.target.value = ''
          }}
        />
      </div>
    </div>
  )
}
