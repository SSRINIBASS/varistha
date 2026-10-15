"use client";

/**
 * Agent Lifecycle Page.
 * Visual control plane for agent promotion, gate verification, and stage auditing.
 * Follows docs/SPEC.md § 3.2, § 4.4, § 5.
 */

import React from "react";
import { LifecycleBoard } from "@/components/lifecycle-board";

export default function LifecyclePage() {
  return (
    <div className="py-2">
      <LifecycleBoard />
    </div>
  );
}
