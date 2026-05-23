import React, { useState, useEffect, useRef } from 'react'
import { X, Truck, Phone, MapPin, CreditCard, FileText } from 'lucide-react'
import { getLocations, createTrip, updateTrip, uploadImage, deleteImage, api } from '../api'
import PaymentCard from './PaymentCard'
import Combobox from './Combobox'

// Cache locations globally so we only fetch once per session
let _locationsCache = null

// Vehicle number plate: 2 letters (state) + 2 digits + 4 digits = e.g. GJ011234
const PLATE_REGEX = /^[A-Z]{2}[0-9]{2}[0-9]{4}$/

const EMPTY_FORM = {
  date: new Date().toISOString().slice(0, 10),
  vehicle_number: '',
  state: '',
  city: '',
  driver_phone: '',
  owner_phone: '',
  party_name: '',
  party_contact: '',
  loading_address: '',
  unloading_address: '',
  material: '',
  material_weight: '',
  total_booking: '',
  party_rate: '',
  payment_1: '',
  payment_2: '',
  payment_3: '',
  note: '',
}

const EMPTY_IMG = { file: null, path: null, deleted: false }

function SectionHeader({ icon: Icon, title }) {
  return (
    <div className="flex items-center gap-2 mb-4 pb-2 border-b border-gray-100">
      <Icon size={16} className="text-navy" />
      <span className="text-xs font-bold text-navy uppercase tracking-wider">{title}</span>
    </div>
  )
}

function Field({ label, required, children }) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-xs font-semibold text-gray-600">
        {label}{required && <span className="text-red-500 ml-0.5">*</span>}
      </label>
      {children}
    </div>
  )
}

const inputCls = 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-navy focus:border-transparent'

export default function TripModal({ open, tripId, onClose, onSaved }) {
  const [trip, setTrip] = useState(null)
  const [form, setForm] = useState(EMPTY_FORM)
  const [imgs, setImgs] = useState({ 1: EMPTY_IMG, 2: EMPTY_IMG, 3: EMPTY_IMG })
  const [locations, setLocations] = useState({ states: [], cities: {} })
  const [cities, setCities] = useState([])
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [plateError, setPlateError] = useState('')

  // Load locations once, with caching
  useEffect(() => {
    if (_locationsCache) {
      setLocations(_locationsCache)
      return
    }
    getLocations()
      .then(data => {
        _locationsCache = data
        setLocations(data)
      })
      .catch(err => console.error('Failed to load locations:', err))
  }, [])

  // Load trip data when modal opens
  useEffect(() => {
    if (!open) return
    setError('')
    setPlateError('')
    if (tripId) {
      api.get(`/trips/${tripId}`).then(r => {
        const t = r.data
        setTrip(t)
        setForm({
          date: t.date || EMPTY_FORM.date,
          vehicle_number: t.vehicle_number || '',
          state: t.state || '',
          city: t.city || '',
          driver_phone: t.driver_phone || '',
          owner_phone: t.owner_phone || '',
          party_name: t.party_name || '',
          party_contact: t.party_contact || '',
          loading_address: t.loading_address || '',
          unloading_address: t.unloading_address || '',
          material: t.material || '',
          material_weight: t.material_weight?.toString() || '',
          total_booking: t.total_booking?.toString() || '',
          party_rate: t.party_rate?.toString() || '',
          payment_1: t.payment_1?.toString() || '',
          payment_2: t.payment_2?.toString() || '',
          payment_3: t.payment_3?.toString() || '',
          note: t.note || '',
        })
        setImgs({
          1: { file: null, path: t.payment_1_image || null, deleted: false },
          2: { file: null, path: t.payment_2_image || null, deleted: false },
          3: { file: null, path: t.payment_3_image || null, deleted: false },
        })
        setCities(t.state ? (locations.cities[t.state] || []) : [])
      })
    } else {
      setTrip(null)
      setForm(EMPTY_FORM)
      setImgs({ 1: EMPTY_IMG, 2: EMPTY_IMG, 3: EMPTY_IMG })
      setCities([])
    }
  }, [open, tripId])

  // Update city list when state changes; clear city if it doesn't belong to new state
  useEffect(() => {
    const newCities = form.state ? (locations.cities[form.state] || []) : []
    setCities(newCities)
    if (form.city && !newCities.includes(form.city)) {
      setForm(f => ({ ...f, city: '' }))
    }
  }, [form.state, locations.cities])

  const set = (field) => (e) => setForm(f => ({ ...f, [field]: e.target.value }))
  const setVal = (field, val) => setForm(f => ({ ...f, [field]: val }))

  // Only allow letters and digits while typing the plate; auto-uppercase
  const handlePlateChange = (e) => {
    const raw = e.target.value.replace(/[^A-Za-z0-9]/g, '').toUpperCase().slice(0, 8)
    setForm(f => ({ ...f, vehicle_number: raw }))
    if (plateError) setPlateError('')
  }

  const handlePlateBlur = () => {
    const v = form.vehicle_number
    if (v && !PLATE_REGEX.test(v)) {
      setPlateError('Invalid format. Expected: GJ011234 (2 letters + 2 digits + 4 digits)')
    } else {
      setPlateError('')
    }
  }

  // Block e / E / + / - / . in number inputs (type="number" still allows them)
  const blockNonNumeric = (e) => {
    if (['e', 'E', '+', '-', '.'].includes(e.key)) e.preventDefault()
  }

  const handleSave = async () => {
    if (!form.date || !form.vehicle_number || !form.loading_address || !form.unloading_address || !form.total_booking) {
      setError('Please fill in all required fields.')
      return
    }
    if (!PLATE_REGEX.test(form.vehicle_number)) {
      setPlateError('Invalid format. Expected: GJ011234 (2 letters + 2 digits + 4 digits)')
      setError('Please fix the vehicle number before saving.')
      return
    }
    const totalBooking = parseFloat(form.total_booking) || 0
    const p1 = parseFloat(form.payment_1) || 0
    const p2 = parseFloat(form.payment_2) || 0
    const p3 = parseFloat(form.payment_3) || 0
    const totalPaid = p1 + p2 + p3
    if (totalPaid > totalBooking) {
      setError(`Total payments (₹${totalPaid.toLocaleString('en-IN')}) exceed Total Booking (₹${totalBooking.toLocaleString('en-IN')}). Please correct the amounts.`)
      return
    }
    setSaving(true)
    setError('')
    try {
      const data = {
        date: form.date,
        vehicle_number: form.vehicle_number.toUpperCase(),
        state: form.state,
        city: form.city,
        driver_phone: form.driver_phone,
        owner_phone: form.owner_phone,
        party_name: form.party_name,
        party_contact: form.party_contact,
        note: form.note,
        loading_address: form.loading_address,
        unloading_address: form.unloading_address,
        material: form.material,
        material_weight: parseFloat(form.material_weight) || 0,
        total_booking: parseFloat(form.total_booking) || 0,
        party_rate: parseFloat(form.party_rate) || 0,
        payment_1: parseFloat(form.payment_1) || 0,
        payment_2: parseFloat(form.payment_2) || 0,
        payment_3: parseFloat(form.payment_3) || 0,
        payment_1_image: trip?.payment_1_image || null,
        payment_2_image: trip?.payment_2_image || null,
        payment_3_image: trip?.payment_3_image || null,
      }

      let id
      if (trip) {
        await updateTrip(trip.id, data)
        id = trip.id
      } else {
        const res = await createTrip(data)
        id = res.id
      }

      // Handle image uploads and deletions
      for (const n of [1, 2, 3]) {
        const s = imgs[n]
        if (s.deleted && (trip?.[`payment_${n}_image`] || s.path)) {
          await deleteImage(id, n).catch(() => {})
        }
        if (s.file) {
          await uploadImage(id, n, s.file).catch(() => {})
        }
      }

      onSaved()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save trip.')
    } finally {
      setSaving(false)
    }
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center sm:p-4">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />

      {/* Modal — bottom-sheet on mobile, centered dialog on sm+ */}
      <div className="relative bg-white rounded-t-2xl sm:rounded-2xl shadow-2xl w-full sm:max-w-3xl max-h-[95vh] sm:max-h-[92vh] flex flex-col overflow-hidden">

        {/* Header */}
        <div className="flex items-center justify-between px-4 sm:px-6 py-3 sm:py-4 bg-navy text-white flex-shrink-0">
          <div className="flex items-center gap-3">
            <Truck size={20} />
            <span className="text-base font-bold">{trip ? 'Edit Trip' : 'New Trip'}</span>
          </div>
          <button onClick={onClose} className="hover:bg-white/20 rounded-lg p-1 transition-colors">
            <X size={20} />
          </button>
        </div>

        {/* Body */}
        <div className="overflow-y-auto flex-1 p-4 sm:p-6 space-y-4 sm:space-y-6">

          {/* Trip Details */}
          <div className="bg-blue-50 rounded-xl p-4 sm:p-5">
            <SectionHeader icon={Truck} title="Trip Details" />
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Field label="Date" required>
                <input type="date" value={form.date} onChange={set('date')} className={inputCls} />
              </Field>
              <Field label="Vehicle Number" required>
                <input
                  type="text"
                  value={form.vehicle_number}
                  onChange={handlePlateChange}
                  onBlur={handlePlateBlur}
                  placeholder="e.g. GJ01AB1234"
                  maxLength={8}
                  className={inputCls + ' uppercase font-mono tracking-widest' + (plateError ? ' border-red-400 ring-1 ring-red-400' : '')}
                />
                {plateError && (
                  <p className="text-xs text-red-500 mt-0.5">{plateError}</p>
                )}
                <p className="text-xs text-gray-400">Format: 2 letters + 2 digits + 4 digits · e.g. GJ011234</p>
              </Field>
              <Field label="State">
                <Combobox
                  options={locations.states}
                  value={form.state}
                  onChange={val => setVal('state', val)}
                  placeholder="Search state…"
                />
              </Field>
              <Field label="City">
                <Combobox
                  options={cities}
                  value={form.city}
                  onChange={val => setVal('city', val)}
                  placeholder={form.state ? 'Search city…' : 'Select state first'}
                  disabled={!form.state}
                />
              </Field>
            </div>
          </div>

          {/* Contact Details */}
          <div className="bg-green-50 rounded-xl p-4 sm:p-5">
            <SectionHeader icon={Phone} title="Contact Details" />
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Field label="Driver Phone">
                <input type="tel" value={form.driver_phone} onChange={set('driver_phone')} placeholder="10-digit number" className={inputCls} />
              </Field>
              <Field label="Owner Phone">
                <input type="tel" value={form.owner_phone} onChange={set('owner_phone')} placeholder="10-digit number" className={inputCls} />
              </Field>
              <Field label="Party Name">
                <input type="text" value={form.party_name} onChange={set('party_name')} placeholder="Party / consignee name" className={inputCls} />
              </Field>
              <Field label="Party Contact">
                <input type="tel" value={form.party_contact} onChange={set('party_contact')} placeholder="10-digit number" className={inputCls} />
              </Field>
            </div>
          </div>

          {/* Route */}
          <div className="bg-orange-50 rounded-xl p-4 sm:p-5">
            <SectionHeader icon={MapPin} title="Route" />
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Field label="From (Loading Point)" required>
                <input
                  type="text"
                  value={form.loading_address}
                  onChange={set('loading_address')}
                  placeholder="e.g. Surat Textile Market"
                  className={inputCls}
                />
              </Field>
              <Field label="To (Unloading Point)" required>
                <input
                  type="text"
                  value={form.unloading_address}
                  onChange={set('unloading_address')}
                  placeholder="e.g. Mumbai APMC Yard"
                  className={inputCls}
                />
              </Field>
              <Field label="Material">
                <input
                  type="text"
                  value={form.material}
                  onChange={set('material')}
                  placeholder="e.g. Cotton Bales, Steel Rods"
                  className={inputCls}
                />
              </Field>
              <Field label="Weight (T)">
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={form.material_weight}
                  onChange={set('material_weight')}
                  onKeyDown={blockNonNumeric}
                  placeholder="0"
                  className={inputCls}
                />
              </Field>
            </div>
          </div>

          {/* Payment Details */}
          <div className="bg-purple-50 rounded-xl p-4 sm:p-5">
            <SectionHeader icon={CreditCard} title="Payment Details" />
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
              <Field label="Total Booking (₹)" required>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm font-semibold">₹</span>
                  <input
                    type="number"
                    min="0"
                    step="1"
                    value={form.total_booking}
                    onChange={set('total_booking')}
                    onKeyDown={blockNonNumeric}
                    placeholder="0"
                    className={inputCls + ' pl-7'}
                  />
                </div>
              </Field>
              <Field label="Party Rate (₹)">
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm font-semibold">₹</span>
                  <input
                    type="number"
                    min="0"
                    step="1"
                    value={form.party_rate}
                    onChange={set('party_rate')}
                    onKeyDown={blockNonNumeric}
                    placeholder="0"
                    className={inputCls + ' pl-7'}
                  />
                </div>
                {form.party_rate && parseFloat(form.party_rate) > 0 && form.total_booking && (
                  <p className="text-xs text-emerald-600 font-semibold mt-1">
                    Commission: ₹{(parseFloat(form.party_rate) - parseFloat(form.total_booking || 0)).toLocaleString('en-IN')}
                  </p>
                )}
              </Field>
            </div>
            {/* Live payment summary */}
            {(() => {
              const booking = parseFloat(form.total_booking) || 0
              const paid = (parseFloat(form.payment_1) || 0) + (parseFloat(form.payment_2) || 0) + (parseFloat(form.payment_3) || 0)
              const over = paid > booking
              const pct  = booking > 0 ? Math.min((paid / booking) * 100, 100) : 0
              return booking > 0 ? (
                <div className="mb-2">
                  <div className="flex justify-between text-xs mb-1">
                    <span className={over ? 'text-red-600 font-semibold' : 'text-gray-500'}>
                      Paid: ₹{paid.toLocaleString('en-IN')}
                    </span>
                    <span className={over ? 'text-red-600 font-semibold' : 'text-gray-500'}>
                      {over
                        ? `Over by ₹${(paid - booking).toLocaleString('en-IN')}`
                        : `Remaining: ₹${(booking - paid).toLocaleString('en-IN')}`}
                    </span>
                  </div>
                  <div className="w-full h-1.5 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${over ? 'bg-red-500' : paid === booking ? 'bg-green-500' : 'bg-navy'}`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              ) : null
            })()}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {[1, 2, 3].map(n => (
                <PaymentCard
                  key={n}
                  label={`Payment ${n}`}
                  n={n}
                  amount={form[`payment_${n}`]}
                  onAmountChange={val => setVal(`payment_${n}`, val)}
                  onKeyDown={blockNonNumeric}
                  imgState={imgs[n]}
                  onFileSelect={file => setImgs(s => ({ ...s, [n]: { ...s[n], file, deleted: false } }))}
                  onRemove={() => setImgs(s => ({ ...s, [n]: { ...s[n], file: null, deleted: true } }))}
                />
              ))}
            </div>
          </div>

          {/* Note */}
          <div className="bg-yellow-50 rounded-xl p-4 sm:p-5">
            <SectionHeader icon={FileText} title="Note" />
            <textarea
              value={form.note}
              onChange={set('note')}
              placeholder="Add any notes or remarks about this trip…"
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-base focus:outline-none focus:ring-2 focus:ring-navy focus:border-transparent resize-y"
            />
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm">
              {error}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 px-4 sm:px-6 py-3 sm:py-4 bg-gray-50 border-t border-gray-200 flex-shrink-0">
          <button
            onClick={onClose}
            className="flex-1 sm:flex-none px-5 py-2.5 sm:py-2 rounded-lg text-sm font-medium text-gray-600 bg-white border border-gray-300 hover:bg-gray-100 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex-1 sm:flex-none px-6 py-2.5 sm:py-2 rounded-lg text-sm font-bold text-white bg-navy hover:bg-navy-light disabled:opacity-50 transition-colors"
          >
            {saving ? 'Saving…' : trip ? 'Save Changes' : 'Create Trip'}
          </button>
        </div>
      </div>
    </div>
  )
}
