import { Outlet, Link, useNavigate } from 'react-router-dom'
import NavBar from './NavBar.jsx'
export default function Layout(){
  return (
    <div className="min-h-screen">
      <NavBar/>
      <main className="container mx-auto p-6">
        <Outlet/>
      </main>
    </div>
  )
}
