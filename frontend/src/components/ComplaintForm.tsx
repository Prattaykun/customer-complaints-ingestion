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
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useAppSelector } from "@/store/hooks";

import { AnimatedFormField } from "@/components/AnimatedFormField";

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
  const complaint = useAppSelector((state) => state.complaint);

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
                  value={complaint.complainantEmail || (complaint.complainantContact && complaint.complainantContact.includes("@") ? complaint.complainantContact : "")}
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
                  value={complaint.complainantPhone || (!complaint.complainantContact.includes("@") ? complaint.complainantContact : "")}
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
              {/* Risk Score */}
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

              {/* Recommended Actions */}
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

              {/* Root Cause */}
              {complaint.rootCauseHypothesis && (
                <div className="risk-section">
                  <Label className="form-label">Root Cause Hypothesis</Label>
                  <p className="risk-text">{complaint.rootCauseHypothesis}</p>
                </div>
              )}

              {/* CAPA */}
              {complaint.capaRecommendation && (
                <div className="risk-section">
                  <Label className="form-label">CAPA Recommendation</Label>
                  <p className="risk-text">{complaint.capaRecommendation}</p>
                </div>
              )}

              {/* Completeness */}
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

              {/* Summary */}
              {complaint.complaintSummary && (
                <div className="risk-section">
                  <Label className="form-label">AI Summary</Label>
                  <p className="risk-text">{complaint.complaintSummary}</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </ScrollArea>
    </div>
  );
}
