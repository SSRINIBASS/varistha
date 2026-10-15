import { describe, expect, it } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import React from "react";
import { TraceWaterfall } from "@/components/trace-waterfall";
import type { Span } from "@/lib/types";

describe("TraceWaterfall", () => {
  it("renders empty message when spans array is empty", () => {
    render(<TraceWaterfall spans={[]} />);
    expect(
      screen.getByText("No OpenTelemetry spans recorded for this execution trace.")
    ).toBeDefined();
  });

  it("renders hierarchical spans and allows clicking to inspect attributes", () => {
    const mockSpans: Span[] = [
      {
        id: "span-root",
        trace_id: "trace-123",
        name: "agent.run",
        kind: "SERVER",
        start_time: "2026-10-15T10:00:00.000Z",
        end_time: "2026-10-15T10:00:01.000Z",
        duration_ms: 1000,
        status_code: "OK",
        attributes: {
          "varistha.agent_name": "lead-researcher",
          "varistha.stage": "prototype",
        },
        events: [],
      },
      {
        id: "span-llm",
        trace_id: "trace-123",
        parent_span_id: "span-root",
        name: "llm.call",
        kind: "CLIENT",
        start_time: "2026-10-15T10:00:00.200Z",
        end_time: "2026-10-15T10:00:00.900Z",
        duration_ms: 700,
        status_code: "OK",
        attributes: {
          "gen_ai.request.model": "gpt-4o-mini",
          "gen_ai.usage.total_tokens": 350,
          "varistha.cost_usd": 0.002,
        },
        events: [],
      },
    ];

    render(<TraceWaterfall spans={mockSpans} />);

    // Span names appear
    expect(screen.getAllByText("agent.run").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("llm.call").length).toBeGreaterThanOrEqual(1);

    // Default active root span attributes rendered
    expect(screen.getByText("lead-researcher")).toBeDefined();

    // Click child LLM span to inspect attributes
    const llmRow = screen.getAllByText("llm.call")[0];
    if (llmRow) fireEvent.click(llmRow);

    // Inspector now shows LLM attributes
    expect(screen.getByText("gpt-4o-mini")).toBeDefined();
    expect(screen.getByText("350")).toBeDefined();
  });
});
