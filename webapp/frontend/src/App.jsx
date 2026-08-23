import { useEffect, useMemo, useState } from "react";

const LABELS = {
  prompt_injection_merchant_content: "Prompt injection",
  multiturn_trust_poisoning: "Trust poisoning",
  recommendation_bias: "Recommendation bias",
  legitimate: "Legitimate payment",
};

function pct(value) {
  return `${((value || 0) * 100).toFixed(1)}%`;
}

function verdictClass(verdict) {
  if (verdict === "block" || verdict === "blocked") return "bad";
  if (verdict === "step_up_required") return "warn";
  return "ok";
}

export default function App() {
  const [catalog, setCatalog] = useState(null);
  const [selectedId, setSelectedId] = useState("");
  const [result, setResult] = useState(null);
  const [evaluation, setEvaluation] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [showEval, setShowEval] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch("/api/catalog").then((r) => r.json()),
      fetch("/api/evaluation").then((r) => r.json()),
      fetch("/api/metrics").then((r) => r.json()),
    ])
      .then(([cat, ev, met]) => {
        setCatalog(cat);
        setEvaluation(ev);
        setMetrics(met);
        const first = cat.featured?.[0];
        if (first) {
          setSelectedId(first);
          return simulate(first);
        }
        return null;
      })
      .catch((err) => setError(err.message));
  }, []);

  async function simulate(conversationId) {
    setBusy(true);
    setError("");
    try {
      const response = await fetch("/api/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ conversationId }),
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail || "Simulation failed");
      }
      const payload = await response.json();
      setSelectedId(conversationId);
      setResult(payload);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  const summary = evaluation?.summary;
  const turns = result?.transcript?.turns || [];
  const featured = catalog?.featured || [];

  const scoreWidth = useMemo(() => {
    const score = result?.detectorScore ?? 0;
    return `${Math.max(3, Math.min(100, score * 100)).toFixed(1)}%`;
  }, [result]);

  return (
    <div className="page">
      <header className="top">
        <div>
          <p className="kicker">Mastercard Innovation Challenge</p>
          <h1>Agentic Payment Defense Lab</h1>
          <p className="lede">
            Closed loop: generate a fraud transcript, intercept it with a deterministic gate,
            then score residual behavioral risk with the ML detector.
          </p>
        </div>
        <div className="status-chip">Live on local JSONL + trained model</div>
      </header>

      <section className="controls">
        <h2>Select an attack</h2>
        <div className="featured">
          {featured.map((id) => {
            const type = Object.entries(catalog?.groups || {}).find(([, rows]) =>
              rows.some((row) => row.conversationId === id)
            )?.[0];
            return (
              <button
                key={id}
                className={selectedId === id ? "primary selected" : "primary"}
                onClick={() => simulate(id)}
                disabled={busy}
              >
                {LABELS[type] || id}
                <span>{id}</span>
              </button>
            );
          })}
          <button className="ghost" onClick={() => setShowEval((v) => !v)}>
            {showEval ? "Hide" : "View"} evaluation breakdown
          </button>
        </div>
        <div className="picker-row">
          {Object.entries(catalog?.groups || {}).map(([type, rows]) => (
            <label key={type}>
              {LABELS[type]}
              <select
                value={type === result?.attackType ? selectedId : ""}
                onChange={(event) => event.target.value && simulate(event.target.value)}
              >
                <option value="">Choose transcript</option>
                {rows.map((row) => (
                  <option key={row.conversationId} value={row.conversationId}>
                    {row.conversationId} · ${row.amount ?? "—"}
                  </option>
                ))}
              </select>
            </label>
          ))}
        </div>
      </section>

      {error ? <p className="error">{error}</p> : null}

      {result ? (
        <section className="result-grid">
          <article className="card transcript">
            <h2>Transcript</h2>
            <p className="meta">
              {result.conversationId} · {LABELS[result.attackType] || result.attackType} · ground
              truth {result.groundTruth}
            </p>
            <div className="turns">
              {turns.map((turn) => (
                <div key={`${turn.turn_number}-${turn.role}`} className={`turn ${turn.role}`}>
                  <strong>
                    {turn.role}
                    <em>T{turn.turn_number}</em>
                  </strong>
                  <p>{turn.content}</p>
                </div>
              ))}
            </div>
          </article>

          <div className="stack">
            <article className="card">
              <h2>Deterministic gate</h2>
              <p className={`verdict ${verdictClass(result.gateVerdict)}`}>{result.gateVerdict}</p>
              <ul>
                {(result.gateReasons || []).map((reason) => (
                  <li key={reason}>{reason}</li>
                ))}
              </ul>
            </article>

            <article className="card">
              <h2>ML detector</h2>
              <p className="score-label">Fraud probability</p>
              <p className="score">{(result.detectorScore * 100).toFixed(1)}%</p>
              <div className="meter">
                <span style={{ width: scoreWidth }} />
              </div>
              <p className="meta">{result.mlFlag ? "Flagged as fraud" : "Below 0.50 threshold"}</p>
            </article>

            <article className="card final">
              <h2>Final verdict</h2>
              <p className={`verdict ${verdictClass(result.finalVerdict)}`}>{result.finalVerdict}</p>
              <p className="meta">
                Payee {result.transferDetails?.payee_id || "none"} · $
                {result.transferDetails?.amount ?? "—"} · source{" "}
                {result.transferDetails?.source_of_instruction || "n/a"}
              </p>
            </article>
          </div>
        </section>
      ) : (
        <p className="meta">Loading a sample transcript…</p>
      )}

      {showEval && summary ? (
        <section className="card eval">
          <h2>Gate vs detector breakdown</h2>
          <table>
            <thead>
              <tr>
                <th>Category</th>
                <th>Count</th>
                <th>Percentage</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Gate caught</td>
                <td>{summary.gate_caught}</td>
                <td>{pct(summary.gate_catch_rate ?? summary.gate_caught_rate)}</td>
              </tr>
              <tr>
                <td>Detector caught</td>
                <td>{summary.detector_caught}</td>
                <td>{pct(summary.detector_catch_rate ?? summary.detector_caught_rate)}</td>
              </tr>
              <tr>
                <td>Both caught</td>
                <td>{summary.both_caught}</td>
                <td>{pct(summary.both_caught_rate)}</td>
              </tr>
              <tr>
                <td>Missed</td>
                <td>{summary.missed}</td>
                <td>{pct(summary.false_negative_rate ?? summary.missed_rate)}</td>
              </tr>
              <tr className="total">
                <td>Combined catch rate</td>
                <td>{summary.total_attacks - summary.missed}</td>
                <td>{pct(summary.combined_catch_rate ?? summary.combined_defense_rate)}</td>
              </tr>
            </tbody>
          </table>
          {metrics ? (
            <p className="meta">
              Detector holdout: precision {metrics.precision.toFixed(3)} · recall{" "}
              {metrics.recall.toFixed(3)} · F1 {metrics.f1.toFixed(3)} · AUC {metrics.auc.toFixed(3)}
            </p>
          ) : null}
        </section>
      ) : null}
    </div>
  );
}
