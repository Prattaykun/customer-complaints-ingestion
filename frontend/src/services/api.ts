import axios from "axios";

const getApiBaseUrl = () => {
  const envUrl = import.meta.env.VITE_API_BASE_URL;
  if (!envUrl) return "http://localhost:8000/api";
  const trimmed = envUrl.trim().replace(/\/+$/, "");
  return trimmed.endsWith("/api") ? trimmed : `${trimmed}/api`;
};

const API_BASE_URL = getApiBaseUrl();

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

export interface ComplaintData {
  id?: string | null;
  productName?: string;
  productStrength?: string;
  dosageForm?: string;
  batchNumber?: string;
  lotNumber?: string;
  manufacturingDate?: string;
  expiryDate?: string;
  complaintCategory?: string;
  complaintDescription?: string;
  complainantName?: string;
  complainantContact?: string;
  complainantPhone?: string;
  complainantEmail?: string;
  countryCode?: string;
  dateOfComplaint?: string;
  dateOfIncident?: string;
  severityLevel?: string;
  riskScore?: number;
  recommendedActions?: string[];
  rootCauseHypothesis?: string;
  capaRecommendation?: string;
  complaintSummary?: string;
  completenessScore?: number;
  status?: string;
}

export interface ChatRequest {
  message: string;
  complaint_id?: string | null;
  complaint_data?: ComplaintData;
  chat_history?: { role: string; content: string }[];
}

export interface ChatResponse {
  response: string;
  complaint_data: ComplaintData | null;
  tool_calls: { tool: string; result: unknown }[];
}

export interface UploadResponse {
  response: string;
  complaint_data: ComplaintData | null;
  extracted_text: string;
  tool_calls: { tool: string; result: unknown }[];
}

export async function sendChatMessage(
  request: ChatRequest
): Promise<ChatResponse> {
  const { data } = await api.post<ChatResponse>("/chat", request);
  return data;
}

export async function uploadDocument(
  file: File
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await api.post<UploadResponse>("/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function getComplaints(): Promise<ComplaintData[]> {
  const { data } = await api.get<ComplaintData[]>("/complaints");
  return data;
}

export async function getComplaint(id: string): Promise<ComplaintData> {
  const { data } = await api.get<ComplaintData>(`/complaints/${id}`);
  return data;
}

export interface DuplicateDetails {
  matched_complaint_id?: string;
  matched_product?: string;
  matched_batch?: string;
  similarity_score: number;
  confidence: number;
  explanation: string;
}

export interface SubmitResponse {
  success: boolean;
  message: string;
  complaint: ComplaintData | null;
  duplicate_detected: boolean;
  duplicate_details: DuplicateDetails | null;
}

export async function submitComplaint(
  complaintData: ComplaintData,
  force: boolean = false
): Promise<SubmitResponse> {
  const { data } = await api.post<SubmitResponse>(
    `/complaints/submit?force=${force}`,
    complaintData
  );
  return data;
}

export default api;
