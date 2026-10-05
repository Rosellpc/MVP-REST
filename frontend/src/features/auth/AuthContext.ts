import { createContext } from "react";
import type { StaffUser } from "./authApi";

export const AuthContext = createContext<{
  user: StaffUser | null;
  loading: boolean;
  error: string;
  refresh: () => Promise<void>;
  signIn: (username: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
} | null>(null);
