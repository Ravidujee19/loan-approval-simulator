import { useState } from 'react'
import { login } from '../services/api.jsx'
import { useAuth } from '../store/auth.js'
import { Link, useNavigate } from 'react-router-dom'
import '../styles/login.css'           

export default function Login(){
  const [email,setEmail]=useState('ravidu@gmail.com')
  const [password,setPassword]=useState('pizza@123')
  const [err,setErr]=useState(null)
  const { login: setAuth } = useAuth()
  const nav = useNavigate()

  async function onSubmit(e){
    e.preventDefault()
    try{
      const res = await login(email,password)
      setAuth(res.access_token, res.role)
      nav('/dashboard')
    }catch(e){ setErr('Invalid credentials') }
  }

  return (
    <div className="login-page">
      <div className="max-w-md mx-auto">
        <div className="login-card">
          <h1 className="text-2xl font-semibold mb-6">Login</h1>

          {err && <div className="login-alert">{err}</div>}

          <form onSubmit={onSubmit} className="space-y-4">
            <input className="login-input" value={email}
                   onChange={e=>setEmail(e.target.value)} placeholder="user1@example.com" />
            <input className="login-input" type="password" value={password}
                   onChange={e=>setPassword(e.target.value)} placeholder="••••••••" />
            <button className="login-btn w-full" type="submit">Login</button>
          </form>

          <p className="mt-4 text-sm text-slate-400">
            No account? <Link to="/register" className="login-link">Register</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
