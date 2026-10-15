import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";
import { StageBadge, StatusBadge, AutonomyBadge } from "@/components/badges";

describe("StageBadge", () => {
  it("renders Draft stage with icon and text", () => {
    render(<StageBadge stage="draft" />);
    expect(screen.getByText("Draft")).toBeDefined();
  });

  it("renders Prototype stage", () => {
    render(<StageBadge stage="prototype" />);
    expect(screen.getByText("Prototype")).toBeDefined();
  });

  it("renders Staging stage", () => {
    render(<StageBadge stage="staging" />);
    expect(screen.getByText("Staging")).toBeDefined();
  });

  it("renders Production stage", () => {
    render(<StageBadge stage="production" />);
    expect(screen.getByText("Production")).toBeDefined();
  });

  it("renders Deprecated stage", () => {
    render(<StageBadge stage="deprecated" />);
    expect(screen.getByText("Deprecated")).toBeDefined();
  });

  it("renders Retired stage", () => {
    render(<StageBadge stage="retired" />);
    expect(screen.getByText("Retired")).toBeDefined();
  });
});

describe("StatusBadge", () => {
  it("renders Completed status", () => {
    render(<StatusBadge status="completed" />);
    expect(screen.getByText("Completed")).toBeDefined();
  });

  it("renders Running status", () => {
    render(<StatusBadge status="running" />);
    expect(screen.getByText("Running")).toBeDefined();
  });

  it("renders Failed status", () => {
    render(<StatusBadge status="failed" />);
    expect(screen.getByText("Failed")).toBeDefined();
  });

  it("renders Waiting Approval status", () => {
    render(<StatusBadge status="waiting_approval" />);
    expect(screen.getByText("Waiting Approval")).toBeDefined();
  });
});

describe("AutonomyBadge", () => {
  it("renders autonomy level and description title", () => {
    render(<AutonomyBadge autonomy="L1" />);
    const badge = screen.getByText("L1");
    expect(badge).toBeDefined();
    expect(badge.getAttribute("title")).toContain("L1 Act with approval");
  });
});
