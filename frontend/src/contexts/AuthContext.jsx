import { createContext, useContext, useMemo, useState } from "react";

const AuthContext = createContext(null);
const TOKEN_KEY = "alby_token";
const ROLE_KEY = "alby_role";
const LEGACY_TOKEN_KEY = "token";
const LEGACY_ROLE_KEY = "role";

export function AuthProvider({ children }) {
  const [token, setToken] = useState(localStorage.getItem(TOKEN_KEY) || localStorage.getItem(LEGACY_TOKEN_KEY));
  const [role, setRole] = useState(localStorage.getItem(ROLE_KEY) || localStorage.getItem(LEGACY_ROLE_KEY));

  const login = (nextToken, nextRole) => {
    localStorage.setItem(TOKEN_KEY, nextToken);
    localStorage.setItem(ROLE_KEY, nextRole);
    localStorage.removeItem(LEGACY_TOKEN_KEY);
    localStorage.removeItem(LEGACY_ROLE_KEY);
    setToken(nextToken);
    setRole(nextRole);
  };

  const logout = () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(ROLE_KEY);
    localStorage.removeItem(LEGACY_TOKEN_KEY);
    localStorage.removeItem(LEGACY_ROLE_KEY);
    setToken(null);
    setRole(null);
  };

  const value = useMemo(() => ({ token, role, login, logout }), [token, role]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
