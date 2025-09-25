import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || "http://localhost:8000",
});

// Backend endpoints for Applicant Evaluator
export async function createApplicant() {
  const { data } = await api.post("/api/v1/applicants/");
  return data.applicant_id;
}

export async function uploadDocs(applicantId, files) {
  const fd = new FormData();
  for (const f of files) fd.append("files", f);
  const { data } = await api.post(`/api/v1/applicants/${applicantId}/documents`, fd, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function evaluateWithForm(applicantId, payload) {
  const { data } = await api.post(`/api/v1/applicants/${applicantId}/evaluate-with-form`, payload);
  return data;
}

export default api;
