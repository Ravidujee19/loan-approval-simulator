import { useEffect, useMemo, useState } from "react";
import {
  createApplicant,
  uploadDocs,
  evaluateWithForm,
  prefillFromText,
  prefillFromPdf,
} from "./services/api";
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

  // meta returned by prefill: confidences & provenance
  const [prefillMeta, setPrefillMeta] = useState({ confidence: {}, provenance: {}, fields: {} });
  const [log, setLog] = useState("");

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
    // if user edits a previously auto-filled field, drop its auto flag
    setPrefillMeta((m) => {
      if (m.fields && m.fields[name]) {
        const newFields = { ...m.fields };
        delete newFields[name];
        const newConf = { ...m.confidence };
        delete newConf[name];
        const newProv = { ...m.provenance };
        delete newProv[name];
        return { ...m, fields: newFields, confidence: newConf, provenance: newProv };
      }
      return m;
    });
  };

  const handleUpload = async () => {
    if (!files?.length) return;
    setBusy(true);
    try {
      await uploadDocs(applicantId, files);
      alert("Documents uploaded");
    } catch (err) {
      console.error(err);
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
        loan_term: Number(form.loan_term || 0), // YEARS
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

  // Auto-prefill handlers
  const handlePrefillFromText = async (text) => {
    if (!text || !applicantId) return;
    setBusy(true);
    setLog("Extracting from text...");
    try {
      const res = await prefillFromText(applicantId, text);
      applyPrefillResult(res);
      setLog("Prefill applied — please verify fields.");
    } catch (err) {
      console.error(err);
      setLog("Prefill failed: " + (err?.response?.data?.detail || err?.message));
    } finally {
      setBusy(false);
    }
  };

  const handlePrefillFromPdf = async (file) => {
    if (!file || !applicantId) return;
    setBusy(true);
    setLog("Uploading PDF and extracting...");
    try {
      const res = await prefillFromPdf(applicantId, file);
      applyPrefillResult(res);
      setLog("PDF prefill applied — check values.");
    } catch (err) {
      console.error(err);
      setLog("PDF prefill failed: " + (err?.response?.data?.detail || err?.message));
    } finally {
      setBusy(false);
    }
  };

  // merge text + PDF prefill with confidence 
  const applyPrefillResult = (res) => {
    if (!res) return;
    const fields = res.fields || {};
    const conf = res.confidence || {};
    const provArr = res.provenance || [];

    // merge into form based on confidence
    setForm((s) => {
      const mergedFields = { ...s };
      for (const key in fields) {
        const prevConf = prefillMeta.confidence?.[key] ?? 0;
        const newConfVal = conf[key] ?? 0;
        if (!mergedFields[key] || newConfVal >= prevConf) {
          mergedFields[key] = fields[key];
        }
      }
      return mergedFields;
    });

    // merge confidence and provenance
    setPrefillMeta((prev) => {
      const mergedConf = { ...prev.confidence };
      const mergedProv = { ...prev.provenance };
      const mergedFields = { ...prev.fields };

      for (const key in fields) {
        const prevC = mergedConf[key] ?? 0;
        const newC = conf[key] ?? 0;

        // update field if new confidence is higher
        if (!mergedFields[key] || newC >= prevC) {
          mergedFields[key] = fields[key];
          mergedConf[key] = newC;
        }

        // update provenance if confidence is higher
        const provItem = provArr.find((p) => p.field === key);
        if (provItem && newC >= prevC) {
          mergedProv[key] = provItem;
        }
      }

      return { confidence: mergedConf, provenance: mergedProv, fields: mergedFields };
    });
  };

  // small helper to render confidence/provenance next to fields
  const FieldMeta = ({ name }) => {
    const conf = prefillMeta.confidence?.[name];
    const prov = prefillMeta.provenance?.[name];
    if (!conf && !prov) return null;
    return (
      <div style={{ display: "inline-block", marginLeft: 8 }}>
        {conf != null && (
          <span className="small-badge" title={`Auto extracted (confidence ${(conf * 100).toFixed(0)}%)`}>
            auto {(conf * 100).toFixed(0)}%
          </span>
        )}
        {prov?.snippet && (
          <span className="prov" title={prov.snippet.length > 200 ? prov.snippet.slice(0, 200) + "…" : prov.snippet}>
            ⓘ
          </span>
        )}
      </div>
    );
  };

  return (
    <div className="container">
      <div className="card">
        <h1>Loan Approval Simulator</h1>

        <div style={{ marginBottom: 10 }}>
          <span className="badge">
            {applicantId ? `Applicant: ${applicantId.slice(0, 8)}…` : "Creating…"}
          </span>
        </div>

        <h2>Auto Prefill</h2>
        <div className="auto-prefill">
          <div style={{ marginBottom: 8 }}>
            <textarea id="prefillText" placeholder="Paste raw text here (application, payslip, bank statement...)" rows={5} style={{ width: "100%" }} />
            <div style={{ marginTop: 6 }}>
              <button
                onClick={() => {
                  const t = document.getElementById("prefillText").value;
                  handlePrefillFromText(t);
                }}
                disabled={!applicantId || busy}
              >
                Prefill from text
              </button>
            </div>
          </div>

          <div style={{ marginTop: 8 }}>
            <label>
              Upload PDF (digital or scanned):
              <input
                type="file"
                accept="application/pdf"
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) handlePrefillFromPdf(f);
                }}
                disabled={!applicantId || busy}
              />
            </label>
          </div>

          <div style={{ marginTop: 8 }}>
            <em>{log}</em>
          </div>
        </div>

        <h2>Enter Your Details</h2>
        <div className="row">
          <div>
            <label>Loan ID</label>
            <input name="loan_id" value={form.loan_id} onChange={onChange} />
          </div>

          <div>
            <label>No. of Dependents <FieldMeta name="no_of_dependents" /></label>
            <input name="no_of_dependents" type="number" min="0" value={form.no_of_dependents} onChange={onChange} />
          </div>

          <div>
            <label>Education <FieldMeta name="education" /></label>
            <select name="education" value={form.education} onChange={onChange}>
              <option value="Graduate">Graduate</option>
              <option value="Not Graduate">Not Graduate</option>
            </select>
          </div>

          <div>
            <label>Self Employed <FieldMeta name="self_employed" /></label>
            <select name="self_employed" value={form.self_employed} onChange={onChange}>
              <option value="No">No</option>
              <option value="Yes">Yes</option>
            </select>
          </div>

          <div>
            <label>Annual Income (LKR) <FieldMeta name="income_annum" /></label>
            <input name="income_annum" type="number" min="0" value={form.income_annum} onChange={onChange} />
          </div>

          <div>
            <label>Requested Loan Amount (LKR) <FieldMeta name="loan_amount" /></label>
            <input name="loan_amount" type="number" min="0" value={form.loan_amount} onChange={onChange} />
          </div>

          <div>
            <label>Loan Term (years) <FieldMeta name="loan_term" /></label>
            <input name="loan_term" type="number" min="2" max="20" value={form.loan_term} onChange={onChange} />
          </div>

          <div>
            <label>CIBIL Score <FieldMeta name="cibil_score" /></label>
            <input name="cibil_score" type="number" min="300" max="900" value={form.cibil_score} onChange={onChange} />
          </div>

          <div>
            <label>Residential Assets <FieldMeta name="residential_assets_value" /></label>
            <input name="residential_assets_value" type="number" min="0" value={form.residential_assets_value} onChange={onChange} />
          </div>

          <div>
            <label>Commercial Assets <FieldMeta name="commercial_assets_value" /></label>
            <input name="commercial_assets_value" type="number" min="0" value={form.commercial_assets_value} onChange={onChange} />
          </div>

          <div>
            <label>Luxury Assets <FieldMeta name="luxury_assets_value" /></label>
            <input name="luxury_assets_value" type="number" min="0" value={form.luxury_assets_value} onChange={onChange} />
          </div>

          <div>
            <label>Bank Assets <FieldMeta name="bank_asset_value" /></label>
            <input name="bank_asset_value" type="number" min="0" value={form.bank_asset_value} onChange={onChange} />
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
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 8 }}>
            <span className={`badge ${result?.consistency?.hard_stops?.length ? "stop" : "ok"}`}>
              {result?.consistency?.hard_stops?.length ? "Hard stops present" : "No hard stops"}
            </span>
          </div>
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

//