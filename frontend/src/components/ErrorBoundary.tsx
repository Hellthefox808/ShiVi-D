/**
 * ShiVi Operations Console - React Error Boundary
 * ==================================================
 *
 * Briefing:
 *     Top-level React class-based error boundary (`ErrorBoundary`) designed to catch
 *     unhandled JavaScript exceptions occurring during component rendering, lifecycle methods,
 *     and child tree evaluation.
 *
 * Reason:
 *     In life-safety disaster operations, a single malformed sensor packet, GIS polygon rendering glitch,
 *     or transient telemetry anomaly must never crash the entire mission dashboard into a blank white screen.
 *     The ErrorBoundary catches the fault, displays a tactical recovery interface detailing the exception,
 *     reassures the operator that background outbox and audit integrity remain protected, and provides
 *     a single-click reload mechanism.
 */

"use client";

import React, { Component, ErrorInfo, ReactNode } from "react";
import { AlertTriangle, RotateCcw } from "lucide-react";

/**
 * Briefing:
 *     Props accepted by ErrorBoundary.
 */
interface Props {
  // Explanation: Wrapped child component subtree to protect.
  children: ReactNode;
}

/**
 * Briefing:
 *     Internal component state tracking exception occurrence and error details.
 */
interface State {
  // Explanation: True if an uncaught exception occurred in any descendant component.
  hasError: boolean;
  // Explanation: The captured Error instance, containing message and stack trace.
  error: Error | null;
}

/**
 * Briefing:
 *     Error boundary class implementation adhering to the React error boundary contract.
 */
export class ErrorBoundary extends Component<Props, State> {
  // Explanation: Initial component state indicating normal operation.
  public state: State = {
    hasError: false,
    error: null,
  };

  /**
   * Briefing:
   *     Static lifecycle invoked immediately after an error is thrown by a descendant component.
   *
   * Reason:
   *     Updates state synchronously to trigger the fallback UI rendering on the next render pass.
   *
   * @param error The thrown JavaScript error.
   */
  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  /**
   * Briefing:
   *     Lifecycle method invoked after an error has been caught.
   *
   * Reason:
   *     Logs diagnostic error details and component stack trace for post-incident technical analysis.
   *
   * @param error The thrown error.
   * @param errorInfo Component stack information detailing where the failure originated.
   */
  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("[ErrorBoundary] Caught error:", error, errorInfo);
  }

  /**
   * Briefing:
   *     Recovery handler resetting state and refreshing the browser window.
   *
   * Reason:
   *     Allows the operator to remount the tactical application without needing to manually inspect dev tools.
   */
  private handleReset = () => {
    this.setState({ hasError: false, error: null });
    window.location.reload();
  };

  /**
   * Briefing:
   *     Renders either the fallback tactical disaster recovery screen or the normal child tree.
   */
  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-slate-50 text-slate-900 flex items-center justify-center p-6">
          <div className="bg-white border border-red-200 rounded-2xl p-8 max-w-lg w-full text-center shadow-xl">
            <div className="w-16 h-16 bg-red-50 border border-red-200 rounded-full flex items-center justify-center mx-auto mb-6 text-red-600">
              <AlertTriangle className="w-8 h-8" />
            </div>
            <h2 className="text-2xl font-bold mb-2 text-slate-900">Common Operational Picture Error</h2>
            <p className="text-slate-600 text-sm mb-6">
              A critical rendering or telemetry synchronization anomaly occurred. The local SQLite outbox and
              audit integrity remain protected.
            </p>
            {this.state.error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-left font-mono text-xs text-red-800 mb-6 overflow-x-auto">
                {this.state.error.message}
              </div>
            )}
            <button
              onClick={this.handleReset}
              className="inline-flex items-center justify-center gap-2 w-full py-3 px-4 bg-amber-500 hover:bg-amber-600 text-white font-bold rounded-xl shadow-md shadow-amber-500/20 transition-all"
            >
              <RotateCcw className="w-4 h-4" /> Reload Operational Picture
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
