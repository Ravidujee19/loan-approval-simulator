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
        return {
          ...m,
          fields: newFields,
          confidence: newConf,
          provenance: newProv,
        };
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

      return {
        confidence: mergedConf,
        provenance: mergedProv,
        fields: mergedFields,
      };
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
          {/* loan_id stays in state (not shown in result) */}

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

          {/* <div style={{ marginLeft: 12 }}>
            <input
              type="file"
              multiple
              onChange={(e) => setFiles(Array.from(e.target.files || []))}
              disabled={!applicantId || busy}
            />
           
          </div> */}
        </div>
      </div>
      
      {busy && (
  <div className="thinking-box">
    <div className="spinner"></div>
    <p>🤔 Thinking... analyzing your loan request</p>
  </div>
)}


      {result && <ResultTabs result={result} formSnapshot={form} />}
    </div>
  );
}

/* ===================== Result Views ===================== */

function ResultTabs({ result, formSnapshot }) {
  // tabs: summary, explanation, impact
  const [tab, setTab] = useState("summary"); // "summary" | "llm" | "impact"

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
          Explanation
        </button>
        <button
          className={`tab ${tab === "impact" ? "active" : ""}`}
          onClick={() => setTab("impact")}
        >
          Impact
        </button>
      </div>

      {tab === "summary" ? (
        <SummaryPage result={result} formSnapshot={formSnapshot} />
      ) : tab === "llm" ? (
        <LLMPage result={result} />
      ) : (
        <ShapPage result={result} />
      )}
    </div>
  );
}

/* ---------------- Summary Page ---------------- */

function SummaryPage({ result, formSnapshot }) {
  // Which fields to show
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

  // Prefer backend value, otherwise use form value
  const features = FEATURE_KEYS.map((k) => ({
    key: k,
    value:
      result?.[k] !== undefined && result?.[k] !== null
        ? result[k]
        : formSnapshot?.[k],
  }));

  // Recommendation info
  const reco = result?.recommendation || {};
  const risk = reco?.risk_level ?? "—";
  const actions = Array.isArray(reco?.recommendations)
    ? reco.recommendations
    : [];

  // Decision + score from model (handle both nesting styles)
  const prediction =
    result?.inference?.prediction ?? result?.prediction ?? null;
  const scoreOutOf100 =
    result?.inference?.score ?? result?.score ?? null;

  return (
    <div>
      <h2>
        Based on your details, here's how we currently assess your loan request
        and what you should do next.
      </h2>

      {/* Top badges: risk and approval decision */}
      <div
        style={{
          display: "flex",
          gap: 12,
          flexWrap: "wrap",
          marginBottom: 16,
        }}
      >
        <Badge tone={riskTone(risk)}>{`Risk Level: ${risk}`}</Badge>
        <DecisionPill prediction={prediction} />
      </div>

      {/* Info + side status card */}
      <section style={{ marginBottom: 20 }}>
        <h3>Your Information</h3>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "minmax(0,1fr) 220px",
            gap: "16px",
            alignItems: "start",
          }}
        >
          {/* left column: table of applicant features */}
          <div className="grid-table">
            {features.map(({ key, value }) => (
              <div key={key} className="row">
                <div className="cell label">{labelize(key)}</div>
                <div className="cell value">{formatValue(key, value)}</div>
              </div>
            ))}
          </div>

          {/* right column: decision / score card */}
          <div
            style={{
              background: "rgba(15,23,42,0.6)",
              border: "1px solid rgba(148,163,184,0.4)",
              borderRadius: "14px",
              padding: "16px",
              boxShadow:
                "0 24px 60px rgba(0,0,0,0.9),0 0 30px rgba(56,189,248,0.3),0 0 80px rgba(99,102,241,0.3)",
              minHeight: "140px",
              display: "flex",
              flexDirection: "column",
              justifyContent: "space-between",
            }}
          >
            <div style={{ marginBottom: "12px" }}>
              <div
                style={{
                  fontSize: "0.8rem",
                  fontWeight: 500,
                  color: "#94a3b8",
                  marginBottom: "4px",
                  textShadow:
                    "0 0 8px rgba(16,185,129,0.4), 0 0 24px rgba(99,102,241,0.4)",
                }}
              >
                Decision
              </div>
              <DecisionPill prediction={prediction} />
            </div>

            <div>
              <div
                style={{
                  fontSize: "0.8rem",
                  fontWeight: 500,
                  color: "#94a3b8",
                  marginBottom: "4px",
                  textShadow:
                    "0 0 8px rgba(56,189,248,0.4), 0 0 24px rgba(99,102,241,0.4)",
                }}
              >
                Confidence Score
              </div>
              <div
                style={{
                  fontSize: "1rem",
                  fontWeight: 600,
                  color: "#fff",
                  textShadow:
                    "0 0 10px rgba(255,255,255,0.6), 0 0 30px rgba(16,185,129,0.6), 0 0 60px rgba(99,102,241,0.4)",
                }}
              >
                {scoreOutOf100 != null
                  ? `${Number(scoreOutOf100).toFixed(2)} / 100`
                  : "—"}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Recommendations */}
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

/* ---------------- Explanation Page ---------------- */

function LLMPage({ result }) {
  const text = result?.llm_explanation;
  return (
    <div>
      <h2>
        Here’s a detailed explanation of the factors that influenced your loan
        decision.
      </h2>
      {text ? (
        <div className="llm-box">{text}</div>
      ) : (
        <em>No explanation available.</em>
      )}
    </div>
  );
}

/* ---------------- Impact / SHAP Page ---------------- */

function ShapPage({ result }) {
  // We try inference.shap_values first; fallback to shap_values at root.
  const shapObj =
    result?.inference?.shap_values ||
    result?.shap_values ||
    {};

  // convert dict {feature: value} -> sorted array
  const shapData = Object.entries(shapObj)
    .map(([feature, value]) => ({
      feature,
      value: Number(value || 0),
    }))
    .sort((a, b) => Math.abs(b.value) - Math.abs(a.value))
    .slice(0, 8); // show top 8

  return (
    <div>
      <h2>
        These factors had the biggest positive or negative impact on your loan
        assessment.
      </h2>

      {shapData.length === 0 ? (
        <em>No impact data available.</em>
      ) : (
        <div style={{ marginTop: 16 }}>
          <ShapBarChart data={shapData} />
          <div
            style={{
              fontSize: "0.8rem",
              color: "#9ca3af",
              marginTop: 8,
            }}
          >
            Green bars helped approval. Red bars made approval harder.
          </div>
        </div>
      )}
    </div>
  );
}

/* SVG SHAP chart */
function ShapBarChart({ data }) {
  // Layout
  const width = 600;
  const barHeight = 28;
  const gap = 8;
  const leftCol = 200; // left label column
  const chartWidth = width - leftCol;

  // max |value| for scaling
  const maxMag = Math.max(
    ...data.map((d) => Math.abs(d.value)),
    1 // avoid div by zero
  );

  return (
    <svg
      width="100%"
      viewBox={`0 0 ${width} ${data.length * (barHeight + gap)}`}
      style={{
        maxWidth: "100%",
        borderRadius: "12px",
        background: "rgba(15,23,42,0.6)",
        border: "1px solid rgba(148,163,184,0.4)",
        boxShadow:
          "0 24px 60px rgba(0,0,0,0.9),0 0 30px rgba(56,189,248,0.3),0 0 80px rgba(99,102,241,0.3)",
      }}
    >
      <defs>
        <linearGradient id="gradPos" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="rgb(16,185,129)" stopOpacity="0.4" />
          <stop offset="100%" stopColor="rgb(16,185,129)" stopOpacity="0.9" />
        </linearGradient>
        <linearGradient id="gradNeg" x1="100%" y1="0%" x2="0%" y2="0%">
          <stop offset="0%" stopColor="rgb(239,68,68)" stopOpacity="0.4" />
          <stop offset="100%" stopColor="rgb(239,68,68)" stopOpacity="0.9" />
        </linearGradient>
      </defs>

      {data.map((d, i) => {
        const y = i * (barHeight + gap);

        const frac = Math.abs(d.value) / maxMag;
        const halfWidth = chartWidth / 2;
        const barLen = frac * halfWidth;

        // middle (0 impact) line
        const originX = leftCol + halfWidth;

        const isPositive = d.value >= 0;
        const rectX = isPositive ? originX : originX - barLen;
        const rectW = barLen;
        const fillGrad = isPositive ? "url(#gradPos)" : "url(#gradNeg)";

        return (
          <g key={d.feature}>
            {/* Feature name on the left */}
            <text
              x={12}
              y={y + barHeight * 0.7}
              fill="#fff"
              fontSize="12"
              style={{ fontFamily: "Inter, system-ui, sans-serif" }}
            >
              {labelize(d.feature)}
            </text>

            {/* Center line */}
            <line
              x1={originX}
              y1={y}
              x2={originX}
              y2={y + barHeight}
              stroke="rgba(255,255,255,0.2)"
              strokeWidth="1"
            />

            {/* Impact bar */}
            <rect
              x={rectX}
              y={y}
              width={rectW}
              height={barHeight}
              rx={6}
              fill={fillGrad}
              stroke="rgba(255,255,255,0.2)"
              strokeWidth="1"
            />

            {/* Value label */}
            <text
              x={isPositive ? rectX + rectW + 6 : rectX - 6}
              y={y + barHeight * 0.7}
              fill="#f8fafc"
              fontSize="12"
              textAnchor={isPositive ? "start" : "end"}
              style={{
                fontFamily: "Inter, system-ui, sans-serif",
                textShadow:
                  "0 0 8px rgba(255,255,255,0.6),0 0 24px rgba(16,185,129,0.6)",
              }}
            >
              {d.value.toFixed(2)}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

/* ---------- Small UI atoms & helpers ---------- */

function Badge({ children, tone = "neutral" }) {
  return <span className={`badge tone-${tone}`}>{children}</span>;
}

function DecisionPill({ prediction }) {
  const clean = String(prediction || "").toLowerCase();
  const approved = clean.includes("approve");

  const bg = approved
    ? "radial-gradient(circle at 0% 0%, #10b981 0%, #0d9488 60%)"
    : "radial-gradient(circle at 0% 0%, #ef4444 0%, #dc2626 60%)";

  const shadow = approved
    ? "0 0 12px rgba(16,185,129,0.6), 0 0 40px rgba(16,185,129,0.4)"
    : "0 0 12px rgba(239,68,68,0.6), 0 0 40px rgba(239,68,68,0.4)";

  return (
    <div
      style={{
        minWidth: "140px",
        borderRadius: "14px",
        border: "1px solid rgba(255,255,255,0.18)",
        background: bg,
        color: "#fff",
        fontWeight: 600,
        fontSize: "0.9rem",
        lineHeight: "1.3rem",
        textAlign: "center",
        padding: "12px 14px",
        boxShadow: shadow,
        textShadow:
          "0 0 8px rgba(0,0,0,0.6), 0 0 20px rgba(255,255,255,0.4)",
      }}
    >
      {approved ? "Likely Approved" : "At Risk of Rejection"}
    </div>
  );
}

function riskTone(risk) {
  const r = String(risk || "").toLowerCase();
  if (r.includes("high")) return "danger";
  if (r.includes("medium")) return "warn";
  if (r.includes("low")) return "ok";
  return "neutral";
}

function labelize(key) {
  // snake_case -> Title Case
  return key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatValue(key, v) {
  if (v === null || v === undefined || v === "") return "—";
  // money-ish values
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
  // pretty print numbers except cibil_score
  if (!isNaN(Number(v)) && key !== "cibil_score") {
    return Number(v).toLocaleString();
  }
  return String(v);
}
