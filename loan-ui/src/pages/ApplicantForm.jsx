import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { createApplicant } from "../services/api.jsx";
import "../styles/applicant.css";

export default function ApplicantForm() {
  const navigate = useNavigate();
  const [data, setData] = useState({
    first_name: "Ravi",
    last_name: "Perera",
    email: "user1@example.com",
    phone: "+94",
    dob: "1996-01-02",
    employment_status: "employed",
    employer_name: "Tech",
    monthly_income: 120000,
    other_income: 0,
    existing_monthly_debt: 10000,
  });
  const [res, setRes] = useState(null);
  const [err, setErr] = useState("");
  const [ok, setOk] = useState("");
  const [loading, setLoading] = useState(false);

  function onChange(k, v) {
    setData((p) => ({ ...p, [k]: v }));
  }

  async function onSubmit(e) {
    e.preventDefault();
    setErr("");
    setOk("");
    setRes(null);
    setLoading(true);
    try {
      // cast numeric fields
      const body = {
        ...data,
        monthly_income: Number(data.monthly_income),
        other_income: Number(data.other_income),
        existing_monthly_debt: Number(data.existing_monthly_debt),
      };
      const r = await createApplicant(body);
      setRes(r);
      if (r?.id) {
        localStorage.setItem("last_applicant_id", String(r.id));
      }
      setOk(`Applicant created successfully. ID: ${r?.id ?? "—"}`);
    } catch (e) {
      setErr(e?.response?.data?.detail || "Failed to create applicant");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="applicant-page">
      <div className="applicant-wrap">
        <div className="applicant-card">
          <h1 className="text-2xl font-semibold mb-1">Create Applicant</h1>
          <div className="mb-5 text-sm text-slate-300">
            Step 1 of 2 — Applicant
          </div>

          {err && <div className="applicant-error">{err}</div>}
          {ok && <div className="applicant-ok">{ok}</div>}

          <form onSubmit={onSubmit} className="space-y-5">
            <div className="applicant-grid">
              <label>
                <span className="applicant-label">First name</span>
                <input
                  className="applicant-control"
                  value={data.first_name}
                  onChange={(e) => onChange("first_name", e.target.value)}
                  placeholder="First name"
                  required
                />
              </label>

              <label>
                <span className="applicant-label">Last name</span>
                <input
                  className="applicant-control"
                  value={data.last_name}
                  onChange={(e) => onChange("last_name", e.target.value)}
                  placeholder="Last name"
                  required
                />
              </label>

              <label>
                <span className="applicant-label">Email</span>
                <input
                  type="email"
                  className="applicant-control"
                  value={data.email}
                  onChange={(e) => onChange("email", e.target.value)}
                  placeholder="name@example.com"
                  required
                />
              </label>

              <label>
                <span className="applicant-label">Phone</span>
                <input
                  type="tel"
                  className="applicant-control"
                  value={data.phone}
                  onChange={(e) => onChange("phone", e.target.value)}
                  placeholder="+94xxxxxxxxx"
                />
                <p className="applicant-help mt-1">Include country code.</p>
              </label>

              <label>
                <span className="applicant-label">Date of birth</span>
                <input
                  type="date"
                  className="applicant-control"
                  value={data.dob}
                  onChange={(e) => onChange("dob", e.target.value)}
                  required
                />
              </label>

              <label>
                <span className="applicant-label">Employment status</span>
                <select
                  className="applicant-control"
                  value={data.employment_status}
                  onChange={(e) =>
                    onChange("employment_status", e.target.value)
                  }
                >
                  <option value="employed">Employed</option>
                  <option value="self_employed">Self-employed</option>
                  <option value="student">Student</option>
                  <option value="unemployed">Unemployed</option>
                  <option value="retired">Retired</option>
                </select>
              </label>

              <label className="sm:col-span-2">
                <span className="applicant-label">Employer name</span>
                <input
                  className="applicant-control"
                  value={data.employer_name}
                  onChange={(e) => onChange("employer_name", e.target.value)}
                  placeholder="Company"
                />
              </label>

              <label>
                <span className="applicant-label">Monthly income</span>
                <input
                  type="number"
                  min="0"
                  step="1000"
                  className="applicant-control"
                  value={data.monthly_income}
                  onChange={(e) => onChange("monthly_income", e.target.value)}
                  placeholder="120000"
                  required
                />
              </label>

              <label>
                <span className="applicant-label">Other income</span>
                <input
                  type="number"
                  min="0"
                  step="1000"
                  className="applicant-control"
                  value={data.other_income}
                  onChange={(e) => onChange("other_income", e.target.value)}
                  placeholder="0"
                />
              </label>

              <label className="sm:col-span-2">
                <span className="applicant-label">Existing monthly debt</span>
                <input
                  type="number"
                  min="0"
                  step="500"
                  className="applicant-control"
                  value={data.existing_monthly_debt}
                  onChange={(e) =>
                    onChange("existing_monthly_debt", e.target.value)
                  }
                  placeholder="10000"
                />
              </label>
            </div>

            <button
              className="applicant-btn w-full"
              type="submit"
              disabled={loading}
            >
              {loading ? "Saving…" : "Save"}
            </button>
          </form>

          {res?.id && (
            <div className="mt-3">
              <button
                type="button"
                className="applicant-btn w-full"
                onClick={() =>
                  navigate(`/loans/new?step=2&applicantId=${res.id}`)
                }
              >
                Next: Create Loan
              </button>
            </div>
          )}

          {res && (
            <pre className="applicant-json">{JSON.stringify(res, null, 2)}</pre>
          )}
        </div>
      </div>
    </div>
  );
}

// import { useState } from 'react'
// import { createApplicant } from '../services/api.jsx'
// export default function ApplicantForm(){
//   const [data,setData]=useState({
//     first_name:'Ravi', last_name:'Perera', email:'user1@example.com', phone:'+94',
//     dob:'1996-01-02', employment_status:'employed', employer_name:'Tech',
//     monthly_income:120000, other_income:0, existing_monthly_debt:10000
//   })
//   const [res,setRes]=useState(null)
//   async function onSubmit(e){
//     e.preventDefault()
//     const r = await createApplicant(data)
//     setRes(r)
//   }
//   return (
//     <div className="card max-w-2xl mx-auto">
//       <h1 className="text-xl font-semibold mb-4">Create Applicant</h1>
//       <form onSubmit={onSubmit} className="grid grid-cols-2 gap-3">
//         {Object.keys(data).map(k=>(
//           <input key={k} className="input" value={data[k]} onChange={e=>setData({...data,[k]:e.target.value})} placeholder={k}/>
//         ))}
//         <button className="btn col-span-2" type="submit">Save</button>
//       </form>
//       {res && <pre className="mt-4 text-xs">{JSON.stringify(res,null,2)}</pre>}
//     </div>
//   )
// }
