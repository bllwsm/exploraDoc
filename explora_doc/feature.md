# Next Changes Implementation Plan

## Overview
This document outlines the implementation plan for the next set of features to enhance ExploraDoc with QA/Exploratory testing modes and a comprehensive testing charter section.

## New Features to Implement

### 1. Test Type Dropdown (Before Title)
**Location**: `ui.py` - `_create_test_title_section()` method
**Implementation**:
- Add a small dropdown before the title input field
- Options: "QA" and "Exploratory"
- Default value: none
- Store selection in a new StringVar (e.g., `test_type_var`)
- Update the placeholder text dynamically based on selection
- **UI Layout**: `[Test Type Dropdown] [Document Title: *] [Title Entry]`

### 2. Remove Branch Dropdown
**Location**: `ui.py` - `ScreenshotEntryUI._create_fields()` method
**Implementation**:
- Remove the existing branch dropdown (lines ~385-393)
- Remove the "Branch:" label
- Update the `ScreenshotMeta` model to remove branch field
- Update export functionality to not include branch information

### 3. Testing Charter Section with Separate Controls
**Location**: New section in `ui.py` and `models.py`
**Implementation**:
- **Separate Controls**:
  - **Dropdown Button**: Controls UI visibility (expand/collapse fields)
  - **Export Toggle**: Controls whether charter is included in exported Word document
- **UI Layout**: `[▼ Testing Charter] [Include in Export Toggle]`
- **Behavior**:
  - Dropdown expanded: Shows all charter fields for editing
  - Dropdown collapsed: Hides charter fields but preserves data
  - Export toggle ON: Charter included in Word document export
  - Export toggle OFF: Charter completely excluded from Word document export
- **Position**: Before the "Test Evidence" (screenshots) section
- **Fields**:
  - Required fields marked with (*) : Objective, What's going to be checked
  - Optional fields: Prerequisites, Exclusions, Defects, Peer Review
  - Support bullet points for "What's going to be checked"
  - Single line for peer review

## Implementation Order

1. **Phase 1**: Test Type Dropdown
   - Add test type selection before title
   - Update placeholder text logic
   - Pass test type to export function

2. **Phase 2**: Remove Branch Dropdown
   - Remove branch UI elements
   - Update data models
   - Remove branch from export

3. **Phase 3**: Testing Charter Section with Separate Controls
   - Create TestingCharter data model
   - Implement separate dropdown and export toggle controls
   - Add field validation for required fields when export toggle is ON
   - Integrate with export functionality (only when export toggle is ON)

## Validation Requirements

- **Objective** and **What's going to be checked** are required when export toggle is ON
- Show validation errors with red styling for empty required fields
- Disable export if required charter fields are empty when export toggle is ON
- Update button states based on validation status
- Validation runs regardless of UI visibility state (dropdown can be collapsed but validation still applies if export toggle is ON)

## UI/UX Considerations

- Use consistent spacing and styling with existing UI
- Clear visual distinction between dropdown (UI visibility) and toggle (export inclusion)
- Provide clear visual feedback for required fields
- Ensure responsive layout that works with different window sizes
- Dropdown button shows arrow indicator (▼/▶) for expand/collapse state

## Testing Scenarios

1. **UI Visibility Control**:
   - Expand dropdown: fields visible and editable
   - Collapse dropdown: fields hidden but data preserved
   - Export toggle state doesn't affect UI visibility

2. **Export Inclusion Control**:
   - Export toggle ON + fields filled: charter included in export
   - Export toggle OFF: charter excluded from export regardless of field content
   - Export toggle ON + required fields empty: validation error prevents export

3. **Combined Scenarios**:
   - Dropdown collapsed + export toggle ON: hidden fields still validated and exported
   - Dropdown expanded + export toggle OFF: visible fields not exported
   - Test both QA and Exploratory modes with charter enabled/disabled

4. **Word Document Output**:
   - Verify export format matches requirements
   - Charter appears before evidence section when included
   - Test type header included in all exports
