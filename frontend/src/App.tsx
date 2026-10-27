import { LedgerGrid } from "./grids/LedgerGrid";

export default function App() {
  return (
    <main style={{ fontFamily: "system-ui, sans-serif", padding: 24 }}>
      <h1>Gam'eya</h1>
      <p>AI-run savings circles on PayPal. Organiser control room (scaffold).</p>
      <LedgerGrid circleId="golden" />
    </main>
  );
}
