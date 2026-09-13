import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import {
  AlertTriangle,
  CheckCircle2,
  Package,
  Activity,
  Send,
  Phone,
  Mail,
  Globe,
  ClipboardList,
} from "lucide-react";

/**
 * OpenUI Lang Parser & Generative UI Component Renderer.
 * Parses compact OpenUI Lang markup constructs such as:
 * <ComplaintCard title="..." product="..." batch="..." severity="..." risk="..." />
 * <RiskGauge level="..." score="..." />
 * <CompletenessWidget score="..." missing="..." />
 * <MissingInfoForm title="..." fields="complainantEmail,complainantPhone,countryCode" prompt="..." />
 */

export interface OpenUIComponentProps {
  [key: string]: string | number | boolean;
}

export interface OpenUIElement {
  tag: string;
  props: OpenUIComponentProps;
  children?: string | OpenUIElement[];
}

/**
 * Parses OpenUI Lang tags in AI co-pilot responses.
 */
export function parseOpenUILang(text: string): { plainText: string; openUIElements: OpenUIElement[] } {
  const elements: OpenUIElement[] = [];
  
  // Regex to match OpenUI Lang component tags like <ComplaintCard prop="val" ... />
  const tagRegex = /<([A-Z][a-zA-Z0-9]+)\s+([^>]*?)\/?>/g;
  let match;
  
  while ((match = tagRegex.exec(text)) !== null) {
    const tagName = match[1];
    const attrString = match[2];
    
    // Parse attributes
    const props: OpenUIComponentProps = {};
    const attrRegex = /([a-zA-Z0-9_]+)=(?:"([^"]*)"|'([^']*)'|([^\s>]+))/g;
    let attrMatch;
    while ((attrMatch = attrRegex.exec(attrString)) !== null) {
      const key = attrMatch[1];
      const val = attrMatch[2] ?? attrMatch[3] ?? attrMatch[4];
      props[key] = isNaN(Number(val)) ? val : Number(val);
    }
    
    elements.push({ tag: tagName, props });
  }

  // Remove the OpenUI tags from plain text for clean chat bubble rendering
  const plainText = text.replace(tagRegex, "").trim();

  return { plainText, openUIElements: elements };
}

/**
 * Interactive OpenUI Missing Information Form Component
 */
export function MissingInfoFormComponent({
  element,
  onSubmit,
}: {
  element: OpenUIElement;
  onSubmit?: (data: Record<string, string>) => void;
}) {
  const fieldsProp = String(element.props.fields || "complainantEmail,complainantPhone,countryCode");
  const fieldList = fieldsProp.split(",").map((f) => f.trim()).filter(Boolean);
  const title = String(element.props.title || "Provide Missing Details");
  const prompt = String(element.props.prompt || "Please fill in the required fields below:");

  const [formValues, setFormValues] = useState<Record<string, string>>({
    countryCode: "+1",
    complainantEmail: "",
    complainantPhone: "",
  });
  const [submitted, setSubmitted] = useState(false);

  const handleInputChange = (field: string, val: string) => {
    setFormValues((prev) => ({ ...prev, [field]: val }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitted(true);
    if (onSubmit) {
      onSubmit(formValues);
    }
  };

  const countryCodeOptions = [
    { code: "+1", label: "+1 (USA / Canada)" },
    { code: "+44", label: "+44 (United Kingdom)" },
    { code: "+91", label: "+91 (India)" },
    { code: "+49", label: "+49 (Germany)" },
    { code: "+33", label: "+33 (France)" },
    { code: "+81", label: "+81 (Japan)" },
    { code: "+86", label: "+86 (China)" },
    { code: "+61", label: "+61 (Australia)" },
    { code: "+55", label: "+55 (Brazil)" },
    { code: "+41", label: "+41 (Switzerland)" },
  ];

  const getFieldLabel = (field: string) => {
    switch (field) {
      case "complainantEmail":
        return "Complainant Email";
      case "complainantPhone":
        return "Phone Number";
      case "countryCode":
        return "Country Code";
      case "productName":
        return "Product Name";
      case "batchNumber":
        return "Batch Number";
      case "complainantName":
        return "Complainant Name";
      default:
        return field.replace(/([A-Z])/g, " $1").replace(/^./, (str) => str.toUpperCase());
    }
  };

  if (submitted) {
    return (
      <div className="my-3 p-3 rounded-lg border border-emerald-500/30 bg-emerald-500/10 text-emerald-950 dark:text-emerald-200 text-xs flex items-center justify-between">
        <div className="flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          <span className="font-medium">Details submitted to QMS Co-pilot successfully!</span>
        </div>
        <Badge variant="outline" className="text-[10px] bg-emerald-50 text-emerald-700 border-emerald-300">
          Submitted
        </Badge>
      </div>
    );
  }

  return (
    <Card className="my-3 border border-blue-200 dark:border-blue-900/50 bg-gradient-to-br from-blue-50/50 to-indigo-50/30 dark:from-slate-900 dark:to-blue-950/40 shadow-sm">
      <CardHeader className="py-2.5 px-3.5 flex flex-row items-center justify-between pb-2 border-b border-blue-100 dark:border-blue-900/40">
        <div className="flex items-center gap-2">
          <ClipboardList className="w-4 h-4 text-blue-600 dark:text-blue-400" />
          <CardTitle className="text-xs font-semibold text-blue-950 dark:text-blue-100">
            {title}
          </CardTitle>
        </div>
        <Badge className="text-[10px] bg-blue-100 text-blue-700 dark:bg-blue-900/50 dark:text-blue-300 border-none">
          Action Required
        </Badge>
      </CardHeader>
      <CardContent className="p-3.5 text-xs space-y-3">
        <p className="text-muted-foreground text-[11px] leading-relaxed">{prompt}</p>
        <form onSubmit={handleSubmit} className="space-y-2.5">
          {fieldList.includes("countryCode") && (
            <div className="space-y-1">
              <Label className="text-[11px] font-medium flex items-center gap-1.5 text-slate-700 dark:text-slate-300">
                <Globe className="w-3 h-3 text-blue-500" />
                Country Code
              </Label>
              <select
                value={formValues.countryCode || "+1"}
                onChange={(e) => handleInputChange("countryCode", e.target.value)}
                className="w-full h-8 text-xs rounded-md border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-2.5 py-1 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                {countryCodeOptions.map((opt) => (
                  <option key={opt.code} value={opt.code}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
          )}

          {fieldList.includes("complainantPhone") && (
            <div className="space-y-1">
              <Label className="text-[11px] font-medium flex items-center gap-1.5 text-slate-700 dark:text-slate-300">
                <Phone className="w-3 h-3 text-blue-500" />
                Phone Number
              </Label>
              <Input
                type="tel"
                placeholder="e.g. (555) 123-4567"
                value={formValues.complainantPhone || ""}
                onChange={(e) => handleInputChange("complainantPhone", e.target.value)}
                className="h-8 text-xs bg-white dark:bg-slate-900"
              />
            </div>
          )}

          {fieldList.includes("complainantEmail") && (
            <div className="space-y-1">
              <Label className="text-[11px] font-medium flex items-center gap-1.5 text-slate-700 dark:text-slate-300">
                <Mail className="w-3 h-3 text-blue-500" />
                Email Address
              </Label>
              <Input
                type="email"
                placeholder="e.g. john.smith@pharmaretail.com"
                value={formValues.complainantEmail || ""}
                onChange={(e) => handleInputChange("complainantEmail", e.target.value)}
                className="h-8 text-xs bg-white dark:bg-slate-900"
              />
            </div>
          )}

          {fieldList
            .filter((f) => !["countryCode", "complainantPhone", "complainantEmail"].includes(f))
            .map((field) => (
              <div key={field} className="space-y-1">
                <Label className="text-[11px] font-medium text-slate-700 dark:text-slate-300">
                  {getFieldLabel(field)}
                </Label>
                <Input
                  type="text"
                  placeholder={`Enter ${getFieldLabel(field)}...`}
                  value={formValues[field] || ""}
                  onChange={(e) => handleInputChange(field, e.target.value)}
                  className="h-8 text-xs bg-white dark:bg-slate-900"
                />
              </div>
            ))}

          <Button
            type="submit"
            size="sm"
            className="w-full h-8 text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white flex items-center justify-center gap-1.5 mt-2 shadow-sm"
          >
            <Send className="w-3 h-3" />
            Submit Information
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

/**
 * Component Renderer for OpenUI Lang UI Elements
 */
export function RenderOpenUIComponent({
  element,
  onSubmit,
}: {
  element: OpenUIElement;
  onSubmit?: (data: Record<string, string>) => void;
}) {
  const { tag, props } = element;

  switch (tag) {
    case "MissingInfoForm":
      return <MissingInfoFormComponent element={element} onSubmit={onSubmit} />;

    case "ComplaintCard": {
      const severity = String(props.severity || "Minor").toLowerCase();
      const severityBg =
        severity === "critical"
          ? "bg-red-500/10 text-red-700 dark:text-red-400 border-red-200 dark:border-red-900"
          : severity === "major"
          ? "bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-200 dark:border-amber-900"
          : "bg-blue-500/10 text-blue-700 dark:text-blue-400 border-blue-200 dark:border-blue-900";

      return (
        <Card className="my-3 border border-purple-200 dark:border-purple-900/40 bg-gradient-to-br from-purple-500/5 to-blue-500/5 shadow-sm">
          <CardHeader className="py-3 px-4 flex flex-row items-center justify-between pb-2 border-b border-purple-100 dark:border-purple-950">
            <div className="flex items-center gap-2">
              <Package className="w-4 h-4 text-purple-600 dark:text-purple-400" />
              <CardTitle className="text-sm font-semibold text-purple-950 dark:text-purple-100">
                {String(props.title || "Generative Complaint Snapshot")}
              </CardTitle>
            </div>
            <Badge className={`text-xs px-2 py-0.5 border ${severityBg}`}>
              {String(props.severity || "Minor")}
            </Badge>
          </CardHeader>
          <CardContent className="p-4 text-xs space-y-2">
            {props.product && (
              <div className="flex justify-between">
                <span className="text-muted-foreground font-medium">Product:</span>
                <span className="font-semibold text-foreground">{String(props.product)}</span>
              </div>
            )}
            {props.batch && (
              <div className="flex justify-between">
                <span className="text-muted-foreground font-medium">Batch Number:</span>
                <span className="font-mono text-purple-700 dark:text-purple-300 font-semibold">
                  {String(props.batch)}
                </span>
              </div>
            )}
            {props.risk !== undefined && (
              <div className="flex justify-between items-center pt-1 border-t border-dashed">
                <span className="text-muted-foreground font-medium">Risk Score:</span>
                <span className="font-bold text-sm text-purple-600 dark:text-purple-400">
                  {String(props.risk)}/100
                </span>
              </div>
            )}
          </CardContent>
        </Card>
      );
    }

    case "RiskGauge": {
      const score = Number(props.score || 0);
      const level = String(props.level || "Minor");
      return (
        <div className="my-3 p-3 rounded-lg border border-purple-200 dark:border-purple-900/30 bg-purple-500/5 space-y-2">
          <div className="flex items-center justify-between text-xs font-semibold">
            <span className="flex items-center gap-1.5 text-purple-900 dark:text-purple-200">
              <Activity className="w-4 h-4 text-purple-600" />
              OpenUI Risk Assessment: {level}
            </span>
            <span className="text-purple-700 font-bold">{score}% Risk</span>
          </div>
          <Progress value={score} className="h-2 bg-purple-100 dark:bg-purple-950" />
        </div>
      );
    }

    case "CompletenessWidget": {
      const score = Number(props.score || 0);
      const missing = String(props.missing || "");
      return (
        <div className="my-3 p-3 rounded-lg border border-emerald-200 dark:border-emerald-900/30 bg-emerald-500/5 space-y-2">
          <div className="flex items-center justify-between text-xs font-semibold">
            <span className="flex items-center gap-1.5 text-emerald-900 dark:text-emerald-200">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              Record Completeness: {score}%
            </span>
          </div>
          <Progress value={score} className="h-2 bg-emerald-100 dark:bg-emerald-950" />
          {missing && (
            <p className="text-[11px] text-amber-700 dark:text-amber-400 mt-1">
              <AlertTriangle className="w-3 h-3 inline mr-1" />
              Missing: {missing}
            </p>
          )}
        </div>
      );
    }

    default:
      return null;
  }
}
