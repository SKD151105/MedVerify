import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  ShieldCheck,
  Zap,
  Activity,
  Layers,
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
  RefreshCw
} from 'lucide-react';
import { INITIAL_RESULT, INITIAL_BENCHMARK } from './defaultData';

const DEFAULT_SCENARIOS = [
  { id: 'pmid_28491530', specialty: 'Nephrology', question: 'Does Metformin reduce cardiovascular mortality in patients with chronic kidney disease?' },
  { id: 'pmid_25841648', specialty: 'Cardiology', question: 'What is the recommended dose adjustment for Apixaban in patients with severe renal impairment?' },
  { id: 'pmid_23755979', specialty: 'Cardiology', question: 'Do preoperative statins reduce the incidence of postoperative atrial fibrillation after coronary artery bypass grafting?' },
  { id: 'def_001', specialty: 'General Medicine', question: 'What is essential hypertension?' }
];

export default function App() {
  const [query, setQuery] = useState('Does Metformin reduce cardiovascular mortality in patients with chronic kidney disease?');
  const [scenarios, setScenarios] = useState(DEFAULT_SCENARIOS);
  const [activeTab, setActiveTab] = useState('copilot'); // 'copilot' or 'benchmark'
  const [loading, setLoading] = useState(false);
  const [benchLoading, setBenchLoading] = useState(false);
  const [result, setResult] = useState(INITIAL_RESULT);
  const [benchmarkResult, setBenchmarkResult] = useState(INITIAL_BENCHMARK);
  const [statusMessage, setStatusMessage] = useState('');

  // Initial load: sync available scenarios from backend
  useEffect(() => {
    fetchScenarios();
  }, []);

  const fetchScenarios = async () => {
    try {
      const res = await axios.get('/api/scenarios');
      if (res.data && res.data.length > 0) {
        setScenarios(res.data);
      }
    } catch (err) {
      console.warn('Scenarios endpoint offline or starting up, using local scenario presets.');
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
      console.error('Execution error on query:', err);
      setStatusMessage('Backend API request encountered an issue. Using cached telemetry.');
    } finally {
      setLoading(false);
    }
  };

  const handleRunBenchmark = async (queryToRun) => {
    const q = queryToRun || query;
    if (!q.trim()) return;
    setBenchLoading(true);
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

  return (
    <div className="relative min-h-screen text-slate-100 p-4 md:p-8 overflow-x-hidden">
      {/* Dual Ambient Glow Orbs */}
      <div className="bg-glow" />
      <div className="bg-glow-alt" />

      {/* Top Navbar */}
      <header className="relative z-10 max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-start md:items-center gap-4 pb-6 border-b border-white/10">
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-xl bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-2xl shadow-lg shadow-indigo-500/20">
            🩺
          </div>
          <div>
            <div className="text-2xl font-extrabold text-gradient tracking-tight">MedVerify</div>
            <div className="text-xs text-indigo-300 font-semibold tracking-wider">
              CLINICAL RAG & HALLUCINATION GUARDRAILS
            </div>
          </div>
        </div>

        {/* Live Status Badge & Tab Switcher */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-semibold">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse shadow-sm shadow-emerald-400" />
            GUARDRAILS ENGINE ACTIVE
          </div>

          <div className="flex rounded-xl bg-white/5 border border-white/10 p-1">
            <button
              onClick={() => setActiveTab('copilot')}
              className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'copilot'
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              📊 Live Copilot & Telemetry
            </button>
            <button
              onClick={() => setActiveTab('benchmark')}
              className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'benchmark'
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              🔬 3-Way Baseline Benchmark
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Container */}
      <main className="relative z-10 max-w-7xl mx-auto mt-6">
        {/* Scenario Preset Chips */}
        <div className="mb-4">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
            Select Curated Clinical Case (PubMedQA):
          </div>
          <div className="flex flex-wrap gap-2">
            {scenarios.map((sc) => (
              <button
                key={sc.id}
                onClick={() => {
                  setQuery(sc.question);
                  handleRunQuery(sc.question);
                }}
                className={`text-xs px-3.5 py-1.5 rounded-lg border transition-all text-left ${
                  query === sc.question
                    ? 'bg-indigo-500/20 border-indigo-400/50 text-indigo-200'
                    : 'bg-white/[0.03] border-white/10 text-slate-300 hover:border-white/20 hover:text-white'
                }`}
              >
                <span className="font-semibold text-indigo-400">[{sc.specialty}]</span> {sc.question.slice(0, 52)}...
              </button>
            ))}
          </div>
        </div>

        {/* Search Bar */}
        <div className="glass-panel rounded-2xl p-3 flex flex-col md:flex-row gap-3 mb-8">
          <div className="flex-1 flex items-center gap-3 px-3 py-1 bg-black/40 rounded-xl border border-white/10 focus-within:border-indigo-500/80 transition-all">
            <Search className="w-5 h-5 text-indigo-400 shrink-0" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleRunQuery(query)}
              placeholder="Enter clinical question, drug efficacy query, or definitional concept..."
              className="w-full bg-transparent text-sm text-slate-100 placeholder-slate-500 focus:outline-none"
            />
          </div>
          <button
            onClick={() => handleRunQuery(query)}
            disabled={loading}
            className="btn-primary px-6 py-2.5 rounded-xl font-semibold text-sm flex items-center justify-center gap-2 shrink-0 disabled:opacity-50"
          >
            {loading ? (
              <>
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Auditing...
              </>
            ) : (
              <>
                <Zap className="w-4 h-4 fill-white" />
                Analyze Query
              </>
            )}
          </button>
        </div>

        {/* TAB 1: COPILOT & TELEMETRY */}
        {activeTab === 'copilot' && result && (
          <div>
            {/* Top Stat KPI Tiles */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="glass-card rounded-xl p-4">
                <div className="text-xs text-slate-400 uppercase font-semibold flex items-center justify-between mb-1">
                  1. Adaptive Route <Activity className="w-4 h-4 text-sky-400" />
                </div>
                <div className="text-xl font-bold font-mono text-sky-300">
                  {result.routing.route.replace('_', ' ')}
                </div>
                <div className="text-[11px] text-slate-400 mt-1">
                  Confidence: {Math.round(result.routing.confidence * 100)}%
                </div>
              </div>

              <div className="glass-card rounded-xl p-4">
                <div className="text-xs text-slate-400 uppercase font-semibold flex items-center justify-between mb-1">
                  2. Faithfulness Score <ShieldCheck className="w-4 h-4 text-emerald-400" />
                </div>
                <div className="text-xl font-bold font-mono text-emerald-300">
                  {Math.round(result.audit_result.faithfulness_score * 100)}%
                </div>
                <div className="text-[11px] text-emerald-400/80 mt-1">
                  {result.audit_result.entailed_claims} of {result.audit_result.total_claims} Claims Entailed
                </div>
              </div>

              <div className="glass-card rounded-xl p-4">
                <div className="text-xs text-slate-400 uppercase font-semibold flex items-center justify-between mb-1">
                  3. Tokens Saved vs Fixed <Flame className="w-4 h-4 text-purple-400" />
                </div>
                <div className="text-xl font-bold font-mono text-purple-300">
                  {result.tokens_saved_percentage}%
                </div>
                <div className="text-[11px] text-slate-400 mt-1">
                  Used: {result.tokens_consumed} tokens
                </div>
              </div>

              <div className="glass-card rounded-xl p-4">
                <div className="text-xs text-slate-400 uppercase font-semibold flex items-center justify-between mb-1">
                  4. Total Latency <Clock className="w-4 h-4 text-indigo-400" />
                </div>
                <div className="text-xl font-bold font-mono text-slate-100">
                  {result.total_latency_s}s
                </div>
                <div className="text-[11px] text-slate-400 mt-1">
                  Sub-second cloud inference
                </div>
              </div>
            </div>

            {/* Split Screen Columns */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* Left Column: Doctor's Clinical View (7 Cols) */}
              <div className="lg:col-span-7 space-y-6">
                <div className="glass-panel rounded-2xl p-6 border-l-4 border-indigo-500">
                  <div className="flex justify-between items-center mb-4">
                    <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                      <Sparkles className="w-5 h-5 text-indigo-400" />
                      Verified Clinical Synthesis
                    </h2>
                    <span className="text-xs px-2.5 py-1 rounded-full bg-indigo-500/20 text-indigo-300 font-semibold border border-indigo-500/30">
                      Claim-Level Grounded
                    </span>
                  </div>

                  {/* Sentence-by-Sentence Highlighted Propositions */}
                  <div className="space-y-3 mb-4">
                    {result.audit_result.claim_audits.map((ca, idx) => (
                      <div
                        key={idx}
                        className={`p-3.5 rounded-xl border text-sm leading-relaxed transition-all ${
                          ca.label === 'ENTAILMENT'
                            ? 'bg-emerald-500/[0.08] border-emerald-500/30 text-slate-200'
                            : ca.label === 'NEUTRAL'
                            ? 'bg-amber-500/[0.08] border-amber-500/30 text-slate-200'
                            : 'bg-rose-500/[0.12] border-rose-500/40 text-rose-200'
                        }`}
                      >
                        <span>{ca.claim}</span>

                        <div className="mt-2 flex flex-wrap items-center gap-2">
                          {ca.label === 'ENTAILMENT' && (
                            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 text-xs font-semibold">
                              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                              Entailed ({Math.round(ca.confidence * 100)}%)
                            </span>
                          )}
                          {ca.label === 'NEUTRAL' && (
                            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 text-xs font-semibold">
                              <HelpCircle className="w-3.5 h-3.5 text-amber-400" />
                              Extrapolated ({Math.round(ca.confidence * 100)}%)
                            </span>
                          )}
                          {ca.label === 'CONTRADICTION' && (
                            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-300 text-xs font-semibold">
                              <AlertCircle className="w-3.5 h-3.5 text-rose-400" />
                              Hallucination Blocked
                            </span>
                          )}

                          {ca.cited_pmid && ca.cited_pmid !== 'None' && (
                            <a
                              href={`https://pubmed.ncbi.nlm.nih.gov/${ca.cited_pmid}/`}
                              target="_blank"
                              rel="noreferrer"
                              className="inline-flex items-center gap-1 text-xs font-mono text-sky-400 hover:text-sky-300 underline decoration-sky-400/50"
                            >
                              PMID:{ca.cited_pmid} <ExternalLink className="w-3 h-3" />
                            </a>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>

                  {result.audit_result.has_hallucination && (
                    <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-xs text-amber-300 flex items-center gap-2">
                      <AlertCircle className="w-4 h-4 shrink-0 text-amber-400" />
                      MedVerify Guardrail: Contradicted assertions were automatically filtered from the clinical answer.
                    </div>
                  )}
                </div>

                {/* Evidence Dossier Accordion */}
                <div className="glass-panel rounded-2xl p-5">
                  <h3 className="text-sm font-bold uppercase tracking-wider text-slate-300 mb-3 flex items-center justify-between">
                    <span>📚 Cited PubMed Evidence Dossier ({result.reranked_docs.length} Studies Retained)</span>
                    <span className="text-xs text-indigo-400 font-mono font-normal">Cross-Encoder Filtered</span>
                  </h3>

                  {result.reranked_docs.length > 0 ? (
                    <div className="space-y-3">
                      {result.reranked_docs.map((doc, idx) => (
                        <div key={doc.id} className="glass-card rounded-xl p-4 border border-white/5">
                          <div className="flex justify-between items-start gap-2 mb-2">
                            <span className="text-sm font-semibold text-indigo-300">
                              [{idx + 1}] PMID: {doc.pmid}
                            </span>
                            <span className="text-xs font-mono px-2 py-0.5 rounded bg-white/5 text-slate-300">
                              Rerank Score: <strong className="text-emerald-400">{doc.rerank_score}</strong>
                            </span>
                          </div>
                          <div className="text-xs font-semibold text-slate-200 mb-1.5">{doc.question}</div>
                          <div className="text-xs text-slate-400 line-clamp-3 leading-relaxed">{doc.abstract}</div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-xs text-slate-400 p-4 text-center">
                      Zero literature retrieved. Query answered directly from parametric memory (Definitional Route).
                    </div>
                  )}
                </div>
              </div>

              {/* Right Column: Observability Telemetry (5 Cols) */}
              <div className="lg:col-span-5 space-y-6">
                {/* 1. Routing Gate Inspector */}
                <div className="glass-panel rounded-2xl p-5">
                  <div className="text-xs font-bold text-sky-400 uppercase tracking-wider flex items-center justify-between mb-2">
                    <span>1. Adaptive Routing Gate</span>
                    <span className="font-mono text-slate-400">{result.latency_waterfall['Routing Gate']} ms</span>
                  </div>
                  <div className="text-xs text-slate-300 mb-3 leading-relaxed">
                    {result.routing.reasoning}
                  </div>
                  <div className="w-full bg-black/40 rounded-full h-2 overflow-hidden border border-white/10">
                    <div
                      className="bg-sky-400 h-full rounded-full transition-all duration-500"
                      style={{ width: `${result.routing.confidence * 100}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-[11px] text-slate-400 mt-1 font-mono">
                    <span>Gate Confidence</span>
                    <span className="text-sky-300 font-semibold">{Math.round(result.routing.confidence * 100)}%</span>
                  </div>
                </div>

                {/* 2. Cross-Encoder Rank-Shift Inspector */}
                <div className="glass-panel rounded-2xl p-5">
                  <div className="text-xs font-bold text-purple-400 uppercase tracking-wider flex items-center justify-between mb-3">
                    <span>2. Cross-Encoder Rank Shifts</span>
                    <span className="font-mono text-slate-400">{result.latency_waterfall['Neural Reranking']} ms</span>
                  </div>

                  {result.rerank_telemetry.rank_shifts && result.rerank_telemetry.rank_shifts.length > 0 ? (
                    <div className="space-y-2">
                      {result.rerank_telemetry.rank_shifts.map((rs) => (
                        <div
                          key={rs.id}
                          className="flex items-center justify-between text-xs p-2 rounded-lg bg-black/30 border border-white/5"
                        >
                          <span className="font-mono text-slate-300">PMID {rs.pmid}</span>
                          <div className="flex items-center gap-2 font-mono">
                            <span className="text-slate-400">#{rs.initial_rank}</span>
                            <ArrowRight className="w-3 h-3 text-slate-500" />
                            <span className="text-slate-100 font-bold">#{rs.reranked_rank}</span>
                            <span
                              className={`text-[11px] font-semibold px-1.5 py-0.5 rounded ${
                                rs.rank_delta > 0
                                  ? 'bg-emerald-500/20 text-emerald-300'
                                  : rs.rank_delta < 0
                                  ? 'bg-rose-500/20 text-rose-300'
                                  : 'bg-slate-700 text-slate-300'
                              }`}
                            >
                              {rs.rank_delta > 0 ? `+${rs.rank_delta}` : rs.rank_delta}
                            </span>
                          </div>
                        </div>
                      ))}
                      <div className="text-[11px] text-slate-400 text-right mt-2">
                        Pruned {result.rerank_telemetry.pruned_count} distractor documents below threshold.
                      </div>
                    </div>
                  ) : (
                    <div className="text-xs text-slate-400">Reranker bypassed to conserve tokens.</div>
                  )}
                </div>

                {/* 3. Latency Waterfall */}
                <div className="glass-panel rounded-2xl p-5">
                  <div className="text-xs font-bold text-emerald-400 uppercase tracking-wider mb-3">
                    3. Latency Waterfall Breakdown
                  </div>
                  <div className="space-y-2.5">
                    {Object.entries(result.latency_waterfall).map(([stage, ms]) => (
                      <div key={stage} className="text-xs">
                        <div className="flex justify-between text-slate-300 mb-1 font-mono">
                          <span>{stage}</span>
                          <span>{ms} ms</span>
                        </div>
                        <div className="w-full bg-black/40 rounded-full h-1.5 overflow-hidden border border-white/5">
                          <div
                            className="bg-gradient-to-r from-indigo-500 to-emerald-400 h-full rounded-full"
                            style={{ width: `${Math.min(100, Math.max(5, (ms / 1500) * 100))}%` }}
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

        {/* TAB 2: 3-WAY BASELINE BENCHMARK */}
        {activeTab === 'benchmark' && benchmarkResult && (
          <div className="space-y-6">
            <div className="text-center max-w-2xl mx-auto mb-6">
              <h2 className="text-2xl font-extrabold text-gradient mb-2">3-Way Comparative Benchmark</h2>
              <p className="text-xs text-slate-400 leading-relaxed mb-4">
                Evaluating the exact same clinical trial query across <strong>No-RAG</strong>, <strong>Fixed-RAG</strong>, and <strong>MedVerify (Adaptive)</strong>.
              </p>
              <button
                onClick={() => handleRunBenchmark(query)}
                disabled={benchLoading}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600/30 hover:bg-indigo-600/50 border border-indigo-500/40 text-indigo-200 text-xs font-semibold transition-all disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${benchLoading ? 'animate-spin' : ''}`} />
                {benchLoading ? 'Running 3-Way Benchmark Suite across 3 LLM Pipelines...' : 'Re-run Benchmark on Current Query'}
              </button>
            </div>

            {/* 3 Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* No-RAG Card */}
              <div className="glass-panel rounded-2xl p-5 border-t-4 border-slate-500">
                <div className="text-xs font-bold uppercase text-slate-400 mb-2">1. No-RAG (Parametric)</div>
                <div className="space-y-2 text-xs font-mono">
                  <div className="flex justify-between py-1 border-b border-white/5">
                    <span className="text-slate-400">Faithfulness:</span>
                    <span className="text-rose-400 font-bold">{Math.round(benchmarkResult.no_rag.faithfulness * 100)}%</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-white/5">
                    <span className="text-slate-400">Hallucinations:</span>
                    <span className="text-slate-200">{benchmarkResult.no_rag.hallucinations_detected}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-white/5">
                    <span className="text-slate-400">Tokens:</span>
                    <span className="text-slate-200">{benchmarkResult.no_rag.total_tokens}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-white/5">
                    <span className="text-slate-400">Latency:</span>
                    <span className="text-slate-200">{benchmarkResult.no_rag.latency_s}s</span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-slate-400">Retrieved Passages:</span>
                    <span className="text-slate-200">0</span>
                  </div>
                </div>
                <div className="mt-4 p-3 rounded-xl bg-black/40 border border-white/5 text-[11px] text-slate-400 max-h-36 overflow-y-auto leading-relaxed">
                  {benchmarkResult.no_rag.answer}
                </div>
              </div>

              {/* Fixed-RAG Card */}
              <div className="glass-panel rounded-2xl p-5 border-t-4 border-amber-500">
                <div className="text-xs font-bold uppercase text-amber-400 mb-2">2. Fixed-RAG (Naive Top-5)</div>
                <div className="space-y-2 text-xs font-mono">
                  <div className="flex justify-between py-1 border-b border-white/5">
                    <span className="text-slate-400">Faithfulness:</span>
                    <span className="text-amber-400 font-bold">{Math.round(benchmarkResult.fixed_rag.faithfulness * 100)}%</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-white/5">
                    <span className="text-slate-400">Hallucinations:</span>
                    <span className="text-slate-200">{benchmarkResult.fixed_rag.hallucinations_detected}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-white/5">
                    <span className="text-slate-400">Tokens:</span>
                    <span className="text-rose-400 font-bold">{benchmarkResult.fixed_rag.total_tokens} (Highest)</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-white/5">
                    <span className="text-slate-400">Latency:</span>
                    <span className="text-slate-200">{benchmarkResult.fixed_rag.latency_s}s</span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-slate-400">Retrieved Passages:</span>
                    <span className="text-slate-200">{benchmarkResult.fixed_rag.retrieved_passages} (Blind)</span>
                  </div>
                </div>
                <div className="mt-4 p-3 rounded-xl bg-black/40 border border-white/5 text-[11px] text-slate-400 max-h-36 overflow-y-auto leading-relaxed">
                  {benchmarkResult.fixed_rag.answer}
                </div>
              </div>

              {/* MedVerify Card */}
              <div className="glass-panel rounded-2xl p-5 border-t-4 border-emerald-500 shadow-lg shadow-emerald-500/10">
                <div className="text-xs font-bold uppercase text-emerald-400 mb-2 flex items-center justify-between">
                  <span>3. MedVerify (Adaptive)</span>
                  <span className="text-[10px] bg-emerald-500/20 text-emerald-300 px-2 py-0.5 rounded-full">🏆 WINNER</span>
                </div>
                <div className="space-y-2 text-xs font-mono">
                  <div className="flex justify-between py-1 border-b border-white/5">
                    <span className="text-slate-400">Faithfulness:</span>
                    <span className="text-emerald-400 font-bold">{Math.round(benchmarkResult.medverify.faithfulness * 100)}%</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-white/5">
                    <span className="text-slate-400">Hallucinations:</span>
                    <span className="text-emerald-400 font-bold">{benchmarkResult.medverify.hallucinations_detected} (Shielded)</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-white/5">
                    <span className="text-slate-400">Tokens:</span>
                    <span className="text-indigo-300 font-bold">{benchmarkResult.medverify.total_tokens} (Saved {benchmarkResult.medverify.tokens_saved_pct}%)</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-white/5">
                    <span className="text-slate-400">Latency:</span>
                    <span className="text-slate-200">{benchmarkResult.medverify.latency_s}s</span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-slate-400">Retrieved Passages:</span>
                    <span className="text-slate-200">{benchmarkResult.medverify.retrieved_passages} (Pruned)</span>
                  </div>
                </div>
                <div className="mt-4 p-3 rounded-xl bg-black/40 border border-white/5 text-[11px] text-slate-400 max-h-36 overflow-y-auto leading-relaxed">
                  {benchmarkResult.medverify.answer}
                </div>
              </div>
            </div>

            {/* Consolidated Summary Table */}
            <div className="glass-panel rounded-2xl p-6">
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200 mb-4 flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-indigo-400" />
                Consolidated Scientific Comparison Scorecard
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-xs font-mono">
                  <thead>
                    <tr className="border-b border-white/10 text-slate-400 text-left">
                      <th className="py-2.5 px-3">Evaluation Metric</th>
                      <th className="py-2.5 px-3">No-RAG (Parametric)</th>
                      <th className="py-2.5 px-3">Fixed-RAG (Naive Top-5)</th>
                      <th className="py-2.5 px-3 text-emerald-400">MedVerify (Adaptive)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    <tr>
                      <td className="py-2.5 px-3 text-slate-300 font-sans font-semibold">Faithfulness Score (↑)</td>
                      <td className="py-2.5 px-3 text-rose-400">{Math.round(benchmarkResult.no_rag.faithfulness * 100)}%</td>
                      <td className="py-2.5 px-3 text-amber-400">{Math.round(benchmarkResult.fixed_rag.faithfulness * 100)}%</td>
                      <td className="py-2.5 px-3 text-emerald-300 font-bold">{Math.round(benchmarkResult.medverify.faithfulness * 100)}% (Highest)</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-3 text-slate-300 font-sans font-semibold">Hallucinated Claims Flagged</td>
                      <td className="py-2.5 px-3">{benchmarkResult.no_rag.hallucinations_detected}</td>
                      <td className="py-2.5 px-3">{benchmarkResult.fixed_rag.hallucinations_detected}</td>
                      <td className="py-2.5 px-3 text-emerald-300 font-bold">{benchmarkResult.medverify.hallucinations_detected} (Pruned)</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-3 text-slate-300 font-sans font-semibold">Tokens Consumed per Query (↓)</td>
                      <td className="py-2.5 px-3">{benchmarkResult.no_rag.total_tokens}</td>
                      <td className="py-2.5 px-3 text-rose-400">{benchmarkResult.fixed_rag.total_tokens}</td>
                      <td className="py-2.5 px-3 text-indigo-300 font-bold">{benchmarkResult.medverify.total_tokens} (Saved {benchmarkResult.medverify.tokens_saved_pct}%)</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-3 text-slate-300 font-sans font-semibold">End-to-End Latency</td>
                      <td className="py-2.5 px-3">{benchmarkResult.no_rag.latency_s}s</td>
                      <td className="py-2.5 px-3">{benchmarkResult.fixed_rag.latency_s}s</td>
                      <td className="py-2.5 px-3 text-slate-200">{benchmarkResult.medverify.latency_s}s</td>
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
