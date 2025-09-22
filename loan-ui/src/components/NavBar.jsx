import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../store/auth.js'
export default function NavBar(){
  const { token, logout } = useAuth()
  const nav = useNavigate()
  return (
    <header className="border-b border-gray-800 bg-gray-950/60">
      <div className="container mx-auto p-4 flex gap-4 items-center">
        <Link to="/" className="font-semibold">Evaluator</Link>
        {token && (
          <>
            <NavLink to="/dashboard" className="hover:underline">Dashboard</NavLink>
            <NavLink to="/applicants/new" className="hover:underline">Applicant</NavLink>
            <NavLink to="/loans/new" className="hover:underline">Loan</NavLink>
          </>
        )}
        <div className="ml-auto">
          {!token ? (
            <>
              <NavLink to="/login" className="mr-3 hover:underline">Login</NavLink>
              <NavLink to="/register" className="hover:underline">Register</NavLink>
            </>
          ) : (
            <button className="btn" onClick={()=>{ logout(); nav('/login') }}>Logout</button>
          )}
        </div>
      </div>
    </header>
  )
}
