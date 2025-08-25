import React, { useState } from "react";
import { useAuth } from "../AuthContext.jsx";
import { useNavigate } from "react-router-dom";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setU] = useState("member1");
  const [password, setP] = useState("password123");
  const [err, setErr] = useState("");

  const submit = async (e) => {
    e.preventDefault();
    setErr("");
    try {
      await login(username, password);
      navigate("/"); // go to Applicant Form
    } catch (e) {
      setErr(e?.response?.data?.detail || "Login failed");
    }
  };

  return (
    <div className="container d-flex justify-content-center align-items-center min-vh-100">
      <div className="row w-100 justify-content-center">
        <div className="col-11 col-sm-8 col-md-6 col-lg-4">
          <div className="card shadow">
            <div className="card-body">
              <h3 className="mb-4 text-center">Officer Login</h3>
              <form onSubmit={submit} className="vstack gap-3">
                <div>
                  <label className="form-label">Username</label>
                  <input className="form-control" value={username} onChange={(e)=>setU(e.target.value)} />
                </div>
                <div>
                  <label className="form-label">Password</label>
                  <input type="password" className="form-control" value={password} onChange={(e)=>setP(e.target.value)} />
                </div>
                {err && <div className="alert alert-danger">{err}</div>}
                <button className="btn btn-primary w-100" type="submit">Sign in</button>
                <p className="text-muted small text-center mb-0">
                  Use <code>member1</code> / <code>password123</code>
                </p>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
