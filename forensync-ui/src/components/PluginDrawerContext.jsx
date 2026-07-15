import { createContext, useContext, useState } from "react";

const PluginDrawerContext = createContext(null);

export function PluginDrawerProvider({ children }) {
  const [open, setOpen] = useState(false);
  return (
    <PluginDrawerContext.Provider
      value={{ open, toggle: () => setOpen((v) => !v), close: () => setOpen(false) }}
    >
      {children}
    </PluginDrawerContext.Provider>
  );
}

export function usePluginDrawer() {
  return useContext(PluginDrawerContext);
}
