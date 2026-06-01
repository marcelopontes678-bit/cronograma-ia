"use client";
import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  clearTokens,
  fetchMe,
  getAccessToken,
  loginRequest,
  logoutRequest,
  saveTokens,
} from "@/lib/auth";
import { Usuario } from "@/lib/types";

export function useAuth() {
  const [user, setUser] = useState<Usuario | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      setLoading(false);
      return;
    }
    fetchMe()
      .then(setUser)
      .catch(() => {
        clearTokens();
        router.replace("/login");
      })
      .finally(() => setLoading(false));
  }, [router]);

  const login = useCallback(
    async (email: string, password: string) => {
      const tokens = await loginRequest(email, password);
      saveTokens(tokens);
      const me = await fetchMe();
      setUser(me);
      router.replace("/dashboard");
    },
    [router]
  );

  const logout = useCallback(async () => {
    await logoutRequest();
    setUser(null);
    router.replace("/login");
  }, [router]);

  return { user, loading, login, logout };
}
