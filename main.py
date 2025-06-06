import base64
from pydantic import BaseModel, Field
import json
from pathlib import Path
import os
from typing import Any, Dict, List, Literal, Optional, Union
from uuid import UUID

import requests
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache
from fastapi_cache.backends.inmemory import InMemoryBackend
from dotenv import load_dotenv
from fastapi import Query
from typing import List, Optional
import html2text
from textwrap import dedent
from models import Bill, BillSummary, TextFormat, TextVersion, President, DocumentType, PresidentialDocument

# Load environment variables from .env file
load_dotenv()

# Constants
CONGRESS_API_KEY = os.getenv("CONGRESS_API_KEY")
CONGRESS_API_HOST = "https://api.congress.gov/v3"

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:1420",
    "http://localhost:5050",
    "https://pro.openbb.dev",
    "https://pro.openbb.co",
    "https://excel.openbb.co",
    "https://excel.openbb.dev",
    "http://localhost:3000",
    "https://pro.azure.openbb.dev"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ROOT_PATH = Path(__file__).parent.resolve()

@app.on_event("startup")
async def startup():
    FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache")

@app.get("/")
def read_root():
    return {"Info": "Government API"}

@app.get("/widgets.json")
def get_widgets():
    """Widgets configuration file for the OpenBB Terminal Pro"""
    return JSONResponse(
        content=json.load((Path(__file__).parent.resolve() / "widgets.json").open())
    )

@app.get("/apps.json")
def get_apps():
    """Apps configuration file for the OpenBB Terminal Pro"""
    return JSONResponse(
        content=json.load((Path(__file__).parent.resolve() / "apps.json").open())
    )

# Returns a list of bills sorted by date of latest action.
@app.get("/congress/bills")
@cache(expire=3600)  # Cache for 1 hour
async def get_bills(
    format: str = Query("json", regex="^(json|xml)$"),
    offset: int = Query(0),
    limit: int = Query(100, le=250),
    fromDateTime: Optional[str] = Query(None),
    toDateTime: Optional[str] = Query(None),
    sort: str = Query("updateDate+desc", regex="^(updateDate\\+asc|updateDate\\+desc)$")
) -> List[Bill]:
    """Get filtered list of bills from Congress API"""
    url = f"{CONGRESS_API_HOST}/bill"

            # Convert date format if provided
    if fromDateTime:
        fromDateTime = f"{fromDateTime}T00:00:00Z"
    if toDateTime:
        toDateTime = f"{toDateTime}T00:00:00Z"
    params = {
        "api_key": CONGRESS_API_KEY,
        "format": format,
        "offset": offset,
        "limit": limit,
        "fromDateTime": fromDateTime,
        "toDateTime": toDateTime,
        "sort": sort
    }



    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        bills_data = response.json().get("bills", [])

        # Transform the response into a list of Bill objects
        bills = [Bill(
            congress=bill.get("congress"),
            latest_action_date=bill.get("latestAction", {}).get("actionDate"),
            latest_action_text=bill.get("latestAction", {}).get("text"),
            number=bill.get("number"),
            origin_chamber=bill.get("originChamber"),
            origin_chamber_code=bill.get("originChamberCode"),
            title=bill.get("title"),
            type=bill.get("type"),
            update_date=bill.get("updateDate"),
            update_date_including_text=bill.get("updateDateIncludingText"),
            url=bill.get("url")
        ) for bill in bills_data]
        
        return bills
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching filtered bills data: {str(e)}")

#Returns a list of bills filtered by the specified congress and bill type, sorted by date of latest action.
@app.get("/congress/{congress}/bills/{billType}/filtered")
async def get_filtered_bills(
    congress: int,  # Path parameter
    billType: str,  # Path parameter
    offset: int = Query(0),
    limit: int = Query(100, le=250)
) -> List[Bill]:
    """Get list of bills from Congress API filtered by congress and bill type"""
    url = f"{CONGRESS_API_HOST}/bill/{congress}/{billType}"
    params = {
        "api_key": CONGRESS_API_KEY,
        "offset": offset,
        "limit": limit
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        bills_data = response.json().get("bills", [])

        # Transform the response into a list of Bill objects
        bills = [Bill(
            congress=bill.get("congress"),
            latest_action_date=bill.get("latestAction", {}).get("actionDate"),
            latest_action_text=bill.get("latestAction", {}).get("text"),
            number=bill.get("number"),
            origin_chamber=bill.get("originChamber"),
            origin_chamber_code=bill.get("originChamberCode"),
            title=bill.get("title"),
            type=bill.get("type"),
            update_date=bill.get("updateDate"),
            update_date_including_text=bill.get("updateDateIncludingText"),
            url=bill.get("url")
        ) for bill in bills_data]
        
        return bills
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching bills data: {str(e)}")

@app.get("/congress/{congress}/bills/{billType}/{billNumber}")
@cache(expire=3600)  # Cache for 1 hour
async def get_bill_details(
    congress: int,  # Path parameter
    billType: str,  # Path parameter
    billNumber: str  # Path parameter
) -> Bill:
    """Get details of a specific bill from Congress API"""
    url = f"{CONGRESS_API_HOST}/bill/{congress}/{billType}/{billNumber}"
    params = {"api_key": CONGRESS_API_KEY}
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        bill_data = response.json()
        
        # Create a Bill object from the response
        bill = Bill(
            congress=bill_data.get("congress"),
            latest_action_date=bill_data.get("latestAction", {}).get("actionDate"),
            latest_action_text=bill_data.get("latestAction", {}).get("text"),
            number=bill_data.get("number"),
            origin_chamber=bill_data.get("originChamber"),
            origin_chamber_code=bill_data.get("originChamberCode"),
            title=bill_data.get("title"),
            type=bill_data.get("type"),
            update_date=bill_data.get("updateDate"),
            update_date_including_text=bill_data.get("updateDateIncludingText"),
            url=bill_data.get("url")
        )
        
        return bill
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching bill details: {str(e)}")

# Returns the list of summaries for a specified bill.
@app.get("/summaries/{congress}/bills/{billType}/{number}")
@cache(expire=3600)  # Cache for 1 hour
async def get_bill_summaries(
    congress: int,
    billType: str,
    number: str,
    format: str = Query("json", regex="^(json|xml)$"),
    offset: int = Query(0),
    limit: int = Query(200, le=250),
    override_bill_number: Optional[str] = Query(None)
) -> str:
    """Get list of summaries for a specified bill from Congress API with markdown formatting"""
    
    # Use override parameters if provided, otherwise use path parameters
    actual_bill_number = override_bill_number if override_bill_number is not None else number
    
    url = f"{CONGRESS_API_HOST}/bill/{congress}/{billType}/{actual_bill_number}/summaries"
    params = {
        "api_key": CONGRESS_API_KEY,
        "format": format,
        "offset": offset,
        "limit": limit
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        summaries_data = response.json().get("summaries", [])

        if not summaries_data:
            return "No summaries available for this bill."

        # Get the first summary (usually there's only one)
        summary = summaries_data[0]
        
        # Initialize HTML to markdown converter
        h = html2text.HTML2Text()
        h.body_width = 0  # Disable line wrapping

        # Convert HTML text to markdown and replace double quotes with single quotes
        markdown_text = h.handle(summary.get("text", "")).replace('"', "'")

        # Format the response in markdown
        markdown = dedent(f"""
# Bill Summary

**Action Date:** {summary.get('actionDate', 'N/A')}  

**Action:** {summary.get('actionDesc', 'N/A')}  
**Last Updated:** {summary.get('updateDate', 'N/A')}  
**Version:** {summary.get('versionCode', 'N/A')}  

## Summary Text

{markdown_text}
        """)

        return markdown
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching bill summaries: {str(e)}")
    

# Returns the list of text versions for a specified bill.
@app.get("/congress/{congress}/bills/{billType}/{number}/text")
@cache(expire=3600)  # Cache for 1 hour
async def get_bill_text_versions(
    congress: int,  # Path parameter
    billType: str,  # Path parameter
    number: str,  # Path parameter
    format: str = Query("json", regex="^(json|xml)$"),
    offset: int = Query(0),
    limit: int = Query(100, le=250),
    override_bill_number: Optional[str] = Query(None)
) -> List[TextVersion]:
    """Get list of text versions for a specified bill from Congress API"""
    
    # Use override parameters if provided, otherwise use path parameters
    actual_bill_number = override_bill_number if override_bill_number is not None else number
    
    url = f"{CONGRESS_API_HOST}/bill/{congress}/{billType}/{actual_bill_number}/text"

    print(url)
    params = {
        "api_key": CONGRESS_API_KEY,
        "format": format,
        "offset": offset,
        "limit": limit
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        text_versions_data = response.json().get("textVersions", [])

        # Filter and transform the response to include only PDF versions
        pdf_versions = []
        for text_version in text_versions_data:
            for format in text_version.get("formats", []):
                # Filter for Formatted Text - can get PDF but file_viewer doesnt work for this yet - https://api.congress.gov/#/bill/bill_text
                # Format is like this             "formats": [
            #     {
            #         "type": "Formatted Text",
            #         "url": "https://www.congress.gov/117/bills/hr3076/BILLS-117hr3076pcs2.htm"
            #     },
            #     {
            #         "type": "PDF",
            #         "url": "https://www.congress.gov/117/bills/hr3076/BILLS-117hr3076pcs2.pdf"
            #     },
            #     {
            #         "type": "Formatted XML",
            #         "url": "https://www.congress.gov/117/bills/hr3076/BILLS-117hr3076pcs2.xml"
            #     }
            # ],
                if format.get("type") == "Formatted Text":
                    pdf_versions.append({
                        "title": text_version.get("type"),
                        "description": f"Text version of the bill as of {text_version.get('date')}",
                        "link": format.get("url")
                    })

        return pdf_versions
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching bill text versions: {str(e)}")

@app.get("/get_bill_html")
async def get_bill_html(path: str) -> str:
    """Fetch HTML content from a given path"""
    try:
        response = requests.get(path)

        response.raise_for_status()

        return response.text
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching HTML content: {str(e)}")


@app.get("/summary/congress/{congress}/bills/{billType}/summaries")
# @cache(expire=3600)  # Cache for 1 hour
async def get_filtered_bill_summaries(
    congress: int,  # Path parameter
    billType: str,  # Path parameter
    format: str = Query("json", regex="^(json|xml)$"),
    offset: int = Query(0),
    limit: int = Query(100, le=250),
    fromDateTime: Optional[str] = Query(None),
    toDateTime: Optional[str] = Query(None),
    sort: str = Query("updateDate+desc", regex="^(updateDate\\+asc|updateDate\\+desc)$")
) -> List[BillSummary]:


    """Get list of summaries for bills filtered by congress and bill type from Congress API"""
    url = f"{CONGRESS_API_HOST}/summaries/{congress}/{billType}"
    params = {
        "api_key": CONGRESS_API_KEY,
        "format": format,
        "offset": offset,
        "limit": limit,
        "fromDateTime": fromDateTime,
        "toDateTime": toDateTime,
        "sort": sort
    }


    try:
        response = requests.get(url, params=params)

        response.raise_for_status()
        summaries_data = response.json().get("summaries", [])


        # Transform the response into a list of BillSummary objects
        summaries = [BillSummary(
            action_date=summary.get("actionDate"),
            action_desc=summary.get("actionDesc"),
            text=summary.get("text"),
            update_date=summary.get("updateDate"),
            version_code=summary.get("versionCode"),
            congress=summary.get("bill", {}).get("congress"),
            number=summary.get("bill", {}).get("number"),
            origin_chamber=summary.get("bill", {}).get("originChamber"),
            origin_chamber_code=summary.get("bill", {}).get("originChamberCode"),
            title=summary.get("bill", {}).get("title"),
            type=summary.get("bill", {}).get("type"),
            update_date_including_text=summary.get("bill", {}).get("updateDateIncludingText"),
            url=summary.get("bill", {}).get("url")
        ) for summary in summaries_data]
        
        return summaries
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching filtered bill summaries: {str(e)}")



## WIP - Dont use yet
@app.get("/daily-congressional-records")
# @cache(expire=3600)  # Cache for 1 hour
async def get_daily_congressional_records(
    format: str = Query("json", regex="^(json|xml)$"),
    offset: int = Query(0),
    limit: int = Query(100, le=250)
) -> List[dict]:
    """Get list of daily congressional records"""
    url = f"{CONGRESS_API_HOST}/daily-congressional-record"
    params = {
        "api_key": CONGRESS_API_KEY,
        "format": format,
        "offset": offset,
        "limit": limit
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json().get("dailyCongressionalRecord", [])
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching daily congressional records: {str(e)}")

## WIP - Dont use yet
@app.get("/daily-congressional-record/{volumeNumber}/{issueNumber}")
# @cache(expire=3600)  # Cache for 1 hour
async def get_congressional_record_by_volume_issue(
    volumeNumber: str,
    issueNumber: str,
    format: str = Query("json", regex="^(json|xml)$")
) -> dict:
    """Get daily congressional records by volume and issue number"""
    url = f"{CONGRESS_API_HOST}/daily-congressional-record/{volumeNumber}/{issueNumber}"
    params = {
        "api_key": CONGRESS_API_KEY,
        "format": format
        }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json().get("issue", {}).get("fullIssue", [])
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching congressional record by volume and issue: {str(e)}")

@app.get("/congress/bills/list")
@cache(expire=3600)  # Cache for 1 hour
async def get_bill_numbers(
    format: str = Query("json", regex="^(json|xml)$"),
    offset: int = Query(0),
    limit: int = Query(250, le=250),
    fromDateTime: Optional[str] = Query(None),
    toDateTime: Optional[str] = Query(None),
    sort: str = Query("updateDate+desc", regex="^(updateDate\\+asc|updateDate\\+desc)$")
) -> List[str]:
    """Get list of bill numbers from Congress API"""
    url = f"{CONGRESS_API_HOST}/bill"
    params = {
        "api_key": CONGRESS_API_KEY,
        "format": format,
        "offset": offset,
        "limit": limit,
        "fromDateTime": fromDateTime,
        "toDateTime": toDateTime,
        "sort": sort
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        bills_data = response.json().get("bills", [])

        # Extract bill numbers from the response and sort them numerically
        bill_numbers = sorted([int(bill.get("number")) for bill in bills_data if bill.get("number")])

        # Convert back to strings to match return type
        bill_numbers = [str(num) for num in bill_numbers]

        print(bill_numbers)

        return bill_numbers
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching bill numbers: {str(e)}")
    


# For getting Presidential Documents
@app.get("/federal-register/presidential-documents")
@cache(expire=3600)  # Cache for 1 hour
async def get_presidential_documents(
    president: President,
    document_types: str = Query(default="executive_order"),
    per_page: int = Query(20, le=100),
    page: int = Query(1, ge=1)
) -> List[PresidentialDocument]:
    """Get presidential documents from the Federal Register API"""
    
    base_url = "https://www.federalregister.gov/api/v1/documents.json"


    # Split the document_types string into a list
    document_types_list = document_types.split(',')
    
    # Build conditions for document types
    document_type_params = [
        f"conditions[presidential_document_type][]={doc_type}"
        for doc_type in document_types_list
    ]
    
    # Construct the full URL with parameters
    params = "&".join([
        f"per_page={per_page}",
        f"page={page}",
        f"conditions[president][]={president.value}",
        "conditions[type][]=PRESDOCU",
        *document_type_params
    ])
    
    url = f"{base_url}?{params}"

    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # Transform the results into PresidentialDocument objects
        documents = [
            PresidentialDocument(
                title=doc["title"],
                type=doc["type"],
                document_number=doc["document_number"],
                html_url=doc["html_url"],
                pdf_url=doc["pdf_url"],
                public_inspection_pdf_url=doc.get("public_inspection_pdf_url"),
                publication_date=doc["publication_date"],
                abstract=doc.get("abstract"),
                excerpts=doc.get("excerpts")
            )
            for doc in data.get("results", [])
        ]
        
        return documents
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching presidential documents: {str(e)}"
        )

# For getting Presidential Documents pdfs
@app.get("/presidential-documents/pdfs")
async def get_presidential_documents(
    president: President = Query(default=President.TRUMP),
    document_types: List[str] = Query(default=["executive_order"]),
    per_page: int = Query(20, le=100),
    page: int = Query(1, ge=1)
) -> List[dict]:
    """Get presidential documents from the Federal Register API"""
    
    base_url = "https://www.federalregister.gov/api/v1/documents.json"
    
    # Build conditions for document types
    document_type_params = [
        f"conditions[presidential_document_type][]={doc_type}"
        for doc_type in document_types
    ]
    
    # Construct the full URL with parameters
    params = "&".join([
        f"per_page={per_page}",
        f"page={page}",
        f"conditions[president][]={president.value}",
        *document_type_params
    ])
    
    url = f"{base_url}?{params}"
    
    try:
        response = requests.get(url)
        data = response.json()

        return [
            {
                "label": (doc.get("title")[:50] + '...') if len(doc.get("title", "")) > 50 else doc.get("title"),
                "value": doc.get("pdf_url")
            }
            for doc in data.get("results", [])
        ]
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching presidential documents: {str(e)}"
        )

# New endpoint for viewing individual presidential document PDFs
@app.get("/presidential-documents/view")
async def view_presidential_document(url: str):
    """View a specific presidential document PDF by URL - downloads and returns as base64"""
    try:
        # Download the PDF from the URL
        response = requests.get(url)
        response.raise_for_status()
        
        # Convert PDF content to base64
        base64_content = base64.b64encode(response.content).decode("utf-8")
        
        # Extract filename from URL for display purposes
        filename = url.split('/')[-1] if '/' in url else "document.pdf"
        if not filename.endswith('.pdf'):
            filename += '.pdf'
        
        # Return plain dictionary to match multi-file viewer expectations
        return {
            "data_format": {"data_type": "pdf", "filename": filename},
            "content": base64_content,
        }
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error downloading presidential document: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing presidential document: {str(e)}"
        )