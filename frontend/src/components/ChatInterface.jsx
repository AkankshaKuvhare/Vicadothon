import React, { useState, useEffect, useRef } from 'react';

export default function ChatInterface({ messages, onSendMessage, isLoading, isCompleted }) {
  const [inputText, setInputText] = useState('');
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Auto-scroll helper
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  // Auto-focus chat input after each agent response (loading transitions from true -> false)
  useEffect(() => {
    if (!isLoading && !isCompleted) {
      inputRef.current?.focus();
    }
  }, [isLoading, isCompleted, messages.length]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!inputText.trim() || isLoading || isCompleted) return;
    
    onSendMessage(inputText.trim());
    setInputText('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      handleSubmit(e);
    }
  };

  return (
    <div className="flex-1 flex flex-col justify-between h-full bg-slate-950/20 text-slate-100 relative">
      
      {/* Session Header Status */}
      <div className="px-6 py-4 border-b border-slate-800 bg-slate-900/40 backdrop-blur-md flex items-center justify-between z-10">
        <div className="flex items-center gap-2">
          <span className={`w-2.5 h-2.5 rounded-full ${isCompleted ? 'bg-slate-500' : 'bg-blue-500 animate-pulse'}`} />
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-200">
            {isCompleted ? 'Interview Completed' : 'Technical Assessment Session'}
          </h2>
        </div>
        {!isCompleted && (
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-500/10 border border-blue-500/25 text-blue-400 font-bold uppercase font-sans">
            Live Diagnostics
          </span>
        )}
      </div>

      {/* Message History Thread */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((msg, idx) => {
          const isInterviewer = msg.role === 'interviewer';
          
          return (
            <div
              key={idx}
              className={`flex w-full ${isInterviewer ? 'justify-start' : 'justify-end'} animate-fade-in`}
            >
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed font-medium shadow-md border ${
                  isInterviewer
                    ? 'bg-slate-900/80 border-slate-800 text-slate-100 rounded-tl-none'
                    : 'bg-blue-600/90 border-blue-500/20 text-white rounded-tr-none'
                }`}
              >
                {/* Role Tag */}
                <span className={`block text-[9px] uppercase tracking-wider font-bold mb-1 ${
                  isInterviewer ? 'text-blue-400' : 'text-blue-200'
                }`}>
                  {isInterviewer ? 'Interviewer' : 'You'}
                </span>
                
                <p className="whitespace-pre-line">{msg.content}</p>
              </div>
            </div>
          );
        })}

        {/* Dynamic Typing Indicator */}
        {isLoading && (
          <div className="flex w-full justify-start animate-fade-in">
            <div className="bg-slate-900/80 border border-slate-800 text-slate-100 rounded-2xl rounded-tl-none px-4 py-3 shadow-md">
              <span className="block text-[9px] uppercase tracking-wider font-bold mb-1.5 text-blue-400">
                Interviewer
              </span>
              <div className="flex items-center gap-1.5 py-1">
                <span className="w-2.5 h-2.5 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-2.5 h-2.5 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-2.5 h-2.5 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Message input panel */}
      <div className="p-4 border-t border-slate-800 bg-slate-900/40 backdrop-blur-md z-10">
        <form onSubmit={handleSubmit} className="flex gap-3 max-w-4xl mx-auto items-end">
          <textarea
            ref={inputRef}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading || isCompleted}
            placeholder={
              isCompleted
                ? 'Interview finished. Scroll up or check feedback.'
                : isLoading
                ? 'Awaiting interviewer response...'
                : 'Type your technical answer details here...'
            }
            className="flex-1 bg-slate-950 border border-slate-800 focus:border-blue-500/50 rounded-xl px-4 py-3 text-sm text-slate-100 placeholder-slate-500 outline-none resize-none min-h-[50px] max-h-[120px] transition-all disabled:opacity-50 font-medium"
            rows={1}
          />
          <button
            type="submit"
            disabled={!inputText.trim() || isLoading || isCompleted}
            className="px-5 py-3 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-sm transition-all duration-300 shadow-md shadow-blue-500/10 hover:shadow-blue-500/20 disabled:opacity-50 disabled:hover:bg-blue-600 disabled:cursor-not-allowed cursor-pointer h-[50px] flex items-center justify-center"
          >
            Send
          </button>
        </form>
      </div>

    </div>
  );
}
