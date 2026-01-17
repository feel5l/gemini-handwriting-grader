# How to Regenerate Marking Forms to Fix "nan" Display

## Quick Steps

1. **Activate the virtual environment:**
   ```bash
   source .venv/bin/activate
   ```

2. **Open the preprocessing notebook:**
   ```bash
   jupyter notebook notebbooks/step4_scoring_preprocessing.ipynb
   ```
   Or use your IDE's notebook interface.

3. **Run all cells in the notebook:**
   - This will regenerate all HTML files in `marking_form/VTC Test/questions/`
   - The new files will use empty strings instead of "nan" for missing answers

4. **Verify the fix:**
   - Start the web server:
     ```bash
     file_name="VTC Test" python server.py 8000
     ```
   - Open your browser and check questions with empty answers
   - Confirm that empty cells show blank instead of "nan"

## What Gets Fixed

The regeneration will update all HTML files to:
- Display empty cells for missing answers (not "nan")
- Use empty alt attributes for images with no answer text
- Show empty input values for metadata fields with no data

## Files That Will Be Updated

All files in these directories will be regenerated:
- `marking_form/VTC Test/questions/NAME/index.html`
- `marking_form/VTC Test/questions/ID/index.html`
- `marking_form/VTC Test/questions/CLASS/index.html`
- `marking_form/VTC Test/questions/Q1/index.html`
- `marking_form/VTC Test/questions/Q2/index.html`
- `marking_form/VTC Test/questions/Q3/index.html`
- `marking_form/VTC Test/questions/Q4/index.html`
- `marking_form/VTC Test/questions/Q5/index.html`

Plus corresponding `question.js`, `style.css`, and `data.csv` files.

## Note

The fix is already implemented in the templates and notebook code. You just need to run the notebook to regenerate the HTML files with the corrected output.
