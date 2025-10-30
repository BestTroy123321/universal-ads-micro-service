import os
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, conint
from dotenv import load_dotenv

from universal_ads_sdk import UniversalAdsClient, APIError, AuthenticationError


app = FastAPI()
load_dotenv()


class ReportRequest(BaseModel):
    start_date: str
    end_date: str
    adaccount_id: str
    campaign_ids: Optional[List[str]] = None
    limit: Optional[conint(gt=0)] = None
    offset: Optional[conint(ge=0)] = None


@app.post("/reports/campaign")
async def get_campaign_report(request: ReportRequest):
    api_key = os.getenv("UNIVERSAL_ADS_API_KEY")
    private_key_pem = os.getenv("UNIVERSAL_ADS_PRIVATE_KEY")

    if not api_key or not private_key_pem:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Missing credentials",
                "message": "Skonfiguruj plik .env (UNIVERSAL_ADS_API_KEY, UNIVERSAL_ADS_PRIVATE_KEY)",
            },
        )

    try:
        base_url = os.getenv("UNIVERSAL_ADS_BASE_URL")
        client = UniversalAdsClient(
            api_key=api_key,
            private_key_pem=private_key_pem,
            base_url=base_url
        )
        params = {
            "start_date": request.start_date,
            "end_date": request.end_date,
            "adaccount_id": request.adaccount_id,
            "campaign_ids": request.campaign_ids,
        }
        if request.limit is not None:
            params["limit"] = request.limit
        if request.offset is not None:
            params["offset"] = request.offset

        report = client.get_campaign_report(**params)
        return report
    except AuthenticationError as e:
        raise HTTPException(
            status_code=400,
            detail={"error": "Authentication failed", "message": str(e)},
        )
    except APIError as e:
        status_code = getattr(e, "status_code", None)
        status = 400 if status_code and 400 <= status_code < 500 else 500
        detail = {"error": "API error", "message": str(e)}
        if hasattr(e, "response_data") and e.response_data is not None:
            detail["response_data"] = e.response_data
        raise HTTPException(status_code=status, detail=detail)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail={"error": "Unexpected error", "message": str(e)}
        )


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)