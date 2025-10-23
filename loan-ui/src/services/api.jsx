import axios from "axios";

// Base Configuration
const baseURL = import.meta.env.VITE_API_URL || "http://localhost:8000";
export const api = axios.create({ baseURL });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Auth
export async function login(email, password) {
  const { data } = await api.post("/api/v1/auth/login", { email, password });
  return data;
}

export async function register(payload) {
  const { data } = await api.post("/api/v1/auth/register", payload);
  return data;
}

// Applicants

// Create a new applicant
export async function createApplicant(payload) {
  const { data } = await api.post("/api/v1/applicants", payload || {});
  return data.applicant_id ?? data;
}

// Upload applicant documents
export async function uploadDocs(applicantId, files) {
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));

  const { data } = await api.post(
    `/api/v1/applicants/${applicantId}/documents`,
    formData,
    { headers: { "Content-Type": "multipart/form-data" } }
  );

  return data;
}

// Evaluate applicant with form
export async function evaluateWithForm(applicantId, payload) {
  const { data } = await api.post(
    `/api/v1/applicants/${applicantId}/evaluate-with-form`,
    payload
  );
  return data;
}

// Retrieve applicant profile
export async function getApplicantProfile(applicantId, loanId) {
  const { data } = await api.get(`/api/v1/applicants/${applicantId}/profile`, {
    params: { loan_id: loanId },
  });
  return data;
}

// Loans
export async function createLoan(payload, key) {
  const { data } = await api.post(
    "/api/v1/loans",
    payload,
    { headers: { "Idempotency-Key": key || crypto.randomUUID() } }
  );
  return data;
}

export async function getLoan(id) {
  const { data } = await api.get(`/api/v1/loans/${id}`);
  return data;
}

// Dashboard Metrics
export async function getMetrics() {
  const { data } = await api.get("/api/v1/stats");
  return data;
}

// Auto-prefill endpoints
/**
 * Send freeform text to backend to extract fields.
 * Expects backend endpoint: POST /api/v1/applicants/{applicant_id}/prefill-from-text
 */
export async function prefillFromText(applicantId, text) {
  const { data } = await api.post(`/api/v1/applicants/${applicantId}/prefill-from-text`, { text });
  return data;
}

/**
 * Upload a PDF to backend to extract fields.
 * Expects backend endpoint: POST /api/v1/applicants/{applicant_id}/prefill-from-pdf
 */
export async function prefillFromPdf(applicantId, file) {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await api.post(`/api/v1/applicants/${applicantId}/prefill-from-pdf`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

