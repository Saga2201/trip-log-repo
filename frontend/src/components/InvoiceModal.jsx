import React, { useEffect, useMemo, useState } from 'react'
import { X, FileText, MapPin, Truck, CreditCard, Wrench, User } from 'lucide-react'
import { getInvoice, createInvoice, updateInvoice, nextSerial, invoicePdfUrl, invoiceAllPdfsUrl } from '../api'

const EMPTY = {
  date: new Date().toISOString().slice(0, 10),
  vehicle_number: '',
  mobile1: '', mobile2: '',
  from_location: '', to_location: '',
  consignor_name: '', consignor_address: '',
  consignee_name: '', consignee_address: '',
  lr_delivery_office_address: '',
  lr_packages: '', lr_description: '',
  lr_weight_nett: '', lr_weight_charged: '', lr_rate: '',
  lr_service_tax: '', lr_st_charge: '', lr_less_advance: '',
  lr_service_tax_payable_by: 'consignor',
  lr_insurance_risk: 'not_insured',
  lr_insurance_company: '', lr_insurance_policy_no: '',
  lr_insurance_policy_date: '', lr_insurance_amount: '',
  lr_ref_invoice_no: '', lr_ref_value: '', lr_ref_gst_no: '',
  pb_bill_to_name: '', pb_bill_to_address: '',
  pb_freight: '', pb_hamali: '', pb_halting: '',
  db_driver_name: '', db_driver_address: '', db_owner_phone: '',
  db_transport_party: '',
  db_fare: '', db_advance: '', db_collection: '',
  db_previous_balance: '', db_advance_deposited: '',
}

const NUMERIC = new Set([
  'lr_packages','lr_weight_nett','lr_weight_charged','lr_rate',
  'lr_service_tax','lr_st_charge','lr_less_advance','lr_insurance_amount','lr_ref_value',
  'pb_freight','pb_hamali','pb_halting',
  'db_fare','db_advance','db_collection','db_previous_balance','db_advance_deposited',
])

const inputCls = 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-navy focus:border-transparent'
const roCls    = inputCls + ' bg-gray-100 font-semibold'

function Field({ label, required, hint, children }) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-xs font-semibold text-gray-600">
        {label}{required && <span className="text-red-500 ml-0.5">*</span>}
        {hint && <span className="ml-2 text-[10px] font-bold uppercase text-amber-600">{hint}</span>}
      </label>
      {children}
    </div>
  )
}

function Section({ icon: Icon, title, color, children }) {
  return (
    <div className={`bg-${color}-50 rounded-xl p-4 sm:p-5`}>
      <div className="flex items-center gap-2 mb-4 pb-2 border-b border-gray-100">
        <Icon size={16} className="text-navy" />
        <span className="text-xs font-bold text-navy uppercase tracking-wider">{title}</span>
      </div>
      {children}
    </div>
  )
}

export default function InvoiceModal({ open, invoiceId, onClose, onSaved }) {
  const [form, setForm] = useState(EMPTY)
  const [dirty, setDirty] = useState(new Set())  // fields user has manually edited (opt out of mirroring)
  const [serialPreview, setSerialPreview] = useState('')
  const [savedId, setSavedId] = useState(null)   // shows download panel after save
  const [savedSerial, setSavedSerial] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!open) return
    setError('')
    setSavedId(null); setSavedSerial('')
    setDirty(new Set())
    if (invoiceId) {
      getInvoice(invoiceId).then(inv => {
        const next = { ...EMPTY }
        Object.keys(EMPTY).forEach(k => { next[k] = inv[k] ?? EMPTY[k]; if (NUMERIC.has(k)) next[k] = inv[k] != null ? String(inv[k]) : '' })
        setForm(next)
        setSerialPreview(inv.serial_number)
      })
    } else {
      setForm(EMPTY)
      nextSerial(EMPTY.date).then(setSerialPreview).catch(() => setSerialPreview(''))
    }
  }, [open, invoiceId])

  // Refresh serial preview when date crosses an FY boundary (new invoices only)
  useEffect(() => {
    if (!open || invoiceId) return
    nextSerial(form.date).then(setSerialPreview).catch(() => {})
  }, [form.date, open, invoiceId])

  // Mirroring: only for CREATE flow, and only for fields the user hasn't touched.
  const mirrorSet = (key, value) => {
    setForm(f => {
      if (dirty.has(key)) return f
      return { ...f, [key]: value }
    })
  }
  useEffect(() => { if (!invoiceId) mirrorSet('pb_bill_to_name', form.consignor_name) }, [form.consignor_name])
  useEffect(() => { if (!invoiceId) mirrorSet('pb_bill_to_address', form.consignor_address) }, [form.consignor_address])

  // Computed values (read-only fields shown to the user)
  const lrFreight = useMemo(() => (parseFloat(form.lr_weight_charged) || 0) * (parseFloat(form.lr_rate) || 0), [form.lr_weight_charged, form.lr_rate])
  const lrFinal   = useMemo(() => lrFreight + (parseFloat(form.lr_service_tax) || 0) + (parseFloat(form.lr_st_charge) || 0) - (parseFloat(form.lr_less_advance) || 0), [lrFreight, form.lr_service_tax, form.lr_st_charge, form.lr_less_advance])
  useEffect(() => { if (!invoiceId) mirrorSet('pb_freight', String(lrFreight || '')) }, [lrFreight])
  useEffect(() => { if (!invoiceId) mirrorSet('db_fare',    String(lrFreight || '')) }, [lrFreight])
  const pbTotal   = useMemo(() => (parseFloat(form.pb_freight) || 0) + (parseFloat(form.pb_hamali) || 0) + (parseFloat(form.pb_halting) || 0), [form.pb_freight, form.pb_hamali, form.pb_halting])
  const dbBalance = useMemo(() => (parseFloat(form.db_fare) || 0) - (parseFloat(form.db_advance) || 0), [form.db_fare, form.db_advance])

  const set = (key) => (e) => {
    setDirty(d => { const nd = new Set(d); nd.add(key); return nd })
    setForm(f => ({ ...f, [key]: e.target.value }))
  }
  const setVal = (key, v) => {
    setDirty(d => { const nd = new Set(d); nd.add(key); return nd })
    setForm(f => ({ ...f, [key]: v }))
  }

  const handleSave = async () => {
    if (!form.date || !form.vehicle_number) { setError('Date and Vehicle Number are required.'); return }
    setSaving(true); setError('')
    try {
      // Convert numeric strings to numbers on the wire
      const payload = {}
      Object.keys(EMPTY).forEach(k => {
        payload[k] = NUMERIC.has(k) ? (parseFloat(form[k]) || 0) : (form[k] || '')
      })
      payload.vehicle_number = payload.vehicle_number.toUpperCase()
      if (invoiceId) {
        const updated = await updateInvoice(invoiceId, payload)
        setSavedId(invoiceId); setSavedSerial(updated.serial_number)
      } else {
        const res = await createInvoice(payload)
        setSavedId(res.id); setSavedSerial(res.serial_number)
      }
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to save invoice.')
    } finally {
      setSaving(false)
    }
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center sm:p-4">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-white rounded-t-2xl sm:rounded-2xl shadow-2xl w-full sm:max-w-4xl max-h-[95vh] sm:max-h-[92vh] flex flex-col overflow-hidden">
        <div className="flex items-center justify-between px-4 sm:px-6 py-3 sm:py-4 bg-navy text-white">
          <div className="flex items-center gap-3">
            <FileText size={20} />
            <span className="text-base font-bold">
              {invoiceId ? 'Edit Invoice' : 'New Invoice'} · <span className="opacity-80 font-normal text-sm">{serialPreview}</span>
            </span>
          </div>
          <button onClick={onClose} className="hover:bg-white/20 rounded-lg p-1"><X size={20} /></button>
        </div>

        <div className="overflow-y-auto flex-1 p-4 sm:p-6 space-y-4 sm:space-y-6">

          <Section icon={FileText} title="Common Header" color="blue">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <Field label="Serial #"><div className={roCls + ' font-mono text-navy'}>{serialPreview || '—'}</div></Field>
              <Field label="Date" required><input type="date" value={form.date} onChange={set('date')} className={inputCls} /></Field>
              <Field label="Vehicle Number" required>
                <input type="text" value={form.vehicle_number} onChange={set('vehicle_number')} placeholder="e.g. GJ01AB1234" className={inputCls + ' uppercase font-mono tracking-widest'} />
              </Field>
              <Field label="Mobile 1">
                <input type="tel" inputMode="numeric" maxLength={10}
                  value={form.mobile1}
                  onChange={e => setVal('mobile1', e.target.value.replace(/\D/g,'').slice(0,10))}
                  placeholder="10-digit number" className={inputCls} />
              </Field>
              <Field label="Mobile 2">
                <input type="tel" inputMode="numeric" maxLength={10}
                  value={form.mobile2}
                  onChange={e => setVal('mobile2', e.target.value.replace(/\D/g,'').slice(0,10))}
                  placeholder="10-digit number" className={inputCls} />
              </Field>
            </div>
          </Section>

          <Section icon={MapPin} title="Route & Parties" color="orange">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Field label="From (Loading)"><input value={form.from_location} onChange={set('from_location')} className={inputCls} /></Field>
              <Field label="To (Unloading)"><input value={form.to_location} onChange={set('to_location')} className={inputCls} /></Field>
              <Field label="Consignor Name"><input value={form.consignor_name} onChange={set('consignor_name')} className={inputCls} /></Field>
              <Field label="Consignor Address"><input value={form.consignor_address} onChange={set('consignor_address')} className={inputCls} /></Field>
              <Field label="Consignee Name"><input value={form.consignee_name} onChange={set('consignee_name')} className={inputCls} /></Field>
              <Field label="Consignee Address"><input value={form.consignee_address} onChange={set('consignee_address')} className={inputCls} /></Field>
            </div>
          </Section>

          <Section icon={Truck} title="LR Details" color="green">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
              <div className="sm:col-span-2"><Field label="Delivery Office Address"><input value={form.lr_delivery_office_address} onChange={set('lr_delivery_office_address')} className={inputCls} /></Field></div>
              <Field label="Packages"><input type="number" min="0" value={form.lr_packages} onChange={set('lr_packages')} className={inputCls} /></Field>
              <Field label="Description (Said to Contain)"><input value={form.lr_description} onChange={set('lr_description')} className={inputCls} /></Field>
              <Field label="Weight Nett (kg)"><input type="number" min="0" step="0.01" value={form.lr_weight_nett} onChange={set('lr_weight_nett')} className={inputCls} /></Field>
              <Field label="Weight Charged (kg)"><input type="number" min="0" step="0.01" value={form.lr_weight_charged} onChange={set('lr_weight_charged')} className={inputCls} /></Field>
              <Field label="Rate (₹/kg)"><input type="number" min="0" step="0.01" value={form.lr_rate} onChange={set('lr_rate')} className={inputCls} /></Field>
              <Field label="Total Freight"><div className={roCls}>₹{lrFreight.toLocaleString('en-IN')}</div></Field>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-4">
              <Field label="Service Tax (₹)"><input type="number" min="0" value={form.lr_service_tax} onChange={set('lr_service_tax')} className={inputCls} /></Field>
              <Field label="St. Charge (₹)"><input type="number" min="0" value={form.lr_st_charge} onChange={set('lr_st_charge')} className={inputCls} /></Field>
              <Field label="Less Advance (₹)"><input type="number" min="0" value={form.lr_less_advance} onChange={set('lr_less_advance')} className={inputCls} /></Field>
            </div>
            <div className="mb-4">
              <label className="text-xs font-semibold text-gray-600 block mb-1">Service Tax Payable By</label>
              <div className="flex gap-4 text-sm">
                {['consignor','consignee','transporter'].map(v => (
                  <label key={v} className="flex items-center gap-2 capitalize">
                    <input type="radio" name="stp" checked={form.lr_service_tax_payable_by === v} onChange={() => setVal('lr_service_tax_payable_by', v)} />
                    {v}
                  </label>
                ))}
              </div>
            </div>
            <div className="border-t border-green-200 pt-4">
              <div className="text-xs font-bold text-navy mb-2">INSURANCE</div>
              <div className="flex gap-4 text-sm mb-3">
                <label className="flex items-center gap-2">
                  <input type="radio" name="risk" checked={form.lr_insurance_risk === 'not_insured'} onChange={() => setVal('lr_insurance_risk', 'not_insured')} />
                  Not insured (Owner's risk)
                </label>
                <label className="flex items-center gap-2">
                  <input type="radio" name="risk" checked={form.lr_insurance_risk === 'insured'} onChange={() => setVal('lr_insurance_risk', 'insured')} />
                  Insured
                </label>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
                <Field label="Company"><input value={form.lr_insurance_company} onChange={set('lr_insurance_company')} className={inputCls} /></Field>
                <Field label="Policy No"><input value={form.lr_insurance_policy_no} onChange={set('lr_insurance_policy_no')} className={inputCls} /></Field>
                <Field label="Policy Date"><input type="date" value={form.lr_insurance_policy_date} onChange={set('lr_insurance_policy_date')} className={inputCls} /></Field>
                <Field label="Amount"><input type="number" min="0" value={form.lr_insurance_amount} onChange={set('lr_insurance_amount')} className={inputCls} /></Field>
              </div>
            </div>
            <div className="border-t border-green-200 pt-4 mt-4">
              <div className="text-xs font-bold text-navy mb-2">REFERENCE (Consignor's own invoice)</div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <Field label="Invoice No"><input value={form.lr_ref_invoice_no} onChange={set('lr_ref_invoice_no')} className={inputCls} /></Field>
                <Field label="Value (₹)"><input type="number" min="0" value={form.lr_ref_value} onChange={set('lr_ref_value')} className={inputCls} /></Field>
                <Field label="GST No"><input value={form.lr_ref_gst_no} onChange={set('lr_ref_gst_no')} className={inputCls} /></Field>
              </div>
            </div>
          </Section>

          <Section icon={CreditCard} title="Party Bill Details" color="purple">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Field label="Bill To Name" hint="mirrors consignor"><input value={form.pb_bill_to_name} onChange={set('pb_bill_to_name')} className={inputCls} /></Field>
              <Field label="Bill To Address" hint="mirrors consignor"><input value={form.pb_bill_to_address} onChange={set('pb_bill_to_address')} className={inputCls} /></Field>
              <Field label="Freight (₹)" hint="mirrors LR total"><input type="number" min="0" value={form.pb_freight} onChange={set('pb_freight')} className={inputCls} /></Field>
              <Field label="Hamali (₹)"><input type="number" min="0" value={form.pb_hamali} onChange={set('pb_hamali')} className={inputCls} /></Field>
              <Field label="Halting (₹)"><input type="number" min="0" value={form.pb_halting} onChange={set('pb_halting')} className={inputCls} /></Field>
              <Field label="Total Amount"><div className={roCls}>₹{pbTotal.toLocaleString('en-IN')}</div></Field>
            </div>
          </Section>

          <Section icon={User} title="Driver Bill Details" color="yellow">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
              <Field label="Driver / Owner Name"><input value={form.db_driver_name} onChange={set('db_driver_name')} className={inputCls} /></Field>
              <Field label="Owner Phone"><input type="tel" inputMode="numeric" maxLength={10} value={form.db_owner_phone} onChange={e => setVal('db_owner_phone', e.target.value.replace(/\D/g,'').slice(0,10))} className={inputCls} /></Field>
              <div className="sm:col-span-2"><Field label="Driver Address"><input value={form.db_driver_address} onChange={set('db_driver_address')} className={inputCls} /></Field></div>
              <div className="sm:col-span-2"><Field label="Transport Party (broker/agent)"><input value={form.db_transport_party} onChange={set('db_transport_party')} className={inputCls} /></Field></div>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-4">
              <Field label="Fare (₹)" hint="mirrors LR total"><input type="number" min="0" value={form.db_fare} onChange={set('db_fare')} className={inputCls} /></Field>
              <Field label="Advance (₹)"><input type="number" min="0" value={form.db_advance} onChange={set('db_advance')} className={inputCls} /></Field>
              <Field label="Balance Fare"><div className={roCls}>₹{dbBalance.toLocaleString('en-IN')}</div></Field>
              <Field label="Previous Balance"><input type="number" min="0" value={form.db_previous_balance} onChange={set('db_previous_balance')} className={inputCls} /></Field>
              <Field label="Advance Deposited"><input type="number" min="0" value={form.db_advance_deposited} onChange={set('db_advance_deposited')} className={inputCls} /></Field>
              <Field label="Collection (Vasuli)"><input type="number" min="0" value={form.db_collection} onChange={set('db_collection')} className={inputCls} /></Field>
            </div>
          </Section>

          {savedId && (
            <div className="bg-green-50 border border-green-200 rounded-xl p-4">
              <div className="font-semibold text-green-800 mb-2">Invoice {savedSerial} saved. Download PDFs:</div>
              <div className="flex flex-wrap gap-2">
                <a href={invoicePdfUrl(savedId, 'lr')} target="_blank" rel="noopener noreferrer" className="px-3 py-1.5 rounded-lg bg-white border border-green-300 text-sm hover:bg-green-100">LR</a>
                <a href={invoicePdfUrl(savedId, 'party_bill')} target="_blank" rel="noopener noreferrer" className="px-3 py-1.5 rounded-lg bg-white border border-green-300 text-sm hover:bg-green-100">Party Bill</a>
                <a href={invoicePdfUrl(savedId, 'driver_bill')} target="_blank" rel="noopener noreferrer" className="px-3 py-1.5 rounded-lg bg-white border border-green-300 text-sm hover:bg-green-100">Driver Bill</a>
                <a href={invoiceAllPdfsUrl(savedId)} target="_blank" rel="noopener noreferrer" className="px-3 py-1.5 rounded-lg bg-navy text-white text-sm hover:bg-navy-light font-semibold">All (ZIP)</a>
              </div>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm">{error}</div>
          )}
        </div>

        <div className="flex items-center justify-end gap-3 px-4 sm:px-6 py-3 sm:py-4 bg-gray-50 border-t border-gray-200">
          <button onClick={onClose} className="flex-1 sm:flex-none px-5 py-2 rounded-lg text-sm font-medium text-gray-600 bg-white border border-gray-300 hover:bg-gray-100">
            {savedId ? 'Done' : 'Cancel'}
          </button>
          {!savedId && (
            <button onClick={handleSave} disabled={saving} className="flex-1 sm:flex-none px-6 py-2 rounded-lg text-sm font-bold text-white bg-navy hover:bg-navy-light disabled:opacity-50">
              {saving ? 'Saving…' : invoiceId ? 'Save Changes' : 'Save & Generate PDFs'}
            </button>
          )}
          {savedId && (
            <button onClick={onSaved} className="flex-1 sm:flex-none px-6 py-2 rounded-lg text-sm font-bold text-white bg-navy hover:bg-navy-light">Return to List</button>
          )}
        </div>
      </div>
    </div>
  )
}
