export type StaffUser = {
  id: number;
  username: string;
  display_name: string;
  roles: string[];
  permissions: string[];
};

export class AuthError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

export async function request(path: string, init: RequestInit = {}) {
  const response = await fetch(`/api/v1/${path}`, {
    credentials: "same-origin",
    cache: "no-store",
    ...init,
    signal: init.signal ? AbortSignal.any([init.signal, AbortSignal.timeout(10000)]) : AbortSignal.timeout(10000),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new AuthError(
    data.detail ?? (response.status === 403 ? "Acceso denegado o sesión vencida. Vuelve a iniciar sesión." : "No se pudo completar la solicitud."),
    response.status,
  );
  return data;
}

export async function post(path: string, body = {}) {
  const { csrfToken } = await request("auth/csrf/");
  return request(path, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
    body: JSON.stringify(body),
  });
}

export async function getSession(): Promise<StaffUser | null> {
  try { return await request("auth/me/"); }
  catch (error) {
    if (error instanceof AuthError && [401, 403].includes(error.status)) return null;
    throw error;
  }
}

export async function login(username: string, password: string): Promise<StaffUser> {
  const data = await post("auth/login/", { username, password });
  return data.user;
}

export async function logout() { await post("auth/logout/"); }

export function checkArea(area: string, signal: AbortSignal) {
  return request(`${area}/access/`, { signal });
}
