# Data Directory

This directory contains the input files required for the AI grading system.

## Required Files

Before running the grading workflow, prepare the following files in this directory:

### 1. Scanned Student Scripts (PDF)
**File**: `<exam_prefix>.pdf`  
**Example**: `VTC Test.pdf`

- Single PDF containing all scanned handwritten answer sheets
- Each student's complete answer sheet should be included
- Supports various PDF formats

### 2. Student Name List (Excel)
**File**: `<exam_prefix> Name List.xlsx`  
**Example**: `VTC Test Name List.xlsx`

- Excel file with student information
- **Required columns**: `ID`, `NAME`, `CLASS`
- See `sample/VTC Test Name List.xlsx` for template

### 3. Answer Sheet Template (Word)
**File**: `<exam_prefix> Answer Sheet.docx`  
**Example**: `VTC Test Answer Sheet.docx`

- Word template for generating individual answer sheets
- Must include placeholders: `Name:`, `Student ID:`, `Class:`
- See `sample/VTC Test Answer Sheet.docx` for template

### 4. Marking Scheme (Word)
**File**: `<exam_prefix> Marking Scheme.docx`  
**Example**: `VTC Test Marking Scheme.docx`

- Word document with questions, answers, and marking rubric
- Will be parsed by AI to extract marking criteria
- See `sample/VTC Test Marking Scheme.docx` for template

## Important Notes

- **File naming**: All files must use the same `<exam_prefix>` (e.g., "VTC Test")
- **Templates**: Copy templates from `sample/` directory and customize
- **Excel format**: Name list must have exact column names: `ID`, `NAME`, `CLASS`

## Setup Instructions

1. Copy template files from `sample/` directory:
   ```bash
   cp sample/VTC\ Test\ Name\ List.xlsx data/
   cp sample/VTC\ Test\ Answer\ Sheet.docx data/
   cp sample/VTC\ Test\ Marking\ Scheme.docx data/
   ```

2. Customize the files with your exam details

3. Add your scanned PDF: `data/<exam_prefix>.pdf`

4. Run the grading workflow starting from Step 1

## See Also

- Main README: `../README.md`
- Configuration Guide: `../docs/CONFIGURATION.md`
- Sample files: `../sample/`