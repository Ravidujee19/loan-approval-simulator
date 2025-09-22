import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getLoan } from '../services/api.jsx'
import Badge from '../components/Badge.jsx'
import '../styles/loan-detail.css'

export default function LoanDetail(){
  const { id } = useParams()
  const navigate = useNavigate()
  const [loan, setLoan] = useState(null)
  const [loading, setLoading] = useState(true)
  const [err, setErr] = useState('')

  const num = new Intl.NumberFormat() // locale-aware formatting

  useEffect(() => {
    let ok = true
    setLoading(true); setErr('')
    getLoan(id)
      .then((data) => { if (ok) setLoan(data) })
      .catch((e) => { if (ok) setErr(e?.response?.data?.detail || 'Failed to load loan') })
      .finally(() => { if (ok) setLoading(false) })
    return () => { ok = false }
  }, [id])

  if (loading) {
    return (
      <div className="loanDetail-page">
        <div className="loanDetail-wrap">
          <div className="loanDetail-card loanDetail-skeleton">
            <div className="loanDetail-skel-line w-1/3" />
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="loanDetail-skel-line h-16" />
              <div className="loanDetail-skel-line h-16" />
              <div className="loanDetail-skel-line h-16" />
            </div>
            <div className="loanDetail-skel-line w-2/3" />
            <div className="loanDetail-skel-line w-full h-24" />
          </div>
        </div>
      </div>
    )
  }

  if (err) {
    return (
      <div className="loanDetail-page">
        <div className="loanDetail-wrap">
          <div className="loanDetail-card">
            <div className="loanDetail-error">{err}</div>
            <button className="loanDetail-btn" onClick={() => navigate(-1)}>← Back</button>
          </div>
        </div>
      </div>
    )
  }

  if (!loan) return null

  return (
    <div className="loanDetail-page">
      <div className="loanDetail-wrap">
        <div className="loanDetail-card">
          <div className="loanDetail-header">
            <h1 className="loanDetail-title">Loan {loan.loan_id}</h1>
            <div className="loanDetail-actions">
              <button className="loanDetail-btn" onClick={() => navigate(-1)}>← Back</button>
            </div>
          </div>

          <div className="loanDetail-meta">
            <div className="loanDetail-item">
              <div className="loanDetail-label">Amount</div>
              <div className="loanDetail-value">{num.format(loan.amount_requested)}</div>
            </div>
            <div className="loanDetail-item">
              <div className="loanDetail-label">Term</div>
              <div className="loanDetail-value">{loan.term_months} months</div>
            </div>
            <div className="loanDetail-item">
              <div className="loanDetail-label">Status</div>
              <div className="loanDetail-value">{loan.status}</div>
            </div>
          </div>

          {loan.evaluation && (
            <div className="loanDetail-section">
              <div className="mb-3">
                <Badge kind={loan.evaluation.eligibility}>
                  {loan.evaluation.eligibility ? 'Eligible' : 'Not eligible'}
                </Badge>
              </div>

              <div className="mb-2">
                <span className="loanDetail-label">Score</span>
                <div className="loanDetail-value">{loan.evaluation.score}</div>
              </div>

              {Array.isArray(loan.evaluation.reasons) ? (
                <ul className="loanDetail-list mt-2">
                  {loan.evaluation.reasons.map((r, i) => <li key={i}>{r}</li>)}
                </ul>
              ) : (
                <pre className="loanDetail-json mt-2">
                  {JSON.stringify(loan.evaluation.reasons, null, 2)}
                </pre>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}


// import { useEffect, useState } from 'react'
// import { useParams } from 'react-router-dom'
// import { getLoan } from '../services/api.jsx'
// import Badge from '../components/Badge.jsx'
// export default function LoanDetail(){
//   const { id } = useParams()
//   const [loan,setLoan]=useState(null)
//   useEffect(()=>{ getLoan(id).then(setLoan) },[id])
//   if(!loan) return null
//   return (
//     <div className="card">
//       <h1 className="text-xl mb-2">Loan {loan.loan_id}</h1>
//       <div className="space-y-1">
//         <div>Amount: {loan.amount_requested}</div>
//         <div>Term: {loan.term_months} months</div>
//         <div>Status: {loan.status}</div>
//       </div>
//       {loan.evaluation && (
//         <div className="mt-4">
//           <Badge kind={loan.evaluation.eligibility}>{loan.evaluation.eligibility}</Badge>
//           <div>Score: {loan.evaluation.score}</div>
//           <ul className="list-disc pl-6">
//             {loan.evaluation.reasons.map((r,i)=><li key={i}>{r}</li>)}
//           </ul>
//         </div>
//       )}
//     </div>
//   )
// }
