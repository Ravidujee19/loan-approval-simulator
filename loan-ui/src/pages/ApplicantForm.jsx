import React, { useState } from "react";
import { useAuth } from "../AuthContext.jsx";
import { evaluate } from "../api";

const init = {
  name: "A. Silva",
  age: 26,
  income: 150000,
  expenses: 60000,
  loan_amount: 800000,
  tenure_months: 36,
  employment_type: "FULL_TIME",
  past_defaults: 0,
  card_utilization: 0.32,
  inquiries_last6m: 1,
  interest_rate_annual: 18,
};

export default function ApplicantForm() {
  const { logout } = useAuth();
  const [f, setF] = useState(init);
  const [out, setOut] = useState(null);
  const [err, setErr] = useState("");

  const upd = (k, v) => setF((s) => ({ ...s, [k]: v }));

  const submit = async (e) => {
    e.preventDefault();
    setErr(""); setOut(null);
    try {
      const res = await evaluate(f);
      setOut(res);
    } catch (e) {
      setErr(e?.response?.data?.detail || "Error contacting API");
    }
  };

  return (
    <div className="container py-4">
      <div className="d-flex align-items-center justify-content-between mb-3">
        <h3 className="mb-0">Loan Applicant Evaluator</h3>
        <button className="btn btn-outline-secondary" onClick={logout}>Logout</button>
      </div>

      <form onSubmit={submit} className="row g-3">
        {[
          ["name","text"],["age","number"],["income","number"],["expenses","number"],
          ["loan_amount","number"],["tenure_months","number"],
          ["past_defaults","number"],["card_utilization","number"],
          ["inquiries_last6m","number"],["interest_rate_annual","number"]
        ].map(([k,type])=>(
          <div className="col-md-4" key={k}>
            <label className="form-label">{k}</label>
            <input
              type={type}
              className="form-control"
              value={f[k]}
              onChange={(e)=>upd(k, type==="text"? e.target.value : Number(e.target.value))}
            />
          </div>
        ))}

        <div className="col-md-4">
          <label className="form-label">employment_type</label>
          <select className="form-select" value={f.employment_type} onChange={(e)=>upd("employment_type", e.target.value)}>
            {["FULL_TIME","PART_TIME","SELF_EMPLOYED","GOVERNMENT","STUDENT","RETIRED"].map(x=><option key={x} value={x}>{x}</option>)}
          </select>
        </div>

        <div className="col-12">
          <button className="btn btn-primary">Evaluate</button>
        </div>
      </form>

      {err && <div className="alert alert-danger mt-3">{err}</div>}

      {out && (
        <div className="card mt-3">
          <div className="card-body">
            {out.valid ? (
              <>
                <h5 className="card-title mb-2">Result: {out.band} ({out.score})</h5>
                <p className="mb-2">
                  <strong>EMI:</strong> {out.features.emi} &nbsp;|&nbsp;
                  <strong>DTI:</strong> {out.features.dti} &nbsp;|&nbsp;
                  <strong>Burden:</strong> {out.features.burden}
                </p>
                <p className="mb-0">
                  <strong>Factors:</strong> {Array.isArray(out.factors) ? out.factors.join(", ") : "—"}
                </p>
              </>
            ) : (
              <div className="alert alert-warning mb-0">{out.message}</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
