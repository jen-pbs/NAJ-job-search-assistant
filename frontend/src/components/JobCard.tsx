"use client";

import { Job } from "@/lib/api";
import SaveToNotionButton from "./SaveToNotionButton";

interface JobCardProps {
  job: Job;
  index: number;
}

export default function JobCard({ job, index }: JobCardProps) {
  const sourceColors: Record<string, string> = {
    Indeed: "bg-blue-50 text-blue-600 border-blue-200",
    LinkedIn: "bg-sky-50 text-sky-600 border-sky-200",
    Glassdoor: "bg-green-50 text-green-600 border-green-200",
    ZipRecruiter: "bg-emerald-50 text-emerald-600 border-emerald-200",
    BioSpace: "bg-lime-50 text-lime-600 border-lime-200",
    PharmiWeb: "bg-teal-50 text-teal-600 border-teal-200",
    "Science Careers": "bg-violet-50 text-violet-600 border-violet-200",
    HealthECareers: "bg-cyan-50 text-cyan-600 border-cyan-200",
    USAJobs: "bg-indigo-50 text-indigo-600 border-indigo-200",
    HigherEdJobs: "bg-purple-50 text-purple-600 border-purple-200",
    AcademicKeys: "bg-fuchsia-50 text-fuchsia-600 border-fuchsia-200",
    Wellfound: "bg-orange-50 text-orange-600 border-orange-200",
    BuiltIn: "bg-red-50 text-red-600 border-red-200",
    Craigslist: "bg-amber-50 text-amber-600 border-amber-200",
  };

  const badgeColor = sourceColors[job.source || ""] || "bg-slate-50 text-slate-500 border-slate-200";

  const initials = (job.company || "?")
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase() || "")
    .join("");

  return (
    <div className="bg-white border border-slate-200/60 rounded-xl p-5 hover:border-slate-300 hover:shadow-sm transition-all">
      <div className="flex items-start gap-4">
        {/* Company avatar */}
        <div className="w-11 h-11 rounded-lg bg-gradient-to-br from-indigo-100 to-purple-100 border border-indigo-200/40 flex items-center justify-center flex-shrink-0">
          <span className="text-xs font-bold text-indigo-600">{initials}</span>
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <div className="flex items-center gap-2 mb-0.5">
                <span className="text-[10px] text-slate-300 font-mono">#{index + 1}</span>
                <h3 className="font-semibold text-slate-900 text-sm leading-snug">{job.title}</h3>
              </div>

              {job.company && (
                <p className="text-xs text-slate-600 font-medium">{job.company}</p>
              )}

              <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                {job.is_remote && (
                  <span className="text-[10px] px-2 py-0.5 rounded-full border font-semibold bg-green-50 text-green-700 border-green-200">
                    REMOTE
                  </span>
                )}

                {job.salary && (
                  <span className="text-[10px] px-2 py-0.5 rounded-full border font-medium bg-emerald-50 text-emerald-700 border-emerald-200">
                    {job.salary}
                  </span>
                )}

                {job.location && (
                  <span className="text-xs text-slate-500 flex items-center gap-1">
                    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M15 10.5a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
                      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1 1 15 0Z" />
                    </svg>
                    {job.location}
                  </span>
                )}

                {job.source && (
                  <span className={`text-[10px] px-2 py-0.5 rounded-full border font-medium ${badgeColor}`}>
                    {job.source}
                  </span>
                )}

                {job.date_posted && (
                  <span className="text-[10px] text-slate-400">
                    {job.date_posted}
                  </span>
                )}
              </div>

              {job.description && (
                <p className="mt-2 text-xs text-slate-400 line-clamp-2 leading-relaxed">
                  {job.description}
                </p>
              )}
            </div>

            <div className="flex flex-col gap-1.5 flex-shrink-0">
              <a
                href={job.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-indigo-600 border border-indigo-200/60 rounded-lg hover:bg-indigo-50 transition-colors"
              >
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 0 0 3 8.25v10.5A2.25 2.25 0 0 0 5.25 21h10.5A2.25 2.25 0 0 0 18 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
                </svg>
                Apply
              </a>
              <SaveToNotionButton
                purpose="jobs"
                fields={{
                  Name: job.title,
                  Title: job.title,
                  Company: job.company || "",
                  Location: job.location || "",
                  Salary: job.salary || "",
                  URL: job.url,
                  Link: job.url,
                  Source: job.source || "",
                  "Date Posted": job.date_posted || "",
                  Description: job.description || "",
                }}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
