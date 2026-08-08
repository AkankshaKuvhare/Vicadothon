import React from 'react';

export default function FeedbackDashboard({ feedback, candidateName, onReset }) {
  if (!feedback) return null;
  const { summary, strengths = [], gaps = [], next = [] } = feedback;

  const handleDownload = () => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(feedback, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `PrepPal_Feedback_${candidateName.replace(/\s+/g, '_')}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  return (
    <div className="flex-1 flex flex-col p-8 overflow-y-auto max-w-4xl mx-auto w-full text-slate-200 animate-fade-in">
      
      {/* Dashboard Header */}
      <div className="text-center mb-8">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-bold uppercase tracking-wider mb-3">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          Evaluation Complete
        </div>
        <h2 className="text-3xl font-extrabold text-slate-100 tracking-tight">
          Technical Assessment Report
        </h2>
        <p className="text-slate-400 text-sm mt-1">
          Structured review of curriculum mastery and learning style diagnostics for <span className="font-semibold text-slate-300">{candidateName}</span>
        </p>
      </div>

      {/* 1. Summary Card */}
      <div className="backdrop-blur-xl bg-slate-900/40 border border-slate-800 rounded-2xl p-6 mb-6 shadow-xl relative overflow-hidden">
        <div className="absolute top-0 left-0 w-2 h-full bg-gradient-to-b from-blue-500 to-indigo-500" />
        <h3 className="text-lg font-bold text-slate-100 mb-3 flex items-center gap-2">
          <span className="text-blue-400">📊</span> Executive Summary
        </h3>
        <p className="text-slate-300 text-sm leading-relaxed font-medium">
          {summary}
        </p>
      </div>

      {/* 2. Strengths and Gaps Split Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        
        {/* Strengths Card */}
        <div className="backdrop-blur-xl bg-slate-900/40 border border-slate-800 rounded-2xl p-6 shadow-lg relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-1 bg-emerald-500" />
          <h3 className="text-base font-bold text-slate-100 mb-4 flex items-center gap-2">
            <span className="text-emerald-400">✓</span> Technical Strengths
          </h3>
          <ul className="space-y-3">
            {strengths.map((str, idx) => (
              <li key={idx} className="flex gap-3 text-sm text-slate-300 font-medium">
                <span className="text-emerald-500 text-base">✦</span>
                <span>{str}</span>
              </li>
            ))}
            {strengths.length === 0 && (
              <li className="text-slate-500 text-sm italic">No specific strengths logged.</li>
            )}
          </ul>
        </div>

        {/* Gaps / Growth Areas Card */}
        <div className="backdrop-blur-xl bg-slate-900/40 border border-slate-800 rounded-2xl p-6 shadow-lg relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-1 bg-amber-500" />
          <h3 className="text-base font-bold text-slate-100 mb-4 flex items-center gap-2">
            <span className="text-amber-400">⚠</span> Conceptual Gaps
          </h3>
          <ul className="space-y-3">
            {gaps.map((gap, idx) => (
              <li key={idx} className="flex gap-3 text-sm text-slate-300 font-medium">
                <span className="text-amber-500 text-base">✦</span>
                <span>{gap}</span>
              </li>
            ))}
            {gaps.length === 0 && (
              <li className="text-slate-500 text-sm italic">No skill gaps identified.</li>
            )}
          </ul>
        </div>
      </div>

      {/* 3. Action Plan / Next Steps */}
      <div className="backdrop-blur-xl bg-slate-900/40 border border-slate-800 rounded-2xl p-6 mb-8 shadow-xl relative overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-1 bg-indigo-500" />
        <h3 className="text-lg font-bold text-slate-100 mb-4 flex items-center gap-2">
          <span className="text-indigo-400">🚀</span> Actionable Learning Path
        </h3>
        <div className="space-y-3">
          {next.map((step, idx) => (
            <div key={idx} className="flex items-start gap-3 bg-slate-950/40 border border-slate-800/50 rounded-xl p-3.5 hover:bg-slate-950/80 transition-colors">
              <div className="w-5 h-5 rounded-md bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-bold flex items-center justify-center mt-0.5">
                {idx + 1}
              </div>
              <span className="text-sm text-slate-300 font-medium leading-relaxed">
                {step}
              </span>
            </div>
          ))}
          {next.length === 0 && (
            <p className="text-slate-500 text-sm italic">No action steps suggested.</p>
          )}
        </div>
      </div>

      {/* Footer / Download & Reset Buttons */}
      <div className="flex justify-center gap-4 pb-8 flex-wrap">
        <button
          onClick={handleDownload}
          className="px-6 py-3 rounded-xl bg-blue-600 hover:bg-blue-500 border border-blue-500/20 text-white font-semibold transition-all duration-300 shadow-md hover:shadow-lg cursor-pointer text-sm"
        >
          Download Feedback (JSON)
        </button>
        <button
          onClick={onReset}
          className="px-6 py-3 rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-200 hover:text-white font-semibold transition-all duration-300 shadow-md hover:bg-slate-800 hover:shadow-lg cursor-pointer text-sm"
        >
          Start New Interview
        </button>
      </div>

    </div>
  );
}
