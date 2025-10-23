import { create } from 'zustand'
export const useAuth = create((set)=>({
  token: localStorage.getItem('token') || null,
  role: localStorage.getItem('role') || null,
  login: (t, r) => { localStorage.setItem('token', t); localStorage.setItem('role', r); set({ token: t, role: r }) },
  logout: () => { localStorage.removeItem('token'); localStorage.removeItem('role'); set({ token: null, role: null }) }
}))
