from fastapi import HTTPException


class SessionNotFound(HTTPException):
    def __init__(self, session_id: str):
        super().__init__(status_code=404, detail=f"Session '{session_id}' not found. Upload a file first.")


class MappingNotConfirmed(HTTPException):
    def __init__(self):
        super().__init__(status_code=422, detail="Column mapping not confirmed yet. Call POST /mapping/confirm first.")


class DataNotCleaned(HTTPException):
    def __init__(self):
        super().__init__(status_code=422, detail="Data not cleaned yet. Call POST /clean first.")


class RequiredColumnsError(HTTPException):
    def __init__(self, missing: list[str]):
        super().__init__(
            status_code=422,
            detail=f"Required columns missing after mapping: {missing}. Check your column mapping."
        )
