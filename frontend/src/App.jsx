import React, { useState, useEffect } from 'react';
import CandidateSelector from './components/CandidateSelector';
import CandidateSidebar from './components/CandidateSidebar';
import ChatInterface from './components/ChatInterface';
import FeedbackDashboard from './components/FeedbackDashboard';
import useInterview from './hooks/useInterview';

const API_BASE = 'http://localhost:8000';

export default function App() {
  const [candidates, setCandidates] = useState([]);
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');

  // Instantiate hook logic layer
  const { initializeInterview, sendMessage, getInterviewState } = useInterview();
  
  const {
    messages,
    done,
    feedback,
    currentDay,
    questionsAnswered,
    totalQuestions,
    targetDays,
    isLoading,
    error,
    resetInterview
  } = getInterviewState();

  // Load cohort candidates on mount
  useEffect(() => {
    fetch(`${API_BASE}/api/candidates`)
      .then((res) => {
        if (!res.ok) throw new Error('Failed to load candidate list');
        return res.json();
      })
      .then((data) => {
        setCandidates(data.candidates || []);
      })
      .catch((err) => {
        console.error('[FRONTEND] Fetch candidates error:', err);
        setErrorMessage(
          'Failed to connect to the backend server. Please verify the FastAPI service is running on http://127.0.0.1:8000.'
        );
      });
  }, []);

  // Update localized error if hook captures api issue
  useEffect(() => {
    if (error) {
      setErrorMessage(error);
    }
  }, [error]);

  const handleSelectCandidate = async (candidate) => {
    setSelectedCandidate(candidate);
    setErrorMessage('');
    await initializeInterview(candidate);
  };

  const handleReset = () => {
    setSelectedCandidate(null);
    setErrorMessage('');
    resetInterview();
  };

  // Onboarding screen: Select candidate
  if (!selectedCandidate) {
    return (
      <div className="relative">
        {errorMessage && (
          <div className="fixed top-4 left-1/2 transform -translate-x-1/2 z-50 bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm px-6 py-3.5 rounded-xl shadow-xl backdrop-blur-md max-w-lg text-center font-medium">
            {errorMessage}
          </div>
        )}
        <CandidateSelector
          candidates={candidates}
          onSelectCandidate={handleSelectCandidate}
        />
      </div>
    );
  }

  // Interview cockpit screen: Split panel visualization
  return (
    <div className="flex flex-col md:flex-row h-screen w-screen bg-slate-950 text-slate-100 overflow-hidden font-sans">
      
      {/* LEFT PANEL: Candidate Sidebar */}
      <CandidateSidebar
        candidate={selectedCandidate}
        interviewPlan={{
          targetDays,
          questions: Array.from({ length: totalQuestions }, (_, i) => ({
            day: targetDays[i % targetDays.length] || 1, // Fallback layout mapping
            category: "INTERVIEW"
          })),
          done
        }}
        currentQuestionIndex={questionsAnswered}
      />

      {/* RIGHT PANEL: Live Chat OR Evaluation Dashboard */}
      <main className="flex-1 flex flex-col h-full bg-slate-900/20 relative">
        {errorMessage && (
          <div className="absolute top-18 left-1/2 transform -translate-x-1/2 z-50 bg-rose-500/20 border border-rose-500/30 text-rose-300 text-xs px-4 py-2.5 rounded-lg shadow-lg backdrop-blur-md font-medium">
            {errorMessage}
          </div>
        )}

        {done && feedback ? (
          <FeedbackDashboard
            feedback={feedback}
            candidateName={selectedCandidate.member.name}
            onReset={handleReset}
          />
        ) : (
          <ChatInterface
            messages={messages}
            onSendMessage={sendMessage}
            isLoading={isLoading}
            isCompleted={done}
          />
        )}
      </main>

    </div>
  );
}
