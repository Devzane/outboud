import CSVUploader from "@/components/CSVUploader";
import { Users, Mail, Activity } from "lucide-react";

export default function Dashboard() {
  return (
    <div className="mx-auto max-w-5xl space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-1 text-sm text-gray-500">
          Welcome to the Outbound Engine. Manage your leads and cold email sequences.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="flex items-center rounded-xl border bg-white p-6 shadow-sm">
          <div className="rounded-full bg-blue-100 p-3 text-blue-600">
            <Users className="h-6 w-6" />
          </div>
          <div className="ml-4">
            <h3 className="text-sm font-medium text-gray-500">Total Leads</h3>
            <p className="text-2xl font-bold text-gray-900">---</p>
          </div>
        </div>
        <div className="flex items-center rounded-xl border bg-white p-6 shadow-sm">
          <div className="rounded-full bg-green-100 p-3 text-green-600">
            <Mail className="h-6 w-6" />
          </div>
          <div className="ml-4">
            <h3 className="text-sm font-medium text-gray-500">Emails Sent</h3>
            <p className="text-2xl font-bold text-gray-900">---</p>
          </div>
        </div>
        <div className="flex items-center rounded-xl border bg-white p-6 shadow-sm">
          <div className="rounded-full bg-purple-100 p-3 text-purple-600">
            <Activity className="h-6 w-6" />
          </div>
          <div className="ml-4">
            <h3 className="text-sm font-medium text-gray-500">Active Campaigns</h3>
            <p className="text-2xl font-bold text-gray-900">---</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div>
          <CSVUploader />
        </div>
        <div className="rounded-xl border bg-white p-8 shadow-sm">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Pipeline Status</h2>
          <div className="space-y-4">
            <div className="border-l-4 border-blue-500 bg-blue-50 p-4">
              <p className="text-sm font-medium text-blue-800">API Servers Offline</p>
              <p className="mt-1 text-sm text-blue-700">The verification and dispatch workers are currently not running.</p>
            </div>
            {/* We will add more pipeline status here later */}
          </div>
        </div>
      </div>
    </div>
  );
}
