# Jira Integration MVP User Journey for ExploraDoc

This guide describes the MVP (Minimum Viable Product) flow for attaching an exported Word document to a Jira ticket using API token authentication.

---

## MVP User Flow

1. **User clicks "Export"**  
   - The document is exported as usual.

2. **On the Success Modal:**  
   - Add a new button: **"Attach to Jira Ticket"**

3. **If user clicks "Attach to Jira Ticket":**  
   - Open a new window/dialog.

4. **Jira Attachment Window:**
   - **Dropdown:** Show 3 Jira boards (either hardcoded or fetched via API).
   - **Board Selection:** User selects their board.
   - **Ticket Selection:**  
     - Show a dropdown/list of tickets from the active sprint on that board.
     - User selects their ticket.
   - **Attach:**  
     - User clicks "Attach" to upload the exported document to the selected Jira ticket as an attachment.

---

## Implementation Steps

### 1. UI Changes

- **Success Modal:**  
  - Add a button: `Attach to Jira Ticket`
- **Jira Attachment Dialog:**  
  - Dropdown for board selection (3 boards)
  - Dropdown for ticket selection (tickets from active sprint)
  - Attach button

### 2. Backend Integration

- **API Token Authentication Only**
- **Fetch Boards:**  
  - Use Jira API to list boards (limit to 3 for MVP)
- **Fetch Active Sprint Tickets:**  
  - For selected board, fetch active sprint and its issues
- **Attach Document:**  
  - Upload the exported Word document as an attachment to the selected ticket

### 3. User Journey Example

1. User exports a document.
2. Success modal appears with "Attach to Jira Ticket" button.
3. User clicks the button.
4. New window opens:
   - User selects their board from dropdown.
   - User selects a ticket from the active sprint.
   - User clicks "Attach".
5. Document is attached to the selected Jira ticket.
6. Show confirmation or error message.

---

## Authentication Setup

### API Token Authentication (Our Approach)

For this ExploraDoc integration, we'll use **API Token authentication** because it's:
- **Simple to implement** - No complex OAuth flows
- **Secure** - Token-based authentication with HTTPS
- **Perfect for desktop apps** - Single-user scenarios
- **Quick to set up** - Get started in minutes

#### Steps to Get Your API Token

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

---

## Python Dependencies

Add the following dependencies to your `requirements.txt` file:

- `atlassian-python-api>=3.41.0`
- `requests>=2.31.0`
- `python-dotenv>=1.0.0`

---

## Configuration Management

- Use a `.env` file for Jira configuration variables:
  - `JIRA_BASE_URL`
  - `JIRA_EMAIL`
  - `JIRA_API_TOKEN`
- Add `.env` to `.gitignore`
- Never commit sensitive credentials

---

## Resources

- [Atlassian Python API Documentation](https://atlassian-python-api.readthedocs.io/)
- [Jira Cloud REST API Reference](https://developer.atlassian.com/cloud/jira/platform/rest/v3/)

---

This MVP guide focuses only on the API token approach and the streamlined user journey for attaching exported documents to Jira