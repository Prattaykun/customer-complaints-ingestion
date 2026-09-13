import { AlertTriangle, ShieldAlert, X, Package, Hash, BarChart3, Brain } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import type { DuplicateDetails } from "@/services/api";

interface DuplicateAlertModalProps {
  isOpen: boolean;
  details: DuplicateDetails;
  onDismiss: () => void;
  isSubmitting?: boolean;
}

export default function DuplicateAlertModal({
  isOpen,
  details,
  onDismiss,
}: DuplicateAlertModalProps) {
  if (!isOpen) return null;

  const similarityPercent = Math.round(details.similarity_score * 100);
  const confidencePercent = Math.round(details.confidence * 100);

  return (
    <div className="duplicate-modal-overlay" onClick={onDismiss}>
      <div
        className="duplicate-modal-container"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="duplicate-modal-header">
          <div className="duplicate-modal-header-left">
            <div className="duplicate-modal-icon">
              <ShieldAlert size={22} />
            </div>
            <div>
              <h3 className="duplicate-modal-title">
                Duplicate Complaint Rejected
              </h3>
              <p className="duplicate-modal-subtitle">
                Embedding retrieval + LLM verification found a matching record
              </p>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={onDismiss}
            className="duplicate-modal-close"
          >
            <X size={16} />
          </Button>
        </div>

        <div className="duplicate-modal-body">
          <div className="duplicate-modal-scores">
            <div className="duplicate-modal-score-card">
              <div className="duplicate-modal-score-label">
                <BarChart3 size={14} className="text-amber-600" />
                <span>Embedding Similarity</span>
              </div>
              <div className="duplicate-modal-score-value text-amber-700 dark:text-amber-400">
                {similarityPercent}%
              </div>
              <Progress
                value={similarityPercent}
                className="h-1.5 mt-1.5 bg-amber-100 dark:bg-amber-950"
              />
            </div>
            <div className="duplicate-modal-score-card">
              <div className="duplicate-modal-score-label">
                <Brain size={14} className="text-purple-600" />
                <span>LLM Confidence</span>
              </div>
              <div className="duplicate-modal-score-value text-purple-700 dark:text-purple-400">
                {confidencePercent}%
              </div>
              <Progress
                value={confidencePercent}
                className="h-1.5 mt-1.5 bg-purple-100 dark:bg-purple-950"
              />
            </div>
          </div>

          <div className="duplicate-modal-match">
            <div className="duplicate-modal-match-title">
              <AlertTriangle size={14} className="text-amber-600" />
              Matched Existing Complaint
            </div>
            <div className="duplicate-modal-match-fields">
              {details.matched_product && (
                <div className="duplicate-modal-match-row">
                  <Package size={13} className="text-slate-400" />
                  <span className="duplicate-modal-match-label">Product:</span>
                  <span className="duplicate-modal-match-value">
                    {details.matched_product}
                  </span>
                </div>
              )}
              {details.matched_batch && (
                <div className="duplicate-modal-match-row">
                  <Hash size={13} className="text-slate-400" />
                  <span className="duplicate-modal-match-label">Batch:</span>
                  <Badge
                    variant="outline"
                    className="text-[11px] font-mono px-1.5"
                  >
                    {details.matched_batch}
                  </Badge>
                </div>
              )}
              {details.matched_complaint_id && (
                <div className="duplicate-modal-match-row">
                  <span className="duplicate-modal-match-label">
                    Record ID:
                  </span>
                  <span className="duplicate-modal-match-value text-[11px] font-mono text-slate-500 truncate max-w-[200px]">
                    {details.matched_complaint_id}
                  </span>
                </div>
              )}
            </div>
          </div>

          {details.explanation && (
            <div className="duplicate-modal-explanation">
              <div className="duplicate-modal-explanation-label">
                <Brain size={13} className="text-blue-500" />
                AI Analysis
              </div>
              <p className="duplicate-modal-explanation-text">
                {details.explanation}
              </p>
            </div>
          )}
        </div>

        <div className="duplicate-modal-footer">
          <Button
            size="sm"
            onClick={onDismiss}
            className="duplicate-modal-dismiss-btn"
          >
            Reject & Review Record
          </Button>
        </div>
      </div>
    </div>
  );
}
