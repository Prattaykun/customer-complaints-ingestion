import axios from "axios";

const API_BASE_URL = "http://localhost:8000/api";

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

export default api;
