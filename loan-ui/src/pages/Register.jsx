import { useState } from 'react'
import { register, login } from '../services/api.jsx'
import { useAuth } from '../store/auth.js'
import { useNavigate } from 'react-router-dom'
import '../styles/register.css'   // <-- page-scoped styles

export default function Register(){
  const [email,setEmail]=useState('user1@example.com')
  const [password,setPassword]=useState('User@12345')
  const [role,setRole]=useState('applicant')
  const [loading, setLoading] = useState(false)
  const [err, setErr] = useState('')
  const [ok, setOk] = useState('')
  const { login: setAuth } = useAuth()
  const nav = useNavigate()

  async function onSubmit(e){
    e.preventDefault()
    setErr(''); setOk(''); setLoading(true)
    try{
      await register({ email, password, role })
      setOk('Account created. Signing you in…')
      const res = await login(email, password)
      setAuth(res.access_token, res.role)
      nav('/dashboard')
    }catch(e){
      setErr(e?.response?.data?.detail || 'Registration failed')
    }finally{
      setLoading(false)
    }
  }

  return (
    <div className="register-page">
      <div className="max-w-md mx-auto">
        <div className="register-card">
          <h1 className="text-2xl font-semibold mb-6">Register</h1>

          {err && <div className="register-alert">{err}</div>}
          {ok && <div className="register-ok">{ok}</div>}

          <form onSubmit={onSubmit} className="space-y-4">
            <input
              className="register-input"
              value={email}
              onChange={e=>setEmail(e.target.value)}
              placeholder="Email"
              type="email"
            />
            <input
              className="register-input"
              type="password"
              value={password}
              onChange={e=>setPassword(e.target.value)}
              placeholder="Password"
            />
            <select
              className="register-input"
              value={role}
              onChange={e=>setRole(e.target.value)}
            >
              <option value="applicant">Applicant</option>
              <option value="admin">Admin</option>
            </select>
            <button className="register-btn w-full" type="submit" disabled={loading}>
              {loading ? 'Creating…' : 'Create account'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}


// import { useState } from 'react'
// import { register, login } from '../services/api.jsx'
// import { useAuth } from '../store/auth.js'
// import { useNavigate } from 'react-router-dom'
// export default function Register(){
//   const [email,setEmail]=useState('user1@example.com')
//   const [password,setPassword]=useState('User@12345')
//   const [role,setRole]=useState('applicant')
//   const { login: setAuth } = useAuth()
//   const nav = useNavigate()
//   async function onSubmit(e){
//     e.preventDefault()
//     await register({ email, password, role })
//     const res = await login(email, password)
//     setAuth(res.access_token, res.role)
//     nav('/dashboard')
//   }
//   return (
//     <div className="max-w-md mx-auto card">
//       <h1 className="text-xl font-semibold mb-4">Register</h1>
//       <form onSubmit={onSubmit} className="space-y-3">
//         <input className="input" value={email} onChange={e=>setEmail(e.target.value)} placeholder="Email"/>
//         <input className="input" type="password" value={password} onChange={e=>setPassword(e.target.value)} placeholder="Password"/>
//         <select className="input" value={role} onChange={e=>setRole(e.target.value)}>
//           <option value="applicant">Applicant</option>
//           <option value="admin">Admin</option>
//         </select>
//         <button className="btn w-full" type="submit">Create account</button>
//       </form>
//     </div>
//   )
// }
