import { useState, useEffect } from "react";
import { Provider } from "react-redux";
import { store } from "@/store/store";
import { TooltipProvider } from "@/components/ui/tooltip";
import Header from "@/components/Header";
import ComplaintForm from "@/components/ComplaintForm";
import CopilotChat from "@/components/CopilotChat";
import ComplaintsList from "@/components/ComplaintsList";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { setComplaintData, resetComplaint } from "@/store/complaintSlice";
import { clearChat } from "@/store/chatSlice";
import { getComplaint, type ComplaintData } from "@/services/api";
import { Loader2 } from "lucide-react";

function AppContent() {
  const [activeView, setActiveView] = useState<"list" | "form">("list");
  const [isLoadingRoute, setIsLoadingRoute] = useState(false);
  const dispatch = useAppDispatch();
  const currentComplaint = useAppSelector((state) => state.complaint);

  // Helper function to safely update browser URL
  const pushUrl = (path: string) => {
    if (window.location.pathname !== path) {
      window.history.pushState({}, "", path);
    }
  };

  const handleNavigateToList = () => {
    pushUrl("/complaints");
    setActiveView("list");
  };

  const handleNewComplaint = () => {
    dispatch(resetComplaint());
    dispatch(clearChat());
    pushUrl("/complaints/new");
    setActiveView("form");
  };

  const [pendingAnalysis, setPendingAnalysis] = useState<ComplaintData | null>(null);

  const handleSelectComplaint = (complaint: ComplaintData) => {
    dispatch(clearChat());
    dispatch(setComplaintData(complaint));
    if (complaint.id) {
      pushUrl(`/complaints/${complaint.id}`);
    } else {
      pushUrl("/complaints/new");
    }
    setPendingAnalysis(complaint);
    setActiveView("form");
  };

  // Sync URL changes with view & store state
  useEffect(() => {
    const handleUrlChange = async () => {
      const path = window.location.pathname;

      if (path === "/complaints/new") {
        dispatch(resetComplaint());
        dispatch(clearChat());
        setActiveView("form");
      } else if (path.startsWith("/complaints/") && path !== "/complaints/" && path !== "/complaints") {
        const complaintId = path.replace("/complaints/", "").trim();
        if (complaintId && complaintId !== "new") {
          setIsLoadingRoute(true);
          dispatch(clearChat());
          try {
            const data = await getComplaint(complaintId);
            if (data) {
              dispatch(setComplaintData(data));
              setPendingAnalysis(data);
            }
          } catch (err) {
            console.error("Failed to fetch complaint by ID:", err);
          } finally {
            setIsLoadingRoute(false);
          }
          setActiveView("form");
        }
      } else {
        setActiveView("list");
      }
    };

    handleUrlChange();

    window.addEventListener("popstate", handleUrlChange);
    return () => window.removeEventListener("popstate", handleUrlChange);
  }, [dispatch]);

  // Keep URL updated if complaint.id changes while on /complaints/new
  useEffect(() => {
    if (activeView === "form" && currentComplaint.id && window.location.pathname === "/complaints/new") {
      pushUrl(`/complaints/${currentComplaint.id}`);
    }
  }, [activeView, currentComplaint.id]);

  return (
    <div className="app-root">
      <Header
        activeView={activeView}
        onNavigate={handleNavigateToList}
        onNewComplaint={handleNewComplaint}
      />
      {isLoadingRoute ? (
        <div className="flex-1 flex flex-col items-center justify-center py-24 gap-3 text-slate-500">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
          <p className="text-sm font-medium">Loading complaint details...</p>
        </div>
      ) : activeView === "list" ? (
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
            <CopilotChat
              pendingAnalysis={pendingAnalysis}
              onAnalysisConsumed={() => setPendingAnalysis(null)}
            />
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
