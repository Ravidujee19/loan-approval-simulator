import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API || "http://localhost:5001",
});

export function setAuth(token) {
  if (token) api.defaults.headers.common.Authorization = `Bearer ${token}`;
  else delete api.defaults.headers.common.Authorization;
}

export async function login(username, password) {
  const { data } = await api.post("/login", { username, password });
  return data; // { access_token, token_type }
}

export async function evaluate(payload) {
  const { data } = await api.post("/evaluate", payload);
  return data;
}

export default api;
