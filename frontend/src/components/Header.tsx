import { Bot, Shield, Plus, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";

interface HeaderProps {
  activeView: "list" | "form";
  onNavigate: (view: "list" | "form") => void;
  onNewComplaint: () => void;
}

export default function Header({
  activeView,
  onNavigate,
  onNewComplaint,
}: HeaderProps) {
  return (
    <header className="header">
      <div className="header-inner">
        <div className="header-brand cursor-pointer" onClick={() => onNavigate("list")}>
          <div className="header-logo">
            <Shield className="header-logo-icon" />
          </div>
          <div>
            <h1 className="header-title flex items-center gap-2">
              PharmaQMS
              <span className="text-[10px] font-normal px-2 py-0.5 rounded bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-900">
                21 CFR 211 / ICH Q10
              </span>
            </h1>
            <p className="header-subtitle">
              Customer Complaint Management System
            </p>
          </div>
        </div>

        <div className="header-actions">
          <div className="header-badge">
            <Bot size={14} />
            <span>AI Co-pilot Active</span>
          </div>

          {activeView === "form" && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => onNavigate("list")}
              className="header-new-btn border-slate-300 dark:border-slate-700"
            >
              <ArrowLeft size={14} />
              Complaints List
            </Button>
          )}

          <Button
            size="sm"
            onClick={onNewComplaint}
            className="header-new-btn bg-blue-600 hover:bg-blue-700 text-white font-semibold shadow-sm"
          >
            <Plus size={14} />
            + New Complaint
          </Button>
        </div>
      </div>
    </header>
  );
}
