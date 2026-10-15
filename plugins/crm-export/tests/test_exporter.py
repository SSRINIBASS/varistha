"""Tests for crm-export plugin."""

from __future__ import annotations

import pytest
from exporter import (
    LeadValidationError,
    export_leads,
    export_leads_to_csv,
    export_to_hubspot_format,
    export_to_salesforce_format,
    validate_leads,
)


def test_validate_leads_success() -> None:
    valid_leads = [
        {"email": "alex@startup.io", "first_name": "Alex", "company": "Startup AI"},
        {"company_name": "Enterprise Corp", "notes": "Series B funded"},
    ]
    validate_leads(valid_leads)


def test_validate_leads_empty_rejected() -> None:
    with pytest.raises(LeadValidationError, match="non-empty list"):
        validate_leads([])


def test_validate_leads_missing_identifier_rejected() -> None:
    bad_leads = [{"notes": "Just some notes without an email or company"}]
    with pytest.raises(LeadValidationError, match="lacks an identifier"):
        validate_leads(bad_leads)


def test_export_leads_to_csv() -> None:
    leads = [
        {
            "email": "sarah@acme.com",
            "first_name": "Sarah",
            "last_name": "Connor",
            "company": "Acme Corp",
            "title": "VP Engineering",
        },
        {
            "email": "john@cyberdyne.org",
            "first_name": "John",
            "last_name": "Smith",
            "company_name": "Cyberdyne Systems",
            "title": "Director of Security",
        },
    ]
    csv_output = export_leads_to_csv(leads)
    lines = csv_output.splitlines()
    assert len(lines) == 3  # Header + 2 data rows
    assert "email,first_name,last_name,company,title" in lines[0]
    assert "sarah@acme.com,Sarah,Connor,Acme Corp,VP Engineering" in lines[1]
    assert "john@cyberdyne.org,John,Smith,Cyberdyne Systems,Director of Security" in lines[2]


def test_export_to_hubspot_format() -> None:
    leads = [
        {
            "email": "maya@fintech.io",
            "first_name": "Maya",
            "last_name": "Lin",
            "company": "Fintech Global",
            "title": "Head of Product",
            "linkedin_url": "https://linkedin.com/in/mayalin",
        }
    ]
    res = export_to_hubspot_format(leads)
    assert res["count"] == 1
    assert res["target"] == "hubspot"
    props = res["inputs"][0]["properties"]
    assert props["email"] == "maya@fintech.io"
    assert props["firstname"] == "Maya"
    assert props["lastname"] == "Lin"
    assert props["company"] == "Fintech Global"
    assert props["jobtitle"] == "Head of Product"
    assert props["linkedin"] == "https://linkedin.com/in/mayalin"


def test_export_to_salesforce_format() -> None:
    leads = [
        {
            "email": "david@cloudscale.net",
            "first_name": "David",
            "last_name": "Miller",
            "company": "CloudScale",
            "title": "Chief Architect",
            "notes": "Interested in private LLM deployment",
        }
    ]
    res = export_to_salesforce_format(leads)
    assert res["count"] == 1
    assert res["target"] == "salesforce"
    record = res["records"][0]
    assert record["attributes"]["type"] == "Lead"
    assert record["Company"] == "CloudScale"
    assert record["FirstName"] == "David"
    assert record["LastName"] == "Miller"
    assert record["Email"] == "david@cloudscale.net"
    assert record["Title"] == "Chief Architect"
    assert record["Description"] == "Interested in private LLM deployment"


@pytest.mark.asyncio
async def test_export_leads_router() -> None:
    leads = [{"email": "test@lead.com", "company": "Test Co"}]

    csv_res = await export_leads(leads, format="csv")
    assert csv_res["format"] == "csv"
    assert "test@lead.com" in csv_res["payload"]

    hs_res = await export_leads(leads, format="hubspot")
    assert hs_res["format"] == "hubspot"
    assert hs_res["payload"]["count"] == 1

    sf_res = await export_leads(leads, format="salesforce")
    assert sf_res["format"] == "salesforce"
    assert sf_res["payload"]["count"] == 1

    json_res = await export_leads(leads, format="json")
    assert json_res["format"] == "json"
    assert json_res["payload"] == leads

    with pytest.raises(ValueError, match="Unsupported export format"):
        await export_leads(leads, format="unsupported_format")
