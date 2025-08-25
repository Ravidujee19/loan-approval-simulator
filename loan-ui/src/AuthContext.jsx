import React, { createContext, useContext, useEffect, useState } from "react";
import { login as apiLogin, setAuth } from "./api";

const Ctx = createContext({ token: null, login: async () => {}, logout: () => {} });
export const useAuth = () => useContext(Ctx);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem("jwt"));

  useEffect(() => setAuth(token), [token]);

  const login = async (username, password) => {
    const res = await apiLogin(username, password);
    setToken(res.access_token);
    localStorage.setItem("jwt", res.access_token);
  };

  const logout = () => {
    setToken(null);
    localStorage.removeItem("jwt");
  };

  return <Ctx.Provider value={{ token, login, logout }}>{children}</Ctx.Provider>;
}
