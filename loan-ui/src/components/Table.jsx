export default function Table({ cols=[], rows=[] }){
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm">
        <thead><tr>{cols.map(c=><th key={c} className="text-left px-3 py-2 border-b border-gray-800">{c}</th>)}</tr></thead>
        <tbody>
          {rows.map((r,i)=>(
            <tr key={i} className="border-b border-gray-900">
              {cols.map(c=><td key={c} className="px-3 py-2">{r[c]}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
