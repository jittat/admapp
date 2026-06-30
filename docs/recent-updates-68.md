# Recent Updates Summary

## Overview
This document summarizes all changes made from commit `85872b6086befcecd1d4bbed35c864c3ba9b142a` to the current HEAD (`f1b7673`).

**Statistics:** 106 commits, 120 files changed, 3,203 insertions, 448 deletions

---

## Major Feature Additions

### 1. Interview Management System
- **Interview Date Management**: Added custom interview dates for projects and faculties
- **Faculty-Specific Interview Dates**: New model `AdmissionProjectFacultyInterviewDate` for managing interview schedules
- **Interview Status Tracking**: Enhanced UI to show interview status and dates
- **Interview Call Import**: Multiple scripts for importing interview calls with support for multiple calls per applicant
- **Interview Description Templates**: Enhanced templates showing result and confirmation dates

**Key Files:**
- `criteria/models/admission_criteria.py` - Added interview date fields
- `criteria/templates/criteria/include/faculty_interview_date_form.html` - New form for setting interview dates
- `backoffice/templates/backoffice/projects/list_major_interview_status.html` - Interview status display
- `scripts/import_interview_calls.py` - Interview call import functionality

### 2. Multi-Major Criteria System
- **Basic Criteria Validation**: Implemented criteria checking for applicants applying to multiple majors
- **Multi-Major Support**: Added fields and logic to handle multiple major applications
- **Criteria Results Display**: Enhanced applicant lists to show basic criteria results
- **Staff-Only Editing**: Added permission controls for criteria editing

**Key Files:**
- `appl/migrations/0087_admissionprojectround_multimajor_criteria_check_required.py`
- `backoffice/templates/backoffice/projects/include/multimajor_criteria_buttons.html`
- `backoffice/models.py` - Added criteria check permissions

### 3. T-Score Integration
- **T-Score Calculation**: Integrated T-Score as a criteria for evaluation
- **Score Display**: Added T-Score columns in Excel reports and UI tables
- **Score Headers**: Enhanced score table headers for various exam types

**Key Files:**
- `backoffice/templates/backoffice/projects/include/score_table/` - Score table enhancements
- `criteria/criteria_options.py` - T-Score criteria options

### 4. CUPT Export Configuration System
- **Export Models**: New models for configuring CUPT exports
- **Custom Project Rules**: `CuptExportCustomProject` and `CuptExportAdditionalProjectRule`
- **Program Major Codes**: Support for multiple program major codes per export rule
- **Admin Interface**: Enhanced admin interface for export configuration

**Key Files:**
- `criteria/models/cupt_export_config.py` - New export configuration models
- `criteria/views/cuptexport_fields.py` - Export field management
- `criteria/views/export-config-67.json` - Configuration file

---

## Import/Export Enhancements

### Data Export Scripts
- **Applicant Export**: Multiple scripts for exporting applicant data with various filters
- **Major Data Export**: Scripts for exporting major information and criteria
- **Project Export**: Enhanced project data export with interview information
- **Criteria Export**: JSON export for criteria data

### Data Import Scripts
- **Round 1/2 Support**: Separate import workflows for different admission rounds
- **Interview Calls**: Enhanced import for interview scheduling
- **Project Details**: Improved project detail imports with subround support
- **TCAS Integration**: Updated TCAS applicant import scripts

**Key Scripts:**
- `scripts/export_paid_applicants_w_info_criteria.py` - Comprehensive applicant export
- `scripts/import_interview_calls_create.py` - Interview call creation
- `scripts/import_apapps68.py` - AP application import
- `scripts/export_major_slots.py` - Major slot export

---

## UI/UX Improvements

### Enhanced Project Listings
- **Better Sorting**: Improved sorting by major code and project rankings
- **Display Options**: Enhanced project display with titles and codes
- **Status Indicators**: Visual indicators for application and interview status
- **Confirmation Information**: Shows confirmed slots and cancellation data

### Applicant Management
- **Score Display**: Enhanced score tables with T-Score integration
- **Status Tracking**: Better tracking of applicant progress through the system
- **Cultural Program Support**: Special handling for cultural program applicants
- **Medical Program Enhancements**: Flexible document requirements for medical programs

### Administrative Interface
- **Backoffice Enhancements**: Improved project management interface
- **Message Display**: Added messaging system for project and applicant pages
- **Print Templates**: Updated print templates for various application types
- **Permission Controls**: Enhanced permission system for different user roles

**Key Templates:**
- `backoffice/templates/backoffice/projects/list_applicants_by_majors.html`
- `appl/templates/appl/include/project_accepted_result_acceptance_posthook.html`
- `supplements/templates/supplements/cultural/applicant_info.html`

---

## Data Model Enhancements

### Core Models
- **Admission Projects**: Added display rank, custom interview dates
- **Admission Rounds**: Added acceptance result dates and confirmation dates
- **Project Rounds**: Multi-major criteria requirements, staff-only editing flags
- **Applicants**: Enhanced with acceptance tracking and criteria results

### New Models
- **Export Configuration**: Models for CUPT export customization
- **Interview Management**: Faculty-specific interview date models
- **Profile Extensions**: Additional permissions for criteria checking

**Key Migrations:**
- `appl/migrations/0084_admissionproject_custom_interview_end_date_and_more.py`
- `appl/migrations/0086_admissionround_acceptance_result_date_and_more.py`
- `criteria/migrations/0029_cuptexportcustomproject_and_more.py`

---

## Security and Administrative Features

### Permission System
- **Criteria Editing**: Staff-only permissions for criteria modifications
- **Basic Criteria Checks**: Additional permissions for criteria validation
- **User Generation**: Enhanced backoffice user generation scripts

### System Improvements
- **Password Recovery**: Added spam warnings for forgotten password attempts
- **Document Requirements**: Flexible document upload requirements
- **Hardcoded Constants**: Removed hardcoded values for better maintainability

### Configuration Management
- **Environment Files**: Updated .gitignore and environment configurations
- **Fixture Updates**: Updated campus and faculty fixture data
- **Script Permissions**: Updated permissions for various utility scripts

---

## Recent Bug Fixes and Improvements

### Latest Updates (Most Recent)
- **f1b7673**: Updated more messages
- **dae5fa2**: Updated doc and survey links  
- **9200448**: Fixed score header error
- **7a94597**: Updated tcas3 import script
- **26ad5d0**: Imports majors with dup

### Performance and Display
- **Score Display**: Fixed various score display issues
- **Project Listings**: Improved project sorting and display
- **Import Scripts**: Enhanced error handling and duplicate management
- **Template Rendering**: Fixed template rendering issues

### User Experience
- **Message Updates**: Improved user-facing messages throughout the system
- **Link Updates**: Updated documentation and survey links
- **Form Enhancements**: Better form handling and validation
- **Print Functionality**: Enhanced print templates for applications

---

## Technical Debt and Maintenance

### Code Quality Improvements
- Removed hardcoded constants and magic numbers
- Enhanced error handling in import/export scripts
- Improved template organization and consistency
- Better separation of concerns in view functions

### Documentation and Configuration
- Updated fixture data for current academic requirements
- Enhanced script documentation and usage examples
- Improved configuration management for different environments
- Better error messages and user guidance

---

## Impact Assessment

### High Impact Changes
1. **Multi-Major Support**: Fundamental change affecting how applications are processed
2. **T-Score Integration**: New scoring methodology implementation
3. **Interview Management**: Complete overhaul of interview scheduling system
4. **Export Configuration**: Flexible export system for external integrations

### Medium Impact Changes
1. **UI Enhancements**: Improved user experience across the application
2. **Import/Export Scripts**: Enhanced data management capabilities
3. **Permission System**: Better access control and security

### Low Impact Changes
1. **Message Updates**: Improved user communication
2. **Bug Fixes**: Various small fixes and improvements
3. **Template Updates**: Visual and functional improvements

---

*This summary covers 106 commits spanning major feature additions, system enhancements, and maintenance improvements to the admission application management system.*