import React from 'react';

export default function CandidateSelector({ candidates, onSelectCandidate }) {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center justify-center p-8">
      <div className="max-w-6xl w-full text-center mb-12">
        <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight bg-gradient-to-r from-blue-400 via-indigo-400 to-purple-400 bg-clip-text text-transparent drop-shadow-md">
          PrepPal Interview Cockpit
        </h1>
        <p className="mt-4 text-lg text-slate-400 max-w-2xl mx-auto font-medium">
          Select a candidate profile from the cohort. PrepPal will analyze their 31-day curriculum logs to generate a personalized technical assessment plan.
        </p>
      </div>

      <div className="max-w-6xl w-full grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {candidates.map((candidate) => {
          const { member, signals } = candidate;
          const initial = member.name ? member.name[0] : '?';
          
          return (
            <div
              key={member.id}
              onClick={() => onSelectCandidate(candidate)}
              className="group relative backdrop-blur-xl bg-slate-900/50 border border-slate-800 hover:border-blue-500/50 hover:bg-slate-900/80 transition-all duration-300 rounded-2xl p-6 cursor-pointer flex flex-col justify-between shadow-lg hover:shadow-blue-500/5"
            >
              {/* Decorative Accent Glow */}
              <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 via-transparent to-purple-500/5 opacity-0 group-hover:opacity-100 transition-opacity rounded-2xl pointer-events-none" />

              <div>
                {/* Header Avatar and Basic Info */}
                <div className="flex items-center gap-4 mb-4">
                  <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-xl font-bold shadow-md shadow-blue-500/10">
                    {initial}
                  </div>
                  <div>
                    <h3 className="text-xl font-semibold text-slate-100 group-hover:text-blue-400 transition-colors">
                      {member.name}
                    </h3>
                    <p className="text-sm text-slate-400 font-medium">{member.jobRole}</p>
                  </div>
                </div>

                {/* Subtitle Details */}
                <div className="grid grid-cols-2 gap-2 text-xs text-slate-400 mb-6 bg-slate-950/40 rounded-lg p-3 border border-slate-800/50">
                  <div>
                    <span className="block text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Experience</span>
                    <span className="font-medium text-slate-300">{member.yearsExperience} Years</span>
                  </div>
                  <div>
                    <span className="block text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Education</span>
                    <span className="font-medium text-slate-300 truncate block" title={member.education}>
                      {member.education || 'N/A'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Performance Indicators */}
              <div className="border-t border-slate-800/80 pt-4 mt-auto">
                <div className="flex justify-between items-center text-xs text-slate-400 mb-2">
                  <span>Missions Completed</span>
                  <span className="font-semibold text-slate-200">{signals.missionsCompleted} / 31</span>
                </div>
                {/* Visual mini-bar */}
                <div className="w-full bg-slate-950 rounded-full h-1.5 overflow-hidden border border-slate-800">
                  <div
                    className="bg-gradient-to-r from-blue-500 to-indigo-500 h-full rounded-full transition-all"
                    style={{ width: `${(signals.missionsCompleted / 31) * 100}%` }}
                  />
                </div>

                <div className="flex gap-4 mt-4 justify-between text-[11px] text-slate-400 font-medium">
                  <span className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-emerald-500" />
                    {signals.missionsFirstTry} First Try
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-indigo-500" />
                    {signals.commitDays} Commit Days
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
