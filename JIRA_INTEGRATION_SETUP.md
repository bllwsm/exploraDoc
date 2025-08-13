# Jira Integration Setup Guide for ExploraDoc

This guide walks you through implementing Jira integration in your ExploraDoc application, allowing users to export Word documents directly to Jira issues as attachments with comments.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Authentication Setup](#authentication-setup)
3. [Python Dependencies](#python-dependencies)
4. [Configuration Management](#configuration-management)
5. [UI Implementation](#ui-implementation)
6. [Backend Integration](#backend-integration)
7. [Testing](#testing)
8. [Implementation Phases](#implementation-phases)
9. [Deployment Considerations](#deployment-considerations)

## Prerequisites

### What You Already Have
- ✅ Atlassian Connect app created with OAuth 2.0
- ✅ Client ID and Client Secret from Atlassian Developer Console
- ✅ ExploraDoc application with existing export functionality

### What You Need to Understand
- **Authentication Types**: Atlassian offers multiple authentication methods
- **Connect Apps vs OAuth Apps**: Different authentication flows
- **Jira Cloud vs Server**: Different API endpoints and capabilities

## Authentication Setup

### API Token Authentication (Our Approach)

For this ExploraDoc integration, we'll use **API Token authentication** because it's:
- **Simple to implement** - No complex OAuth flows
- **Secure** - Token-based authentication with HTTPS
- **Perfect for desktop apps** - Single-user scenarios
- **Quick to set up** - Get started in minutes

### Steps to Get Your API Token

1. **Go to Atlassian Account Settings**
   - Visit: [https://id.atlassian.com/manage-profile/security/api-tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
   - Sign in with your Atlassian account

2. **Create New API Token**
   - Click "Create API token"
   - Label it descriptively (e.g., "ExploraDoc Integration")
   - Copy the generated token immediately (you won't see it again!)
   - Store it securely in your password manager

3. **What You'll Need for Configuration**
   - **Jira URL**: Your Atlassian domain (e.g., `https://yourcompany.atlassian.net`)
   - **Email**: The email address for your Atlassian account
   - **API Token**: The token you just created

### Alternative Authentication Methods (Future Consideration)

While we're using API tokens for this implementation, other methods exist:
- **OAuth 2.0**: For multi-user applications requiring user consent flows
- **Connect App JWT**: For server-to-server communication in Atlassian Connect apps

These can be implemented later if your needs change, but API tokens are perfect for getting started.

## Python Dependencies

### Required Packages

Add the following dependencies to your `requirements.txt` file:

- `atlassian-python-api>=3.41.0` - Main library for Jira API integration
- `requests>=2.31.0` - HTTP requests library (dependency of atlassian-python-api)
- `python-dotenv>=1.0.0` - Environment variable management for secure configuration

### Installation Steps

1. Open terminal in your project directory
2. Ensure your virtual environment is activated
3. Run pip install command to install all required packages
4. Verify installation by importing the main atlassian library

## Configuration Management

### Create Configuration Structure

1. **Create Configuration Directory**
   - Create a new `config` folder in your `explora_doc` directory
   - Add `__init__.py` file to make it a Python package

2. **Jira Configuration File Setup**
   - Create `jira_config.py` in the config directory
   - Import required modules: `os`, `pathlib.Path`, `typing.Optional`, `dotenv.load_dotenv`
   - Create `JiraConfig` class with properties for:
     - Base URL (Jira instance URL)
     - Email address for authentication
     - API token for authentication
   - Add validation method to check if API token configuration is complete
   - Create global configuration instance

3. **Environment File Creation**
   - Create `.env` file in your project root directory
   - Add Jira configuration variables:
     - `JIRA_BASE_URL` - Your Atlassian domain URL
     - `JIRA_EMAIL` - Your email address
     - `JIRA_API_TOKEN` - Your API token
     - `JIRA_DEFAULT_PROJECT` - Optional default project key

4. **Security Configuration**
   - Add `.env` to your `.gitignore` file
   - Never commit sensitive credentials to version control
   - Create `.env.example` template file with placeholder values

## UI Implementation

### Add Export to Jira Button

1. **Update Main Toolbar**
   - Locate the `_create_toolbar` method in `explora_doc/ui.py`
   - Add new "Export to Jira" button after existing buttons
   - Configure button properties:
     - Text: "Export to Jira"
     - Icon: Jira export icon (optional)
     - Command: Link to controller method
     - Initial state: Disabled
     - Size: 120x32 pixels
   - Position button in toolbar using pack layout

2. **Button State Management**
   - Button should be disabled when no screenshots are available
   - Enable button when screenshots are captured
   - Update state when screenshots are added or removed

### Create Jira Export Dialog

1. **Create New Dialog File**
   - Create `explora_doc/jira_integration.py` file
   - Import required modules for UI components and threading

2. **Dialog Class Structure**
   - Create `JiraExportDialog` class
   - Initialize with parent window, screenshots data, and export callback
   - Set up modal dialog window (600x500 pixels)
   - Center dialog on parent window

3. **Dialog Interface Components**
   - **Title section**: "Export Document to Jira Issue"
   - **Status section**: Connection status indicator with colored messages
   - **Project selection**: Dropdown combobox for available projects
   - **Issue selection**: Dropdown combobox for issues in selected project
   - **Comment section**: Multi-line text box for optional comments
   - **Button section**: Cancel and Export buttons

4. **Dialog Functionality**
   - Load Jira data in background thread to prevent UI freezing
   - Populate project dropdown when connection is established
   - Load issues when project is selected
   - Handle export process with progress indication
   - Show success/error messages
   - Close dialog on successful export

5. **State Management**
   - Track selected project and issue
   - Manage loading states for dropdowns
   - Handle enable/disable states for export button
   - Show appropriate status messages

## Backend Integration

### Create Jira Client

1. **Create Jira Client File**
   - Create `explora_doc/jira_client.py` file
   - Import required modules: `logging`, `typing`, `pathlib`, `atlassian.Jira`
   - Import configuration from local config module

2. **JiraClient Class Structure**
   - Initialize Jira client instance in constructor
   - Handle API token authentication
   - Implement error handling and logging throughout

3. **Core Functionality Methods**
   - **Connection Testing**: Verify Jira connectivity and authentication
   - **Project Retrieval**: Get list of projects accessible to user
   - **Issue Retrieval**: Get issues for specific project using JQL queries
   - **Document Export**: Upload document as attachment with optional comment
   - **Issue Details**: Get detailed information about specific issues

4. **Authentication Implementation**
   - Primary method: API token authentication for Jira Cloud
   - Set up Jira client with URL, email, and API token
   - Enable cloud mode for Jira Cloud instances
   - Handle authentication errors gracefully

5. **Error Handling and Logging**
   - Log all major operations and errors
   - Return boolean success indicators
   - Provide meaningful error messages
   - Handle network timeouts and authentication failures

### Update Main Application Controller

1. **Import New Modules**
   - Add imports for `JiraExportDialog` and `JiraClient` in `app.py`

2. **Add Dialog Method**
   - Create `show_jira_export_dialog` method in `ExploraDocApp` class
   - Check if screenshots exist before showing dialog
   - Initialize dialog with screenshots data and export callback

3. **Implement Export Callback**
   - Create `_export_to_jira` method to handle actual export process
   - Generate Word document using existing exporter
   - Create temporary file for upload
   - Call Jira client to upload document and add comment
   - Clean up temporary files after upload
   - Return success/failure status

4. **Button State Management**
   - Add `update_jira_button_state` method
   - Enable/disable Jira button based on screenshot availability
   - Call state update when screenshots are added or removed

5. **UI Integration**
   - Update `refresh_screenshots` method in UI class
   - Call button state update when screenshot list changes
   - Ensure button reflects current application state

## Testing

### Unit Tests

1. **Create Test Structure**
   - Create `tests/test_jira_integration.py` file
   - Set up test class for `JiraClient` functionality
   - Use mock objects to avoid actual Jira API calls during testing

2. **Test Cases to Implement**
   - **Client Initialization**: Test with different configuration scenarios
   - **Connection Testing**: Mock successful and failed connections
   - **Project Retrieval**: Test project list formatting and error handling
   - **Issue Retrieval**: Test JQL query execution and response processing
   - **Document Export**: Test attachment upload and comment addition

3. **Mocking Strategy**
   - Mock Jira configuration for different authentication methods
   - Mock Jira API responses for consistent testing
   - Mock file system operations for document handling

### Manual Testing Steps

1. **Configuration Testing**
   - Run basic connection test script
   - Verify API token authentication works
   - Test with invalid credentials to ensure proper error handling

2. **Project and Issue Retrieval**
   - Test project list retrieval
   - Verify project dropdown population
   - Test issue loading for different projects

3. **End-to-End Integration Test**
   - Launch ExploraDoc application
   - Capture several screenshots with descriptions
   - Click "Export to Jira" button
   - Select project and issue from dropdowns
   - Add comment text
   - Complete export process
   - Verify attachment appears in Jira issue
   - Confirm comment is added to issue

4. **Error Scenario Testing**
   - Test with no network connection
   - Test with invalid Jira credentials
   - Test with insufficient Jira permissions
   - Test with non-existent issues
   - Verify appropriate error messages are displayed

## Implementation Phases

### Phase 1: Basic Implementation (Week 1-2)

**Goal**: Get basic Jira integration working with API token authentication

**Tasks**:
- [ ] Set up Python dependencies and configuration structure
- [ ] Create environment file with API token configuration
- [ ] Implement basic Jira client with connection testing
- [ ] Add "Export to Jira" button to main UI
- [ ] Create simple export dialog with project selection
- [ ] Implement document attachment functionality
- [ ] Test with single Jira instance and project

**Deliverables**:
- Working API token authentication
- Basic project/issue selection interface
- Document attachment to Jira issues
- Success/error feedback to user

**Success Criteria**:
- User can export Word documents to existing Jira issues
- Basic error handling for connection and authentication failures
- UI button enables/disables based on screenshot availability

### Phase 2: Enhanced User Experience (Week 3-4)

**Goal**: Improve user interface and add advanced features

**Tasks**:
- [ ] Enhance export dialog with better UI and status indicators
- [ ] Add issue search and filtering capabilities
- [ ] Implement comment system for exported documents
- [ ] Add progress indicators for long operations
- [ ] Improve error messages and user guidance
- [ ] Add configuration validation and setup wizard
- [ ] Implement proper logging and debug modes

**Deliverables**:
- Polished export dialog with loading states
- Issue search functionality
- Comment attachment with document exports
- Better error handling and user feedback
- Configuration validation

**Success Criteria**:
- Smooth user experience with clear feedback
- Users can search for specific issues
- Comments are properly attached to Jira issues
- Clear error messages guide users to solutions

### Phase 3: Advanced Features (Week 5-6)

**Goal**: Add enhanced integration features and scalability

**Tasks**:
- [ ] Add support for multiple Jira instances
- [ ] Create batch export functionality
- [ ] Add custom field mapping for issues
- [ ] Implement template-based document generation
- [ ] Add integration with Jira workflows
- [ ] Create user preferences and settings
- [ ] Consider OAuth 2.0 for enterprise scenarios

**Deliverables**:
- Multi-instance Jira support
- Batch export capabilities
- Custom field integration
- User preferences system
- Enterprise authentication options

**Success Criteria**:
- Support for multiple Jira instances in same application
- Ability to export multiple documents at once
- Custom fields can be mapped from document data
- OAuth available for enterprise deployments

### Phase 4: Settings UI and Multi-User Support (Week 7-8)

**Goal**: Add user-friendly settings interface and prepare for production

**Tasks**:
- [ ] **Settings Tab Implementation**
  - Add Settings tab to main application window
  - Create settings page with Jira configuration fields
  - Implement secure credential storage (encrypted JSON config)
  - Add "Test Connection" functionality within settings
  - Include input validation and user feedback
- [ ] **Multi-User Configuration Support**
  - Support per-user settings storage
  - Remove dependency on manual `.env` file editing
  - Add settings import/export functionality
  - Implement settings reset to defaults option
- [ ] **Production Readiness**
  - Comprehensive testing and bug fixes
  - Performance optimization for large exports
  - Create deployment packages and installers
  - Write user documentation and help system
  - Implement auto-update mechanism
- [ ] **User Experience Polish**
  - Add first-run setup wizard that guides to Settings tab
  - Create video tutorials and demos
  - Add analytics and usage tracking (optional)
  - Implement user preferences and customization options

**Settings Tab Components**:
- **Jira Configuration Section**:
  - Jira URL input field with validation
  - Email address input field
  - API token input field (masked for security)
  - Test Connection button with status indicators
- **User Interface**:
  - Save Settings button
  - Reset to Defaults button
  - Settings status display (configured/not configured)
  - Link to API token generation guide
- **Advanced Options**:
  - Default project selection
  - Export preferences
  - Debug mode toggle

**Deliverables**:
- Settings tab integrated into main application
- User-friendly Jira configuration interface
- Secure multi-user credential storage
- Production-ready application with installers
- Comprehensive user documentation

**Success Criteria**:
- Users can configure Jira settings without editing files
- Multiple users can use the same application with different credentials
- Settings are stored securely and persist between sessions
- Application runs reliably in production environments
- First-time users can complete setup through guided interface

## Deployment Considerations

### Security Best Practices

1. **Credential Management**
   - Never hardcode API tokens or passwords in source code
   - Use environment variables for all sensitive configuration
   - Implement secure token storage for desktop applications
   - Regularly rotate API tokens and review access permissions

2. **Permission Management**
   - Use least-privilege principle for Jira access
   - Request only necessary permissions for Jira operations
   - Validate user permissions before attempting operations
   - Handle permission-denied scenarios gracefully

3. **Data Protection**
   - Don't log sensitive information (tokens, passwords)
   - Encrypt stored configuration when possible
   - Use HTTPS for all Jira API communications
   - Implement secure temporary file handling

### Configuration for Different Environments

1. **Development Environment**
   - Use development Jira instance when available
   - Create separate API tokens for development
   - Enable debug logging for troubleshooting
   - Use test projects and issues for development

2. **Production Environment**
   - Use production Jira instance
   - Implement proper error logging and monitoring
   - Disable debug features in production builds
   - Configure automatic backup of user settings

3. **Testing Environment**
   - Create isolated test environment
   - Use mock Jira instances for automated testing
   - Implement comprehensive test coverage
   - Test with different Jira versions and configurations

### Distribution Strategy

1. **Application Packaging**
   - Don't include `.env` files in distribution packages
   - Provide `.env.example` template with placeholder values
   - Include setup instructions for Jira configuration
   - Create installer that guides through configuration

2. **User Setup Process**
   - Implement first-run configuration wizard
   - Provide clear instructions for obtaining API tokens
   - Include connection testing in setup process
   - Offer troubleshooting guidance for common issues

3. **Updates and Maintenance**
   - Implement automatic update checking
   - Provide migration scripts for configuration changes
   - Maintain backward compatibility when possible
   - Create rollback procedures for failed updates

### Error Handling and User Experience

1. **Connection Issues**
   - Provide clear error messages for network problems
   - Implement retry mechanisms with exponential backoff
   - Offer offline mode or cached data when possible
   - Guide users through network troubleshooting

2. **Authentication Failures**
   - Clearly explain authentication requirements
   - Provide links to Jira token generation pages
   - Offer step-by-step authentication setup guide
   - Detect and handle expired tokens gracefully

3. **Permission Issues**
   - Explain required Jira permissions clearly
   - Provide guidance for requesting additional permissions
   - Handle read-only access scenarios appropriately
   - Offer alternative workflows for limited permissions

4. **Network and Performance Issues**
   - Handle timeouts and connection errors gracefully
   - Implement progress indicators for long operations
   - Provide cancel options for running operations
   - Optimize for slow network connections

### Monitoring and Support

1. **Logging Strategy**
   - Implement comprehensive application logging
   - Log all Jira API interactions (without sensitive data)
   - Create rotation policy for log files
   - Provide log export functionality for support

2. **Error Reporting**
   - Implement optional crash reporting
   - Allow users to submit error reports easily
   - Include relevant system information in reports
   - Provide privacy controls for error reporting

3. **Performance Monitoring**
   - Track operation completion times
   - Monitor memory usage for large exports
   - Identify bottlenecks in Jira interactions
   - Optimize based on usage patterns

### Troubleshooting Guide

1. **Common Authentication Issues**
   - Invalid API token or expired credentials
   - Incorrect Jira URL configuration
   - Email address doesn't match Jira account
   - Two-factor authentication conflicts

2. **Permission and Access Issues**
   - User doesn't have access to projects
   - Insufficient permissions for creating attachments
   - Project or issue doesn't exist or is archived
   - Organization-level access restrictions

3. **Network and Connectivity Issues**
   - Firewall blocking Jira API requests
   - Proxy configuration problems
   - DNS resolution issues for Jira domain
   - SSL certificate validation problems

4. **Application-Specific Issues**
   - Document generation failures
   - Temporary file access problems
   - UI responsiveness during large operations
   - Memory issues with large screenshot sets

### Debug Mode and Diagnostics

1. **Debug Mode Activation**
   - Environment variable to enable debug mode
   - Command-line flag for verbose logging
   - UI option in settings for debug features
   - Automatic debug mode for development builds

2. **Diagnostic Information**
   - System information collection
   - Jira connectivity testing tools
   - Configuration validation utilities
   - Performance profiling options

3. **Support Tools**
   - Configuration export/import functionality
   - Log file viewer within application
   - Connection testing wizard
   - Reset to default settings option

## Resources and Documentation

### Official Documentation Links
- [Atlassian Python API Documentation](https://atlassian-python-api.readthedocs.io/)
- [Jira Cloud REST API Reference](https://developer.atlassian.com/cloud/jira/platform/rest/v3/)
- [Atlassian Connect Documentation](https://developer.atlassian.com/cloud/jira/platform/getting-started-with-connect/)
- [OAuth 2.0 for Atlassian Cloud](https://developer.atlassian.com/cloud/jira/platform/oauth-2-3lo-apps/)

### Community Resources
- [Atlassian Developer Community](https://community.developer.atlassian.com/)
- [Stack Overflow Atlassian Tags](https://stackoverflow.com/questions/tagged/atlassian)
- [GitHub Atlassian Python API Issues](https://github.com/atlassian-api/atlassian-python-api/issues)

### Development Tools
- [Postman Collection for Jira API](https://developer.atlassian.com/cloud/jira/platform/postman/)
- [Jira API Explorer](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/)
- [Atlassian CLI Tools](https://developer.atlassian.com/cloud/admin/cli/)

---

This guide provides a comprehensive foundation for implementing Jira integration in your ExploraDoc application. Start with Phase 1 using the API token approach for simplicity, then evolve through the phases as your requirements grow and your implementation matures.
