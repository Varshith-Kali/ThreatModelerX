import logging
import subprocess
import json
import os
import tempfile
from typing import List, Dict, Any, Optional
import asyncio
import aiohttp
import time

from ..models import Finding, SeverityLevel, ScanRequest

logger = logging.getLogger("autothreatmap.scanner.zap")

class ZapRunner:
    """
    OWASP ZAP scanner integration for Dynamic Application Security Testing (DAST)
    """
    
    def __init__(self, zap_api_url: str = "http://localhost:8080", api_key: Optional[str] = None):
        self.zap_api_url = zap_api_url
        self.api_key = api_key or os.environ.get("ZAP_API_KEY", "")
        
    async def scan(self, scan_request: ScanRequest) -> List[Finding]:
        """
        Run OWASP ZAP active scan against a target URL
        
        Args:
            scan_request: The scan request containing target URL
            
        Returns:
            List of security findings
        """
        if not scan_request.target_url:
            logger.warning("No target URL provided for ZAP scan")
            return []
            
        logger.info(f"Starting ZAP scan against {scan_request.target_url}")
        
        try:
            # Step 1: Spider the target to discover endpoints
            spider_id = await self._start_spider(scan_request.target_url)
            if not spider_id:
                return []
                
            # Step 2: Wait for spider to complete
            await self._wait_for_spider_completion(spider_id)
            
            # Step 3: Start active scan
            scan_id = await self._start_active_scan(scan_request.target_url)
            if not scan_id:
                return []
                
            # Step 4: Wait for active scan to complete
            await self._wait_for_scan_completion(scan_id)
            
            # Step 5: Retrieve scan results
            findings = await self._get_scan_results()
            
            logger.info(f"ZAP scan completed with {len(findings)} findings")
            return findings
            
        except Exception as e:
            logger.error(f"Error during ZAP scan: {str(e)}")
            return []
    
    async def _start_spider(self, target_url: str) -> Optional[str]:
        """Start ZAP spider against target URL"""
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    'apikey': self.api_key,
                    'url': target_url,
                    'maxChildren': '10',  # Limit crawl for demo purposes
                    'recurse': 'true',
                    'contextName': '',
                    'subtreeOnly': 'false'
                }
                async with session.get(f"{self.zap_api_url}/JSON/spider/action/scan/", params=params) as response:
                    if response.status != 200:
                        logger.error(f"Failed to start ZAP spider: {response.status}")
                        return None
                    data = await response.json()
                    return data.get('scan')
        except Exception as e:
            logger.error(f"Error starting ZAP spider: {str(e)}")
            return None
    
    async def _wait_for_spider_completion(self, spider_id: str, timeout: int = 600) -> bool:
        """Wait for ZAP spider to complete"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                async with aiohttp.ClientSession() as session:
                    params = {
                        'apikey': self.api_key,
                        'scanId': spider_id
                    }
                    async with session.get(f"{self.zap_api_url}/JSON/spider/view/status/", params=params) as response:
                        if response.status != 200:
                            logger.error(f"Failed to get spider status: {response.status}")
                            return False
                        data = await response.json()
                        status = int(data.get('status', '0'))
                        if status >= 100:
                            logger.info(f"Spider completed: {status}%")
                            return True
                        logger.info(f"Spider progress: {status}%")
            except Exception as e:
                logger.error(f"Error checking spider status: {str(e)}")
                
            await asyncio.sleep(5)  # Check every 5 seconds
            
        logger.warning("Spider timed out")
        return False
    
    async def _start_active_scan(self, target_url: str) -> Optional[str]:
        """Start ZAP active scan against target URL"""
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    'apikey': self.api_key,
                    'url': target_url,
                    'recurse': 'true',
                    'inScopeOnly': 'false',
                    'scanPolicyName': '',
                    'method': '',
                    'postData': ''
                }
                async with session.get(f"{self.zap_api_url}/JSON/ascan/action/scan/", params=params) as response:
                    if response.status != 200:
                        logger.error(f"Failed to start ZAP active scan: {response.status}")
                        return None
                    data = await response.json()
                    return data.get('scan')
        except Exception as e:
            logger.error(f"Error starting ZAP active scan: {str(e)}")
            return None
    
    async def _wait_for_scan_completion(self, scan_id: str, timeout: int = 1800) -> bool:
        """Wait for ZAP active scan to complete"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                async with aiohttp.ClientSession() as session:
                    params = {
                        'apikey': self.api_key,
                        'scanId': scan_id
                    }
                    async with session.get(f"{self.zap_api_url}/JSON/ascan/view/status/", params=params) as response:
                        if response.status != 200:
                            logger.error(f"Failed to get scan status: {response.status}")
                            return False
                        data = await response.json()
                        status = int(data.get('status', '0'))
                        if status >= 100:
                            logger.info(f"Active scan completed: {status}%")
                            return True
                        logger.info(f"Active scan progress: {status}%")
            except Exception as e:
                logger.error(f"Error checking scan status: {str(e)}")
                
            await asyncio.sleep(10)  # Check every 10 seconds
            
        logger.warning("Active scan timed out")
        return False
    
    async def _get_scan_results(self) -> List[Finding]:
        """Get ZAP scan results and convert to Finding objects"""
        findings = []
        
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    'apikey': self.api_key,
                    'baseurl': ''
                }
                async with session.get(f"{self.zap_api_url}/JSON/core/view/alerts/", params=params) as response:
                    if response.status != 200:
                        logger.error(f"Failed to get ZAP alerts: {response.status}")
                        return []
                    data = await response.json()
                    alerts = data.get('alerts', [])
                    
                    for alert in alerts:
                        severity = self._map_severity(alert.get('risk'))
                        finding = Finding(
                            id=f"ZAP-{hash(alert.get('name', '') + alert.get('url', ''))}",
                            title=alert.get('name', 'Unknown ZAP Finding'),
                            description=alert.get('description', ''),
                            severity=severity,
                            confidence=self._map_confidence(alert.get('confidence')),
                            location=alert.get('url', ''),
                            line_number=0,  # ZAP doesn't provide line numbers
                            snippet=alert.get('evidence', ''),
                            scanner="OWASP ZAP",
                            rule_id=alert.get('pluginId', ''),
                            cwe_id=self._extract_cwe(alert.get('cweid', '0')),
                            recommendation=alert.get('solution', ''),
                            references=alert.get('reference', ''),
                            tags=["DAST", "ZAP"],
                            metadata={
                                "attack": alert.get('attack', ''),
                                "param": alert.get('param', ''),
                                "evidence": alert.get('evidence', ''),
                                "method": alert.get('method', '')
                            }
                        )
                        findings.append(finding)
        except Exception as e:
            logger.error(f"Error getting ZAP scan results: {str(e)}")
            
        return findings
    
    def _map_severity(self, zap_risk: str) -> SeverityLevel:
        """Map ZAP risk levels to our severity levels"""
        risk_map = {
            "3": SeverityLevel.CRITICAL,
            "2": SeverityLevel.HIGH,
            "1": SeverityLevel.MEDIUM,
            "0": SeverityLevel.LOW,
            "Informational": SeverityLevel.INFO
        }
        return risk_map.get(zap_risk, SeverityLevel.INFO)
    
    def _map_confidence(self, zap_confidence: str) -> float:
        """Map ZAP confidence levels to float values"""
        confidence_map = {
            "3": 0.9,  # High
            "2": 0.7,  # Medium
            "1": 0.5,  # Low
            "0": 0.3   # Informational
        }
        return confidence_map.get(zap_confidence, 0.5)
    
    def _extract_cwe(self, cwe_str: str) -> int:
        """Extract CWE ID from ZAP CWE string"""
        try:
            return int(cwe_str)
        except (ValueError, TypeError):
            return 0