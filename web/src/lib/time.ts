// Temperature conversions
export const kToC = (k: number): number => k - 273.15;
export const kToF = (k: number): number => (k - 273.15) * (9 / 5) + 32;
export const cToF = (c: number): number => (c * 9 / 5) + 32;

// Time utilities for temporal joining and slider
export const parseTimestamp = (timestamp: string): Date => new Date(timestamp);

export const formatTimestamp = (date: Date): string => {
  return date.toISOString().replace(/\.\d{3}Z$/, 'Z');
};

export const isStale = (timestamp: string, maxAgeMinutes: number = 10): boolean => {
  const age = Date.now() - parseTimestamp(timestamp).getTime();
  return age > maxAgeMinutes * 60 * 1000;
};

// As-of temporal join: find nearest timestamp within tolerance
export const findNearestTimestamp = (
  targetTime: string,
  availableTimestamps: string[],
  toleranceMinutes: number = 3
): string | null => {
  const target = parseTimestamp(targetTime);
  const tolerance = toleranceMinutes * 60 * 1000;
  
  let nearestTime: string | null = null;
  let minDiff = Infinity;
  
  for (const timestamp of availableTimestamps) {
    const candidate = parseTimestamp(timestamp);
    const diff = Math.abs(target.getTime() - candidate.getTime());
    
    if (diff <= tolerance && diff < minDiff) {
      minDiff = diff;
      nearestTime = timestamp;
    }
  }
  
  return nearestTime;
};

// Generate time steps for animation
export const generateTimeSteps = (
  timestamps: string[], 
  currentIndex: number = 0
): { current: string; next: string | null; prev: string | null } => {
  const sortedTimestamps = [...timestamps].sort();
  
  return {
    current: sortedTimestamps[currentIndex] || sortedTimestamps[0],
    next: sortedTimestamps[currentIndex + 1] || null,
    prev: sortedTimestamps[currentIndex - 1] || null
  };
};

// Format time for display
export const formatDisplayTime = (timestamp: string): string => {
  const date = parseTimestamp(timestamp);
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    timeZoneName: 'short'
  });
};

// Calculate playback FPS timing
export const PLAYBACK_FPS = 5;
export const FRAME_INTERVAL_MS = 1000 / PLAYBACK_FPS;