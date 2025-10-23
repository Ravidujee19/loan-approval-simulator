export default function FormField({ label, children }){
  return (
    <label className="block space-y-1">
      <span className="text-sm text-gray-300">{label}</span>
      {children}
    </label>
  )
}
