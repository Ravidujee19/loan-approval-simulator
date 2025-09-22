import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { createLoan } from "../services/api.jsx";
import "../styles/loan.css";

// Read applicantId from URL or fallback to localStorage
function useInitialApplicantId() {
  const location = useLocation();
  const params = new URLSearchParams(location.search);
  const fromQuery = params.get("applicantId") || "";
  const fallback = localStorage.getItem("last_applicant_id") || "";
  return fromQuery || fallback;
}

export default function LoanForm() {
  const navigate = useNavigate();
  const initialApplicantId = useInitialApplicantId();
  const [missingApplicant, setMissingApplicant] = useState(!initialApplicantId);

  const [payload, setPayload] = useState({
    applicant_id: initialApplicantId || "",
    amount_requested: 1000000,
    term_months: 36,
    loan_type: "personal",
    purpose: "education",
  });
  const [res, setRes] = useState(null);
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(e) {
    e.preventDefault();
    setErr("");
    setRes(null);
    setLoading(true);
    try {
      // ensure numeric types go out as numbers
      const body = {
        ...payload,
        amount_requested: Number(payload.amount_requested),
        term_months: Number(payload.term_months),
      };
      const r = await createLoan(body);
      setRes(r);
    } catch (e) {
      setErr(e?.response?.data?.detail || "Failed to submit loan");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="loan-page">
      <div className="loan-wrap">
        <div className="loan-card">
          <div className="flex items-center justify-between mb-1">
            <h1 className="text-2xl font-semibold">Submit Loan</h1>
            <button
              type="button"
              className="loan-btn px-3 py-2"
              onClick={() => navigate("/applicants/new?step=1")}
            >
              ← Back to Step 1
            </button>
          </div>
          <div className="mb-5 text-sm text-slate-300">Step 2 of 2 — Loan</div>

          {err && <div className="loan-error">{err}</div>}
          {missingApplicant && (
            <div className="loan-error">
              No applicant selected. Please go back to{" "}
              <button
                type="button"
                className="underline underline-offset-4"
                onClick={() => navigate("/applicants/new?step=1")}
              >
                Step 1
              </button>{" "}
              and create/select an applicant.
            </div>
          )}

          <form onSubmit={onSubmit} className="space-y-5">
            <div className="loan-grid">
              <label>
                <span className="loan-label">Applicant ID</span>
                <input
                  className="loan-control"
                  value={payload.applicant_id}
                  onChange={(e) =>
                    setPayload((p) => ({ ...p, applicant_id: e.target.value }))
                  }
                  placeholder="e.g. user-123"
                  required
                />
                <p className="loan-help mt-1">
                  Must match an existing applicant.
                </p>
              </label>

              <label>
                <span className="loan-label">Amount Requested</span>
                <input
                  className="loan-control"
                  type="number"
                  min="0"
                  step="1000"
                  value={payload.amount_requested}
                  onChange={(e) =>
                    setPayload((p) => ({
                      ...p,
                      amount_requested: e.target.value,
                    }))
                  }
                  placeholder="1000000"
                  required
                />
                <p className="loan-help mt-1">Use whole currency units.</p>
              </label>

              <label>
                <span className="loan-label">Term (months)</span>
                <input
                  className="loan-control"
                  type="number"
                  min="6"
                  max="360"
                  step="6"
                  value={payload.term_months}
                  onChange={(e) =>
                    setPayload((p) => ({ ...p, term_months: e.target.value }))
                  }
                  placeholder="36"
                  required
                />
              </label>

              <label>
                <span className="loan-label">Loan Type</span>
                <select
                  className="loan-control"
                  value={payload.loan_type}
                  onChange={(e) =>
                    setPayload((p) => ({ ...p, loan_type: e.target.value }))
                  }
                >
                  <option value="personal">Personal</option>
                  <option value="home">Home</option>
                  <option value="auto">Auto</option>
                  <option value="small_business">Small Business</option>
                </select>
              </label>
            </div>

            <label className="block">
              <span className="loan-label">Purpose</span>
              <select
                className="loan-control"
                value={payload.purpose}
                onChange={(e) =>
                  setPayload((p) => ({ ...p, purpose: e.target.value }))
                }
              >
                <option value="education">Education</option>
                <option value="medical">Medical</option>
                <option value="debt_consolidation">Debt consolidation</option>
                <option value="home_improvement">Home improvement</option>
                <option value="other">Other</option>
              </select>
            </label>

            <button
              className="loan-btn w-full"
              type="submit"
              disabled={loading || !payload.applicant_id}
            >
              {loading ? "Evaluating…" : "Evaluate"}
            </button>
          </form>

          {res && (
            <div className="loan-result">
              <div className="mb-2">
                Loan ID: <span className="text-slate-200">{res.loan_id}</span>
              </div>
              <div className="mb-2">
                Status:{" "}
                <span
                  className={`loan-badge ${
                    res.status === "approved"
                      ? "loan-badge-approved"
                      : "loan-badge-rejected"
                  }`}
                >
                  {res.status}
                </span>
              </div>

              {res.evaluation && (
                <div className="mt-3">
                  <div className="mb-1">
                    Eligibility:{" "}
                    <span className="text-slate-200">
                      {res.evaluation.eligibility ? "Eligible" : "Not eligible"}
                    </span>
                  </div>
                  <div className="mb-2">
                    Score:{" "}
                    <span className="text-slate-200">
                      {res.evaluation.score}
                    </span>
                  </div>
                  <pre className="loan-json">
                    {JSON.stringify(res.evaluation.reasons, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// import { useEffect, useState } from 'react'
// import { createLoan } from '../services/api.jsx'
// export default function LoanForm(){
//   const [payload,setPayload]=useState({
//     applicant_id:'', amount_requested:1000000, term_months:36, loan_type:'personal', purpose:'education'
//   })
//   const [res,setRes]=useState(null)
//   async function onSubmit(e){
//     e.preventDefault()
//     const r = await createLoan(payload)
//     setRes(r)
//   }
//   return (
//     <div className="card max-w-xl mx-auto">
//       <h1 className="text-xl font-semibold mb-4">Submit Loan</h1>
//       <form onSubmit={onSubmit} className="space-y-3">
//         {['applicant_id','amount_requested','term_months','loan_type','purpose'].map(k=>(
//           <input key={k} className="input" value={payload[k]} onChange={e=>setPayload({...payload,[k]:e.target.value})} placeholder={k}/>
//         ))}
//         <button className="btn w-full" type="submit">Evaluate</button>
//       </form>
//       {res && (
//         <div className="mt-4">
//           <div className="mb-2">Loan ID: {res.loan_id}</div>
//           <div className="mb-2">Status: {res.status}</div>
//           {res.evaluation && (
//             <div className="mt-2">
//               <div>Eligibility: {res.evaluation.eligibility}</div>
//               <div>Score: {res.evaluation.score}</div>
//               <pre className="text-xs">{JSON.stringify(res.evaluation.reasons,null,2)}</pre>
//             </div>
//           )}
//         </div>
//       )}
//     </div>
//   )
// }
