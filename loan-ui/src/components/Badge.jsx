export default function Badge({ kind, children }){
  const color = kind==='pass' ? 'bg-emerald-700' : kind==='fail' ? 'bg-rose-700' : 'bg-amber-700'
  return <span className={`badge ${color}`}>{children}</span>
}
