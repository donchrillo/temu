import { useState, useEffect } from 'react';

interface ProgressOverlayProps {
  isOpen: boolean;
  title?: string;
  progress: number;
  text: string;
}

export function ProgressOverlay({ isOpen, title = 'Verarbeite...', progress, text }: ProgressOverlayProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50 animate-fade-in" />
      
      {/* Dialog Content */}
      <div className="relative bg-card rounded-lg shadow-lg p-8 max-w-sm w-full mx-4 animate-scale-in">
        {/* Icon */}
        <div className="text-center mb-4">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-primary-light flex items-center justify-center">
            <span className="text-3xl">⚙️</span>
          </div>
        </div>
        
        {/* Title */}
        <h3 className="text-lg font-semibold text-text text-center mb-2">
          {title}
        </h3>
        
        {/* Text */}
        <p className="text-sm text-text-secondary text-center mb-4">
          {text}
        </p>
        
        {/* Progress Bar */}
        <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
          <div 
            className="bg-primary h-4 rounded-full transition-all duration-300 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>
        
        {/* Percent */}
        <p className="text-center text-sm font-medium text-text mt-2">
          {Math.round(progress)}%
        </p>
      </div>
    </div>
  );
}

// Hook für automatischen Progress
export function useProgress(initialText: string = 'Verarbeite...') {
  const [isOpen, setIsOpen] = useState(false);
  const [progress, setProgress] = useState(0);
  const [text, setText] = useState(initialText);
  const [intervalId, setIntervalId] = useState<ReturnType<typeof setInterval> | null>(null);

  const startProgress = (newText?: string) => {
    setText(newText || initialText);
    setProgress(0);
    setIsOpen(true);
    
    // Auto-increment bis 90%
    const id = setInterval(() => {
      setProgress(prev => {
        if (prev >= 90) {
          clearInterval(id);
          return 90;
        }
        return prev + Math.random() * 15;
      });
    }, 300);
    
    setIntervalId(id);
  };

  const updateProgress = (newProgress: number, newText?: string) => {
    setProgress(newProgress);
    if (newText) setText(newText);
  };

  const stopProgress = (finalText?: string) => {
    if (intervalId) {
      clearInterval(intervalId);
      setIntervalId(null);
    }
    
    setProgress(100);
    if (finalText) setText(finalText);
    
    // Kurz anzeigen dann schließen
    setTimeout(() => {
      setIsOpen(false);
      setProgress(0);
      setText(initialText);
    }, 500);
  };

  const closeProgress = () => {
    if (intervalId) {
      clearInterval(intervalId);
      setIntervalId(null);
    }
    setIsOpen(false);
    setProgress(0);
    setText(initialText);
  };

  // Cleanup
  useEffect(() => {
    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [intervalId]);

  return {
    isOpen,
    progress,
    text,
    startProgress,
    updateProgress,
    stopProgress,
    closeProgress,
    ProgressComponent: () => (
      <ProgressOverlay 
        isOpen={isOpen} 
        title="Verarbeite..."
        progress={progress} 
        text={text} 
      />
    )
  };
}
