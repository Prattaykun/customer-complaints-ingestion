import { useState } from "react";
import {
  Package,
  Hash,
  Calendar,
  AlertTriangle,
  FileText,
  User,
  ClipboardList,
  CheckCircle2,
  Activity,
  Mail,
  Phone,
  Globe,
  Send,
  Loader2,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { setComplaintData } from "@/store/complaintSlice";
import { addMessage } from "@/store/chatSlice";
import {
  submitComplaint,
  type DuplicateDetails,
} from "@/services/api";
import { AnimatedFormField } from "@/components/AnimatedFormField";
import DuplicateAlertModal from "@/components/DuplicateAlertModal";

function SeverityBadge({ level }: { level: string }) {
  const colorMap: Record<string, string> = {
    Critical: "severity-critical",
    Major: "severity-major",
    Minor: "severity-minor",
  };

  if (!level) return <Badge className="severity-empty">Not Assessed</Badge>;

  return (
    <Badge className={colorMap[level] || "severity-empty"}>
      <AlertTriangle size={12} />
      {level}
    </Badge>
  );
}

export default function ComplaintForm() {
  const dispatch = useAppDispatch();
  const complaint = useAppSelector((state) => state.complaint);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitSuccess, setSubmitSuccess] = useState<string | null>(null);
  const [duplicateOpen, setDuplicateOpen] = useState(false);
  const [duplicateDetails, setDuplicateDetails] =
    useState<DuplicateDetails | null>(null);

  const canSubmit = Boolean(
    complaint.productName ||
      complaint.complaintDescription ||
      complaint.batchNumber
  );

  const handleSubmit = async () => {
    if (!canSubmit || isSubmitting) return;

    setIsSubmitting(true);
    setSubmitError(null);
    setSubmitSuccess(null);
    setDuplicateOpen(false);
    setDuplicateDetails(null);

    try {
      const response = await submitComplaint(complaint, false);

      if (response.duplicate_detected && response.duplicate_details) {
        setDuplicateDetails(response.duplicate_details);
        setDuplicateOpen(true);
        dispatch(
          addMessage({
            id: Date.now().toString(),
            role: "assistant",
            content:
              `**Duplicate complaint rejected.**\n\n` +
              `${response.message}\n\n` +
              `Similarity: ${Math.round((response.duplicate_details.similarity_score || 0) * 100)}% · ` +
              `LLM confidence: ${Math.round((response.duplicate_details.confidence || 0) * 100)}%\n\n` +
              `${response.duplicate_details.explanation || ""}`,
            timestamp: new Date().toISOString(),
          })
        );
        return;
      }

      if (!response.success) {
        setSubmitError(response.message || "Submission failed.");
        return;
      }

      if (response.complaint) {
        dispatch(setComplaintData(response.complaint));
      } else {
        dispatch(setComplaintData({ status: "submitted" }));
      }

      setSubmitSuccess(response.message || "Complaint submitted successfully.");
      dispatch(
        addMessage({
          id: Date.now().toString(),
          role: "assistant",
          content:
            `**Complaint submitted successfully.**\n\n` +
            `No duplicates were detected by the  retrieval + LLM verification pipeline. ` +
            `The record is now saved with status **submitted**.`,
          timestamp: new Date().toISOString(),
        })
      );
    } catch (error) {
      console.error("Submit error:", error);
      setSubmitError(
        "Failed to submit complaint. Ensure the backend is running and try again."
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="complaint-form-container">
      <ScrollArea className="complaint-form-scroll">
        <div className="complaint-form-inner">
          {/* Title */}
          <div className="complaint-form-header">
            <div className="complaint-form-title-row">
              <ClipboardList size={20} className="text-primary" />
              <h2 className="complaint-form-title">Log Customer Complaint</h2>
            </div>
            {complaint.status !== "draft" && (
              <Badge className="status-badge">{complaint.status}</Badge>
            )}
          </div>

          {/* Product Information */}
          <Card className="form-section-card">
            <CardHeader className="form-section-header">
              <CardTitle className="form-section-title">
                <Package size={16} />
                Product Information
              </CardTitle>
            </CardHeader>
            <CardContent className="form-section-content">
              <div className="form-grid-2">
                <AnimatedFormField
                  label="Product Name"
                  value={complaint.productName}
                  fieldKey="productName"
                  icon={Package}
                />
                <AnimatedFormField
                  label="Strength"
                  value={complaint.productStrength}
                  fieldKey="productStrength"
                />
              </div>
              <AnimatedFormField
                label="Dosage Form"
                value={complaint.dosageForm}
                fieldKey="dosageForm"
              />
            </CardContent>
          </Card>

          {/* Batch Details */}
          <Card className="form-section-card">
            <CardHeader className="form-section-header">
              <CardTitle className="form-section-title">
                <Hash size={16} />
                Batch Details
              </CardTitle>
            </CardHeader>
            <CardContent className="form-section-content">
              <div className="form-grid-2">
                <AnimatedFormField
                  label="Batch Number"
                  value={complaint.batchNumber}
                  fieldKey="batchNumber"
                  icon={Hash}
                />
                <AnimatedFormField
                  label="Lot Number"
                  value={complaint.lotNumber}
                  fieldKey="lotNumber"
                />
              </div>
              <div className="form-grid-2">
                <AnimatedFormField
                  label="Manufacturing Date"
                  value={complaint.manufacturingDate}
                  fieldKey="manufacturingDate"
                  icon={Calendar}
                />
                <AnimatedFormField
                  label="Expiry Date"
                  value={complaint.expiryDate}
                  fieldKey="expiryDate"
                  icon={Calendar}
                />
              </div>
            </CardContent>
          </Card>

          {/* Complaint Details */}
          <Card className="form-section-card">
            <CardHeader className="form-section-header">
              <CardTitle className="form-section-title">
                <FileText size={16} />
                Complaint Details
              </CardTitle>
            </CardHeader>
            <CardContent className="form-section-content">
              <AnimatedFormField
                label="Category"
                value={complaint.complaintCategory}
                fieldKey="complaintCategory"
              />
              <AnimatedFormField
                label="Description"
                value={complaint.complaintDescription}
                fieldKey="complaintDescription"
                icon={FileText}
                isTextarea
                rows={3}
              />
              <div className="form-grid-2">
                <AnimatedFormField
                  label="Complainant Name"
                  value={complaint.complainantName}
                  fieldKey="complainantName"
                  icon={User}
                />
                <AnimatedFormField
                  label="Complainant Email"
                  value={complaint.complainantEmail}
                  fieldKey="complainantEmail"
                  icon={Mail}
                />
              </div>
              <div className="form-grid-2">
                <AnimatedFormField
                  label="Country Code"
                  value={complaint.countryCode}
                  fieldKey="countryCode"
                  icon={Globe}
                />
                <AnimatedFormField
                  label="Complainant Phone"
                  value={complaint.complainantPhone}
                  fieldKey="complainantPhone"
                  icon={Phone}
                />
              </div>
              <div className="form-grid-2">
                <AnimatedFormField
                  label="Date of Complaint"
                  value={complaint.dateOfComplaint}
                  fieldKey="dateOfComplaint"
                  icon={Calendar}
                />
                <AnimatedFormField
                  label="Date of Incident"
                  value={complaint.dateOfIncident}
                  fieldKey="dateOfIncident"
                  icon={Calendar}
                />
              </div>
            </CardContent>
          </Card>

          {/* AI Risk Assessment */}
          <Card className="risk-assessment-card">
            <CardHeader className="form-section-header">
              <CardTitle className="form-section-title">
                <Activity size={16} />
                AI Risk Assessment
              </CardTitle>
              <SeverityBadge level={complaint.severityLevel} />
            </CardHeader>
            <CardContent className="form-section-content">
              <div className="risk-score-section">
                <div className="risk-score-header">
                  <Label className="form-label">Risk Score</Label>
                  <span className="risk-score-value">
                    {complaint.riskScore}/100
                  </span>
                </div>
                <Progress
                  value={complaint.riskScore}
                  className="risk-progress"
                />
              </div>

              <Separator className="form-separator" />

              {complaint.recommendedActions.length > 0 && (
                <div className="risk-section">
                  <Label className="form-label">Recommended Actions</Label>
                  <div className="risk-actions-list">
                    {complaint.recommendedActions.map((action, i) => (
                      <div key={i} className="risk-action-item">
                        <CheckCircle2
                          size={14}
                          className="risk-action-icon"
                        />
                        <span>{action}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {complaint.rootCauseHypothesis && (
                <div className="risk-section">
                  <Label className="form-label">Root Cause Hypothesis</Label>
                  <p className="risk-text">{complaint.rootCauseHypothesis}</p>
                </div>
              )}

              {complaint.capaRecommendation && (
                <div className="risk-section">
                  <Label className="form-label">CAPA Recommendation</Label>
                  <p className="risk-text">{complaint.capaRecommendation}</p>
                </div>
              )}

              {complaint.completenessScore > 0 && (
                <>
                  <Separator className="form-separator" />
                  <div className="risk-score-section">
                    <div className="risk-score-header">
                      <Label className="form-label">Completeness Score</Label>
                      <span className="completeness-value">
                        {complaint.completenessScore}%
                      </span>
                    </div>
                    <Progress
                      value={complaint.completenessScore}
                      className="completeness-progress"
                    />
                  </div>
                </>
              )}

              {complaint.complaintSummary && (
                <div className="risk-section">
                  <Label className="form-label">AI Summary</Label>
                  <p className="risk-text">{complaint.complaintSummary}</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Submit Action */}
          <div className="complaint-submit-bar">
            <div className="complaint-submit-copy">
              <p className="complaint-submit-title">Ready to submit?</p>
              <p className="complaint-submit-desc">
                Submits to the complaints table after  retrieval
                and LLM duplicate verification. Duplicates are rejected.
              </p>
            </div>
            <Button
              className="complaint-submit-btn"
              onClick={handleSubmit}
              disabled={!canSubmit || isSubmitting || complaint.status === "submitted"}
            >
              {isSubmitting ? (
                <Loader2 size={15} className="animate-spin mr-1.5" />
              ) : (
                <Send size={15} className="mr-1.5" />
              )}
              {complaint.status === "submitted"
                ? "Already Submitted"
                : isSubmitting
                  ? "Checking Duplicates..."
                  : "Submit Complaint"}
            </Button>
          </div>

          {submitSuccess && (
            <div className="complaint-submit-success">{submitSuccess}</div>
          )}
          {submitError && (
            <div className="complaint-submit-error">{submitError}</div>
          )}
        </div>
      </ScrollArea>

      {duplicateDetails && (
        <DuplicateAlertModal
          isOpen={duplicateOpen}
          details={duplicateDetails}
          onDismiss={() => {
            setDuplicateOpen(false);
            setSubmitError(
              "Submission rejected: potential duplicate complaint detected."
            );
          }}
          isSubmitting={false}
        />
      )}
    </div>
  );
}
