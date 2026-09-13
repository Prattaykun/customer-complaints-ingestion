import { useState } from "react";
import { Provider } from "react-redux";
import { store } from "@/store/store";
import { TooltipProvider } from "@/components/ui/tooltip";
import Header from "@/components/Header";
import ComplaintForm from "@/components/ComplaintForm";
import CopilotChat from "@/components/CopilotChat";
import ComplaintsList from "@/components/ComplaintsList";
import { useAppDispatch } from "@/store/hooks";
import { setComplaintData, resetComplaint } from "@/store/complaintSlice";
import { clearChat } from "@/store/chatSlice";
import type { ComplaintData } from "@/services/api";

function AppContent() {
  const [activeView, setActiveView] = useState<"list" | "form">("list");
  const dispatch = useAppDispatch();

  const handleNewComplaint = () => {
    dispatch(resetComplaint());
    dispatch(clearChat());
    setActiveView("form");
  };

  const handleSelectComplaint = (complaint: ComplaintData) => {
    dispatch(setComplaintData(complaint));
    setActiveView("form");
  };

  return (
    <div className="app-root">
      <Header
        activeView={activeView}
        onNavigate={setActiveView}
        onNewComplaint={handleNewComplaint}
      />
      {activeView === "list" ? (
        <ComplaintsList
          onNewComplaint={handleNewComplaint}
          onSelectComplaint={handleSelectComplaint}
        />
      ) : (
        <main className="app-main">
          <div className="app-panel app-panel-left">
            <ComplaintForm />
          </div>
          <div className="app-divider" />
          <div className="app-panel app-panel-right">
            <CopilotChat />
          </div>
        </main>
      )}
    </div>
  );
}

function App() {
  return (
    <Provider store={store}>
      <TooltipProvider>
        <AppContent />
      </TooltipProvider>
    </Provider>
  );
}

export default App;
