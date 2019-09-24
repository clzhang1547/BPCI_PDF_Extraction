# BPCI PDF Extraction Tool
This is the code to extract responses from PDF questionnaires sent to BPCI participants.

### extract_pdf_fields.py
code to parse responses

### get_risk_profile.py
code to produce risk_profile.json - manual steps needed, see code

### GUI.py
code of GUI

### info.json
JSON mapping PDF item (ComboBox1, etc.) to num(int), text(question), id(decimal id), local(local int id within questionnaire group), and group (group description).

### risk_profile.json
JSON mapping id(decimal id) to response of question(clean string), Response Weights, Risk Level, and risk_score

## To Do
* Update code per request from health if any issues when processing PDFs