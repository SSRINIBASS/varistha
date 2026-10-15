import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import React from "react";
import { PluginRiskBadge, ApprovalRequiredBadge } from "@/components/badges";
import { PluginCard } from "@/components/plugins/plugin-card";
import { PluginInspector } from "@/components/plugins/plugin-inspector";
import { PluginExplorer } from "@/components/plugins/plugin-explorer";
import type { PluginInfo } from "@/lib/types";

describe("Plugin Badges", () => {
  it("renders PluginRiskBadge variants correctly", () => {
    const { rerender } = render(<PluginRiskBadge risk="low" />);
    expect(screen.getByText("Low Risk")).toBeDefined();

    rerender(<PluginRiskBadge risk="medium" />);
    expect(screen.getByText("Medium Risk")).toBeDefined();

    rerender(<PluginRiskBadge risk="high" />);
    expect(screen.getByText("High Risk")).toBeDefined();
  });

  it("renders ApprovalRequiredBadge variants correctly", () => {
    const { rerender } = render(<ApprovalRequiredBadge required={true} />);
    expect(screen.getByText("Approval Required")).toBeDefined();

    rerender(<ApprovalRequiredBadge required={false} />);
    expect(screen.getByText("Auto-Executable")).toBeDefined();
  });
});

describe("PluginCard", () => {
  const mockPlugin: PluginInfo = {
    name: "web-fetch",
    version: "0.1.0",
    description: "Fetch web pages and convert to markdown",
    transport: "in-process",
    risk: "low",
    scopes: ["network:read"],
    requires_approval: false,
    untrusted_output: true,
    config_schema: {
      type: "object",
      properties: {
        timeout_seconds: { type: "integer", default: 15 },
      },
    },
    tools: ["web_fetch"],
  };

  it("renders plugin metadata, badges, and capabilities", () => {
    render(<PluginCard plugin={mockPlugin} />);

    expect(screen.getByText("web-fetch")).toBeDefined();
    expect(screen.getByText("v0.1.0")).toBeDefined();
    expect(screen.getByText("In-Process")).toBeDefined();
    expect(screen.getByText("Low Risk")).toBeDefined();
    expect(screen.getByText("Auto-Executable")).toBeDefined();
    expect(screen.getByText("Untrusted Output")).toBeDefined();
    expect(screen.getByText("network:read")).toBeDefined();
    expect(screen.getByText("web_fetch")).toBeDefined();
  });

  it("calls onInspect when inspect button is clicked", () => {
    const handleInspect = vi.fn();
    render(<PluginCard plugin={mockPlugin} onInspect={handleInspect} />);

    const inspectBtn = screen.getByText("Inspect Manifest");
    fireEvent.click(inspectBtn);

    expect(handleInspect).toHaveBeenCalledWith(mockPlugin);
  });
});

describe("PluginInspector", () => {
  const mockPlugin: PluginInfo = {
    name: "crm-export",
    version: "1.0.0",
    description: "Export qualified leads to CRM",
    transport: "mcp-stdio",
    risk: "medium",
    scopes: ["crm:write"],
    requires_approval: true,
    untrusted_output: false,
    config_schema: {
      type: "object",
      properties: {
        crm_endpoint: { type: "string" },
      },
    },
    tools: ["export_lead", "update_lead"],
  };

  it("renders nothing when isOpen is false", () => {
    const { container } = render(
      <PluginInspector plugin={mockPlugin} isOpen={false} onClose={vi.fn()} />
    );
    expect(container.firstChild).toBeNull();
  });

  it("renders modal details and allows switching tabs", () => {
    const handleClose = vi.fn();
    render(
      <PluginInspector plugin={mockPlugin} isOpen={true} onClose={handleClose} />
    );

    expect(screen.getByText("crm-export")).toBeDefined();
    expect(screen.getByText("Medium Risk")).toBeDefined();
    expect(screen.getByText("Approval Required")).toBeDefined();
    expect(screen.getByText("crm:write")).toBeDefined();
    expect(screen.getByText("export_lead")).toBeDefined();
    expect(screen.getByText("update_lead")).toBeDefined();

    // Switch to Config Schema tab
    const schemaTab = screen.getByText("Config Schema");
    fireEvent.click(schemaTab);
    expect(screen.getByText(/"crm_endpoint"/)).toBeDefined();

    // Switch to Raw Manifest tab
    const manifestTab = screen.getByText("Raw Manifest");
    fireEvent.click(manifestTab);
    expect(screen.getByText("Copy JSON")).toBeDefined();

    // Close button
    const closeBtn = screen.getByText("Close");
    fireEvent.click(closeBtn);
    expect(handleClose).toHaveBeenCalled();
  });
});

describe("PluginExplorer", () => {
  const mockPlugins: PluginInfo[] = [
    {
      name: "web-fetch",
      version: "0.1.0",
      description: "Fetch web pages and convert to markdown",
      transport: "in-process",
      risk: "low",
      scopes: ["network:read"],
      requires_approval: false,
      untrusted_output: true,
      tools: ["web_fetch"],
    },
    {
      name: "crm-export",
      version: "1.0.0",
      description: "Export qualified leads to CRM hub",
      transport: "mcp-stdio",
      risk: "medium",
      scopes: ["crm:write"],
      requires_approval: true,
      untrusted_output: false,
      tools: ["crm_export"],
    },
    {
      name: "system-shell",
      version: "0.2.0",
      description: "Execute arbitrary host commands",
      transport: "mcp-stdio",
      risk: "high",
      scopes: ["system:exec"],
      requires_approval: true,
      untrusted_output: true,
      tools: ["exec_cmd"],
    },
  ];

  it("filters plugins by search query", () => {
    render(<PluginExplorer plugins={mockPlugins} />);

    expect(screen.getByText("web-fetch")).toBeDefined();
    expect(screen.getByText("crm-export")).toBeDefined();
    expect(screen.getByText("system-shell")).toBeDefined();

    const searchInput = screen.getByPlaceholderText(
      "Search plugins by name, scope, tool, or description..."
    );
    fireEvent.change(searchInput, { target: { value: "crm" } });

    expect(screen.getByText("crm-export")).toBeDefined();
    expect(screen.queryByText("web-fetch")).toBeNull();
    expect(screen.queryByText("system-shell")).toBeNull();
  });

  it("filters plugins by risk level", () => {
    render(<PluginExplorer plugins={mockPlugins} />);

    // Click "High" risk filter
    const highFilterBtn = screen.getByRole("button", { name: "high" });
    fireEvent.click(highFilterBtn);

    expect(screen.getByText("system-shell")).toBeDefined();
    expect(screen.queryByText("web-fetch")).toBeNull();
    expect(screen.queryByText("crm-export")).toBeNull();

    // Reset filters
    const resetBtn = screen.getByText("Reset filters");
    fireEvent.click(resetBtn);

    expect(screen.getByText("web-fetch")).toBeDefined();
    expect(screen.getByText("crm-export")).toBeDefined();
    expect(screen.getByText("system-shell")).toBeDefined();
  });

  it("filters plugins by approval policy", () => {
    render(<PluginExplorer plugins={mockPlugins} />);

    // Click "Auto-Executable"
    const autoFilterBtn = screen.getByRole("button", { name: "Auto-Executable" });
    fireEvent.click(autoFilterBtn);

    expect(screen.getByText("web-fetch")).toBeDefined();
    expect(screen.queryByText("crm-export")).toBeNull();
    expect(screen.queryByText("system-shell")).toBeNull();
  });
});
