type Token = { id: string; email: string };
type Checkout = { token?: Token; error?: { user_message?: string }; culqi: () => void; open: () => void; close: () => void };
export type Authentication = { eci: string; xid: string; cavv: string; protocolVersion: string; directoryServerTransactionId?: string };
type ThreeDS = { publicKey: string; settings: unknown; options: unknown; generateDevice: () => Promise<string>; initAuthentication: (token: string) => void; reset: () => void };
declare global {
  interface Window { CulqiCheckout?: new (key: string, config: unknown) => Checkout; Culqi3DS?: ThreeDS }
}

const scripts = new Map<string, Promise<void>>();
function loadScript(src: string) {
  if (!scripts.has(src)) {
    scripts.set(src, new Promise<void>((resolve, reject) => {
      const script = document.createElement("script");
      const timer = window.setTimeout(() => { script.remove(); scripts.delete(src); reject(new Error("Culqi tardó en cargar. Reintenta abrir el formulario.")); }, 15000);
      script.src = src; script.async = true;
      script.onload = () => { clearTimeout(timer); resolve(); };
      script.onerror = () => { clearTimeout(timer); script.remove(); scripts.delete(src); reject(new Error("No se pudo cargar Culqi.")); };
      document.body.appendChild(script);
    }));
  }
  return scripts.get(src)!;
}

export async function openCheckout(key: string, amount: number, onToken: (token: Token) => void, onError: (message: string) => void) {
  await loadScript("https://js.culqi.com/checkout-js");
  if (!window.CulqiCheckout) throw new Error("Culqi Checkout no está disponible.");
  const checkout = new window.CulqiCheckout(key, {
    settings: { title: "REST-OS · Pruebas", currency: "PEN", amount },
    options: { lang: "es", modal: true, installments: false,
      paymentMethods: { tarjeta: true, yape: false, billetera: false, bancaMovil: false, agente: false, cuotealo: false },
      paymentMethodsSort: ["tarjeta"] },
    appearance: { theme: "default", menuType: "sliderTop",
      variables: { colorBackground: "#1e2023", colorText: "#f4f4f4", colorPrimary: "#b9bcc1", borderRadius: "16px" },
      defaultStyle: { bannerColor: "#1e2023", buttonBackground: "#4c4e51", buttonTextColor: "#ffffff" } },
  });
  let handled = false;
  checkout.culqi = () => {
    if (checkout.token && !handled) { handled = true; checkout.close(); onToken(checkout.token); }
    else if (checkout.error) onError(checkout.error.user_message || "No se pudo obtener el medio de pago.");
  };
  checkout.open();
  return checkout;
}

export async function setup3DS(key: string, amount: number, email: string) {
  await loadScript("https://3ds.culqi.com");
  const three = window.Culqi3DS;
  if (!three) throw new Error("No se pudo cargar la autenticación.");
  three.reset(); three.publicKey = key;
  three.settings = { charge: { totalAmount: amount, currency: "PEN", returnUrl: window.location.origin + "/checkout" }, card: { email } };
  three.options = { showModal: true, showLoading: true, showIcon: true, style: { btnColor: "#4c4e51", btnTextColor: "#ffffff" } };
  const device = await three.generateDevice();
  if (!device) throw new Error("No se pudo verificar el dispositivo. No se inició el cargo.");
  return device;
}

export function authenticate(token: string, signal?: AbortSignal): Promise<Authentication> {
  return new Promise((resolve, reject) => {
    const cleanup = () => { clearTimeout(timer); window.removeEventListener("message", listener); signal?.removeEventListener("abort", abort); };
    const abort = () => { cleanup(); reject(new Error("Autenticación interrumpida. Consulta el intento antes de volver a pagar.")); };
    const listener = (event: MessageEvent) => {
      if (event.origin !== window.location.origin || !event.data || typeof event.data !== "object") return;
      const auth = event.data.parameters3DS;
      if (auth && ["eci", "xid", "cavv", "protocolVersion"].every(k => typeof auth[k] === "string")) { cleanup(); resolve(auth); }
      else if (event.data.error) { cleanup(); reject(new Error("Autenticación no completada. Consulta el estado del pago.")); }
    };
    const timer = window.setTimeout(() => { cleanup(); reject(new Error("La autenticación no terminó. Conservamos tu referencia de pago.")); }, 180000);
    window.addEventListener("message", listener);
    signal?.addEventListener("abort", abort, { once: true });
    if (signal?.aborted) { abort(); return; }
    try { window.Culqi3DS!.initAuthentication(token); } catch { cleanup(); reject(new Error("No se pudo iniciar la autenticación.")); }
  });
}
