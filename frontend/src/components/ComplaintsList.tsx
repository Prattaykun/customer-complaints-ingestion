import { useState, useEffect } from "react";
import {
  Plus,
  Search,
  ChevronLeft,
  ChevronRight,
  ClipboardList,
  AlertTriangle,
  Package,
  Calendar,
  User,
  Trash2,
  Edit3,
  Loader2,
  RefreshCw,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { getComplaints, type ComplaintData } from "@/services/api";
import api from "@/services/api";

interface ComplaintsListProps {
  onNewComplaint: () => void;
  onSelectComplaint: (complaint: ComplaintData) => void;
}

export default function ComplaintsList({
  onNewComplaint,
  onSelectComplaint,
}: ComplaintsListProps) {
  const [complaints, setComplaints] = useState<ComplaintData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(5);

  const fetchComplaintsList = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getComplaints();
      setComplaints(data);
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Failed to load complaints ledger."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchComplaintsList();
  }, []);

  const handleDelete = async (e: React.MouseEvent, id?: string | null) => {
    e.stopPropagation();
    if (!id) return;
    if (!confirm("Are you sure you want to delete this complaint record?")) return;

    try {
      await api.delete(`/complaints/${id}`);
      setComplaints((prev) => prev.filter((c) => c.id !== id));
    } catch (err) {
      alert("Failed to delete complaint record.");
    }
  };

  // Filter complaints based on search
  const filteredComplaints = complaints.filter((item) => {
    const query = searchTerm.toLowerCase();
    return (
      (item.productName || "").toLowerCase().includes(query) ||
      (item.batchNumber || "").toLowerCase().includes(query) ||
      (item.complainantName || "").toLowerCase().includes(query) ||
      (item.complaintCategory || "").toLowerCase().includes(query)
    );
  });

  // Pagination calculation
  const totalItems = filteredComplaints.length;
  const totalPages = Math.ceil(totalItems / pageSize) || 1;
  const validCurrentPage = Math.min(currentPage, totalPages);
  const startIndex = (validCurrentPage - 1) * pageSize;
  const endIndex = Math.min(startIndex + pageSize, totalItems);
  const currentComplaints = filteredComplaints.slice(startIndex, endIndex);

  const getSeverityBadgeClass = (level?: string) => {
    switch ((level || "").toLowerCase()) {
      case "critical":
        return "bg-red-500/10 text-red-700 dark:text-red-400 border-red-200 dark:border-red-900";
      case "major":
        return "bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-200 dark:border-amber-900";
      case "minor":
        return "bg-blue-500/10 text-blue-700 dark:text-blue-400 border-blue-200 dark:border-blue-900";
      default:
        return "bg-slate-100 text-slate-600 border-slate-200";
    }
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-gradient-to-r from-blue-900/10 via-purple-900/5 to-slate-900/10 p-6 rounded-2xl border border-blue-200/50 dark:border-blue-900/30 backdrop-blur-sm shadow-sm">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-blue-600 text-white shadow-md">
              <ClipboardList size={20} />
            </div>
            <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">
              Submitted Customer Complaints
            </h2>
          </div>
          <p className="text-xs text-muted-foreground pl-10">
            QMS Complaints Ledger — Compliant with FDA 21 CFR Part 211 & ICH Q10 standards
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchComplaintsList}
            disabled={loading}
            className="text-xs gap-1.5 h-9"
          >
            <RefreshCw size={13} className={loading ? "animate-spin" : ""} />
            Refresh
          </Button>
          <Button
            size="sm"
            onClick={onNewComplaint}
            className="bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs gap-1.5 h-9 px-4 shadow-md transition-all hover:scale-[1.02]"
          >
            <Plus size={15} />
            New Complaint
          </Button>
        </div>
      </div>

      {/* Main Ledger Card */}
      <Card className="border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
        <CardHeader className="py-4 px-6 bg-slate-50/50 dark:bg-slate-900/50 border-b border-slate-200 dark:border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <CardTitle className="text-sm font-semibold text-slate-800 dark:text-slate-200 flex items-center gap-2">
            <Package size={16} className="text-blue-600" />
            Complaint Records ({totalItems})
          </CardTitle>

          {/* Search Input */}
          <div className="relative w-full sm:w-72">
            <Search className="absolute left-3 top-2.5 size-4 text-muted-foreground" />
            <Input
              placeholder="Search product, batch, category..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
              className="pl-9 h-9 text-xs bg-white dark:bg-slate-950 border-slate-200 dark:border-slate-800"
            />
          </div>
        </CardHeader>

        <CardContent className="p-0">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-16 text-muted-foreground gap-3">
              <Loader2 size={28} className="animate-spin text-blue-600" />
              <p className="text-xs font-medium">Loading complaints ledger...</p>
            </div>
          ) : error ? (
            <div className="py-12 text-center text-red-500 text-xs space-y-2">
              <AlertTriangle className="mx-auto size-6" />
              <p>{error}</p>
              <Button size="sm" variant="outline" onClick={fetchComplaintsList}>
                Try Again
              </Button>
            </div>
          ) : currentComplaints.length === 0 ? (
            <div className="py-16 text-center text-muted-foreground space-y-3">
              <ClipboardList className="mx-auto size-10 text-slate-300 dark:text-slate-700" />
              <p className="text-sm font-semibold text-slate-700 dark:text-slate-300">
                {searchTerm ? "No complaints match your search." : "No complaints logged yet."}
              </p>
              <p className="text-xs text-muted-foreground max-w-sm mx-auto">
                {searchTerm
                  ? "Try searching with a different product name or batch number."
                  : "Click the ' New Complaint' button above to log a new complaint with the AI Co-pilot."}
              </p>
              {!searchTerm && (
                <Button size="sm" onClick={onNewComplaint} className="mt-2 text-xs bg-blue-600 text-white">
                  <Plus size={14} className="mr-1" />
                  + Log First Complaint
                </Button>
              )}
            </div>
          ) : (
            <div className="overflow-auto max-h-[calc(100vh-320px)] min-h-[300px] relative">
              <table className="w-full text-left text-xs border-collapse min-w-[850px]">
                <thead>
                  <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-500 font-semibold uppercase tracking-wider text-[11px]">
                    <th className="py-3 px-4 sticky top-0 z-10 bg-slate-100/95 dark:bg-slate-900/95 backdrop-blur-sm shadow-sm">Product Details</th>
                    <th className="py-3 px-4 sticky top-0 z-10 bg-slate-100/95 dark:bg-slate-900/95 backdrop-blur-sm shadow-sm">Batch / Lot</th>
                    <th className="py-3 px-4 sticky top-0 z-10 bg-slate-100/95 dark:bg-slate-900/95 backdrop-blur-sm shadow-sm">Category</th>
                    <th className="py-3 px-4 sticky top-0 z-10 bg-slate-100/95 dark:bg-slate-900/95 backdrop-blur-sm shadow-sm">Complainant</th>
                    <th className="py-3 px-4 sticky top-0 z-10 bg-slate-100/95 dark:bg-slate-900/95 backdrop-blur-sm shadow-sm">Severity & Risk</th>
                    <th className="py-3 px-4 sticky top-0 z-10 bg-slate-100/95 dark:bg-slate-900/95 backdrop-blur-sm shadow-sm">Date</th>
                    <th className="py-3 px-4 text-right sticky top-0 z-10 bg-slate-100/95 dark:bg-slate-900/95 backdrop-blur-sm shadow-sm">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60">
                  {currentComplaints.map((item) => (
                    <tr
                      key={item.id || Math.random()}
                      onClick={() => onSelectComplaint(item)}
                      className="hover:bg-blue-50/40 dark:hover:bg-slate-800/40 transition-colors cursor-pointer group"
                    >
                      <td className="py-3.5 px-4">
                        <div className="font-semibold text-slate-900 dark:text-slate-100 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                          {item.productName || "—"}
                        </div>
                        {item.productStrength && (
                          <div className="text-[11px] text-muted-foreground mt-0.5">
                            {item.productStrength} {item.dosageForm && `• ${item.dosageForm}`}
                          </div>
                        )}
                      </td>

                      <td className="py-3.5 px-4 font-mono font-medium text-slate-700 dark:text-slate-300">
                        {item.batchNumber ? (
                          <span className="px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
                            {item.batchNumber}
                          </span>
                        ) : (
                          "—"
                        )}
                      </td>

                      <td className="py-3.5 px-4 text-slate-700 dark:text-slate-300">
                        {item.complaintCategory || "—"}
                      </td>

                      <td className="py-3.5 px-4">
                        <div className="flex items-center gap-1.5 font-medium text-slate-800 dark:text-slate-200">
                          <User size={12} className="text-muted-foreground" />
                          {item.complainantName || "—"}
                        </div>
                        {(item.complainantEmail || item.complainantPhone || item.complainantContact) && (
                          <div className="text-[11px] text-muted-foreground truncate max-w-[180px]">
                            {item.countryCode && `${item.countryCode} `}
                            {item.complainantPhone || item.complainantEmail || item.complainantContact}
                          </div>
                        )}
                      </td>

                      <td className="py-3.5 px-4">
                        <div className="flex items-center gap-2">
                          <Badge
                            className={`text-[11px] font-semibold border ${getSeverityBadgeClass(
                              item.severityLevel
                            )}`}
                          >
                            {item.severityLevel || "Not Assessed"}
                          </Badge>
                          {item.riskScore !== undefined && item.riskScore > 0 && (
                            <span className="text-[11px] font-bold text-slate-600 dark:text-slate-400">
                              {item.riskScore}/100
                            </span>
                          )}
                        </div>
                      </td>

                      <td className="py-3.5 px-4 text-muted-foreground whitespace-nowrap">
                        <div className="flex items-center gap-1">
                          <Calendar size={12} />
                          {item.dateOfComplaint || "—"}
                        </div>
                      </td>

                      <td className="py-3.5 px-4 text-right whitespace-nowrap">
                        <div className="flex items-center justify-end gap-1.5" onClick={(e) => e.stopPropagation()}>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => onSelectComplaint(item)}
                            className="h-7 px-2.5 text-xs text-blue-600 hover:text-blue-700 hover:bg-blue-50 dark:hover:bg-blue-950/50"
                          >
                            <Edit3 size={13} className="mr-1" />
                            View / Edit
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={(e) => handleDelete(e, item.id)}
                            className="h-7 w-7 p-0 text-slate-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-950/50"
                            title="Delete Complaint"
                          >
                            <Trash2 size={13} />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>

        {/* Footer Pagination Controls */}
        {!loading && filteredComplaints.length > 0 && (
          <div className="py-3.5 px-6 bg-slate-50/50 dark:bg-slate-900/50 border-t border-slate-200 dark:border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs">
            <div className="text-muted-foreground">
              Showing <span className="font-semibold text-slate-900 dark:text-slate-100">{totalItems === 0 ? 0 : startIndex + 1}</span> to{" "}
              <span className="font-semibold text-slate-900 dark:text-slate-100">{endIndex}</span> of{" "}
              <span className="font-semibold text-slate-900 dark:text-slate-100">{totalItems}</span> complaints
            </div>

            <div className="flex items-center gap-4">
              {/* Page Size Select */}
              <div className="flex items-center gap-1.5 text-muted-foreground">
                <span>Rows:</span>
                <select
                  value={pageSize}
                  onChange={(e) => {
                    setPageSize(Number(e.target.value));
                    setCurrentPage(1);
                  }}
                  className="h-7 text-xs rounded border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 px-2 py-0.5 font-medium focus:outline-none"
                >
                  <option value={5}>5</option>
                  <option value={10}>10</option>
                  <option value={20}>20</option>
                  <option value={50}>50</option>
                </select>
              </div>

              {/* Page Buttons */}
              <div className="flex items-center gap-1">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  disabled={validCurrentPage === 1}
                  className="h-7 w-7 p-0"
                >
                  <ChevronLeft size={14} />
                </Button>

                <span className="px-2 font-medium text-slate-700 dark:text-slate-300">
                  Page {validCurrentPage} of {totalPages}
                </span>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                  disabled={validCurrentPage >= totalPages}
                  className="h-7 w-7 p-0"
                >
                  <ChevronRight size={14} />
                </Button>
              </div>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}
