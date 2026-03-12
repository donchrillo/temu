import { Component, type ErrorInfo, type ReactNode } from 'react';
import { Button } from '@/components/ui/button';
import { AlertCircle, RefreshCw } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State;

  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  private handleReload = () => {
    window.location.reload();
  };

  private handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="flex flex-col items-center justify-center min-h-[400px] p-8">
          <div className="bg-danger/10 rounded-full p-4 mb-4">
            <AlertCircle className="w-12 h-12 text-danger" />
          </div>
          <h2 className="text-xl font-semibold text-text mb-2">
            Etwas ist schief gelaufen
          </h2>
          <p className="text-text-secondary text-center mb-6 max-w-md">
            Entschuldigung, es ist ein unerwarteter Fehler aufgetreten.
            Bitte versuchen Sie es erneut.
          </p>
          {this.state.error && (
            <pre className="text-xs text-text-secondary bg-gray-100 p-4 rounded-lg mb-6 max-w-lg overflow-auto">
              {this.state.error.message}
            </pre>
          )}
          <div className="flex gap-3">
            <Button variant="secondary" onClick={this.handleReset}>
              Erneut versuchen
            </Button>
            <Button variant="primary" onClick={this.handleReload}>
              <RefreshCw className="w-4 h-4 mr-2" />
              Seite neu laden
            </Button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}