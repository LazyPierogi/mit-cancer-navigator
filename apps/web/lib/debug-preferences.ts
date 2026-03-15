export type NavigatorDebugPreferences = {
  showClinicalModifiers: boolean;
};

const STORAGE_KEY = "nsclc-navigator-debug-preferences";
const UPDATE_EVENT = "nsclc:navigator-debug-preferences";

export const DEFAULT_NAVIGATOR_DEBUG_PREFERENCES: NavigatorDebugPreferences = {
  showClinicalModifiers: false
};

export function readNavigatorDebugPreferences(): NavigatorDebugPreferences {
  if (typeof window === "undefined") {
    return DEFAULT_NAVIGATOR_DEBUG_PREFERENCES;
  }

  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return DEFAULT_NAVIGATOR_DEBUG_PREFERENCES;
    }

    return {
      ...DEFAULT_NAVIGATOR_DEBUG_PREFERENCES,
      ...JSON.parse(raw)
    };
  } catch {
    return DEFAULT_NAVIGATOR_DEBUG_PREFERENCES;
  }
}

export function updateNavigatorDebugPreferences(
  updates: Partial<NavigatorDebugPreferences>
): NavigatorDebugPreferences {
  const next = {
    ...readNavigatorDebugPreferences(),
    ...updates
  };

  if (typeof window !== "undefined") {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
    window.dispatchEvent(new CustomEvent(UPDATE_EVENT, { detail: next }));
  }

  return next;
}

export function subscribeNavigatorDebugPreferences(
  onChange: (next: NavigatorDebugPreferences) => void
): () => void {
  if (typeof window === "undefined") {
    return () => undefined;
  }

  const handleStorage = (event: StorageEvent) => {
    if (event.key && event.key !== STORAGE_KEY) {
      return;
    }
    onChange(readNavigatorDebugPreferences());
  };

  const handleCustomEvent = (event: Event) => {
    const detail = (event as CustomEvent<NavigatorDebugPreferences>).detail;
    onChange(detail ?? readNavigatorDebugPreferences());
  };

  window.addEventListener("storage", handleStorage);
  window.addEventListener(UPDATE_EVENT, handleCustomEvent as EventListener);

  return () => {
    window.removeEventListener("storage", handleStorage);
    window.removeEventListener(UPDATE_EVENT, handleCustomEvent as EventListener);
  };
}
