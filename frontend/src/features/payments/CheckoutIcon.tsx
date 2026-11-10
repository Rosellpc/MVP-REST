export default function CheckoutIcon({ kind }: { kind: "card" | "wallet" | "arrow" | "check" | "bag" }) {
  const paths = {
    card: <><rect x="3" y="5" width="18" height="14" rx="3" /><path d="M3 10h18M7 15h3" /></>,
    wallet: <><path d="M19 8V5H5a2 2 0 0 0-2 2v12h17V8H5a1 1 0 0 1 0-2" /><path d="M16 12h5v4h-5z" /></>,
    arrow: <><path d="M5 12h14m-5-5 5 5-5 5" /></>,
    check: <><path d="m6 12 4 4 8-8" /></>,
    bag: <><path d="M5 7h14l1 14H4L5 7Z" /><path d="M9 8V6a3 3 0 0 1 6 0v2" /></>,
  };
  return <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[kind]}</svg>;
}
