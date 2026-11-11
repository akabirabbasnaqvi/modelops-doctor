import { Component, type ErrorInfo, type ReactNode } from "react";

import { logError } from "../lib/logger";

type Props = {
  children: ReactNode;
  /**
   * When this value changes, a caught error is cleared and the children are
   * rendered again. The layout passes the current path, so navigating away
   * from a broken page recovers without a full reload.
   */
  resetKey?: unknown;
};

type State = {
  error: Error | null;
};

/**
 * Contains a render-time crash to the page that caused it.
 *
 * Without this, any exception thrown while rendering unmounts the whole
 * React tree: the sidebar disappears along with the page and the user is
 * left with a blank screen and no way to navigate. Error boundaries have to
 * be class components; React has no hook equivalent.
 */
export default class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    logError("Page failed to render", error, {
      componentStack: info.componentStack,
    });
  }

  componentDidUpdate(previousProps: Props): void {
    if (
      this.state.error !== null &&
      previousProps.resetKey !== this.props.resetKey
    ) {
      this.setState({ error: null });
    }
  }

  private handleRetry = (): void => {
    this.setState({ error: null });
  };

  render(): ReactNode {
    if (this.state.error === null) {
      return this.props.children;
    }

    return (
      <section className="panel" role="alert">
        <h2>This page failed to load</h2>

        <p>
          Something went wrong while rendering this page. The rest of the app
          still works — use the navigation to go elsewhere, or try again.
        </p>

        <div className="alert error">{this.state.error.message}</div>

        <button
          className="primary-button"
          type="button"
          onClick={this.handleRetry}
        >
          Try again
        </button>
      </section>
    );
  }
}
