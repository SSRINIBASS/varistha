import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import React from "react";
import { EmptyState } from "@/components/empty-state";
import { ErrorAlert } from "@/components/error-alert";
import { TableSkeleton, WaterfallSkeleton } from "@/components/loading-skeleton";

describe("EmptyState", () => {
  it("renders title, description, and handles button click", () => {
    const handleClick = vi.fn();
    render(
      <EmptyState
        title="No items found"
        description="Try adding a new item to get started."
        action={{
          label: "Create Item",
          onClick: handleClick,
        }}
      />
    );

    expect(screen.getByText("No items found")).toBeDefined();
    expect(screen.getByText("Try adding a new item to get started.")).toBeDefined();

    const button = screen.getByRole("button", { name: "Create Item" });
    fireEvent.click(button);
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});

describe("ErrorAlert", () => {
  it("renders error message and triggers retry handler", () => {
    const handleRetry = vi.fn();
    render(
      <ErrorAlert
        title="Network Error"
        message="Failed to fetch data from API"
        onRetry={handleRetry}
      />
    );

    expect(screen.getByText("Network Error")).toBeDefined();
    expect(screen.getByText("Failed to fetch data from API")).toBeDefined();

    const retryBtn = screen.getByRole("button", { name: /try again/i });
    fireEvent.click(retryBtn);
    expect(handleRetry).toHaveBeenCalledTimes(1);
  });
});

describe("LoadingSkeletons", () => {
  it("renders TableSkeleton and WaterfallSkeleton", () => {
    const { rerender } = render(<TableSkeleton rows={3} columns={4} />);
    expect(screen.getByTestId("table-skeleton")).toBeDefined();

    rerender(<WaterfallSkeleton bars={3} />);
    expect(screen.getByTestId("waterfall-skeleton")).toBeDefined();
  });
});
