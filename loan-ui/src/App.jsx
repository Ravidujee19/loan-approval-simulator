import { useEffect, useMemo, useState } from "react";
import { createApplicant, uploadDocs, evaluateWithForm } from "./api";
import "./styles.css";

export default function App() {
  const [applicantId, setApplicantId] = useState(null);
  const [files, setFiles] = useState([]);
  const [form, setForm] = useState({
    loan_id: crypto.randomUUID(),
    no_of_dependents: 2,
    education: "Not Graduate",
    self_employed: "Yes",
    income_annum: 900000,
    loan_amount: 2000000,
    loan_term: 5,
    cibil_score: 420,
    residential_assets_value: 200000,
    commercial_assets_value: 0,
    luxury_assets_value: 0,
    bank_asset_value: 50000,
  });
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);

  useEffect(() => {
    (async () => {
      const id = await createApplicant();
      setApplicantId(id);
    })();
  }, []);

  const canSubmit = useMemo(() => !!applicantId && !busy, [applicantId, busy]);

  const onChange = (e) => {
    const { name, value, type, checked } = e.target;
    setForm((s) => ({ ...s, [name]: type === "checkbox" ? checked : value }));
  };

  const handleUpload = async () => {
    if (!files?.length) return;
    setBusy(true);
    try {
      await uploadDocs(applicantId, files);
      alert("Documents uploaded");
    } catch {
      alert("Upload failed");
    } finally {
      setBusy(false);
    }
  };

  const handleEvaluate = async () => {
    setBusy(true);
    try { 
      const payload = {
        ...form,
        no_of_dependents: Number(form.no_of_dependents || 0),
        income_annum: Number(form.income_annum || 0),
        loan_amount: Number(form.loan_amount || 0),
        loan_term: Number(form.loan_term || 0),  // YEARS
        cibil_score: Number(form.cibil_score || 0),
        residential_assets_value: Number(form.residential_assets_value || 0),
        commercial_assets_value: Number(form.commercial_assets_value || 0),
        luxury_assets_value: Number(form.luxury_assets_value || 0),
        bank_asset_value: Number(form.bank_asset_value || 0),
      };
      const data = await evaluateWithForm(applicantId, payload);
      setResult(data);
    } catch (e) {
      console.error(e);
      alert("Evaluate failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="container">
      <div className="card">
        <h1>Loan Approval Simulator</h1>
        {/* <div style={{ marginBottom: 10 }}>
          <span className="badge">
            {applicantId ? `Applicant: ${applicantId.slice(0, 8)}…` : "Creating…"}
          </span>
        </div>

        <h2>Documents</h2>
        <input type="file" multiple onChange={(e) => setFiles(Array.from(e.target.files || []))} />
        <div className="actions">
          <button disabled={!canSubmit || !files.length} onClick={handleUpload}>Upload Docs</button>
          <button className="secondary" onClick={() => setFiles([])}>Clear</button>
        </div> */}

        <h2>Enter Your Details</h2>
        <div className="row">
          <div>
            <label>Loan ID</label>
            <input name="loan_id" value={form.loan_id} onChange={onChange} />
          </div>
          <div>
            <label>No. of Dependents</label>
            <input name="no_of_dependents" type="number" min="0" value={form.no_of_dependents} onChange={onChange}/>
          </div>
          <div>
            <label>Education</label>
            <select name="education" value={form.education} onChange={onChange}>
              <option value="Graduate">Graduate</option>
              <option value="Not Graduate">Not Graduate</option>
            </select>
          </div>
          <div>
            <label>Self Employed</label>
            <select name="self_employed" value={form.self_employed} onChange={onChange}>
              <option value="No">No</option>
              <option value="Yes">Yes</option>
            </select>
          </div>
          <div>
            <label>Annual Income (LKR)</label>
            <input name="income_annum" type="number" min="0" value={form.income_annum} onChange={onChange}/>
          </div>
          <div>
            <label>Requested Loan Amount (LKR)</label>
            <input name="loan_amount" type="number" min="0" value={form.loan_amount} onChange={onChange}/>
          </div>
          <div>
            <label>Loan Term (years)</label>
            <input name="loan_term" type="number" min="2" max="20" value={form.loan_term} onChange={onChange}/>
          </div>
          <div>
            <label>CIBIL Score</label>
            <input name="cibil_score" type="number" min="300" max="900" value={form.cibil_score} onChange={onChange}/>
          </div>
          <div>
            <label>Residential Assets</label>
            <input name="residential_assets_value" type="number" min="0" value={form.residential_assets_value} onChange={onChange}/>
          </div>
          <div>
            <label>Commercial Assets</label>
            <input name="commercial_assets_value" type="number" min="0" value={form.commercial_assets_value} onChange={onChange}/>
          </div>
          <div>
            <label>Luxury Assets</label>
            <input name="luxury_assets_value" type="number" min="0" value={form.luxury_assets_value} onChange={onChange}/>
          </div>
          <div>
            <label>Bank Assets</label>
            <input name="bank_asset_value" type="number" min="0" value={form.bank_asset_value} onChange={onChange}/>
          </div>
        </div>

        <div className="actions">
          <button disabled={!canSubmit} onClick={handleEvaluate}>
            Evaluate
          </button>
        </div>
      </div>

      {result && (
        <div className="card" style={{ marginTop: 16 }}>
          <h2>Result</h2>
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 8 }}>
            <span className={`badge ${result?.consistency?.hard_stops?.length ? 'stop' : 'ok'}`}>
              {result?.consistency?.hard_stops?.length ? 'Hard stops present' : 'No hard stops'}
            </span>
            {/* <span className="badge">
              Confidence: {(result?.quality?.overall_confidence ?? 0).toFixed(2)}
            </span> */}
          </div>
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
