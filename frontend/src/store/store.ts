import { configureStore } from "@reduxjs/toolkit";
import complaintReducer from "./complaintSlice";
import chatReducer from "./chatSlice";

export const store = configureStore({
  reducer: {
    complaint: complaintReducer,
    chat: chatReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
