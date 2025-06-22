"use client";

import React, { createContext, useContext, useReducer } from "react";
import { journalDataReducer, initialState } from "./reducer";
import type { JournalDataState, JournalDataAction } from "./types";

interface JournalDataContextType {
  state: JournalDataState;
  dispatch: React.Dispatch<JournalDataAction>;
}

const JournalDataContext = createContext<JournalDataContextType | undefined>(
  undefined
);

export const useJournalDataContext = () => {
  const context = useContext(JournalDataContext);
  if (context === undefined) {
    throw new Error(
      "useJournalDataContext must be used within a JournalDataProvider"
    );
  }
  return context;
};

interface JournalDataProviderProps {
  children: React.ReactNode;
}

export const JournalDataProvider: React.FC<JournalDataProviderProps> = ({
  children,
}) => {
  const [state, dispatch] = useReducer(journalDataReducer, initialState);

  return (
    <JournalDataContext.Provider value={{ state, dispatch }}>
      {children}
    </JournalDataContext.Provider>
  );
};