import { useState, useEffect, useCallback } from 'react';

const API_BASE = 'http://localhost:8000';

// Secure fallback UUID generator
const generateUUID = () => {
  if (typeof window !== 'undefined' && window.crypto && window.crypto.randomUUID) {
    return window.crypto.randomUUID();
  }
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
};

export default function useInterview() {
  const [sessionId, setSessionId] = useState('');
  const [candidate, setCandidate] = useState(null);
  const [messages, setMessages] = useState([]);
  const [done, setDone] = useState(false);
  const [feedback, setFeedback] = useState(null);
  
  // Sidebar progress mapping
  const [interviewPlan, setInterviewPlan] = useState(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  
  // Loading & error bounds
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Generate UUID session token on mount
  useEffect(() => {
    setSessionId(generateUUID());
  }, []);

  // Fetch target days and active pointers from metadata route
  const syncPlanMetadata = useCallback(async (activeSessionId) => {
    try {
      const res = await fetch(`${API_BASE}/api/interview/session/${activeSessionId}`);
      if (!res.ok) throw new Error('Failed to synchronize interview target day maps.');
      const data = await res.json();
      
      setInterviewPlan(data);
      setCurrentQuestionIndex(data.currentQuestionIndex);
      if (data.done) {
        setDone(true);
      }
    } catch (err) {
      console.error('[useInterview] Sync error:', err);
    }
  }, []);

  // Initialize Technical Interview Session (Turn 1)
  const initializeInterview = useCallback(async (selectedCandidate) => {
    setIsLoading(true);
    setError(null);
    setCandidate(selectedCandidate);
    setMessages([]);
    setDone(false);
    setFeedback(null);
    setInterviewPlan(null);
    setCurrentQuestionIndex(0);

    // Generate a fresh session ID for this specific interview
    const newSessionId = generateUUID();
    setSessionId(newSessionId);

    try {
      const response = await fetch(`${API_BASE}/api/interview`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sessionId: newSessionId,
          candidate: selectedCandidate
        }),
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'API failed to initialize interview planner.');
      }

      const data = await response.json();
      
      // Save opening question in dialogue thread
      setMessages([{ role: 'interviewer', content: data.reply }]);
      
      // Load planning days and questions array from metadata GET
      await syncPlanMetadata(newSessionId);
    } catch (err) {
      console.error('[useInterview] Init failed:', err);
      setError(err.message || 'Connection failed. Verify local API server is running.');
      setCandidate(null);
    } finally {
      setIsLoading(false);
    }
  }, [syncPlanMetadata]);

  // Submit response (Turns 2..N)
  const sendMessage = useCallback(async (userMessage) => {
    if (isLoading || done || !userMessage.trim()) return;

    setError(null);
    setIsLoading(true);
    
    // Optimistic UI updates
    const userMsgObj = { role: 'candidate', content: userMessage };
    setMessages((prev) => [...prev, userMsgObj]);

    try {
      const response = await fetch(`${API_BASE}/api/interview`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sessionId: sessionId,
          message: userMessage
        }),
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'API failed to process conversation turn.');
      }

      const data = await response.json();
      
      // Append interviewer reply
      setMessages((prev) => [...prev, { role: 'interviewer', content: data.reply }]);
      
      if (data.done) {
        setDone(true);
        setFeedback(data.feedback);
      }

      // Sync progress pointer and current active highlight
      await syncPlanMetadata(sessionId);
    } catch (err) {
      console.error('[useInterview] Send message error:', err);
      setError(err.message || 'Failed to submit response. Try again.');
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, isLoading, done, syncPlanMetadata]);

  const resetInterview = useCallback(() => {
    setCandidate(null);
    setMessages([]);
    setDone(false);
    setFeedback(null);
    setInterviewPlan(null);
    setCurrentQuestionIndex(0);
    setError(null);
    setIsLoading(false);
    setSessionId(generateUUID()); // Generate new session UUID
  }, []);

  // Expose current states
  const getInterviewState = useCallback(() => {
    let currentDay = null;
    let questionsAnswered = 0;
    
    if (interviewPlan) {
      const currentQ = interviewPlan.questions?.[currentQuestionIndex];
      if (currentQ) {
        currentDay = currentQ.day;
      }
      questionsAnswered = currentQuestionIndex;
    }

    return {
      messages,
      done,
      feedback,
      currentDay,
      questionsAnswered,
      totalQuestions: interviewPlan?.questions?.length || 0,
      targetDays: interviewPlan?.targetDays || [],
      candidate,
      isLoading,
      error,
      resetInterview
    };
  }, [messages, done, feedback, interviewPlan, currentQuestionIndex, candidate, isLoading, error, resetInterview]);

  return {
    initializeInterview,
    sendMessage,
    getInterviewState,
    syncPlanMetadata
  };
}
