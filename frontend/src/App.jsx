import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  ShieldCheck,
  Zap,
  Activity,
  Clock,
  Sparkles,
  Search,
  ExternalLink,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  BarChart3,
  Flame,
  ArrowRight,
  RefreshCw,
  Sun,
  Moon,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { INITIAL_RESULT, INITIAL_BENCHMARK } from './defaultData';

const DEFAULT_SCENARIOS = [
  { id: 'pmid_28491530', specialty: 'Nephrology', question: 'Does Metformin reduce cardiovascular mortality in patients with chronic kidney disease?' },
  { id: 'pmid_25841648', specialty: 'Cardiology', question: 'What is the recommended dose adjustment for Apixaban in patients with severe renal impairment?' },
  { id: 'pmid_23755979', specialty: 'Cardiology', question: 'Do preoperative statins reduce the incidence of postoperative atrial fibrillation after coronary artery bypass grafting?' },
  { id: 'def_001', specialty: 'General Medicine', question: 'What is essential hypertension?' }
];

export default function App() {
  const [theme, setTheme] = useState('light');
  const [query, setQuery] = useState('Does Metformin reduce cardiovascular mortality in patients with chronic kidney disease?');
  const [scenarios, setScenarios] = useState(DEFAULT_SCENARIOS);
  const [activeTab, setActiveTab] = useState('copilot');
  const [loading, setLoading] = useState(false);
  const [benchLoading, setBenchLoading] = useState(false);
  const [result, setResult] = useState(INITIAL_RESULT);
  const [benchmarkResult, setBenchmarkResult] = useState(INITIAL_BENCHMARK);
  const [statusMessage, setStatusMessage] = useState('');
  const [dossierOpen, setDossierOpen] = useState(false);
  const [rankOpen, setRankOpen] = useState(false);

  const isLight = theme === 'light';

  useEffect(() => {
    fetchScenarios();
  }, []);

  const fetchScenarios = async () => {
    try {
      const res = await axios.get('/api/scenarios');
      if (res.data && res.data.length > 0) setScenarios(res.data);
    } catch {
      // silent — use built-in presets
    }
  };

  const handleRunQuery = async (queryToRun) => {
    const q = queryToRun || query;
    if (!q.trim()) return;
    setLoading(true);
    setStatusMessage('');
    try {
      const resQuery = await axios.post('/api/query', { query: q });
      setResult(resQuery.data);
    } catch (err) {
      console.error('Query error:', err);
      setStatusMessage('Backend request failed — displayed results are from the last successful run.');
    } finally {
      setLoading(false);
    }
  };

  const handleRunBenchmark = async (queryToRun) => {
    const q = queryToRun || query;
    if (!q.trim()) return;
    setBenchLoading(true);
    setStatusMessage('');
    try {
      const resBench = await axios.post('/api/benchmark', { query: q });
      setBenchmarkResult(resBench.data);
    } catch (err) {
      console.error('Benchmark error:', err);
      setStatusMessage('Benchmark run failed or timed out.');
    } finally {
      setBenchLoading(false);
    }
  };

  const fmtRoute = (s) => s.replace(/_/g, ' ');

  const handleAction = (queryToRun) => {
    const q = queryToRun !== undefined ? queryToRun : query;
    if (activeTab === 'benchmark') {
      handleRunBenchmark(q);
    } else {
      handleRunQuery(q);
    }
  };

  return (
    <div className={`theme-${theme} min-h-screen relative p-4 md:p-6 overflow-x-hidden transition-colors duration-200`}>
      <div className="bg-glow" />
      <div className="bg-glow-alt" />

      {/* Header */}
      <header className={`relative z-10 max-w-6xl mx-auto flex flex-col md:flex-row justify-between items-start md:items-center gap-3 pb-5 border-b ${
        isLight ? 'border-slate-200' : 'border-white/10'
      }`}>
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-xl flex items-center justify-center text-xl shadow-sm border ${
            isLight ? 'bg-indigo-50 border-indigo-200' : 'bg-indigo-500/10 border-indigo-500/30'
          }`}>🩺</div>
          <div>
            <div className="text-xl font-extrabold text-gradient tracking-tight">MedVerify</div>
            <div className={`text-[11px] font-semibold tracking-wider ${isLight ? 'text-indigo-500' : 'text-indigo-400'}`}>
              Adaptive RAG · Hallucination Guardrails
            </div>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold border ${
            isLight ? 'bg-emerald-50 border-emerald-200 text-emerald-700' : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
          }`}>
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            Live
          </div>

          <div className={`flex rounded-lg p-0.5 border ${isLight ? 'bg-slate-100 border-slate-200' : 'bg-white/5 border-white/10'}`}>
            <button
              onClick={() => setActiveTab('copilot')}
              className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                activeTab === 'copilot'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : isLight ? 'text-slate-600 hover:text-slate-900' : 'text-slate-400 hover:text-white'
              }`}
            >
              Copilot
            </button>
            <button
              onClick={() => setActiveTab('benchmark')}
              className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                activeTab === 'benchmark'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : isLight ? 'text-slate-600 hover:text-slate-900' : 'text-slate-400 hover:text-white'
              }`}
            >
              Benchmark
            </button>
          </div>

          <button
            onClick={() => setTheme(isLight ? 'dark' : 'light')}
            className={`p-1.5 rounded-lg text-xs flex items-center gap-1 border transition-all ${
              isLight ? 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50' : 'bg-white/10 border-white/15 text-slate-300 hover:bg-white/20'
            }`}
            title="Toggle theme"
          >
            {isLight ? <Moon className="w-3.5 h-3.5" /> : <Sun className="w-3.5 h-3.5 text-amber-300" />}
          </button>
        </div>
      </header>

      <main className="relative z-10 max-w-6xl mx-auto mt-5">
        {/* Scenario Selector */}
        <div className="mb-4">
          <label className={`text-[11px] font-semibold uppercase tracking-wider block mb-1.5 ${isLight ? 'text-slate-400' : 'text-slate-500'}`}>
            Curated Cases
          </label>
          <div className="flex flex-wrap gap-1.5">
            {scenarios.map((sc) => (
              <button
                key={sc.id}
                onClick={() => { setQuery(sc.question); handleAction(sc.question); }}
                className={`text-[11px] px-2.5 py-1 rounded-md border transition-all ${
                  query === sc.question
                    ? isLight
                      ? 'bg-indigo-50 border-indigo-300 text-indigo-800 font-medium'
                      : 'bg-indigo-500/20 border-indigo-400/50 text-indigo-200'
                    : isLight
                    ? 'bg-white border-slate-200 text-slate-600 hover:border-slate-300 hover:bg-slate-50'
                    : 'bg-white/[0.03] border-white/10 text-slate-400 hover:text-white'
                }`}
              >
                <span className="font-semibold text-indigo-500">{sc.specialty}</span>
                {' · '}
                {sc.question.slice(0, 42)}…
              </button>
            ))}
          </div>
        </div>

        {/* Search Bar */}
        <div className="glass-panel rounded-xl p-2.5 flex flex-col md:flex-row gap-2 mb-2">
          <div className={`flex-1 flex items-center gap-2.5 px-3 py-2 rounded-lg border transition-all ${
            isLight
              ? 'bg-slate-50 border-slate-200 focus-within:border-indigo-400 focus-within:bg-white'
              : 'bg-black/40 border-white/10 focus-within:border-indigo-500/60'
          }`}>
            <Search className="w-4 h-4 text-indigo-400 shrink-0" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAction(query)}
              placeholder="Enter clinical question, drug efficacy query, or medical definition…"
              className={`w-full bg-transparent text-sm focus:outline-none ${
                isLight ? 'text-slate-800 placeholder-slate-400' : 'text-slate-100 placeholder-slate-500'
              }`}
            />
          </div>
          <button
            onClick={() => handleAction(query)}
            disabled={activeTab === 'benchmark' ? benchLoading : loading}
            className="btn-primary px-5 py-2 rounded-lg font-semibold text-sm flex items-center justify-center gap-2 shrink-0 disabled:opacity-50"
          >
            {(activeTab === 'benchmark' ? benchLoading : loading) ? (
              <>
                <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                {activeTab === 'benchmark' ? 'Benchmarking…' : 'Auditing…'}
              </>
            ) : (
              <>
                <Zap className="w-3.5 h-3.5 fill-white" />
                {activeTab === 'benchmark' ? 'Run Benchmark' : 'Analyze'}
              </>
            )}
          </button>
        </div>

        {/* Error / Status Banner */}
        {statusMessage && (
          <div className={`mb-4 px-3.5 py-2 rounded-lg border flex items-center gap-2 text-xs ${
            isLight
              ? 'bg-amber-50 border-amber-200 text-amber-800'
              : 'bg-amber-500/10 border-amber-500/30 text-amber-300'
          }`}>
            <AlertCircle className="w-3.5 h-3.5 shrink-0" />
            {statusMessage}
          </div>
        )}

        {/* TAB 1: COPILOT */}
        {activeTab === 'copilot' && result && (
          <div className="mt-5">
            {/* KPI Strip — 3 tiles */}
            <div className="grid grid-cols-3 gap-3 mb-5">
              <div className="glass-card rounded-xl p-3.5">
                <div className={`text-[11px] uppercase font-semibold flex items-center justify-between mb-1 ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>
                  Route <Activity className="w-3.5 h-3.5 text-sky-500" />
                </div>
                <div className="text-base font-bold font-mono text-sky-600 leading-tight">
                  {fmtRoute(result.routing.route)}
                </div>
                <div className={`text-[11px] mt-0.5 ${isLight ? 'text-slate-400' : 'text-slate-500'}`}>
                  {Math.round(result.routing.confidence * 100)}% confidence
                </div>
              </div>

              <div className="glass-card rounded-xl p-3.5">
                <div className={`text-[11px] uppercase font-semibold flex items-center justify-between mb-1 ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>
                  Faithfulness <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
                </div>
                <div className="text-base font-bold font-mono text-emerald-600 leading-tight">
                  {Math.round(result.audit_result.faithfulness_score * 100)}%
                </div>
                <div className="text-[11px] text-emerald-500 mt-0.5">
                  {result.audit_result.entailed_claims}/{result.audit_result.total_claims} claims grounded
                </div>
              </div>

              <div className="glass-card rounded-xl p-3.5">
                <div className={`text-[11px] uppercase font-semibold flex items-center justify-between mb-1 ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>
                  Tokens saved <Flame className="w-3.5 h-3.5 text-purple-500" />
                </div>
                <div className="text-base font-bold font-mono text-purple-600 leading-tight">
                  {result.tokens_saved_percentage}%
                </div>
                <div className={`text-[11px] mt-0.5 ${isLight ? 'text-slate-400' : 'text-slate-500'}`}>
                  {result.tokens_consumed} used · {result.total_latency_s}s total
                </div>
              </div>
            </div>

            {/* Two-column layout */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
              {/* Left: Synthesis + Evidence */}
              <div className="lg:col-span-7 space-y-4">
                {/* Verified Clinical Synthesis */}
                <div className="glass-panel rounded-xl p-5">
                  <div className="flex justify-between items-center mb-3">
                    <h2 className={`text-sm font-bold flex items-center gap-2 ${isLight ? 'text-slate-800' : 'text-slate-100'}`}>
                      <Sparkles className="w-4 h-4 text-indigo-500" />
                      Verified Clinical Synthesis
                    </h2>
                    <span className={`text-[11px] px-2 py-0.5 rounded-full font-semibold border ${
                      isLight ? 'bg-indigo-50 text-indigo-600 border-indigo-200' : 'bg-indigo-500/20 text-indigo-300 border-indigo-500/30'
                    }`}>
                      Claim-grounded
                    </span>
                  </div>

                  <div className="space-y-2.5 mb-3">
                    {result.audit_result.claim_audits.map((ca, idx) => (
                      <div
                        key={idx}
                        className={`px-3.5 py-3 rounded-lg border text-sm leading-relaxed ${
                          ca.label === 'ENTAILMENT'
                            ? isLight
                              ? 'bg-emerald-50/60 border-emerald-200 text-slate-800'
                              : 'bg-emerald-500/[0.07] border-emerald-500/25 text-slate-200'
                            : ca.label === 'NEUTRAL'
                            ? isLight
                              ? 'bg-amber-50/60 border-amber-200 text-slate-800'
                              : 'bg-amber-500/[0.07] border-amber-500/25 text-slate-200'
                            : isLight
                            ? 'bg-rose-50/70 border-rose-200 text-rose-900'
                            : 'bg-rose-500/[0.10] border-rose-500/35 text-rose-200'
                        }`}
                      >
                        <div className="flex items-start gap-2">
                          {/* Colored dot indicator — simpler than a full badge */}
                          <span className={`mt-1.5 w-2 h-2 rounded-full shrink-0 ${
                            ca.label === 'ENTAILMENT' ? 'bg-emerald-500' : ca.label === 'NEUTRAL' ? 'bg-amber-400' : 'bg-rose-500'
                          }`} />
                          <span>{ca.claim}</span>
                        </div>

                        <div className="mt-2 ml-4 flex flex-wrap items-center gap-2">
                          {ca.label === 'ENTAILMENT' && (
                            <span className={`inline-flex items-center gap-1 text-[11px] font-semibold ${isLight ? 'text-emerald-700' : 'text-emerald-400'}`}>
                              <CheckCircle2 className="w-3 h-3" /> Entailed ({Math.round(ca.confidence * 100)}%)
                            </span>
                          )}
                          {ca.label === 'NEUTRAL' && (
                            <span className={`inline-flex items-center gap-1 text-[11px] font-semibold ${isLight ? 'text-amber-700' : 'text-amber-400'}`}>
                              <HelpCircle className="w-3 h-3" /> Extrapolated ({Math.round(ca.confidence * 100)}%)
                            </span>
                          )}
                          {ca.label === 'CONTRADICTION' && (
                            <span className={`inline-flex items-center gap-1 text-[11px] font-semibold ${isLight ? 'text-rose-700' : 'text-rose-400'}`}>
                              <AlertCircle className="w-3 h-3" /> Hallucination blocked
                            </span>
                          )}
                          {ca.cited_pmid && ca.cited_pmid !== 'None' && (
                            <a
                              href={`https://pubmed.ncbi.nlm.nih.gov/${ca.cited_pmid}/`}
                              target="_blank"
                              rel="noreferrer"
                              className="inline-flex items-center gap-1 text-[11px] font-mono text-sky-600 hover:text-sky-700 underline decoration-sky-300/60"
                            >
                              PMID:{ca.cited_pmid} <ExternalLink className="w-2.5 h-2.5" />
                            </a>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>

                  {result.audit_result.has_hallucination && (
                    <div className={`px-3 py-2 rounded-lg border text-xs flex items-center gap-2 ${
                      isLight ? 'bg-amber-50 border-amber-200 text-amber-800' : 'bg-amber-500/10 border-amber-500/30 text-amber-300'
                    }`}>
                      <AlertCircle className="w-3.5 h-3.5 shrink-0 text-amber-500" />
                      Guardrail active: contradicted assertions filtered from the clinical answer.
                    </div>
                  )}
                </div>

                {/* Evidence Dossier — collapsible */}
                <div className="glass-panel rounded-xl overflow-hidden">
                  <button
                    onClick={() => setDossierOpen(o => !o)}
                    className={`w-full flex items-center justify-between px-5 py-3.5 text-left transition-colors ${
                      isLight ? 'hover:bg-slate-50/60' : 'hover:bg-white/[0.03]'
                    }`}
                  >
                    <span className={`text-xs font-bold uppercase tracking-wider flex items-center gap-2 ${isLight ? 'text-slate-700' : 'text-slate-300'}`}>
                      📚 PubMed Evidence Dossier
                      <span className={`font-mono font-normal text-[11px] px-1.5 rounded ${isLight ? 'bg-slate-100 text-slate-500' : 'bg-white/10 text-slate-400'}`}>
                        {result.reranked_docs.length} retained
                      </span>
                    </span>
                    {dossierOpen ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
                  </button>

                  {dossierOpen && (
                    <div className="px-5 pb-4">
                      {result.reranked_docs.length > 0 ? (
                        <div className="space-y-2.5">
                          {result.reranked_docs.map((doc, idx) => (
                            <div key={doc.id} className="glass-card rounded-lg p-3.5">
                              <div className="flex justify-between items-start gap-2 mb-1.5">
                                <span className="text-xs font-semibold text-indigo-600">
                                  [{idx + 1}] PMID {doc.pmid}
                                </span>
                                <span className={`text-[11px] font-mono px-1.5 py-0.5 rounded border ${
                                  isLight ? 'bg-slate-50 border-slate-200 text-slate-600' : 'bg-white/5 border-white/5 text-slate-400'
                                }`}>
                                  Score <strong className="text-emerald-600">{doc.rerank_score}</strong>
                                </span>
                              </div>
                              <div className={`text-xs font-semibold mb-1 ${isLight ? 'text-slate-800' : 'text-slate-200'}`}>
                                {doc.question}
                              </div>
                              <div className={`text-xs line-clamp-2 leading-relaxed ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>
                                {doc.abstract}
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className={`text-xs py-3 ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>
                          No literature retrieved — query answered from parametric memory (Definitional route).
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* Right: Observability */}
              <div className="lg:col-span-5 space-y-4">
                {/* Routing Gate */}
                <div className="glass-panel rounded-xl p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[11px] font-bold text-sky-600 uppercase tracking-wider">Routing Gate</span>
                    <span className={`text-[11px] font-mono ${isLight ? 'text-slate-400' : 'text-slate-500'}`}>
                      {result.latency_waterfall['Routing Gate']} ms
                    </span>
                  </div>
                  <p className={`text-xs leading-relaxed mb-3 ${isLight ? 'text-slate-600' : 'text-slate-300'}`}>
                    {result.routing.reasoning}
                  </p>
                  <div className={`w-full rounded-full h-1.5 overflow-hidden ${isLight ? 'bg-slate-100' : 'bg-black/30'}`}>
                    <div
                      className="bg-sky-500 h-full rounded-full transition-all duration-500"
                      style={{ width: `${result.routing.confidence * 100}%` }}
                    />
                  </div>
                  <div className={`flex justify-between text-[11px] mt-1 font-mono ${isLight ? 'text-slate-400' : 'text-slate-500'}`}>
                    <span>Gate confidence</span>
                    <span className="text-sky-600 font-semibold">{Math.round(result.routing.confidence * 100)}%</span>
                  </div>
                </div>

                {/* Rank Shifts — collapsible */}
                <div className="glass-panel rounded-xl overflow-hidden">
                  <button
                    onClick={() => setRankOpen(o => !o)}
                    className={`w-full flex items-center justify-between px-4 py-3 transition-colors ${
                      isLight ? 'hover:bg-slate-50/60' : 'hover:bg-white/[0.03]'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-[11px] font-bold text-purple-600 uppercase tracking-wider">Cross-Encoder Reranking</span>
                      {result.rerank_telemetry.rank_shifts && result.rerank_telemetry.rank_shifts.length > 0 && (
                        <span className={`text-[11px] font-mono ${isLight ? 'text-slate-400' : 'text-slate-500'}`}>
                          {result.rerank_telemetry.retained_count} kept · {result.rerank_telemetry.pruned_count ?? 0} pruned
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`text-[11px] font-mono ${isLight ? 'text-slate-400' : 'text-slate-500'}`}>
                        {result.latency_waterfall['Neural Reranking']} ms
                      </span>
                      {rankOpen ? <ChevronUp className="w-3.5 h-3.5 text-slate-400" /> : <ChevronDown className="w-3.5 h-3.5 text-slate-400" />}
                    </div>
                  </button>

                  {rankOpen && (
                    <div className="px-4 pb-3">
                      {result.rerank_telemetry.rank_shifts && result.rerank_telemetry.rank_shifts.length > 0 ? (
                        <div className="space-y-1.5">
                          {result.rerank_telemetry.rank_shifts.map((rs) => (
                            <div
                              key={rs.id}
                              className={`flex items-center justify-between text-xs p-2 rounded-lg border ${
                                isLight ? 'bg-slate-50 border-slate-200/80' : 'bg-black/20 border-white/5'
                              }`}
                            >
                              <span className={`font-mono font-medium ${isLight ? 'text-slate-700' : 'text-slate-300'}`}>
                                PMID {rs.pmid}
                              </span>
                              <div className="flex items-center gap-1.5 font-mono">
                                <span className={isLight ? 'text-slate-400' : 'text-slate-500'}>#{rs.initial_rank}</span>
                                <ArrowRight className="w-3 h-3 text-slate-400" />
                                <span className={`font-bold ${isLight ? 'text-slate-800' : 'text-slate-100'}`}>#{rs.reranked_rank}</span>
                                <span className={`text-[11px] font-semibold px-1.5 py-0.5 rounded ${
                                  rs.rank_delta > 0
                                    ? isLight ? 'bg-emerald-100 text-emerald-700' : 'bg-emerald-500/20 text-emerald-300'
                                    : rs.rank_delta < 0
                                    ? isLight ? 'bg-rose-100 text-rose-700' : 'bg-rose-500/20 text-rose-300'
                                    : isLight ? 'bg-slate-200 text-slate-600' : 'bg-slate-700 text-slate-300'
                                }`}>
                                  {rs.rank_delta > 0 ? `+${rs.rank_delta}` : rs.rank_delta}
                                </span>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className={`text-xs py-1 ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>
                          Reranker bypassed — direct parametric answer.
                        </p>
                      )}
                    </div>
                  )}
                </div>

                {/* Latency Waterfall */}
                <div className="glass-panel rounded-xl p-4">
                  <div className="text-[11px] font-bold text-emerald-600 uppercase tracking-wider mb-3">
                    Latency Waterfall
                  </div>
                  <div className="space-y-2">
                    {Object.entries(result.latency_waterfall).map(([stage, ms]) => (
                      <div key={stage} className="text-xs">
                        <div className={`flex justify-between mb-0.5 font-mono ${isLight ? 'text-slate-600' : 'text-slate-400'}`}>
                          <span>{stage}</span>
                          <span className="font-semibold">{ms} ms</span>
                        </div>
                        <div className={`w-full rounded-full h-1 overflow-hidden ${isLight ? 'bg-slate-100' : 'bg-black/30'}`}>
                          <div
                            className="bg-gradient-to-r from-indigo-500 to-emerald-500 h-full rounded-full"
                            style={{ width: `${Math.min(100, Math.max(4, (ms / 1500) * 100))}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: BENCHMARK */}
        {activeTab === 'benchmark' && benchmarkResult && (
          <div className="mt-5 space-y-5">
            <div className="text-center max-w-xl mx-auto">
              <h2 className="text-xl font-extrabold text-gradient mb-1.5">3-Way Comparative Benchmark</h2>
              <p className={`text-xs leading-relaxed mb-3 ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>
                Same clinical query across <strong>No-RAG</strong>, <strong>Fixed-RAG</strong>, and <strong>MedVerify (Adaptive)</strong>.
              </p>
              <button
                onClick={() => handleRunBenchmark(query)}
                disabled={benchLoading}
                className={`inline-flex items-center gap-2 px-4 py-1.5 rounded-lg text-xs font-semibold transition-all border disabled:opacity-50 ${
                  isLight
                    ? 'bg-indigo-50 hover:bg-indigo-100 border-indigo-200 text-indigo-700'
                    : 'bg-indigo-600/30 hover:bg-indigo-600/50 border-indigo-500/40 text-indigo-200'
                }`}
              >
                <RefreshCw className={`w-3 h-3 ${benchLoading ? 'animate-spin' : ''}`} />
                {benchLoading ? 'Running 3-Way Benchmark…' : 'Re-run on current query'}
              </button>
            </div>

            {benchLoading && (
              <div className={`p-3 rounded-lg border text-center text-xs flex items-center justify-center gap-2 ${
                isLight ? 'bg-indigo-50 border-indigo-200 text-indigo-700' : 'bg-indigo-500/10 border-indigo-500/30 text-indigo-300'
              }`}>
                <span className="w-3.5 h-3.5 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
                <span>Running concurrent 3-way evaluation (No-RAG vs Fixed-RAG vs MedVerify)…</span>
              </div>
            )}

            {/* 3 Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* No-RAG */}
              <div className="glass-panel rounded-xl p-4 border-t-4 border-slate-300">
                <div className={`text-xs font-bold uppercase mb-2.5 ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>
                  No-RAG (Parametric)
                </div>
                <div className="space-y-1.5 text-xs font-mono mb-3">
                  {[
                    ['Faithfulness', <span className="text-rose-600 font-bold">{Math.round(benchmarkResult.no_rag.faithfulness * 100)}%</span>],
                    ['Hallucinations', benchmarkResult.no_rag.hallucinations_detected],
                    ['Tokens', benchmarkResult.no_rag.total_tokens],
                    ['Latency', `${benchmarkResult.no_rag.latency_s}s`],
                    ['Retrieved', '0 passages'],
                  ].map(([label, value]) => (
                    <div key={label} className={`flex justify-between py-1 border-b ${isLight ? 'border-slate-100 text-slate-500' : 'border-white/5 text-slate-400'}`}>
                      <span>{label}</span>
                      <span className={isLight ? 'text-slate-800' : 'text-slate-200'}>{value}</span>
                    </div>
                  ))}
                </div>
                <div className={`p-2.5 rounded-lg border text-[11px] max-h-28 overflow-y-auto leading-relaxed ${
                  isLight ? 'bg-slate-50 border-slate-200 text-slate-600' : 'bg-black/30 border-white/5 text-slate-400'
                }`}>
                  {benchmarkResult.no_rag.answer}
                </div>
              </div>

              {/* Fixed-RAG */}
              <div className="glass-panel rounded-xl p-4 border-t-4 border-amber-400">
                <div className="text-xs font-bold uppercase text-amber-600 mb-2.5">Fixed-RAG (Naive Top-5)</div>
                <div className="space-y-1.5 text-xs font-mono mb-3">
                  {[
                    ['Faithfulness', <span className="text-amber-600 font-bold">{Math.round(benchmarkResult.fixed_rag.faithfulness * 100)}%</span>],
                    ['Hallucinations', benchmarkResult.fixed_rag.hallucinations_detected],
                    ['Tokens', <span className="text-rose-600 font-bold">{benchmarkResult.fixed_rag.total_tokens} (highest)</span>],
                    ['Latency', `${benchmarkResult.fixed_rag.latency_s}s`],
                    ['Retrieved', `${benchmarkResult.fixed_rag.retrieved_passages} passages (blind)`],
                  ].map(([label, value]) => (
                    <div key={label} className={`flex justify-between py-1 border-b ${isLight ? 'border-slate-100 text-slate-500' : 'border-white/5 text-slate-400'}`}>
                      <span>{label}</span>
                      <span className={isLight ? 'text-slate-800' : 'text-slate-200'}>{value}</span>
                    </div>
                  ))}
                </div>
                <div className={`p-2.5 rounded-lg border text-[11px] max-h-28 overflow-y-auto leading-relaxed ${
                  isLight ? 'bg-slate-50 border-slate-200 text-slate-600' : 'bg-black/30 border-white/5 text-slate-400'
                }`}>
                  {benchmarkResult.fixed_rag.answer}
                </div>
              </div>

              {/* MedVerify */}
              <div className="glass-panel rounded-xl p-4 border-t-4 border-emerald-500">
                <div className="text-xs font-bold uppercase text-emerald-600 mb-2.5 flex items-center justify-between">
                  <span>MedVerify (Adaptive)</span>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-semibold ${isLight ? 'bg-emerald-100 text-emerald-800' : 'bg-emerald-500/20 text-emerald-300'}`}>
                    🏆 Best
                  </span>
                </div>
                <div className="space-y-1.5 text-xs font-mono mb-3">
                  {[
                    ['Faithfulness', <span className="text-emerald-600 font-bold">{Math.round(benchmarkResult.medverify.faithfulness * 100)}%</span>],
                    ['Hallucinations', <span className="text-emerald-600 font-bold">{benchmarkResult.medverify.hallucinations_detected} (shielded)</span>],
                    ['Tokens', <span className="text-indigo-600 font-bold">{benchmarkResult.medverify.total_tokens} (saved {benchmarkResult.medverify.tokens_saved_pct}%)</span>],
                    ['Latency', `${benchmarkResult.medverify.latency_s}s`],
                    ['Retrieved', `${benchmarkResult.medverify.retrieved_passages} passages (pruned)`],
                  ].map(([label, value]) => (
                    <div key={label} className={`flex justify-between py-1 border-b ${isLight ? 'border-slate-100 text-slate-500' : 'border-white/5 text-slate-400'}`}>
                      <span>{label}</span>
                      <span className={isLight ? 'text-slate-800' : 'text-slate-200'}>{value}</span>
                    </div>
                  ))}
                </div>
                <div className={`p-2.5 rounded-lg border text-[11px] max-h-28 overflow-y-auto leading-relaxed ${
                  isLight ? 'bg-slate-50 border-slate-200 text-slate-600' : 'bg-black/30 border-white/5 text-slate-400'
                }`}>
                  {benchmarkResult.medverify.answer}
                </div>
              </div>
            </div>

            {/* Summary Table */}
            <div className="glass-panel rounded-xl p-5">
              <h3 className={`text-xs font-bold uppercase tracking-wider mb-3 flex items-center gap-2 ${isLight ? 'text-slate-800' : 'text-slate-200'}`}>
                <BarChart3 className="w-3.5 h-3.5 text-indigo-500" />
                Consolidated Scorecard
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-xs font-mono">
                  <thead>
                    <tr className={`border-b text-left ${isLight ? 'border-slate-200 text-slate-500' : 'border-white/10 text-slate-400'}`}>
                      <th className="py-2 px-3">Metric</th>
                      <th className="py-2 px-3">No-RAG</th>
                      <th className="py-2 px-3">Fixed-RAG</th>
                      <th className="py-2 px-3 text-emerald-600">MedVerify</th>
                    </tr>
                  </thead>
                  <tbody className={`divide-y ${isLight ? 'divide-slate-100' : 'divide-white/5'}`}>
                    <tr>
                      <td className={`py-2 px-3 font-sans font-semibold ${isLight ? 'text-slate-800' : 'text-slate-300'}`}>Faithfulness (↑)</td>
                      <td className="py-2 px-3 text-rose-600">{Math.round(benchmarkResult.no_rag.faithfulness * 100)}%</td>
                      <td className="py-2 px-3 text-amber-600">{Math.round(benchmarkResult.fixed_rag.faithfulness * 100)}%</td>
                      <td className="py-2 px-3 text-emerald-600 font-bold">{Math.round(benchmarkResult.medverify.faithfulness * 100)}%</td>
                    </tr>
                    <tr>
                      <td className={`py-2 px-3 font-sans font-semibold ${isLight ? 'text-slate-800' : 'text-slate-300'}`}>Hallucinations flagged</td>
                      <td className="py-2 px-3">{benchmarkResult.no_rag.hallucinations_detected}</td>
                      <td className="py-2 px-3">{benchmarkResult.fixed_rag.hallucinations_detected}</td>
                      <td className="py-2 px-3 text-emerald-600 font-bold">{benchmarkResult.medverify.hallucinations_detected}</td>
                    </tr>
                    <tr>
                      <td className={`py-2 px-3 font-sans font-semibold ${isLight ? 'text-slate-800' : 'text-slate-300'}`}>Tokens consumed (↓)</td>
                      <td className="py-2 px-3">{benchmarkResult.no_rag.total_tokens}</td>
                      <td className="py-2 px-3 text-rose-600">{benchmarkResult.fixed_rag.total_tokens}</td>
                      <td className="py-2 px-3 text-indigo-600 font-bold">{benchmarkResult.medverify.total_tokens}</td>
                    </tr>
                    <tr>
                      <td className={`py-2 px-3 font-sans font-semibold ${isLight ? 'text-slate-800' : 'text-slate-300'}`}>End-to-end latency</td>
                      <td className="py-2 px-3">{benchmarkResult.no_rag.latency_s}s</td>
                      <td className="py-2 px-3">{benchmarkResult.fixed_rag.latency_s}s</td>
                      <td className={`py-2 px-3 ${isLight ? 'text-slate-700' : 'text-slate-200'}`}>{benchmarkResult.medverify.latency_s}s</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
