import { createSlice, type PayloadAction } from "@reduxjs/toolkit";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
  toolCalls?: { tool: string; result: unknown }[];
  isLoading?: boolean;
}

interface ChatState {
  messages: ChatMessage[];
  isLoading: boolean;
  isUploading: boolean;
  error: string | null;
}

const initialState: ChatState = {
  messages: [
    {
      id: "welcome",
      role: "assistant",
      content:
        "Hello! I'm the **AI Co-pilot**, your AI assistant for pharmaceutical complaint management. I can help you:\n\n• **Log a new complaint** — describe the issue in natural language\n• **Edit existing complaints** — tell me what to change\n• **Extract from documents** — upload a PDF or email\n• **Assess risks** — I'll evaluate severity and recommend actions\n\nHow can I help you today?",
      timestamp: new Date().toISOString(),
    },
  ],
  isLoading: false,
  isUploading: false,
  error: null,
};

const chatSlice = createSlice({
  name: "chat",
  initialState,
  reducers: {
    addMessage(state, action: PayloadAction<ChatMessage>) {
      state.messages.push(action.payload);
    },
    setLoading(state, action: PayloadAction<boolean>) {
      state.isLoading = action.payload;
    },
    setUploading(state, action: PayloadAction<boolean>) {
      state.isUploading = action.payload;
    },
    setError(state, action: PayloadAction<string | null>) {
      state.error = action.payload;
    },
    clearChat(state) {
      state.messages = [initialState.messages[0]];
      state.isLoading = false;
      state.isUploading = false;
      state.error = null;
    },
  },
});

export const { addMessage, setLoading, setUploading, setError, clearChat } =
  chatSlice.actions;
export default chatSlice.reducer;
