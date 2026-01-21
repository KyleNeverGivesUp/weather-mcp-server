# document_mcp_server.py
# MCP Server for Document Management System
# Version 1.0 - CONTAINS INTENTIONAL BUGS FOR ASSESSMENT
# 
# Instructions: This code contains multiple categories of issues:
# - Execution-blocking errors (syntax, imports)
# - Runtime bugs (resource leaks, async/sync issues)
# - Security vulnerabilities (injection, hardcoded secrets)
# - Enterprise deployment concerns (logging, scalability)

import os
import sys
import json
import logging
import subprocess
import sqlite3
import hashlib
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import path  # Line 19 - BUG: Should be 'Path' (capital P)

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

# Configuration - HARDCODED FOR DEVELOPMENT
DATABASE_URL = "postgresql://admin:SuperSecret123!@prod-db.company.com:5432/documents"  # Line 25 - SECURITY: Hardcoded credentials
API_KEY = "sk-prod-abc123xyz789secretkey"  # Line 26 - SECURITY: Hardcoded API key
UPLOAD_DIR = "/tmp/uploads"
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

# Setup logging - writes to stdout (BAD for STDIO transport)
logging.basicConfig(level=logging.DEBUG, format="%(message)s")  # Line 31 - BUG: stdout logging breaks STDIO
logger = logging.getLogger(__name__)

# Initialize MCP Server
mcp = FastMCP("Document Management Server")

# Global state - not thread safe
document_cache = {}  # Line 38 - ENTERPRISE: Thread-unsafe global state
user_sessions = {}


class DocumentMetadata(BaseModel):
    id: str
    filename: str
    filepath: str
    size: int
    created_at: datetime
    owner: str
    permissions: Dict[str, List[str]]


def get_db_connection():
    """Create database connection"""
    conn = sqlite3.connect(":memory:")  # Using in-memory for demo
    return conn  # Line 55 - BUG: Connection never closed, resource leak


@mcp.tool()
def search_documents(query: str, user_id: str) -> List[Dict]:
    """
    Search documents by query string.
    
    Args:
        query: Search query string
        user_id: ID of user performing search
    
    Returns:
        List of matching documents
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # SQL query with user input directly interpolated
    sql = f"SELECT * FROM documents WHERE content LIKE '%{query}%'"  # Line 73 - SECURITY: SQL Injection
    print(f"Executing query: {sql}")  # Line 74 - BUG: print() breaks STDIO transport
    
    cursor.execute(sql)
    results = cursor.fetchall()
    
    # Note: Connection not closed - will be garbage collected
    return results


@mcp.tool()
def read_document(document_id: str, user_id: str) -> Dict:
    """Read document content by ID"""
    
    # Check cache first
    if document_id in document_cache:
        return document_cache[document_id]
    
    # Construct file path from document_id without validation
    filepath = f"{UPLOAD_DIR}/{document_id}"  # Line 91 - SECURITY: Path traversal vulnerability
    
    try:
        with open(filepath, "r") as f:
            content = f.read()
            document_cache[document_id] = {
                "id": document_id,
                "content": content,
                "filepath": filepath  # Line 98 - SECURITY: Exposing internal paths
            }
            return document_cache[document_id]
    except FileNotFoundError:
        return {"error": f"Document {document_id} not found at {filepath}"}  # Line 101 - SECURITY: Info leakage
    except Exception as e:
        return {"error": str(e)}  # Line 103 - SECURITY: Stack trace exposure


@mcp.tool()
def execute_document_script(document_id: str, script: str) -> Dict:
    """
    Execute a processing script on a document.
    This allows users to run custom transformations.
    """
    document = read_document(document_id, "system")
    
    if "error" in document:
        return document
    
    # Execute the user-provided script - CRITICAL VULNERABILITY
    result = subprocess.run(
        f"echo '{document['content']}' | {script}",  # Line 118 - SECURITY: Command injection
        shell=True,  # Line 119 - SECURITY: shell=True with user input
        capture_output=True,
        text=True
    )
    
    return {
        "output": result.stdout,
        "errors": result.stderr,
        "exit_code": result.returncode
    }


@mcp.tool()
def upload_document(filename: str, content: str, user_id: str) -> Dict:
    """Upload a new document"""
    
    # Generate document ID using MD5 (weak hash)
    doc_id = hashlib.md5(content.encode()).hexdigest()  # Line 136 - SECURITY: Weak hash algorithm
    
    # Write file directly using user-provided filename
    filepath = os.path.join(UPLOAD_DIR, filename)  # Line 139 - SECURITY: Path traversal via filename
    
    # Create directory if not exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, "w") as f:
        f.write(content)
    
    logger.info(f"Document uploaded: {filepath} by user {user_id}")
    
    return {
        "id": doc_id,
        "filename": filename,
        "filepath": filepath,  # Line 151 - SECURITY: Exposing internal path
        "status": "uploaded"
    }


@mcp.tool()
def delete_document(document_id: str, user_id str) -> Dict:  # Line 157 - BUG: Missing colon after user_id
    """Delete a document by ID"""
    
    # No permission check - anyone can delete
    filepath = f"{UPLOAD_DIR}/{document_id}"  # SECURITY: Path traversal
    
    try:
        os.remove(filepath)
        
        # Remove from cache
        if document_id in document_cache:
            del document_cache[document_id]
        
        return {"status": "deleted", "document_id": document_id}
    except:  # Line 170 - BUG: Bare except clause
        return {"error": "Failed to delete"}


@mcp.tool()
def share_document(document_id: str, target_user: str, permission: str) -> Dict:
    """Share a document with another user"""
    
    # No validation on permission string - accepts anything
    valid_permissions = ["read", "write", "admin"]
    # BUG: permission not validated against valid_permissions
    
    # Store sharing info in global dict
    if document_id not in document_cache:
        document_cache[document_id] = {"permissions": {}}
    
    document_cache[document_id]["permissions"][target_user] = permission
    
    return {
        "document_id": document_id,
        "shared_with": target_user,
        "permission": permission
    }


@mcp.tool()
async def batch_process_documents(document_ids: List[str], operation: str) -> List[Dict]:
    """Process multiple documents in batch"""
    
    results = []
    
    # No rate limiting or batch size limit - DoS vulnerability
    for doc_id in document_ids:  # Line 201 - ENTERPRISE: No batch size limit
        if operation == "read":
            result = read_document(doc_id, "batch_user")  # Line 203 - BUG: Calling sync from async
        elif operation == "delete":
            result = delete_document(doc_id, "batch_user")  # Line 205 - BUG: Calling sync from async
        else:
            result = {"error": f"Unknown operation: {operation}"}
        
        results.append(result)
    
    return results


@mcp.resource("documents://list")
def list_all_documents():
    """List all documents - exposes full file paths"""
    
    documents = []
    
    for filename in os.listdir(UPLOAD_DIR):
        full_path = os.path.join(UPLOAD_DIR, filename)
        documents.append({
            "filename": filename,
            "full_path": full_path,  # Line 223 - SECURITY: Exposing internal paths
            "size": os.path.getsize(full_path)
        })
    
    return json.dumps(documents)


@mcp.resource("config://settings")
def get_config():
    """Return server configuration - EXPOSES SECRETS"""
    return json.dumps({
        "database_url": DATABASE_URL,  # Line 233 - SECURITY: Exposing DB credentials via resource
        "api_key": API_KEY,  # Line 234 - SECURITY: Exposing API key via resource
        "upload_dir": UPLOAD_DIR,
        "max_file_size": MAX_FILE_SIZE
    })


@mcp.tool()
def analyze_document_with_ai(document_id: str, prompt: str) -> Dict:
    """
    Analyze a document using AI.
    The prompt is passed directly to the AI without sanitization.
    """
    document = read_document(document_id, "ai_system")
    
    if "error" in document:
        return document
    
    # Construct AI prompt with document content and user prompt
    # No prompt injection protection
    full_prompt = f"""
    Document content:
    {document["content"]}
    
    User request:
    {prompt}
    """  # Line 257 - SECURITY: No prompt injection mitigation
    
    # Placeholder for AI call
    return {"analysis": f"Analysis pending for prompt: {full_prompt[:100]}..."}


@mcp.tool()
def get_document_history(document_id: str) -> List[Dict]:
    """Get version history for a document"""
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Another SQL injection vulnerability
    sql = f"SELECT * FROM document_history WHERE doc_id = '{document_id}'"  # Line 270 - SECURITY: SQL injection
    cursor.execute(sql)
    
    return cursor.fetchall()
    # BUG: Connection not closed


# Main entry point
if __name__ == "__main__":
    print(f"Starting server with API key: {API_KEY}")  # Line 279 - SECURITY: Logging secrets
    # BUG: print() will break STDIO transport
    mcp.run()

# END OF CODE (282 lines)
