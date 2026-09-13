import { useState, useRef, useEffect } from "react";
import {
  Send,
  Bot,
  User,
  Loader2,
  Wrench,
  Paperclip,
  Sparkles,
  UploadCloud,
  FileText,
  X,
  Trash2,
  FileUp,
  AlertCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { setComplaintData } from "@/store/complaintSlice";
import {
  addMessage,
  setLoading,
  setUploading,
  type ChatMessage,
} from "@/store/chatSlice";
import {
  sendChatMessage,
  uploadDocument,
  type ComplaintData,
} from "@/services/api";
import { parseOpenUILang, RenderOpenUIComponent } from "@/lib/openui";

const SAMPLE_COMPLAINT_DOCUMENT = `From: john.smith@pharmaretail.com
To: quality.complaints@pharmamanufacturer.com
Subject: Urgent - Product Quality Complaint - Amoxicillin Capsules 500mg
Date: September 10, 2026

Dear Quality Assurance Team,

I am writing to report a product quality complaint regarding Amoxicillin Capsules 500mg that we received from one of our retail pharmacy customers.

PRODUCT DETAILS:
- Product Name: Amoxicillin Capsules
- Strength: 500mg
- Dosage Form: Hard Gelatin Capsules
- Batch Number: AMX-2024-0847
- Lot Number: L-2024-03-AMX
- Manufacturing Date: 2024-03-15
- Expiry Date: 2026-03-14
- NDC: 12345-678-90

COMPLAINT DETAILS:
The pharmacy reported that upon opening a sealed bottle of 500 count Amoxicillin 500mg capsules (Batch AMX-2024-0847), approximately 15-20 capsules showed visible discoloration. The affected capsules exhibited yellowish-brown spots on the capsule shell, which was different from the typical opaque yellow/blue appearance.

The pharmacist noted that:
1. The bottle seal was intact upon receipt
2. The discoloration was observed on capsule shells only
3. No unusual odor was detected
4. The affected capsules appeared slightly softer than normal capsules
5. Storage conditions at the pharmacy were within specifications (controlled room temperature, 20-25°C)

The observation was made on September 8, 2026, during routine inventory inspection.

COMPLAINANT INFORMATION:
- Name: Dr. John Smith, PharmD
- Title: Lead Pharmacist
- Pharmacy: MedCare Retail Pharmacy #247
- Contact: john.smith@pharmaretail.com
- Phone: (555) 123-4567

This is being reported as an urgent quality complaint as the product was available for patient dispensing. No adverse events have been reported from patients who may have received capsules from this batch.

We have quarantined the remaining bottles from this batch (approximately 25 bottles) and are awaiting your guidance on further action.

Please advise on the next steps.

Best regards,
Dr. John Smith, PharmD
Lead Pharmacist
MedCare Retail Pharmacy #247`;

function MessageBubble({
  message,
  onFormSubmit,
}: {
  message: ChatMessage;
  onFormSubmit?: (data: Record<string, string>) => void;
}) {
  const isUser = message.role === "user";
  const { plainText, openUIElements } = parseOpenUILang(message.content);

  return (
    <div
      className={`chat-message ${isUser ? "chat-message-user" : "chat-message-assistant"
        }`}
    >
      <div
        className={`chat-avatar ${isUser ? "chat-avatar-user" : "chat-avatar-assistant"
          }`}
      >
        <Avatar className="chat-avatar-inner">
          {isUser ? (
            <User size={16} className="chat-avatar-icon" />
          ) : (
            <Bot size={16} className="chat-avatar-icon" />
          )}
        </Avatar>
      </div>
      <div
        className={`chat-bubble ${isUser ? "chat-bubble-user" : "chat-bubble-assistant"
          }`}
      >
        {message.toolCalls && message.toolCalls.length > 0 && (
          <div className="chat-tool-badges">
            {message.toolCalls.map((tc, idx) => (
              <Badge key={idx} variant="outline" className="chat-tool-badge">
                <Wrench size={10} className="mr-1" />
                {tc.tool.replace(/_/g, " ")}
              </Badge>
            ))}
          </div>
        )}

        {/* Render OpenUI Generative UI Components */}
        {openUIElements && openUIElements.length > 0 && (
          <div className="openui-generative-container">
            {openUIElements.map((el, i) => (
              <RenderOpenUIComponent key={i} element={el} onSubmit={onFormSubmit} />
            ))}
          </div>
        )}

        <div className="chat-content">
          {(plainText || message.content).split("\n").map((line, i) => {
            // Simple markdown: bold
            const formatted = line.replace(
              /\*\*(.*?)\*\*/g,
              "<strong>$1</strong>"
            );
            // Bullet points
            if (line.startsWith("• ") || line.startsWith("- ")) {
              return (
                <p
                  key={i}
                  className="chat-bullet"
                  dangerouslySetInnerHTML={{
                    __html: `<span class="chat-bullet-dot">•</span> ${formatted.replace(/^[•\-]\s*/, "")}`,
                  }}
                />
              );
            }
            if (!line.trim()) return <br key={i} />;
            return (
              <p
                key={i}
                dangerouslySetInnerHTML={{ __html: formatted }}
              />
            );
          })}
        </div>
        <span className="chat-timestamp">
          {new Date(message.timestamp).toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </span>
      </div>
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="chat-message chat-message-assistant">
      <div className="chat-avatar chat-avatar-assistant">
        <Avatar className="chat-avatar-inner">
          <Bot size={16} className="chat-avatar-icon" />
        </Avatar>
      </div>
      <div className="chat-bubble chat-bubble-assistant">
        <div className="typing-indicator">
          <Sparkles size={14} className="typing-sparkle" />
          <span>AI is thinking</span>
          <div className="typing-dots">
            <span className="typing-dot" />
            <span className="typing-dot" />
            <span className="typing-dot" />
          </div>
        </div>
      </div>
    </div>
  );
}

export default function CopilotChat() {
  const dispatch = useAppDispatch();
  const { messages, isLoading, isUploading } = useAppSelector(
    (state) => state.chat
  );
  const complaint = useAppSelector((state) => state.complaint);
  const [input, setInput] = useState("");
  const [showUploadSection, setShowUploadSection] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);
  const [stagedFile, setStagedFile] = useState<File | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const scrollRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  const updateComplaint = (data: ComplaintData) => {
    const mapped: Record<string, unknown> = {};
    for (const [key, value] of Object.entries(data)) {
      if (value !== undefined && value !== null && value !== "") {
        mapped[key] = value;
      }
    }
    dispatch(setComplaintData(mapped));
  };

  const sendMessageText = async (textToSend: string) => {
    const text = textToSend.trim();
    if (!text || isLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      content: text,
      timestamp: new Date().toISOString(),
    };
    dispatch(addMessage(userMessage));
    setInput("");
    dispatch(setLoading(true));

    try {
      const chatHistory = messages
        .filter((m) => m.role !== "system")
        .map((m) => ({ role: m.role, content: m.content }));

      const response = await sendChatMessage({
        message: text,
        complaint_id: complaint.id,
        complaint_data: complaint,
        chat_history: chatHistory.slice(-10), // Last 10 messages for context
      });

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: response.response,
        timestamp: new Date().toISOString(),
        toolCalls: response.tool_calls,
      };
      dispatch(addMessage(assistantMessage));

      if (response.complaint_data) {
        updateComplaint(response.complaint_data);
      }
    } catch (err: unknown) {
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: `Error processing request: ${err instanceof Error ? err.message : "Unknown error"}`,
        timestamp: new Date().toISOString(),
      };
      dispatch(addMessage(errorMessage));
    } finally {
      dispatch(setLoading(false));
    }
  };

  const handleSend = () => sendMessageText(input);

  const handleFormSubmit = (formData: Record<string, string>) => {
    dispatch(setComplaintData(formData));
    const fieldPairs = Object.entries(formData)
      .filter(([_, v]) => v && v.trim())
      .map(([k, v]) => `${k}: ${v}`)
      .join(", ");
    if (fieldPairs) {
      sendMessageText(`Provided missing details - ${fieldPairs}`);
    }
  };

  const processUpload = async (file: File) => {
    if (!file) return;

    dispatch(setUploading(true));
    setUploadError(null);

    const uploadMsg: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      content: `📎 Uploaded document: **${file.name}** (${(file.size / 1024).toFixed(1)} KB)`,
      timestamp: new Date().toISOString(),
    };
    dispatch(addMessage(uploadMsg));
    dispatch(setLoading(true));

    try {
      const response = await uploadDocument(file);

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: response.response,
        timestamp: new Date().toISOString(),
        toolCalls: response.tool_calls,
      };
      dispatch(addMessage(assistantMessage));

      if (response.complaint_data) {
        updateComplaint(response.complaint_data);
      }
      setStagedFile(null);
      setShowUploadSection(false);
    } catch (error) {
      console.error("Upload error:", error);
      const errMsg =
        "I couldn't process the uploaded document. Please ensure the backend server is running and the file is a valid PDF, text, or email file.";
      setUploadError(errMsg);
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: errMsg,
        timestamp: new Date().toISOString(),
      };
      dispatch(addMessage(errorMessage));
    } finally {
      dispatch(setLoading(false));
      dispatch(setUploading(false));
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleFileSelect = (file: File) => {
    setUploadError(null);
    setStagedFile(file);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleLoadSample = () => {
    const blob = new Blob([SAMPLE_COMPLAINT_DOCUMENT], { type: "text/plain" });
    const sampleFile = new File([blob], "amoxicillin_complaint_email.txt", {
      type: "text/plain",
      lastModified: Date.now(),
    });
    handleFileSelect(sampleFile);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="copilot-container">
      {/* Header */}
      <div className="copilot-header">
        <div className="copilot-header-left">
          <div className="copilot-header-icon">
            <Sparkles size={18} />
          </div>
          <div>
            <h2 className="copilot-title">AI Co-pilot</h2>
            <p className="copilot-subtitle">AI-Powered Quality Assistant</p>
          </div>
        </div>
        {/* <Badge className="copilot-model-badge">Groq LLM</Badge> */}
      </div>

      {/* Messages */}
      <ScrollArea className="copilot-messages" ref={scrollRef}>
        <div className="copilot-messages-inner">
          {messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} onFormSubmit={handleFormSubmit} />
          ))}
          {isLoading && <TypingIndicator />}
        </div>
      </ScrollArea>

      {/* Input Area */}
      <div className="copilot-input-area">
        {/* Expandable File Upload Section in Right Chat */}
        {showUploadSection && (
          <div className="copilot-upload-section">
            <div className="copilot-upload-header">
              <div className="copilot-upload-title-wrap">
                <FileUp size={15} className="text-primary" />
                <span className="copilot-upload-title">Upload Complaint Document</span>
                <Badge variant="outline" className="copilot-upload-badge">
                  AI Extraction
                </Badge>
              </div>
              <Button
                variant="ghost"
                size="sm"
                className="copilot-upload-close-btn"
                onClick={() => {
                  setShowUploadSection(false);
                  setStagedFile(null);
                  setUploadError(null);
                }}
                disabled={isUploading}
              >
                <X size={14} />
              </Button>
            </div>

            {/* Staged file card */}
            {stagedFile ? (
              <div className="copilot-staged-card">
                <div className="copilot-staged-info">
                  <FileText size={22} className="copilot-staged-icon" />
                  <div className="copilot-staged-details">
                    <span className="copilot-staged-name" title={stagedFile.name}>
                      {stagedFile.name}
                    </span>
                    <span className="copilot-staged-size">
                      {(stagedFile.size / 1024).toFixed(1)} KB • Ready for AI extraction
                    </span>
                  </div>
                </div>
                <div className="copilot-staged-actions">
                  <Button
                    size="sm"
                    className="copilot-extract-btn"
                    onClick={() => processUpload(stagedFile)}
                    disabled={isUploading || isLoading}
                  >
                    {isUploading ? (
                      <Loader2 size={13} className="animate-spin mr-1" />
                    ) : (
                      <Sparkles size={13} className="mr-1" />
                    )}
                    Extract & Assess
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="copilot-remove-staged-btn"
                    onClick={() => setStagedFile(null)}
                    disabled={isUploading}
                    title="Remove file"
                  >
                    <Trash2 size={13} />
                  </Button>
                </div>
              </div>
            ) : (
              /* Dropzone */
              <div
                className={`copilot-dropzone ${isDragOver ? "copilot-dropzone-active" : ""}`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => !isUploading && fileInputRef.current?.click()}
              >
                <UploadCloud size={24} className="copilot-dropzone-icon" />
                <p className="copilot-dropzone-text">
                  Drag & drop document here, or <span className="copilot-dropzone-link">browse</span>
                </p>
                <p className="copilot-dropzone-hint">
                  Supports PDF, TXT, Email (.eml, .msg), CSV (Max 10MB)
                </p>
              </div>
            )}

            {/* Uploading progress indicator */}
            {isUploading && (
              <div className="copilot-uploading-box">
                <div className="copilot-uploading-row">
                  <Loader2 size={14} className="animate-spin text-primary" />
                  <span>Extracting quality data & assessing risk with LangGraph...</span>
                </div>
              </div>
            )}

            {/* Upload error alert */}
            {uploadError && (
              <div className="text-[11px] text-red-600 flex items-center gap-1 mt-1">
                <AlertCircle size={12} />
                <span>{uploadError}</span>
              </div>
            )}

            {/* Sample file shortcut */}
            {!stagedFile && !isUploading && (
              <div className="copilot-upload-footer">
                <span className="text-[11px] text-muted-foreground">
                  Need a sample document?
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  className="copilot-sample-btn"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleLoadSample();
                  }}
                >
                  <Sparkles size={11} className="mr-1 text-primary" />
                  Load Sample Email
                </Button>
              </div>
            )}
          </div>
        )}

        <div className="copilot-input-wrapper">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Describe a complaint, ask to edit, or upload a document..."
            className="copilot-textarea"
            rows={2}
            disabled={isLoading}
          />
          <div className="copilot-input-actions">
            <input
              type="file"
              ref={fileInputRef}
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) handleFileSelect(f);
              }}
              accept=".pdf,.txt,.eml,.msg,.csv"
              className="hidden"
              id="file-upload"
            />
            <Button
              variant="ghost"
              size="sm"
              className={`copilot-upload-btn ${showUploadSection ? "copilot-upload-btn-active" : ""}`}
              onClick={() => {
                setShowUploadSection((prev) => !prev);
                setUploadError(null);
              }}
              disabled={isLoading || isUploading}
              title={showUploadSection ? "Close file upload" : "Attach complaint document"}
            >
              {isUploading ? (
                <Loader2 size={16} className="animate-spin" />
              ) : (
                <Paperclip size={16} />
              )}
            </Button>
            <Button
              size="sm"
              className="copilot-send-btn"
              onClick={handleSend}
              disabled={!input.trim() || isLoading}
            >
              {isLoading ? (
                <Loader2 size={16} className="animate-spin" />
              ) : (
                <Send size={16} />
              )}
            </Button>
          </div>
        </div>
        <p className="copilot-hint">
          Press <kbd>Enter</kbd> to send, <kbd>Shift+Enter</kbd> for new line
        </p>
      </div>
    </div>
  );
}
