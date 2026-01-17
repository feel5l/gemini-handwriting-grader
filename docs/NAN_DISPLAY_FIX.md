# Fix for "nan" Display in HTML for Empty Student Answers

## Problem
When student answers are empty (no text extracted from OCR), the HTML displays "nan" instead of an empty string. This occurs in:
- The Answer column in the data table (`<td>nan</td>`)
- The alt attribute of answer images (`alt="nan"`)
- The value attribute in input fields (for metadata questions)

## Root Cause
When pandas DataFrames contain None or NaN values and are rendered through Jinja2 templates, they display as the string "nan" instead of empty strings.

## Solution Applied

### 1. Template Fixes (Jinja2 Filters)

**File: `templates/questions/index.html`**
- Changed `{{row["Answer"]}}` to `{{row["Answer"] if row["Answer"] is not none and row["Answer"] == row["Answer"] else ''}}`
- Applied to both `<td>` content and `alt` attribute
- The condition `row["Answer"] == row["Answer"]` checks for NaN (NaN != NaN in Python)

**File: `templates/questions/index-answer.html`**
- Changed input value from `{{row["Answer"]}}` to `{{row["Answer"] if row["Answer"] is not none and row["Answer"] == row["Answer"] else ''}}`
- Ensures empty string instead of "nan" for metadata questions (NAME, ID, CLASS)

### 2. Data Processing Fixes (Pandas)

**File: `notebbooks/step4_scoring_preprocessing.ipynb`**

Added `fillna("")` after assigning Answer column in two places:

**For metadata questions (NAME, ID, CLASS):**
```python
data["Answer"] = answers
# Replace NaN/None with empty string to avoid "nan" display in HTML
data["Answer"] = data["Answer"].fillna("")
```

**For graded questions (Q1, Q2, etc.):**
```python
data["Answer"] = answers
# Replace NaN/None with empty string to avoid "nan" display in HTML
data["Answer"] = data["Answer"].fillna("")
```

## How to Apply the Fix

### For New Processing
1. The notebook changes are already in place
2. Run the preprocessing notebook (step4_scoring_preprocessing.ipynb)
3. The generated HTML files will automatically use empty strings instead of "nan"

### For Existing Generated Files
You need to regenerate the HTML files by re-running the preprocessing notebook:
1. Open `notebbooks/step4_scoring_preprocessing.ipynb`
2. Run all cells to regenerate the marking forms
3. The HTML files in `marking_form/VTC Test/questions/` will be updated

## Files Modified
1. `templates/questions/index.html` - Main question template
2. `templates/questions/index-answer.html` - Metadata question template  
3. `notebbooks/step4_scoring_preprocessing.ipynb` - Data processing notebook

## Verification
After regenerating, check that:
- Empty answers show as blank cells, not "nan"
- Image alt attributes are empty strings for missing answers
- Input fields have empty values, not "nan"

## Example
**Before:**
```html
<td>nan</td>
<img alt="nan" />
<input value="nan" />
```

**After:**
```html
<td></td>
<img alt="" />
<input value="" />
```
