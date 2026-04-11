"use client";

import { useState } from "react";

interface SearchBarProps {
  onSearch: (query: string) => void;
  isLoading: boolean;
  onCancel?: () => void;
  placeholder?: string;
  examples?: string[];
}

export default function SearchBar({ onSearch, isLoading, onCancel, placeholder, examples }: SearchBarProps) {
  const [query, setQuery] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!isLoading && query.trim()) {
      onSearch(query.trim());
    }
  };

  const defaultExamples = [
    "HEOR researchers at large pharma companies",
    "Health economics analysts with consulting experience",
  ];
  const displayExamples = examples || defaultExamples;

  return (
    <div className="w-full max-w-3xl mx-auto">
      <div className="relative group">
        <div className="absolute -inset-0.5 bg-gradient-to-r from-indigo-500/20 to-purple-500/20 rounded-2xl opacity-0 group-focus-within:opacity-100 transition-opacity blur pointer-events-none"></div>
        <div className="relative bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden focus-within:border-indigo-300 transition-colors">
          <form onSubmit={handleSubmit}>
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={placeholder || "Search..."}
              disabled={isLoading}
              className="w-full p-5 pr-28 text-sm border-0 focus:ring-0 resize-none bg-transparent text-slate-800 placeholder-slate-400 outline-none"
              rows={3}
              onKeyDown={(e) => {
                if (!isLoading && e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit(e);
                }
              }}
            />
          </form>
          {isLoading ? (
            <button
              type="button"
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                onCancel?.();
              }}
              className="absolute right-3 bottom-3 px-5 py-2.5 bg-gradient-to-r from-red-600 to-red-500 text-white rounded-xl hover:from-red-700 hover:to-red-600 transition-all text-sm font-medium shadow-sm hover:shadow-md z-10"
            >
              <span className="flex items-center gap-2">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
                Cancel
              </span>
            </button>
          ) : (
            <button
              type="button"
              onClick={query.trim() ? handleSubmit : undefined}
              disabled={!query.trim()}
              className="absolute right-3 bottom-3 px-5 py-2.5 bg-gradient-to-r from-indigo-600 to-indigo-500 text-white rounded-xl hover:from-indigo-700 hover:to-indigo-600 disabled:from-slate-200 disabled:to-slate-200 disabled:text-slate-400 disabled:cursor-not-allowed transition-all text-sm font-medium shadow-sm hover:shadow-md z-10"
            >
              <span className="flex items-center gap-1.5">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
                </svg>
                Search
              </span>
            </button>
          )}
        </div>
      </div>

      <div className="mt-4 flex flex-wrap gap-2 justify-center">
        {displayExamples.map((eq) => (
          <button
            key={eq}
            type="button"
            onClick={() => setQuery(eq)}
            disabled={isLoading}
            className="text-xs px-3 py-1.5 bg-white border border-slate-200/60 text-slate-500 rounded-full hover:border-indigo-200 hover:text-indigo-600 hover:bg-indigo-50/50 transition-all"
          >
            {eq}
          </button>
        ))}
      </div>
    </div>
  );
}
