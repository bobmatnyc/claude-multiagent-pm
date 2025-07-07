#!/usr/bin/env python3
"""
Limited test version of GitHub Issue Link Fixer
Tests the fix on just the first 3 issues to verify everything works correctly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fix_github_issue_links import GitHubAPIClient, GitHubIssueLinkFixer, TokenManager, setup_logging
import logging
from pathlib import Path

def main():
    """Test with limited issues"""
    setup_logging(verbose=True)
    logger = logging.getLogger(__name__)
    
    # Load token
    token = TokenManager.load_token_from_env()
    if not token:
        logger.error("GitHub token not found")
        return 1
    
    # Initialize
    client = GitHubAPIClient(token)
    fixer = GitHubIssueLinkFixer(client, "bobmatnyc/claude-pm")
    
    try:
        # Get first 3 issues only
        response = client.make_request(
            "GET",
            "/repos/bobmatnyc/claude-pm/issues",
            params={"state": "all", "per_page": 3}
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to fetch issues: {response.status_code}")
            return 1
        
        issues = response.json()
        logger.info(f"Testing with {len(issues)} issues")
        
        # Process each issue
        for i, issue in enumerate(issues, 1):
            logger.info(f"Processing test issue {i}: #{issue['number']}")
            
            result = fixer._process_single_issue(issue, dry_run=False, backup_timestamp="test")
            
            if result.success and result.changes_made:
                logger.info(f"✅ Successfully updated issue #{result.issue_number}")
            elif not result.changes_made:
                logger.info(f"⏭️ Issue #{result.issue_number} didn't need changes")
            else:
                logger.error(f"❌ Failed to update issue #{result.issue_number}: {result.error_message}")
        
        logger.info("Limited test completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())