"""
Microsoft 365 integration module for query processing.
Enables integration with Microsoft 365 services for continuous model improvement.
"""

import json
import os
import logging
import time
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

# Optional dependencies - these will be imported only if available
try:
    import msal
    import requests
    from azure.identity import DefaultAzureCredential
    MS365_AVAILABLE = True
except ImportError:
    MS365_AVAILABLE = False

logger = logging.getLogger("query_processor.ms365")

class MS365Connector:
    def __init__(self, client_id=None, client_secret=None, tenant_id=None, scopes=None):
        """
        Initialize Microsoft 365 connector.
        
        Args:
            client_id: Azure AD application ID (optional)
            client_secret: Azure AD application secret (optional)
            tenant_id: Azure AD tenant ID (optional)
            scopes: List of Microsoft Graph API permission scopes
        """
        if not MS365_AVAILABLE:
            raise ImportError("MS365 SDK packages are not installed. Please install them with: "
                            "pip install msal azure-identity pandas")
            
        self.client_id = client_id or os.environ.get("MS365_CLIENT_ID")
        self.client_secret = client_secret or os.environ.get("MS365_CLIENT_SECRET")
        self.tenant_id = tenant_id or os.environ.get("MS365_TENANT_ID")
        self.scopes = scopes or ["https://graph.microsoft.com/.default"]
        
        if not (self.client_id and self.client_secret and self.tenant_id):
            raise ValueError("Microsoft 365 credentials not provided and environment variables not set")
            
        self.token = None
        self.token_expiry = None
        
    def get_token(self):
        """
        Authenticate with Microsoft Graph API and get access token.
        
        Returns:
            Access token string
        """
        # Check if existing token is still valid
        if self.token and self.token_expiry and datetime.now() < self.token_expiry:
            return self.token
            
        try:
            # Create MSAL confidential client
            app = msal.ConfidentialClientApplication(
                self.client_id,
                authority=f"https://login.microsoftonline.com/{self.tenant_id}",
                client_credential=self.client_secret
            )
            
            # Acquire token for client
            result = app.acquire_token_for_client(scopes=self.scopes)
            
            if "access_token" in result:
                self.token = result["access_token"]
                # Set expiry time (default token lifetime is typically 1 hour)
                expires_in = result.get("expires_in", 3600)
                self.token_expiry = datetime.now() + timedelta(seconds=expires_in)
                return self.token
            else:
                error = f"Authentication error: {result.get('error')}: {result.get('error_description')}"
                logger.error(error)
                raise Exception(error)
                
        except Exception as e:
            logger.error(f"Failed to acquire token: {str(e)}")
            raise
        
    def get_graph_data(self, endpoint, params=None):
        """
        Get data from Microsoft Graph API.
        
        Args:
            endpoint: Graph API endpoint path
            params: Optional query parameters
            
        Returns:
            API response as dictionary
        """
        if not self.token:
            self.get_token()
            
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        
        url = f"https://graph.microsoft.com/v1.0/{endpoint}"
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()  # Raise exception for HTTP errors
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Graph API request failed: {str(e)}")
            # If unauthorized, refresh token and retry once
            if response.status_code == 401:
                self.token = None
                self.get_token()
                headers['Authorization'] = f'Bearer {self.token}'
                response = requests.get(url, headers=headers, params=params)
                response.raise_for_status()
                return response.json()
            raise
    
    def get_collaborative_patterns(self, days=7, limit=1000):
        """
        Extract collaboration patterns from Microsoft 365 for model improvement.
        
        Args:
            days: Number of days of historical data to retrieve
            limit: Maximum number of records to retrieve
            
        Returns:
            DataFrame of collaboration patterns
        """
        since_date = (datetime.now() - timedelta(days=days)).isoformat()
        patterns = []
        
        try:
            # Get recent Teams messages
            teams_data = self.get_graph_data(
                "teams/getAllMessages", 
                params={
                    "$filter": f"createdDateTime ge {since_date}",
                    "$top": limit
                }
            )
            
            # Process Teams messages
            if "value" in teams_data:
                for msg in teams_data["value"]:
                    patterns.append({
                        "source": "teams",
                        "text": msg.get("body", {}).get("content", ""),
                        "reactions": len(msg.get("reactions", [])),
                        "replies": len(msg.get("replies", [])),
                        "timestamp": msg.get("createdDateTime")
                    })
            
            # Get recent Outlook emails
            mail_data = self.get_graph_data(
                "me/messages", 
                params={
                    "$filter": f"createdDateTime ge {since_date}",
                    "$top": limit
                }
            )
            
            # Process emails
            if "value" in mail_data:
                for mail in mail_data["value"]:
                    patterns.append({
                        "source": "outlook",
                        "text": mail.get("bodyPreview", ""),
                        "importance": mail.get("importance", "normal"),
                        "has_attachments": mail.get("hasAttachments", False),
                        "timestamp": mail.get("createdDateTime")
                    })
            
            return pd.DataFrame(patterns)
            
        except Exception as e:
            logger.error(f"Error fetching collaboration patterns: {str(e)}")
            return pd.DataFrame(patterns)
    
    def extract_query_patterns(self, days=30):
        """
        Extract common query patterns from Microsoft Search logs.
        
        Args:
            days: Number of days of historical data to retrieve
            
        Returns:
            DataFrame of query patterns
        """
        since_date = (datetime.now() - timedelta(days=days)).isoformat()
        patterns = []
        
        try:
            # Get Microsoft Search insights
            search_data = self.get_graph_data(
                "search/insights", 
                params={
                    "$filter": f"createdDateTime ge {since_date}"
                }
            )
            
            # Process search data
            if "value" in search_data:
                for query in search_data["value"]:
                    patterns.append({
                        "query_text": query.get("queryText", ""),
                        "result_count": query.get("resultCount", 0),
                        "source": query.get("source", "unknown"),
                        "timestamp": query.get("createdDateTime")
                    })
                    
            return pd.DataFrame(patterns)
            
        except Exception as e:
            logger.error(f"Error fetching search patterns: {str(e)}")
            return pd.DataFrame(patterns)
            
    def improve_model_with_insights(self, model, days=30):
        """
        Use MS365 data to improve anomaly detection model.
        
        Args:
            model: The anomaly detection model to improve
            days: Number of days of historical data to use
            
        Returns:
            Improved model
        """
        try:
            # Get collaborative patterns
            patterns_df = self.get_collaborative_patterns(days=days)
            
            # Get search patterns
            search_df = self.extract_query_patterns(days=days)
            
            if patterns_df.empty and search_df.empty:
                logger.warning("No MS365 data available for model improvement")
                return model
                
            # Extract useful features from patterns
            if not patterns_df.empty:
                # Text length distribution
                patterns_df['text_length'] = patterns_df['text'].apply(lambda x: len(x) if isinstance(x, str) else 0)
                
                # Word count distribution
                patterns_df['word_count'] = patterns_df['text'].apply(
                    lambda x: len(x.split()) if isinstance(x, str) else 0
                )
                
                # Feature vector for model enhancement
                text_length_dist = patterns_df['text_length'].describe().to_dict()
                word_count_dist = patterns_df['word_count'].describe().to_dict()
                
                logger.info(f"Enhanced model with {len(patterns_df)} collaboration patterns")
                
                # Here you would typically use these insights to adjust model parameters
                # For demonstration purposes, we're just logging the insights
                
            return model
            
        except Exception as e:
            logger.error(f"Error improving model with MS365 insights: {str(e)}")
            return model
        
class MS365InsightExtractor:
    """
    Extracts insights from Microsoft 365 data to enhance query understanding.
    """
    
    def __init__(self, connector):
        """
        Initialize MS365 insight extractor.
        
        Args:
            connector: MS365Connector instance
        """
        self.connector = connector
        
    def extract_common_topics(self, days=30, min_frequency=2):
        """
        Extract common topics from Microsoft 365 communications.
        
        Args:
            days: Number of days of historical data
            min_frequency: Minimum frequency to consider a topic common
            
        Returns:
            Dictionary of common topics with their frequencies
        """
        patterns_df = self.connector.get_collaborative_patterns(days=days)
        
        if patterns_df.empty:
            return {}
            
        # Simple topic extraction based on word frequency
        all_words = []
        for text in patterns_df['text']:
            if isinstance(text, str):
                words = [word.lower() for word in text.split() 
                         if len(word) > 3 and word.isalnum()]
                all_words.extend(words)
        
        # Count word frequencies
        word_counts = {}
        for word in all_words:
            if word not in word_counts:
                word_counts[word] = 0
            word_counts[word] += 1
        
        # Filter by minimum frequency
        common_topics = {word: count for word, count in word_counts.items() 
                        if count >= min_frequency}
        
        # Sort by frequency (descending)
        common_topics = dict(sorted(common_topics.items(), 
                                    key=lambda x: x[1], reverse=True))
        
        return common_topics
        
    def extract_organization_entities(self, days=30):
        """
        Extract important organization entities (people, teams, projects).
        
        Args:
            days: Number of days of historical data
            
        Returns:
            Dictionary of entity types with lists of entities
        """
        patterns_df = self.connector.get_collaborative_patterns(days=days)
        entities = {
            'people': set(),
            'teams': set(),
            'projects': set()
        }
        
        # This would typically use NER (Named Entity Recognition)
        # For demonstration, we'll use a simple approach
        
        # Get organization data from MS Graph
        try:
            # Get users
            users_data = self.connector.get_graph_data("users", params={"$top": 100})
            if "value" in users_data:
                for user in users_data["value"]:
                    display_name = user.get("displayName")
                    if display_name:
                        entities['people'].add(display_name)
            
            # Get teams
            teams_data = self.connector.get_graph_data("teams", params={"$top": 100})
            if "value" in teams_data:
                for team in teams_data["value"]:
                    display_name = team.get("displayName")
                    if display_name:
                        entities['teams'].add(display_name)
                        
            # Projects would typically come from Project or Planner
            # This is a simplified example
            
        except Exception as e:
            logger.error(f"Error extracting organization entities: {str(e)}")
            
        # Convert sets to lists for JSON serialization
        return {k: list(v) for k, v in entities.items()} 