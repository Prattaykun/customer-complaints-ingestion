import { createSlice, type PayloadAction } from "@reduxjs/toolkit";

export interface ComplaintState {
  id: string | null;
  productName: string;
  productStrength: string;
  dosageForm: string;
  batchNumber: string;
  lotNumber: string;
  manufacturingDate: string;
  expiryDate: string;
  complaintCategory: string;
  complaintDescription: string;
  complainantName: string;
  complainantContact: string;
  complainantPhone: string;
  complainantEmail: string;
  countryCode: string;
  dateOfComplaint: string;
  dateOfIncident: string;
  severityLevel: string;
  riskScore: number;
  recommendedActions: string[];
  rootCauseHypothesis: string;
  capaRecommendation: string;
  complaintSummary: string;
  completenessScore: number;
  status: string;
}

const initialState: ComplaintState = {
  id: null,
  productName: "",
  productStrength: "",
  dosageForm: "",
  batchNumber: "",
  lotNumber: "",
  manufacturingDate: "",
  expiryDate: "",
  complaintCategory: "",
  complaintDescription: "",
  complainantName: "",
  complainantContact: "",
  complainantPhone: "",
  complainantEmail: "",
  countryCode: "",
  dateOfComplaint: "",
  dateOfIncident: "",
  severityLevel: "",
  riskScore: 0,
  recommendedActions: [],
  rootCauseHypothesis: "",
  capaRecommendation: "",
  complaintSummary: "",
  completenessScore: 0,
  status: "draft",
};

const complaintSlice = createSlice({
  name: "complaint",
  initialState,
  reducers: {
    setComplaintData(state, action: PayloadAction<Partial<ComplaintState>>) {
      return { ...state, ...action.payload };
    },
    resetComplaint() {
      return { ...initialState };
    },
    updateField(
      state,
      action: PayloadAction<{ field: keyof ComplaintState; value: unknown }>
    ) {
      const { field, value } = action.payload;
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (state as any)[field] = value;
    },
  },
});

export const { setComplaintData, resetComplaint, updateField } =
  complaintSlice.actions;
export default complaintSlice.reducer;
