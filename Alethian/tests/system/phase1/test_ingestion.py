import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
from app.db.session import get_db

# Mock DB Session
def override_get_db():
    mock_db = MagicMock()
    try:
        yield mock_db
    finally:
        pass

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# Mock PDF Content
SAMPLE_PDF_CONTENT = b"%PDF-1.4 sample pdf content"

# Mock Grobid XML Response
SAMPLE_GROBID_XML = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
    <teiHeader>
        <fileDesc>
            <titleStmt>
                <title level="a" type="main">Test Research Paper Title</title>
            </titleStmt>
        </fileDesc>
    </teiHeader>
    <text>
        <front>
            <div type="abstract">
                <p>This is a test abstract.</p>
            </div>
        </front>
        <body>
            <div>
                <head>Introduction</head>
                <p>This is the introduction section.</p>
            </div>
        </body>
        <back>
            <div type="references">
                <listBibl>
                    <biblStruct>
                        <analytic>
                            <title level="a">Cited Paper A</title>
                            <author><surname>Smith</surname></author>
                        </analytic>
                        <monogr>
                            <imprint><date when="2023" /></imprint>
                        </monogr>
                    </biblStruct>
                </listBibl>
            </div>
        </back>
    </text>
</TEI>
"""

def test_upload_document_success():
    """
    Test uploading a valid PDF document with DB mock.
    """
    with patch("app.core.ingestion.requests.post") as mock_post:
        # Configure the mock to return our sample XML
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = SAMPLE_GROBID_XML.encode('utf-8')
        mock_post.return_value = mock_response

        # Perform the upload
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("test_paper.pdf", SAMPLE_PDF_CONTENT, "application/pdf")}
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert data["filename"] == "test_paper.pdf"
        # Status might be 'complete' now due to sync processing
        assert data["status"] in ["processed", "complete"]
        
        # Check parsed data structure
        parsed_data = data["data"]
        assert parsed_data["title"] == "Test Research Paper Title"
        assert parsed_data["abstract"] == "This is a test abstract."
        assert len(parsed_data["sections"]) == 1
        assert parsed_data["sections"][0]["heading"] == "Introduction"
        assert len(parsed_data["references"]) == 1
        assert parsed_data["references"][0]["title"] == "Cited Paper A"

def test_upload_invalid_file_type():
    """Test uploading a non-PDF file."""
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.txt", b"plain text", "text/plain")}
    )
    assert response.status_code == 400
    assert "Only PDF files are allowed" in response.json()["detail"]

def test_grobid_failure_handling():
    """Test handling of Grobid service failure."""
    with patch("app.core.ingestion.requests.post") as mock_post:
        # Create a real response object to simulate HTTPError
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response
        mock_response.raise_for_status.side_effect = Exception("Grobid Service Unavailable")

        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("fail.pdf", SAMPLE_PDF_CONTENT, "application/pdf")}
        )
        
        assert response.status_code == 500
