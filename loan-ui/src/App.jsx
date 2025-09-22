import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout.jsx'
import Login from './pages/Login.jsx'
import Register from './pages/Register.jsx'
import Dashboard from './pages/Dashboard.jsx'
import ApplicantForm from './pages/ApplicantForm.jsx'
import LoanForm from './pages/LoanForm.jsx'
import LoanDetail from './pages/LoanDetail.jsx'
import NotFound from './pages/NotFound.jsx'
import ProtectedRoute from './components/ProtectedRoute.jsx'
export default function App(){
  return (
    <Routes>
      <Route element={<Layout/>}>
        <Route path="/" element={<Navigate to="/dashboard" replace/>}/>
        <Route path="/login" element={<Login/>}/>
        <Route path="/register" element={<Register/>}/>
        <Route element={<ProtectedRoute/>}>
          <Route path="/dashboard" element={<Dashboard/>}/>
          <Route path="/applicants/new" element={<ApplicantForm/>}/>
          <Route path="/loans/new" element={<LoanForm/>}/>
          <Route path="/loans/:id" element={<LoanDetail/>}/>
        </Route>
        <Route path="*" element={<NotFound/>}/>
      </Route>
    </Routes>
  )
}
