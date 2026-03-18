"use client";

import { Event } from "@/lib/api";

interface EventCardProps {
  event: Event;
  index: number;
}

export default function EventCard({ event, index }: EventCardProps) {
  const sourceColors: Record<string, string> = {
    Eventbrite: "bg-orange-50 text-orange-600 border-orange-200",
    Meetup: "bg-red-50 text-red-600 border-red-200",
    Luma: "bg-purple-50 text-purple-600 border-purple-200",
    ISPOR: "bg-blue-50 text-blue-600 border-blue-200",
    AcademyHealth: "bg-teal-50 text-teal-600 border-teal-200",
    ASHEcon: "bg-cyan-50 text-cyan-600 border-cyan-200",
    IHEA: "bg-sky-50 text-sky-600 border-sky-200",
    SMDM: "bg-violet-50 text-violet-600 border-violet-200",
    Biocom: "bg-green-50 text-green-600 border-green-200",
    BIO: "bg-emerald-50 text-emerald-600 border-emerald-200",
    "BioPharma Dive": "bg-indigo-50 text-indigo-600 border-indigo-200",
    Informa: "bg-amber-50 text-amber-600 border-amber-200",
    BioSpace: "bg-lime-50 text-lime-600 border-lime-200",
  };

  const badgeColor = sourceColors[event.source || ""] || "bg-slate-50 text-slate-500 border-slate-200";

  return (
    <div className="bg-white border border-slate-200/60 rounded-xl p-5 hover:border-slate-300 hover:shadow-sm transition-all">
      <div className="flex items-start gap-4">
        {/* Date block */}
        <div className="w-14 flex-shrink-0 text-center">
          {event.date ? (
            <div className="rounded-lg bg-gradient-to-br from-indigo-50 to-purple-50 border border-indigo-100/50 p-2">
              <p className="text-[10px] font-medium text-indigo-400 uppercase leading-tight">
                {event.date.replace(/\d{4}/, "").replace(/,?\s*$/, "").trim().split(" ")[0]?.slice(0, 3) || "TBD"}
              </p>
              <p className="text-lg font-bold text-indigo-600 leading-tight">
                {event.date.match(/\d{1,2}/)?.[0] || "?"}
              </p>
              <p className="text-[9px] text-indigo-300">
                {event.date.match(/\d{4}/)?.[0] || ""}
              </p>
            </div>
          ) : (
            <div className="rounded-lg bg-slate-50 border border-slate-100 p-2">
              <p className="text-[10px] font-medium text-slate-300 uppercase">Date</p>
              <p className="text-lg font-bold text-slate-300 leading-tight">TBD</p>
            </div>
          )}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-[10px] text-slate-300 font-mono">#{index + 1}</span>
                <h3 className="font-semibold text-slate-900 text-sm leading-snug">{event.title}</h3>
              </div>

              {/* Date full text */}
              {event.date && (
                <p className="text-xs text-slate-600 font-medium mt-0.5">{event.date}</p>
              )}

              <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                {/* Free/Paid badge */}
                {event.is_free === true && (
                  <span className="text-[10px] px-2 py-0.5 rounded-full border font-semibold bg-green-50 text-green-700 border-green-200">
                    FREE
                  </span>
                )}
                {event.is_free === false && (
                  <span className="text-[10px] px-2 py-0.5 rounded-full border font-medium bg-slate-50 text-slate-500 border-slate-200">
                    Paid
                  </span>
                )}

                {event.location && (
                  <span className="text-xs text-slate-500 flex items-center gap-1">
                    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M15 10.5a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
                      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1 1 15 0Z" />
                    </svg>
                    {event.location}
                  </span>
                )}
                {event.source && (
                  <span className={`text-[10px] px-2 py-0.5 rounded-full border font-medium ${badgeColor}`}>
                    {event.source}
                  </span>
                )}
              </div>

              {event.description && (
                <p className="mt-2 text-xs text-slate-400 line-clamp-2 leading-relaxed">
                  {event.description}
                </p>
              )}
            </div>

            <a
              href={event.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-indigo-600 border border-indigo-200/60 rounded-lg hover:bg-indigo-50 transition-colors flex-shrink-0"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 0 0 3 8.25v10.5A2.25 2.25 0 0 0 5.25 21h10.5A2.25 2.25 0 0 0 18 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
              </svg>
              View
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
