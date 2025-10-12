# DevSecOps Automation Project Demo Guide

This guide will help you demonstrate all the features of the DevSecOps Automation Project.

## Setup Instructions

1. Run `setup.bat` to install all dependencies
2. Run `start.bat` to start both backend and frontend servers

## Feature Demonstration

### 1. Dashboard
- Navigate to the Dashboard to see an overview of previous scans
- Explain how the dashboard provides a quick summary of security posture

### 2. Automated Code Scanning
- Click "New Scan" in the navigation
- Enter a repository path (use one of the demo apps: `./demo-apps/node-express` or `./demo-apps/python-flask`)
- Select scan types (SAST, Threat Modeling)
- Start the scan and show the progress indicator
- Explain how the system integrates multiple scanners (Semgrep, Bandit, RetireJS)

### 3. Threat Modeling Engine
- After scan completes, navigate to the "Threats" tab
- Demonstrate the STRIDE-based threat modeling results
- Explain how threats are categorized and prioritized

### 4. Security Architecture Analyzer
- Show how the system analyzes application architecture
- Explain how it identifies relationships between components
- Point out the visualization of component relationships

### 5. Manual Review Mode
- Navigate to the "Findings" tab
- Select a finding and show the manual review interface
- Demonstrate changing status (Open, In Progress, Fixed, False Positive)
- Add reviewer comments and submit the review
- Show how the status updates in real-time

### 6. Unified Vulnerability Report
- Demonstrate exporting findings to JSON or HTML format
- Explain how this provides a comprehensive view of all security issues

### 7. Remediation Guidance & CWE Mapping
- Select a finding and show the remediation guidance
- Point out the CWE mapping and explain its importance
- Show how developers can use this information to fix issues

### 8. Training / Developer Outreach Section
- Navigate to the "Training" tab
- Show the AppSec best practices and resources
- Explain how this helps educate developers on security concepts

## Key Talking Points

- **Comprehensive Security Analysis**: The platform combines SAST, threat modeling, and architecture analysis
- **Developer-Friendly**: Provides actionable remediation guidance and educational resources
- **Flexible Workflow**: Supports both automated scanning and manual review processes
- **Integrated Approach**: All security information is available in one unified interface

## Troubleshooting

If you encounter any issues:
- Check that both backend and frontend servers are running
- Ensure all dependencies are installed correctly
- Verify that the demo apps are available in the `demo-apps` directory