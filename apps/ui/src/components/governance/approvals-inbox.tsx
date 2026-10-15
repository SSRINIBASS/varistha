"use client";

/**
 * Human-in-the-Loop Approvals Inbox.
 * Allows operators to review, approve, reject, or edit proposed agent actions.
 */

import React, { useState } from "react";
import Link from "next/link";
import {
  CheckCircle2,
  XCircle,
  Edit3,
  RefreshCw,
  ExternalLink,
  ChevronRight,
  Filter,
  Check,
} from "lucide-react";
import type { ApprovalItem } from "@/lib/types";
import { resolveApproval } from "@/lib/api";
import { ApprovalStatusBadge } from "@/components/badges";
import { PayloadDiffViewer } from "./payload-diff-viewer";
import { EmptyState } from "@/components/empty-state";

interface ApprovalsInboxProps {
  approvals: ApprovalItem[];
  onRefresh: () => void;
  isLoading?: boolean;
}

export function ApprovalsInbox({
  approvals,
  onRefresh,
  isLoading = false,
}: ApprovalsInboxProps) {
  const [statusFilter, setStatusFilter] = useState<string>("pending");
  const [selectedApproval, setSelectedApproval] = useState<ApprovalItem | null>(null);
  const [isResolving, setIsResolving] = useState<boolean>(false);
  const [rejectReason, setRejectReason] = useState<string>("");
  const [isEditingPayload, setIsEditingPayload] = useState<boolean>(false);
  const [editedPayloadStr, setEditedPayloadStr] = useState<string>("");
  const [jsonError, setJsonError] = useState<string | null>(null);
  const [actionSuccessMsg, setActionSuccessMsg] = useState<string | null>(null);

  const filteredApprovals = approvals.filter((a) => {
    if (statusFilter === "all") return true;
    return a.status.toLowerCase() === statusFilter.toLowerCase();
  });

  const handleOpenDetail = (approval: ApprovalItem) => {
    setSelectedApproval(approval);
    setRejectReason("");
    setIsEditingPayload(false);
    setEditedPayloadStr(JSON.stringify(approval.proposed_payload, null, 2));
    setJsonError(null);
    setActionSuccessMsg(null);
  };

  const handleApprove = async () => {
    if (!selectedApproval) return;
    setIsResolving(true);
    try {
      const updated = await resolveApproval(selectedApproval.id, {
        action: "approve",
        reviewer: "operator",
      });
      setSelectedApproval(updated);
      setActionSuccessMsg("Action approved successfully.");
      onRefresh();
    } catch (err: unknown) {
      setJsonError(err instanceof Error ? err.message : "Failed to approve action");
    } finally {
      setIsResolving(false);
    }
  };

  const handleReject = async () => {
    if (!selectedApproval) return;
    setIsResolving(true);
    try {
      const updated = await resolveApproval(selectedApproval.id, {
        action: "reject",
        notes: rejectReason || "Rejected by operator",
        reviewer: "operator",
      });
      setSelectedApproval(updated);
      setActionSuccessMsg("Action rejected.");
      onRefresh();
    } catch (err: unknown) {
      setJsonError(err instanceof Error ? err.message : "Failed to reject action");
    } finally {
      setIsResolving(false);
    }
  };

  const handleSaveEdited = async () => {
    if (!selectedApproval) return;
    try {
      const parsed = JSON.parse(editedPayloadStr);
      setIsResolving(true);
      const updated = await resolveApproval(selectedApproval.id, {
        action: "edit",
        modified_payload: parsed,
        reviewer: "operator",
        notes: "Modified and approved by operator",
      });
      setSelectedApproval(updated);
      setIsEditingPayload(false);
      setActionSuccessMsg("Payload modified and approved successfully.");
      onRefresh();
    } catch (err: unknown) {
      setJsonError(err instanceof Error ? err.message : "Invalid JSON format");
    } finally {
      setIsResolving(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Controls Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3 rounded-lg border border-border bg-card">
        <div className="flex items-center gap-1.5 overflow-x-auto text-xs">
          <Filter className="w-3.5 h-3.5 text-muted-foreground mr-1" />
          {(["pending", "all", "approved", "rejected", "edited"] as const).map((st) => {
            const count = approvals.filter(
              (a) => st === "all" || a.status.toLowerCase() === st
            ).length;
            const isActive = statusFilter === st;

            return (
              <button
                key={st}
                type="button"
                onClick={() => setStatusFilter(st)}
                className={`px-3 py-1.5 rounded-md font-medium capitalize transition-colors flex items-center gap-1.5 ${
                  isActive
                    ? "bg-primary text-primary-foreground font-semibold shadow-xs"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted"
                }`}
              >
                <span>{st}</span>
                <span
                  className={`px-1.5 py-0.2 rounded-full text-[10px] font-mono ${
                    isActive
                      ? "bg-primary-foreground/20 text-primary-foreground"
                      : "bg-muted text-muted-foreground"
                  }`}
                >
                  {count}
                </span>
              </button>
            );
          })}
        </div>

        <button
          type="button"
          onClick={onRefresh}
          disabled={isLoading}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-border bg-card hover:bg-muted text-xs font-medium text-foreground transition-colors self-start sm:self-auto shadow-xs"
          title="Refresh approvals"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Approvals Table */}
      {filteredApprovals.length === 0 ? (
        <EmptyState
          title={`No ${statusFilter === "all" ? "" : statusFilter} approvals`}
          description={
            statusFilter === "pending"
              ? "All pending agent actions have been resolved. The platform is running smoothly."
              : "No approval requests found matching the selected filter."
          }
        />
      ) : (
        <div className="rounded-lg border border-border bg-card overflow-hidden shadow-xs">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-border bg-muted/40 font-semibold text-muted-foreground">
                  <th className="py-2.5 px-4">Status</th>
                  <th className="py-2.5 px-4">Action / Tool</th>
                  <th className="py-2.5 px-4">Description</th>
                  <th className="py-2.5 px-4">Created</th>
                  <th className="py-2.5 px-4 text-right">Review</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {filteredApprovals.map((item) => (
                  <tr
                    key={item.id}
                    className="hover:bg-muted/30 transition-colors cursor-pointer group"
                    onClick={() => handleOpenDetail(item)}
                  >
                    <td className="py-3 px-4 whitespace-nowrap">
                      <ApprovalStatusBadge status={item.status} />
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      <div className="font-semibold text-foreground flex items-center gap-1.5">
                        <span>{item.tool_name || item.action_type}</span>
                        {item.tool_name && (
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-muted text-muted-foreground font-mono">
                            tool
                          </span>
                        )}
                      </div>
                      <div className="text-[11px] text-muted-foreground font-mono truncate max-w-xs">
                        Run: {item.run_id.slice(0, 8)}...
                      </div>
                    </td>
                    <td className="py-3 px-4 max-w-md truncate text-foreground/90">
                      {item.description}
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap text-muted-foreground">
                      {new Date(item.created_at).toLocaleString()}
                    </td>
                    <td className="py-3 px-4 text-right whitespace-nowrap">
                      <span className="inline-flex items-center gap-1 text-primary group-hover:underline font-semibold">
                        <span>Inspect</span>
                        <ChevronRight className="w-3.5 h-3.5" />
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Review Modal / Drawer */}
      {selectedApproval && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-xs">
          <div className="w-full max-w-3xl rounded-xl border border-border bg-card shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
            {/* Modal Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-muted/30">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <h3 className="text-base font-bold text-foreground">
                    Approval Request: {selectedApproval.tool_name || selectedApproval.action_type}
                  </h3>
                  <ApprovalStatusBadge status={selectedApproval.status} />
                </div>
                <p className="text-xs text-muted-foreground">
                  ID: <code className="font-mono">{selectedApproval.id}</code> &bull; Run:{" "}
                  <Link
                    href={`/runs/${selectedApproval.run_id}`}
                    className="text-primary hover:underline font-mono inline-flex items-center gap-0.5"
                    target="_blank"
                  >
                    <span>{selectedApproval.run_id.slice(0, 8)}...</span>
                    <ExternalLink className="w-3 h-3" />
                  </Link>
                </p>
              </div>

              <button
                type="button"
                onClick={() => setSelectedApproval(null)}
                className="w-8 h-8 rounded-md flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                title="Close"
              >
                &times;
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 space-y-4 overflow-y-auto flex-1">
              {actionSuccessMsg && (
                <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-700 dark:text-emerald-300 text-xs font-medium flex items-center gap-2">
                  <Check className="w-4 h-4 text-emerald-500" />
                  <span>{actionSuccessMsg}</span>
                </div>
              )}

              {jsonError && (
                <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-700 dark:text-rose-300 text-xs font-mono">
                  {jsonError}
                </div>
              )}

              {/* Description & Review Info */}
              <div className="p-3 rounded-lg border border-border bg-muted/20 space-y-2 text-xs">
                <div className="font-semibold text-foreground">Description:</div>
                <div className="text-foreground/90">{selectedApproval.description}</div>
                {selectedApproval.review_notes && (
                  <div className="pt-2 border-t border-border/60">
                    <span className="font-semibold text-muted-foreground">Reviewer Notes: </span>
                    <span className="italic text-foreground">{selectedApproval.review_notes}</span>
                    {selectedApproval.reviewer && (
                      <span className="text-muted-foreground"> ({selectedApproval.reviewer})</span>
                    )}
                  </div>
                )}
              </div>

              {/* Payload Diff or Editor */}
              {isEditingPayload ? (
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs font-semibold text-foreground">
                    <span>Edit Proposed Payload (JSON):</span>
                    <span className="text-[11px] text-muted-foreground">
                      Validate before submitting
                    </span>
                  </div>
                  <textarea
                    value={editedPayloadStr}
                    onChange={(e) => {
                      setEditedPayloadStr(e.target.value);
                      setJsonError(null);
                    }}
                    rows={12}
                    className="w-full p-3 font-mono text-xs rounded-lg border border-border bg-muted/10 text-foreground focus:outline-hidden focus:ring-1 focus:ring-primary focus:border-primary leading-relaxed"
                    placeholder="Enter valid JSON payload..."
                  />
                </div>
              ) : (
                <PayloadDiffViewer
                  proposedPayload={selectedApproval.proposed_payload}
                  approvedPayload={selectedApproval.approved_payload}
                />
              )}

              {/* Rejection Reason Form */}
              {selectedApproval.status === "pending" && !isEditingPayload && (
                <div className="space-y-1.5 pt-2">
                  <label htmlFor="rejection-reason" className="text-xs font-semibold text-muted-foreground">
                    Optional Review Rationale / Rejection Reason:
                  </label>
                  <input
                    id="rejection-reason"
                    type="text"
                    value={rejectReason}
                    onChange={(e) => setRejectReason(e.target.value)}
                    placeholder="e.g. Recipient address unverified or excessive budget"
                    className="w-full px-3 py-1.5 text-xs rounded-md border border-border bg-muted/10 text-foreground focus:outline-hidden focus:ring-1 focus:ring-primary"
                  />
                </div>
              )}
            </div>

            {/* Modal Actions */}
            <div className="flex items-center justify-between px-6 py-3.5 border-t border-border bg-muted/20">
              <button
                type="button"
                onClick={() => setSelectedApproval(null)}
                className="px-4 py-1.5 rounded-md border border-border bg-card hover:bg-muted text-xs font-medium text-foreground transition-colors"
              >
                Close
              </button>

              {selectedApproval.status === "pending" && (
                <div className="flex items-center gap-2">
                  {isEditingPayload ? (
                    <>
                      <button
                        type="button"
                        onClick={() => setIsEditingPayload(false)}
                        className="px-3.5 py-1.5 rounded-md border border-border bg-card hover:bg-muted text-xs font-medium text-foreground transition-colors"
                      >
                        Cancel Edit
                      </button>
                      <button
                        type="button"
                        disabled={isResolving}
                        onClick={handleSaveEdited}
                        className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-md bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold transition-colors shadow-xs"
                      >
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>Save & Approve</span>
                      </button>
                    </>
                  ) : (
                    <>
                      <button
                        type="button"
                        onClick={() => setIsEditingPayload(true)}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-border bg-card hover:bg-muted text-xs font-medium text-foreground transition-colors"
                      >
                        <Edit3 className="w-3.5 h-3.5" />
                        <span>Edit Payload</span>
                      </button>

                      <button
                        type="button"
                        disabled={isResolving}
                        onClick={handleReject}
                        className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-md bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold transition-colors shadow-xs"
                      >
                        <XCircle className="w-3.5 h-3.5" />
                        <span>Reject</span>
                      </button>

                      <button
                        type="button"
                        disabled={isResolving}
                        onClick={handleApprove}
                        className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-md bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold transition-colors shadow-xs"
                      >
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>Approve</span>
                      </button>
                    </>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
