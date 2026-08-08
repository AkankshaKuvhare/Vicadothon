import React from 'react';

const dayTypeMap = {
  1: "FUNDAMENTALS", 2: "FUNDAMENTALS", 3: "FUNDAMENTALS", 4: "FUNDAMENTALS", 5: "FUNDAMENTALS",
  6: "SHIP_IT", 7: "FUNDAMENTALS", 8: "FUNDAMENTALS", 9: "FUNDAMENTALS", 10: "FUNDAMENTALS",
  11: "FUNDAMENTALS", 12: "FUNDAMENTALS", 13: "SHIP_IT", 14: "FUNDAMENTALS", 15: "FUNDAMENTALS",
  16: "FUNDAMENTALS", 17: "FUNDAMENTALS", 18: "FUNDAMENTALS", 19: "FUNDAMENTALS", 20: "SHIP_IT",
  21: "FUNDAMENTALS", 22: "FUNDAMENTALS", 23: "FUNDAMENTALS", 24: "FUNDAMENTALS", 25: "FUNDAMENTALS",
  26: "FUNDAMENTALS", 27: "SHIP_IT", 28: "FUNDAMENTALS", 29: "FUNDAMENTALS", 30: "FUNDAMENTALS",
  31: "CAPSTONE"
};

// Return gradient theme classes based on job role
const getAvatarGradient = (role) => {
  const roleLower = (role || "").toLowerCase();
  if (roleLower.includes("ai") || roleLower.includes("intelligence") || roleLower.includes("ml")) {
    return "from-purple-600 to-indigo-600 shadow-purple-500/10 border-purple-400/20";
  }
  if (roleLower.includes("data") || roleLower.includes("analytics")) {
    return "from-teal-600 to-emerald-600 shadow-teal-500/10 border-teal-400/20";
  }
  if (roleLower.includes("backend")) {
    return "from-rose-600 to-orange-600 shadow-rose-500/10 border-rose-400/20";
  }
  if (roleLower.includes("frontend") || roleLower.includes("web") || roleLower.includes("react")) {
    return "from-cyan-600 to-blue-600 shadow-cyan-500/10 border-cyan-400/20";
  }
  return "from-slate-600 to-indigo-600 shadow-indigo-500/10 border-indigo-400/20";
};

export default function CandidateSidebar({ candidate, interviewPlan, currentQuestionIndex }) {
  if (!candidate) return null;
  const { member, missions } = candidate;

  // Build mapping of days to candidate mission results
  const missionsMap = {};
  missions.forEach(m => {
    missionsMap[m.day] = m;
  });

  // Calculate currentDay from interview plan questions
  let currentDay = null;
  let totalQuestions = 0;
  let targetDays = [];

  if (interviewPlan) {
    totalQuestions = interviewPlan.questions?.length || 0;
    targetDays = interviewPlan.targetDays || [];
    const currentQ = interviewPlan.questions?.[currentQuestionIndex];
    if (currentQ) {
      currentDay = currentQ.day;
    }
  }

  // Get day details helper
  const getDayDetails = (dayNum) => {
    const m = missionsMap[dayNum];
    const type = dayTypeMap[dayNum] || "FUNDAMENTALS";
    
    if (!m) {
      return {
        status: "NEUTRAL",
        label: "Not Attempted",
        attempts: 0,
        type
      };
    }
    
    if (m.skipped) {
      return {
        status: "SKIPPED",
        label: "Skipped Module",
        attempts: 0,
        type
      };
    }
    
    if (!m.passed) {
      return {
        status: "FAILED",
        label: "Failed Mission",
        attempts: m.attempts,
        type
      };
    }
    
    if (m.attempts >= 3) {
      return {
        status: "STRUGGLE",
        label: "Struggled (Passed in 3+ Attempts)",
        attempts: m.attempts,
        type
      };
    }
    
    if (m.attempts === 1) {
      return {
        status: "STRENGTH",
        label: "Strength (First Try Mastery)",
        attempts: 1,
        type
      };
    }

    return {
      status: "NEUTRAL",
      label: "Completed (2 Attempts)",
      attempts: m.attempts,
      type
    };
  };

  const daysArray = Array.from({ length: 31 }, (_, i) => i + 1);

  return (
    <aside className="w-full md:w-[32%] bg-slate-900/60 backdrop-blur-xl border-r border-slate-800 p-6 flex flex-col justify-between overflow-y-auto h-full text-slate-300">
      
      {/* SECTION 1: Candidate Card */}
      <div>
        <div className="flex items-center gap-4 mb-6">
          {/* Role-Colored Avatar */}
          <div className={`w-14 h-14 rounded-full bg-gradient-to-tr ${getAvatarGradient(member.jobRole)} flex items-center justify-center text-2xl font-bold text-slate-100 shadow-lg border`}>
            {member.name ? member.name[0] : '?'}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-bold text-slate-100 leading-tight">
                {member.name}
              </h2>
              <span className={`text-[9px] px-1.5 py-0.5 rounded font-bold uppercase ${
                interviewPlan?.done ? 'bg-slate-800 text-slate-400' : 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
              }`}>
                {interviewPlan?.done ? 'COMPLETED' : 'ACTIVE'}
              </span>
            </div>
            <p className="text-sm text-slate-400 font-medium">{member.jobRole}</p>
            <p className="text-xs text-slate-500 font-semibold uppercase tracking-wider mt-0.5">
              {member.yearsExperience} yrs exp • {member.education || 'Self-Taught'}
            </p>
          </div>
        </div>

        {/* SECTION 2: Interview Session Progress */}
        {interviewPlan && (
          <div className="bg-slate-950/40 rounded-xl p-4 border border-slate-800/80 mb-6">
            <div className="flex justify-between items-center text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
              <span>Interview Progress</span>
              <span className="text-blue-400">
                {currentQuestionIndex} / {totalQuestions} Questions
              </span>
            </div>
            
            {/* Progress Bar */}
            <div className="w-full bg-slate-900 rounded-full h-2 overflow-hidden border border-slate-800">
              <div
                className="bg-gradient-to-r from-blue-500 to-indigo-500 h-full rounded-full transition-all duration-500"
                style={{ width: `${(currentQuestionIndex / totalQuestions) * 100}%` }}
              />
            </div>
            
            <div className="mt-3 flex flex-wrap gap-1.5 items-center">
              <span className="text-[10px] text-slate-500 font-bold uppercase mr-1">Targets:</span>
              {targetDays.map((dayNum) => (
                <span
                  key={dayNum}
                  className={`text-[10px] px-2 py-0.5 rounded font-bold transition-all border ${
                    dayNum === currentDay
                      ? "bg-blue-500/20 text-blue-300 border-blue-400/40 shadow shadow-blue-500/20 animate-pulse"
                      : "bg-slate-900/60 text-slate-400 border-slate-800"
                  }`}
                >
                  Day {dayNum}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* SECTION 3: 31-Day Curriculum Visualization */}
        <div>
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 flex justify-between">
            <span>Curriculum Map (31 Days)</span>
            {currentDay && <span className="text-blue-400 font-semibold animate-pulse">Day {currentDay} active</span>}
          </h3>

          <div className="grid grid-cols-5 sm:grid-cols-6 md:grid-cols-5 lg:grid-cols-7 gap-2">
            {daysArray.map((dayNum) => {
              const details = getDayDetails(dayNum);
              const isCurrent = dayNum === currentDay;
              
              let styleClasses = "";
              if (isCurrent) {
                styleClasses = "bg-blue-600/30 text-blue-200 border-blue-400 ring-2 ring-blue-500/40 shadow-lg shadow-blue-500/10 animate-pulse font-bold";
              } else {
                switch (details.status) {
                  case "STRENGTH":
                    styleClasses = "bg-emerald-950/20 text-emerald-400 border-emerald-900/50 hover:bg-emerald-900/10 hover:border-emerald-700/60";
                    break;
                  case "STRUGGLE":
                    styleClasses = "bg-rose-950/20 text-rose-400 border-rose-900/50 hover:bg-rose-900/10 hover:border-rose-700/60";
                    break;
                  case "FAILED":
                    styleClasses = "bg-red-950/30 text-red-400 border-red-900/60 hover:bg-red-900/10 hover:border-red-700/60";
                    break;
                  case "SKIPPED":
                    styleClasses = "bg-slate-950 text-slate-500 border-slate-900 hover:text-slate-400 hover:border-slate-800";
                    break;
                  default:
                    styleClasses = "bg-slate-900/30 text-slate-400 border-slate-800 hover:bg-slate-800/30";
                }
              }

              return (
                <div
                  key={dayNum}
                  className={`aspect-square flex flex-col items-center justify-center rounded-lg text-xs font-semibold transition-all border cursor-help relative group/cell ${styleClasses}`}
                >
                  <span>{dayNum}</span>
                  
                  {/* Floating Tooltip */}
                  <div className="absolute z-50 bottom-full left-1/2 transform -translate-x-1/2 mb-2 w-48 hidden group-hover/cell:block pointer-events-none">
                    <div className="bg-slate-950 border border-slate-800 rounded-lg p-2.5 shadow-2xl text-[11px] text-slate-300 font-medium">
                      <div className="font-bold text-slate-100 flex justify-between items-center mb-1">
                        <span>Day {dayNum}</span>
                        <span className="text-[9px] px-1.5 py-0.5 rounded bg-slate-900 text-slate-400 uppercase tracking-wider font-bold">
                          {details.type}
                        </span>
                      </div>
                      <div className="text-slate-400">
                        Status: <span className="font-semibold text-slate-200">{details.label}</span>
                      </div>
                      {details.attempts > 0 && (
                        <div className="text-slate-400">
                          Attempts: <span className="font-semibold text-slate-200">{details.attempts}</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* SECTION 4: Map Legend */}
      <div className="border-t border-slate-800 pt-4 mt-6">
        <h4 className="text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-2">Legend</h4>
        <div className="grid grid-cols-2 gap-2 text-[10px] font-medium text-slate-400">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded bg-emerald-950/40 border border-emerald-800/80" />
            <span>Strength (Green)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded bg-rose-950/40 border border-rose-800/80" />
            <span>Struggle (Red)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded bg-slate-950 border border-slate-900" />
            <span>Skipped (Gray)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded bg-blue-950 border border-blue-400 animate-pulse" />
            <span>Current Day (Blue)</span>
          </div>
        </div>
      </div>

    </aside>
  );
}
