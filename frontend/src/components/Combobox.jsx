import React, { useState, useRef, useEffect } from 'react'
import { ChevronDown, X } from 'lucide-react'

/**
 * Searchable combobox dropdown.
 *
 * Props:
 *   options   – string[]
 *   value     – current selected string (or '')
 *   onChange  – (newValue: string) => void
 *   placeholder – string
 *   disabled  – bool
 */
export default function Combobox({ options = [], value, onChange, placeholder = 'Select…', disabled = false }) {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const inputRef = useRef(null)
  const containerRef = useRef(null)

  // Close dropdown when clicking outside
  useEffect(() => {
    const handler = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setOpen(false)
        setQuery('')
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  // When value is cleared from outside, reset query
  useEffect(() => {
    if (!value) setQuery('')
  }, [value])

  const filtered = query
    ? options.filter(o => o.toLowerCase().includes(query.toLowerCase()))
    : options

  const handleSelect = (option) => {
    onChange(option)
    setQuery('')
    setOpen(false)
  }

  const handleClear = (e) => {
    e.stopPropagation()
    onChange('')
    setQuery('')
    setOpen(false)
  }

  const handleInputChange = (e) => {
    setQuery(e.target.value)
    setOpen(true)
  }

  const displayValue = open ? query : (value || '')

  return (
    <div ref={containerRef} className="relative">
      <div
        className={`flex items-center border rounded-lg bg-white transition-all ${
          disabled ? 'bg-gray-100 cursor-not-allowed border-gray-200' :
          open ? 'border-navy ring-2 ring-navy/20' : 'border-gray-300 hover:border-gray-400'
        }`}
      >
        <input
          ref={inputRef}
          type="text"
          value={displayValue}
          onChange={handleInputChange}
          onFocus={() => { if (!disabled) { setOpen(true); setQuery('') } }}
          placeholder={disabled ? '—' : placeholder}
          disabled={disabled}
          className="flex-1 px-3 py-2 text-sm bg-transparent outline-none rounded-lg placeholder-gray-400 disabled:cursor-not-allowed"
        />
        <div className="flex items-center pr-2 gap-0.5">
          {value && !disabled && (
            <button onClick={handleClear} className="p-0.5 text-gray-400 hover:text-gray-600 rounded">
              <X size={13} />
            </button>
          )}
          <ChevronDown
            size={15}
            className={`text-gray-400 transition-transform ${open ? 'rotate-180' : ''}`}
          />
        </div>
      </div>

      {open && !disabled && (
        <div className="absolute z-50 left-0 right-0 mt-1 bg-white border border-gray-200 rounded-xl shadow-xl max-h-56 overflow-y-auto">
          {filtered.length === 0 ? (
            <div className="px-4 py-3 text-sm text-gray-400">No matches found</div>
          ) : (
            filtered.map(option => (
              <div
                key={option}
                onMouseDown={() => handleSelect(option)}
                className={`px-4 py-2.5 text-sm cursor-pointer transition-colors ${
                  option === value
                    ? 'bg-navy text-white font-medium'
                    : 'text-gray-700 hover:bg-blue-50 hover:text-navy'
                }`}
              >
                {option}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  )
}
