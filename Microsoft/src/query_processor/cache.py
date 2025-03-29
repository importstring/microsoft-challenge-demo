"""
Cache module for query processing.
Implements efficient caching of query responses.
"""

import hashlib
import json
import os
from datetime import datetime, timedelta

class QueryCache:
    def __init__(self, cache_dir='./cache', ttl_hours=24):
        """
        Initialize the query cache.
        
        Args:
            cache_dir: Directory to store cache files
            ttl_hours: Time-to-live for cache entries in hours
        """
        self.cache_dir = cache_dir
        self.ttl = timedelta(hours=ttl_hours)
        os.makedirs(cache_dir, exist_ok=True)
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'stored': 0
        }
        
    def _get_cache_key(self, query, model_name):
        """Generate a unique cache key for a query+model combination"""
        hash_input = f"{query}:{model_name}"
        return hashlib.md5(hash_input.encode()).hexdigest()
        
    def get(self, query, model_name):
        """
        Retrieve cached response if available and not expired.
        
        Args:
            query: The query string
            model_name: Name of the model used
            
        Returns:
            Cached response or None if not found/expired
        """
        cache_key = self._get_cache_key(query, model_name)
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        if not os.path.exists(cache_file):
            self.cache_stats['misses'] += 1
            return None
            
        try:
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
                
            # Check if cache is expired
            cached_time = datetime.fromisoformat(cache_data['timestamp'])
            if datetime.now() - cached_time > self.ttl:
                self.cache_stats['misses'] += 1
                return None
                
            self.cache_stats['hits'] += 1
            return cache_data['response']
            
        except Exception as e:
            print(f"Cache retrieval error: {e}")
            self.cache_stats['misses'] += 1
            return None
            
    def set(self, query, model_name, response):
        """
        Store response in cache.
        
        Args:
            query: The query string
            model_name: Name of the model used
            response: The response to cache
            
        Returns:
            Boolean indicating success
        """
        cache_key = self._get_cache_key(query, model_name)
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        cache_data = {
            'query': query,
            'model': model_name,
            'response': response,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f)
            self.cache_stats['stored'] += 1
            return True
        except Exception as e:
            print(f"Cache storage error: {e}")
            return False
            
    def get_stats(self):
        """Return cache performance statistics"""
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = self.cache_stats['hits'] / max(1, total_requests)
        
        return {
            'hits': self.cache_stats['hits'],
            'misses': self.cache_stats['misses'],
            'stored': self.cache_stats['stored'],
            'hit_rate': hit_rate,
            'total_requests': total_requests
        } 