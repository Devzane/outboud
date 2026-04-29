"use client";

import { useEffect, useState } from "react";

export default function Home() {
  const [leads, setLeads] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [actionStatus, setActionStatus] = useState<string>("");

  useEffect(() => {
    fetchLeads();
  }, []);

  const fetchLeads = async () => {
    setLoading(true);
    try {
      const response = await fetch("http://localhost:8001/api/leads");
      const data = await response.json();
      if (data.status === "success") {
        setLeads(data.leads);
      } else {
        setActionStatus(`Error fetching leads: ${data.message}`);
      }
    } catch (error: any) {
      setActionStatus(`Failed to connect to backend: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const triggerSync = async () => {
    setActionStatus("Starting IMAP Sync...");
    try {
      const response = await fetch("http://localhost:8001/api/sync", {
        method: "POST",
      });
      const data = await response.json();
      setActionStatus(data.message || data.status);
    } catch (error: any) {
      setActionStatus(`Sync trigger failed: ${error.message}`);
    }
  };

  const triggerSend = async () => {
    setActionStatus("Starting Daily Sequence...");
    try {
      const response = await fetch("http://localhost:8001/api/send", {
        method: "POST",
      });
      const data = await response.json();
      setActionStatus(data.message || data.status);
    } catch (error: any) {
      setActionStatus(`Send trigger failed: ${error.message}`);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-200 p-8 font-sans">
      <div className="max-w-7xl mx-auto space-y-8">
        
        {/* Header */}
        <header className="flex flex-col md:flex-row justify-between items-start md:items-center border-b border-slate-700 pb-6 gap-4">
          <div>
            <h1 className="text-3xl font-bold text-white tracking-tight">Outbound Pipeline Control</h1>
            <p className="text-sm text-slate-400 mt-1">Manage leads, synchronize IMAP, and launch daily sequences.</p>
          </div>
          <div className="flex gap-4">
            <button 
              onClick={triggerSync}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-600 rounded-md text-sm font-medium transition-colors shadow-sm focus:outline-none focus:ring-2 focus:ring-slate-500"
            >
              Run IMAP Kill-Switch Sync
            </button>
            <button 
              onClick={triggerSend}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-md text-sm font-medium transition-colors shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
            >
              Launch Daily Sequence
            </button>
          </div>
        </header>

        {/* Status Bar */}
        {actionStatus && (
          <div className="bg-slate-800 border-l-4 border-blue-500 p-4 rounded-r-md">
            <p className="text-sm font-medium">{actionStatus}</p>
          </div>
        )}

        {/* Data Table */}
        <div className="bg-slate-800 border border-slate-700 rounded-lg shadow-xl overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-700 flex justify-between items-center bg-slate-800/50">
            <h2 className="text-lg font-medium text-white">Lead Database</h2>
            <button 
              onClick={fetchLeads}
              className="text-xs px-3 py-1 bg-slate-700 hover:bg-slate-600 rounded text-slate-300 transition-colors"
            >
              Refresh Data
            </button>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-xs text-slate-400 uppercase bg-slate-800/80 border-b border-slate-700">
                <tr>
                  <th className="px-6 py-3 font-medium">Company</th>
                  <th className="px-6 py-3 font-medium">First Name</th>
                  <th className="px-6 py-3 font-medium">Email</th>
                  <th className="px-6 py-3 font-medium">Status</th>
                  <th className="px-6 py-3 font-medium text-center">Step</th>
                  <th className="px-6 py-3 font-medium">Next Scheduled</th>
                  <th className="px-6 py-3 font-medium text-center">Replied</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={7} className="px-6 py-12 text-center text-slate-500">
                      <div className="flex justify-center items-center gap-2">
                        <svg className="animate-spin h-5 w-5 text-slate-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        <span>Loading leads from local API...</span>
                      </div>
                    </td>
                  </tr>
                ) : leads.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-6 py-12 text-center text-slate-500">
                      No leads found. Check your Google Sheet connection.
                    </td>
                  </tr>
                ) : (
                  leads.map((lead, idx) => (
                    <tr key={idx} className="border-b border-slate-700/50 hover:bg-slate-750 transition-colors">
                      <td className="px-6 py-4 font-medium text-slate-300">{lead.company_name || "-"}</td>
                      <td className="px-6 py-4">{lead.first_name || "-"}</td>
                      <td className="px-6 py-4 font-mono text-xs">{lead.verified_target_email || "-"}</td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          lead.verification_status?.toLowerCase() === 'valid' ? 'bg-green-500/10 text-green-400' :
                          lead.verification_status?.toLowerCase() === 'bounced' ? 'bg-red-500/10 text-red-400' :
                          'bg-slate-500/10 text-slate-400'
                        }`}>
                          {lead.verification_status || "Unknown"}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-center">
                        <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-slate-700 text-xs font-bold text-slate-300">
                          {lead.sequence_step !== undefined ? lead.sequence_step : "-"}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-slate-400 text-xs">
                        {lead.next_scheduled_date || "-"}
                      </td>
                      <td className="px-6 py-4 text-center">
                        {String(lead.has_replied).toLowerCase() === 'true' ? (
                          <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-green-500/20 text-green-500">
                            ✓
                          </span>
                        ) : (
                          <span className="text-slate-600">-</span>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
