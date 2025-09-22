import React from 'react'

export default function 
ApplicantsTable({ items = [], loading = false, isAdmin = false, onDelete = () => {} }) {
  if (loading) return <div className="dashboard-card text-sm">Loading applicants…</div>
  if (!items || items.length === 0) return <div className="dashboard-card text-sm">No applicants found.</div>

  return (
    <div className="dashboard-card overflow-x-auto">
      <table className="min-w-full text-sm">
        <thead className="text-left">
          <tr className="border-b border-white/10">
            <th className="py-2 pr-4">Name</th>
            <th className="py-2 pr-4">Email</th>
            <th className="py-2 pr-4">Phone</th>
            <th className="py-2 pr-4">Employment</th>
            <th className="py-2 pr-4">Income</th>
            <th className="py-2 pr-4">Debt</th>
            <th className="py-2 pr-4">Created</th>
            {isAdmin && <th className="py-2 pr-4 w-28">Actions</th>}
          </tr>
        </thead>
        <tbody>
          {items.map(a => (
            <tr key={a.id} className="border-b border-white/5">
              <td className="py-2 pr-4">{a.first_name} {a.last_name}</td>
              <td className="py-2 pr-4">{a.email}</td>
              <td className="py-2 pr-4">{a.phone}</td>
              <td className="py-2 pr-4">{a.employment_status || '-'}</td>
              <td className="py-2 pr-4">{a.monthly_income ?? '-'}</td>
              <td className="py-2 pr-4">{a.existing_monthly_debt ?? '-'}</td>
              <td className="py-2 pr-4">
                {a.created_at ? new Date(a.created_at).toLocaleString() : '-'}
              </td>
              {isAdmin && (
                <td className="py-2 pr-4">
                  <button
                    onClick={() => onDelete(a.id)}
                    className="px-2 py-1 text-xs rounded-md border border-rose-500/40 text-rose-300 hover:bg-rose-500/10"
                    title="Delete applicant"
                  >
                    Delete
                  </button>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
      <div className="text-xs text-slate-400 mt-2">Total: {items.length}</div>
    </div>
  )
}
