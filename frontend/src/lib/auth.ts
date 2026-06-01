import axios from "axios";
import { TokenResponse, Usuario } from "./types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function loginRequest(
  email: string,
  password: string
): Promise<TokenResponse> {
  const { data } = await axios.post<TokenResponse>(
    `${BASE_URL}/api/v1/auth/login`,
    { email, password }
  );
  return data;
}

export function saveTokens(tokens: TokenResponse): void {
  sessionStorage.setItem("access_token", tokens.access_token);
  sessionStorage.setItem("refresh_token", tokens.refresh_token);
}

export function clearTokens(): void {
  sessionStorage.removeItem("access_token");
  sessionStorage.removeItem("refresh_token");
}

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return sessionStorage.getItem("access_token");
}

export async function fetchMe(): Promise<Usuario> {
  const token = getAccessToken();
  const { data } = await axios.get<Usuario>(`${BASE_URL}/api/v1/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return data;
}

export async function logoutRequest(): Promise<void> {
  const refreshToken = sessionStorage.getItem("refresh_token");
  if (refreshToken) {
    try {
      await axios.post(
        `${BASE_URL}/api/v1/auth/logout`,
        { refresh_token: refreshToken },
        {
          headers: {
            Authorization: `Bearer ${getAccessToken()}`,
          },
        }
      );
    } catch {
      // ignora erro no logout
    }
  }
  clearTokens();
}
