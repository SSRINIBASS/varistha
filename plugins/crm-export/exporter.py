"""Lead and account export formatter supporting CSV, HubSpot, and Salesforce schemas."""

from __future__ import annotations

import csv
import io
from typing import Any


class LeadValidationError(Exception):
    """Raised when lead dataset fails schema or identifier validation."""


STANDARD_FIELDNAMES = [
    "email",
    "first_name",
    "last_name",
    "company",
    "title",
    "linkedin_url",
    "notes",
    "source",
]


def validate_leads(leads: list[dict[str, Any]]) -> None:
    """Validate that leads collection contains valid lead dictionaries with identifiers."""
    if not isinstance(leads, list) or len(leads) == 0:
        raise LeadValidationError("Leads collection must be a non-empty list.")

    for idx, lead in enumerate(leads):
        if not isinstance(lead, dict):
            raise LeadValidationError(f"Lead at index {idx} must be a dictionary.")

        # Must have at least one identifying property
        has_identifier = any(
            lead.get(k)
            for k in ("email", "company", "company_name", "name", "first_name")
        )
        if not has_identifier:
            raise LeadValidationError(
                f"Lead at index {idx} lacks an identifier (email, company, or name required)."
            )


def export_leads_to_csv(
    leads: list[dict[str, Any]],
    fieldnames: list[str] | None = None,
) -> str:
    """Format leads into CSV string with header row."""
    validate_leads(leads)

    if fieldnames is None:
        # Collect union of keys while preserving standard ordering
        ordered_keys: list[str] = list(STANDARD_FIELDNAMES)
        for lead in leads:
            for k in lead:
                if k not in ordered_keys:
                    ordered_keys.append(k)
        fieldnames = ordered_keys

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()

    for lead in leads:
        # Normalize company_name to company if needed
        row = dict(lead)
        if "company_name" in row and "company" not in row:
            row["company"] = row["company_name"]
        writer.writerow(row)

    return output.getvalue().strip()


def export_to_hubspot_format(leads: list[dict[str, Any]]) -> dict[str, Any]:
    """Convert leads to HubSpot Batch Contacts ingestion payload."""
    validate_leads(leads)

    inputs: list[dict[str, Any]] = []
    for lead in leads:
        properties: dict[str, str] = {}
        if lead.get("email"):
            properties["email"] = str(lead["email"]).strip()
        if lead.get("first_name"):
            properties["firstname"] = str(lead["first_name"]).strip()
        if lead.get("last_name"):
            properties["lastname"] = str(lead["last_name"]).strip()
        if lead.get("company") or lead.get("company_name"):
            properties["company"] = str(lead.get("company") or lead.get("company_name")).strip()
        if lead.get("title"):
            properties["jobtitle"] = str(lead["title"]).strip()
        if lead.get("notes"):
            properties["notes"] = str(lead["notes"]).strip()
        if lead.get("linkedin_url"):
            properties["linkedin"] = str(lead["linkedin_url"]).strip()

        inputs.append({"properties": properties})

    return {
        "inputs": inputs,
        "count": len(inputs),
        "target": "hubspot",
    }


def export_to_salesforce_format(leads: list[dict[str, Any]]) -> dict[str, Any]:
    """Convert leads to Salesforce Lead Composite/sObject payload."""
    validate_leads(leads)

    records: list[dict[str, Any]] = []
    for lead in leads:
        company_val = (
            lead.get("company")
            or lead.get("company_name")
            or "Unknown Organization"
        )
        last_name_val = lead.get("last_name") or lead.get("name") or "Contact"

        record: dict[str, Any] = {
            "attributes": {"type": "Lead"},
            "Company": str(company_val).strip(),
            "LastName": str(last_name_val).strip(),
        }

        if lead.get("first_name"):
            record["FirstName"] = str(lead["first_name"]).strip()
        if lead.get("email"):
            record["Email"] = str(lead["email"]).strip()
        if lead.get("title"):
            record["Title"] = str(lead["title"]).strip()
        if lead.get("notes"):
            record["Description"] = str(lead["notes"]).strip()

        records.append(record)

    return {
        "records": records,
        "count": len(records),
        "target": "salesforce",
    }


async def export_leads(
    leads: list[dict[str, Any]],
    export_format: str = "csv",
    **kwargs: Any,
) -> dict[str, Any]:
    """Export lead records into specified format.

    Args:
        leads: List of lead dictionaries.
        export_format: Destination format ('csv', 'hubspot', 'salesforce', 'json').
        **kwargs: Optional keyword arguments including 'format'.

    Returns:
        Structured dictionary containing format, count, and payload.

    """
    validate_leads(leads)

    chosen_format = str(kwargs.get("format") or export_format)
    normalized_format = chosen_format.lower().strip()

    if normalized_format == "csv":
        csv_text = export_leads_to_csv(leads)
        return {
            "format": "csv",
            "count": len(leads),
            "payload": csv_text,
        }
    if normalized_format == "hubspot":
        payload = export_to_hubspot_format(leads)
        return {
            "format": "hubspot",
            "count": len(leads),
            "payload": payload,
        }
    if normalized_format == "salesforce":
        payload = export_to_salesforce_format(leads)
        return {
            "format": "salesforce",
            "count": len(leads),
            "payload": payload,
        }
    if normalized_format == "json":
        return {
            "format": "json",
            "count": len(leads),
            "payload": leads,
        }

    raise ValueError(
        f"Unsupported export format '{export_format}'. "
        "Use 'csv', 'hubspot', 'salesforce', or 'json'."
    )
