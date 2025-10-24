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
  const [prefillMeta, setPrefillMeta] = useState({
    confidence: {},
    provenance: {},
    fields: {},
  });
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
    if (!files?.length || !applicantId) return;
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
          <span
            className="small-badge"
            title={`Auto extracted (confidence ${(conf * 100).toFixed(0)}%)`}
          >
            auto {(conf * 100).toFixed(0)}%
          </span>
        )}
        {prov?.snippet && (
          <span
            className="prov"
            title={
              prov.snippet.length > 200
                ? prov.snippet.slice(0, 200) + "…"
                : prov.snippet
            }
          >
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

        {/* Removed Applicant/Loan ID display as requested */}

        <h2>Auto Prefill</h2>
        <div className="auto-prefill">
          <div style={{ marginBottom: 8 }}>
            <textarea
              id="prefillText"
              placeholder="Paste raw text here (application, payslip, bank statement...)"
              rows={5}
              style={{ width: "100%" }}
            />
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
          {/* loan_id kept in state but not displayed in result */}
          <div>
            <label>Loan ID</label>
            <input name="loan_id" value={form.loan_id} onChange={onChange} />
          </div>

          <div>
            <label>
              No. of Dependents <FieldMeta name="no_of_dependents" />
            </label>
            <input
              name="no_of_dependents"
              type="number"
              min="0"
              value={form.no_of_dependents}
              onChange={onChange}
            />
          </div>

          <div>
            <label>
              Education <FieldMeta name="education" />
            </label>
            <select name="education" value={form.education} onChange={onChange}>
              <option value="Graduate">Graduate</option>
              <option value="Not Graduate">Not Graduate</option>
            </select>
          </div>

          <div>
            <label>
              Self Employed <FieldMeta name="self_employed" />
            </label>
            <select
              name="self_employed"
              value={form.self_employed}
              onChange={onChange}
            >
              <option value="No">No</option>
              <option value="Yes">Yes</option>
            </select>
          </div>

          <div>
            <label>
              Annual Income (LKR) <FieldMeta name="income_annum" />
            </label>
            <input
              name="income_annum"
              type="number"
              min="0"
              value={form.income_annum}
              onChange={onChange}
            />
          </div>

          <div>
            <label>
              Requested Loan Amount (LKR) <FieldMeta name="loan_amount" />
            </label>
            <input
              name="loan_amount"
              type="number"
              min="0"
              value={form.loan_amount}
              onChange={onChange}
            />
          </div>

          <div>
            <label>
              Loan Term (years) <FieldMeta name="loan_term" />
            </label>
            <input
              name="loan_term"
              type="number"
              min="2"
              max="20"
              value={form.loan_term}
              onChange={onChange}
            />
          </div>

          <div>
            <label>
              CIBIL Score <FieldMeta name="cibil_score" />
            </label>
            <input
              name="cibil_score"
              type="number"
              min="300"
              max="900"
              value={form.cibil_score}
              onChange={onChange}
            />
          </div>

          <div>
            <label>
              Residential Assets <FieldMeta name="residential_assets_value" />
            </label>
            <input
              name="residential_assets_value"
              type="number"
              min="0"
              value={form.residential_assets_value}
              onChange={onChange}
            />
          </div>

          <div>
            <label>
              Commercial Assets <FieldMeta name="commercial_assets_value" />
            </label>
            <input
              name="commercial_assets_value"
              type="number"
              min="0"
              value={form.commercial_assets_value}
              onChange={onChange}
            />
          </div>

          <div>
            <label>
              Luxury Assets <FieldMeta name="luxury_assets_value" />
            </label>
            <input
              name="luxury_assets_value"
              type="number"
              min="0"
              value={form.luxury_assets_value}
              onChange={onChange}
            />
          </div>

          <div>
            <label>
              Bank Assets <FieldMeta name="bank_asset_value" />
            </label>
            <input
              name="bank_asset_value"
              type="number"
              min="0"
              value={form.bank_asset_value}
              onChange={onChange}
            />
          </div>
        </div>

        <div className="actions">
          <button disabled={!canSubmit} onClick={handleEvaluate}>
            Evaluate
          </button>

          {/* Optional: document upload control (kept functional) */}
          <div style={{ marginLeft: 12 }}>
            <input
              type="file"
              multiple
              onChange={(e) => setFiles(Array.from(e.target.files || []))}
              disabled={!applicantId || busy}
            />
            <button onClick={handleUpload} disabled={!files.length || !applicantId || busy}>
              Upload Docs
            </button>
          </div>
        </div>
      </div>

      {result && <ResultTabs result={result} formSnapshot={form} />}
    </div>
  );
}

/* ===================== Result Views ===================== */

function ResultTabs({ result, formSnapshot }) {
  const [tab, setTab] = useState("summary"); // "summary" | "llm"

  return (
    <div className="card" style={{ marginTop: 16 }}>
      <div className="tabs">
        <button
          className={`tab ${tab === "summary" ? "active" : ""}`}
          onClick={() => setTab("summary")}
        >
          Summary
        </button>
        <button
          className={`tab ${tab === "llm" ? "active" : ""}`}
          onClick={() => setTab("llm")}
        >
          LLM Explanation
        </button>
      </div>

      {tab === "summary" ? (
        <SummaryPage result={result} formSnapshot={formSnapshot} />
      ) : (
        <LLMPage result={result} />
      )}
    </div>
  );
}

function SummaryPage({ result, formSnapshot }) {
  // Whitelist of “feature” fields to show (from your form/backend top-level)
  const FEATURE_KEYS = [
    "no_of_dependents",
    "education",
    "self_employed",
    "income_annum",
    "loan_amount",
    "loan_term",
    "cibil_score",
    "residential_assets_value",
    "commercial_assets_value",
    "luxury_assets_value",
    "bank_asset_value",
  ];

  // Prefer values returned in result; fall back to the form snapshot
  const features = FEATURE_KEYS.map((k) => ({
    key: k,
    value:
      result?.[k] !== undefined && result?.[k] !== null
        ? result[k]
        : formSnapshot?.[k],
  }));

  // Recommendation payload (hide cluster)
  const reco = result?.recommendation || {};
  const risk = reco?.risk_level ?? "—";
  const actions = Array.isArray(reco?.recommendations) ? reco.recommendations : [];

  return (
    <div>
      <h2>Based on your details, here's how we currently assess your loan request and what you should do next.
</h2>

      <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 12 }}>
        <Badge tone={riskTone(risk)}>{`Risk Level: ${risk}`}</Badge>
      </div>

      <section style={{ marginBottom: 16 }}>
        <h3>Your Informations</h3>
        <div className="grid-table">
          {features.map(({ key, value }) => (
            <div key={key} className="row">
              <div className="cell label">{labelize(key)}</div>
              <div className="cell value">{formatValue(key, value)}</div>
            </div>
          ))}
        </div>
      </section>

      <section>
        <h3>Recommendations</h3>
        {actions.length ? (
          <ul className="reco-list">
            {actions.map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
        ) : (
          <em>No recommendations provided.</em>
        )}
      </section>
    </div>
  );
}

function LLMPage({ result }) {
  const text = result?.llm_explanation;
  return (
    <div>
      <h2>Here’s a detailed explanation of the factors that influenced your loan decision.
</h2>
      {text ? <div className="llm-box">{text}</div> : <em>No LLM explanation available.</em>}
    </div>
  );
}

/* ---------- Small UI atoms & helpers ---------- */

function Badge({ children, tone = "neutral" }) {
  return <span className={`badge tone-${tone}`}>{children}</span>;
}

function riskTone(risk) {
  const r = String(risk || "").toLowerCase();
  if (r.includes("high")) return "danger";
  if (r.includes("medium")) return "warn";
  if (r.includes("low")) return "ok";
  return "neutral";
}

function labelize(key) {
  // turn snake_case into "Title Case"
  return key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatValue(key, v) {
  if (v === null || v === undefined || v === "") return "—";
  // currency-ish numbers
  const moneyKeys = [
    "income_annum",
    "loan_amount",
    "residential_assets_value",
    "commercial_assets_value",
    "luxury_assets_value",
    "bank_asset_value",
  ];
  if (moneyKeys.includes(key) && !isNaN(Number(v))) {
    return `LKR ${Number(v).toLocaleString()}`;
  }
  // generic number (except CIBIL which we keep raw range 300–900)
  if (!isNaN(Number(v)) && key !== "cibil_score") {
    return Number(v).toLocaleString();
  }
  return String(v);
}
