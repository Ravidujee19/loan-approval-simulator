// loan-ui/src/pages/Dashboard.jsx
import { useEffect, useMemo, useState } from "react";
import {
  getMetrics,
  listApplicants,
  deleteApplicant,
} from "../services/api.jsx";
import ApplicantsTable from "../components/ApplicantsTable.jsx";
import "../styles/dashboard.css";

// Decode role & sub from the stored JWT token (localStorage key: "token")
function useAuthInfo() {
  const token = localStorage.getItem("token");
  let role = "user";
  let sub = null;
  if (token) {
    try {
      const payload = JSON.parse(atob(token.split(".")[1]));
      role = payload?.role || role;
      sub = payload?.sub || null;
    } catch {}
  }
  return { role, sub };
}

export default function Dashboard() {
  // Metrics state (existing behavior)
  const [m, setM] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");
  const num = new Intl.NumberFormat();

  // Applicants state (new)
  const { role, sub } = useAuthInfo();
  const isAdmin = role === "admin";
  const [appsLoading, setAppsLoading] = useState(true);
  const [apps, setApps] = useState([]);
  const [tab, setTab] = useState(isAdmin ? "all" : "mine"); // admin: all|mine
  const [q, setQ] = useState("");

  // Delete (admin only)
  const handleDelete = async (id) => {
    if (!window.confirm("Delete this applicant? This cannot be undone."))
      return;
    try {
      await deleteApplicant(id);
      // Optimistically remove from local state
      setApps((prev) => prev.filter((a) => String(a.id) !== String(id)));
    } catch (e) {
      alert("Failed to delete applicant");
    }
  };

  // Load metrics
  useEffect(() => {
    let alive = true;
    setLoading(true);
    setErr("");
    getMetrics()
      .then((data) => {
        if (alive) setM(data);
      })
      .catch(() => {
        if (alive) setErr("Failed to load metrics");
      })
      .finally(() => {
        if (alive) setLoading(false);
      });
    return () => {
      alive = false;
    };
  }, []);

  // Load applicants
  useEffect(() => {
    let alive = true;
    setAppsLoading(true);
    listApplicants({ limit: 100, offset: 0 })
      .then((data) => {
        if (alive) setApps(data);
      })
      .catch(() => {
        if (alive) setApps([]);
      })
      .finally(() => {
        if (alive) setAppsLoading(false);
      });
    return () => {
      alive = false;
    };
  }, []);

  // Client-side filter: search + (admin) "Only mine"
  const filteredApps = useMemo(() => {
    let arr = apps;
    if (isAdmin && tab === "mine" && sub) {
      arr = arr.filter((a) => String(a.user_id) === String(sub));
    }
    if (q.trim()) {
      const s = q.trim().toLowerCase();
      arr = arr.filter(
        (a) =>
          `${a.first_name} ${a.last_name}`.toLowerCase().includes(s) ||
          (a.email || "").toLowerCase().includes(s)
      );
    }
    return arr;
  }, [apps, isAdmin, tab, sub, q]);

  // Loading skeleton
  if (loading) {
    return (
      <>
        <div className="dashboard-page">
          <div className="dashboard-skeleton">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="dashboard-skel-card space-y-3">
                <div className="dashboard-skel-line w-1/3" />
                <div className="dashboard-skel-line w-2/3 h-8" />
              </div>
            ))}
          </div>
        </div>
      </>
    );
  }

  return (
    <div className="dashboard-page">
      {/* Metrics grid */}
      <div className="dashboard-grid">
        <div className="dashboard-card">
          <div className="dashboard-title">Total Loans</div>
          <div className="dashboard-metric">
            {num.format(m?.total_loans ?? 0)}
          </div>
        </div>

        <div className="dashboard-card">
          <div className="dashboard-title">Outcomes</div>
          <div className="dashboard-code">
            {JSON.stringify(m?.outcomes || {}, null, 2)}
          </div>
        </div>

        <div className="dashboard-card">
          <div className="dashboard-title">By Status</div>
          <div className="dashboard-chips">
            {Object.entries(m?.by_status || {}).map(([status, count]) => {
              const cls =
                status === "approved"
                  ? "dashboard-chip dashboard-chip-a"
                  : status === "rejected"
                  ? "dashboard-chip dashboard-chip-r"
                  : status === "pending"
                  ? "dashboard-chip dashboard-chip-p"
                  : "dashboard-chip dashboard-chip-d";
              return (
                <span key={status} className={cls}>
                  {status}: {num.format(count)}
                </span>
              );
            })}
          </div>
        </div>
      </div>

      {/* Applicants section */}
      <div className="max-w-6xl mx-auto mt-6">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold">Applicants</h2>
          <div className="flex items-center gap-2">
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Search name or email…"
              className="bg-transparent border border-white/10 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-white/20"
            />
            {isAdmin && (
              <div className="inline-flex rounded-xl p-1 border border-white/10 bg-white/5">
                <button
                  onClick={() => setTab("all")}
                  className={`px-3 py-1 text-sm rounded-lg ${
                    tab === "all" ? "bg-white/10" : ""
                  }`}
                >
                  All
                </button>
                <button
                  onClick={() => setTab("mine")}
                  className={`px-3 py-1 text-sm rounded-lg ${
                    tab === "mine" ? "bg-white/10" : ""
                  }`}
                >
                  Only mine
                </button>
              </div>
            )}
          </div>
        </div>

        <ApplicantsTable
          items={filteredApps}
          loading={appsLoading}
          isAdmin={isAdmin}
          onDelete={handleDelete}
        />
      </div>

      {err && (
        <div className="max-w-6xl mx-auto mt-4 rounded-lg border border-rose-500/40 bg-rose-500/10 px-3 py-2 text-sm text-rose-200">
          {err}
        </div>
      )}
    </div>
  );
}

// import { useEffect, useMemo, useState } from 'react'
// import { getMetrics, listApplicants } from '../services/api.jsx'
// import ApplicantsTable from '../components/ApplicantsTable.jsx'
// import '../styles/dashboard.css'

// export default function Dashboard(){
//   const [m, setM] = useState(null)
//   const [loading, setLoading] = useState(true)
//   const [err, setErr] = useState('')
//   const num = new Intl.NumberFormat()

//   useEffect(() => {
//     let alive = true
//     setLoading(true); setErr('')
//     getMetrics()
//       .then(data => { if (alive) setM(data) })
//       .catch(() => { if (alive) setErr('Failed to load metrics') })
//       .finally(() => { if (alive) setLoading(false) })
//     return () => { alive = false }
//   }, [])

//   if (loading) {
//     return (
//       <>
//       <div className="dashboard-page">
//         <div className="dashboard-skeleton">
//           {[...Array(3)].map((_,i)=>(
//             <div key={i} className="dashboard-skel-card space-y-3">
//               <div className="dashboard-skel-line w-1/3" />
//               <div className="dashboard-skel-line w-2/3 h-8" />
//             </div>
//           ))}
//         </div>
//       </div>
//       </>
//     )
//   }

//   return (
//     <div className="dashboard-page">
//       <div className="dashboard-grid">
//         <div className="dashboard-card">
//           <div className="dashboard-title">Total Loans</div>
//           <div className="dashboard-metric">{num.format(m?.total_loans ?? 0)}</div>
//         </div>

//         {/* <div className="dashboard-card">
//           <div className="dashboard-title">User Type</div>
//           <div className="dashboard-metric">{m?.user_type || 'Unknown'}</div>
//         </div> */}
//         {/* move this to header */}

//         <div className="dashboard-card">
//           <div className="dashboard-title">Outcomes</div>
//           <div className="dashboard-code">
//             {JSON.stringify(m?.outcomes || {}, null, 2)}
//           </div>
//         </div>

//         <div className="dashboard-card">
//           <div className="dashboard-title">By Status</div>
//           <div className="dashboard-chips">
//             {Object.entries(m?.by_status || {}).map(([status, count]) => {
//               const cls =
//                 status === 'approved' ? 'dashboard-chip dashboard-chip-a' :
//                 status === 'rejected' ? 'dashboard-chip dashboard-chip-r' :
//                 status === 'pending'  ? 'dashboard-chip dashboard-chip-p' :
//                                         'dashboard-chip dashboard-chip-d'
//               return (
//                 <span key={status} className={cls}>
//                   {status}: {num.format(count)}
//                 </span>
//               )
//             })}
//           </div>
//         </div>

//         {/* Add more cards/sections below if needed */}
//       </div>

//       {err && (
//         <div className="max-w-6xl mx-auto mt-4 rounded-lg border border-rose-500/40 bg-rose-500/10 px-3 py-2 text-sm text-rose-200">
//           {err}
//         </div>
//       )}
//     </div>
//   )
// }
