"""Map free-text contract / procurement language onto enums."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TypeVar

from app.core.enums import ContractType, OpportunityStatus, ProcurementType, RemoteStatus

T = TypeVar("T")

_CONTRACT_MAP: Sequence[tuple[tuple[str, ...], ContractType]] = [
    (("fixed price", "fixed-price", "lump sum"), ContractType.FIXED_PRICE),
    (("time and materials", "t&m", "time & materials"), ContractType.TIME_AND_MATERIALS),
    (("framework",), ContractType.FRAMEWORK),
    (("call off", "call-off", "calloff"), ContractType.CALL_OFF),
    (("grant",), ContractType.GRANT),
    (("subcontract", "sub-contract"), ContractType.SUBCONTRACT),
    (("rfq", "request for quotation"), ContractType.RFQ),
    (("contract",), ContractType.CONTRACT),
]

_PROCUREMENT_MAP: Sequence[tuple[tuple[str, ...], ProcurementType]] = [
    (("tender", "itt", "invitation to tender"), ProcurementType.TENDER),
    (("rfq", "request for quotation"), ProcurementType.RFQ),
    (("grant",), ProcurementType.GRANT),
    (("framework",), ProcurementType.FRAMEWORK),
    (("subcontract", "sub-contract"), ProcurementType.SUBCONTRACT),
    (("freelance", "upwork", "contractor role"), ProcurementType.FREELANCE),
    (("supplier", "supply"), ProcurementType.SUPPLIER),
]

_STATUS_MAP: Sequence[tuple[tuple[str, ...], OpportunityStatus]] = [
    (("expired", "closed", "past"), OpportunityStatus.EXPIRED),
    (("awarded",), OpportunityStatus.AWARDED),
    (("cancelled", "canceled", "withdrawn"), OpportunityStatus.CANCELLED),
    (("open", "live", "published", "active"), OpportunityStatus.OPEN),
]


def _match(text: str, mapping: Sequence[tuple[tuple[str, ...], T]]) -> T | None:
    lowered = text.casefold()
    for needles, result in mapping:
        if any(needle in lowered for needle in needles):
            return result
    return None


def parse_contract_type(*parts: str | None) -> ContractType:
    blob = " ".join(part for part in parts if part)
    if not blob:
        return ContractType.UNKNOWN
    matched = _match(blob, _CONTRACT_MAP)
    return matched if matched is not None else ContractType.UNKNOWN


def parse_procurement_type(*parts: str | None) -> ProcurementType:
    blob = " ".join(part for part in parts if part)
    if not blob:
        return ProcurementType.OTHER
    matched = _match(blob, _PROCUREMENT_MAP)
    return matched if matched is not None else ProcurementType.OTHER


def parse_status(value: str | None) -> OpportunityStatus:
    if not value:
        return OpportunityStatus.UNKNOWN
    matched = _match(value, _STATUS_MAP)
    return matched if matched is not None else OpportunityStatus.UNKNOWN


def parse_remote_status(location: str | None, extra: str | None = None) -> RemoteStatus:
    blob = " ".join(part for part in (location, extra) if part).casefold()
    if "hybrid" in blob:
        return RemoteStatus.HYBRID
    if "remote" in blob:
        return RemoteStatus.REMOTE
    if any(word in blob for word in ("onsite", "on-site", "on site")):
        return RemoteStatus.ONSITE
    return RemoteStatus.UNKNOWN
