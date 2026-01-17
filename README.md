# Gemini-Handwriting-Grader

![@logo.png](images/logo.png)

An AI-powered, comprehensive handwriting grading system that transforms the traditional, time-consuming grading process into an efficient, automated workflow. This system provides educators with professional-grade tools for fair, consistent, and insightful assessment of handwritten student work.

## 🎯 Why This System?

Traditional grading is physically exhausting and inefficient:
- **Manual paper flipping** through hundreds of scripts
- **Repetitive marking** of the same questions across students
- **Inconsistent grading** due to fatigue and memory limitations
- **Time-consuming calculations** and data entry
- **Physical strain** leading to back and neck pain
- **Limited insights** into class performance patterns

## 🚀 Solution

This system leverages Google's Gemini AI to provide:

### **🤖 AI-Powered Intelligence**
- **Advanced OCR** for accurate handwriting recognition
- **Intelligent Grading** with contextual understanding
- **Performance Analytics** with actionable insights
- **Automated Report Generation** with professional formatting

### **📊 Comprehensive Analytics**
- **Individual Performance Reports** with AI-generated feedback
- **Class-Level Analytics** with strengths and focus areas
- **Visual Charts** for data-driven decision making
- **Question-Level Analysis** for curriculum improvement

### **🛡️ Production-Ready Reliability**
- **Robust Error Handling** with graceful degradation
- **Modern Libraries** (pypdf 6.5.0, updated dependencies)
- **Intelligent Caching** for efficient API usage
- **Comprehensive Validation** at every processing step

### **📄 Professional Output**
- **Multi-Format Reports** (Excel, Word, PowerPoint, PDF)
- **Embedded Visualizations** in professional documents
- **Stratified Samples** for moderation and review
- **Email Distribution** with personalized insights

This system is completely **offline-capable** and can be used by all educators through GitHub Codespaces or local installation.

## 🔄 Workflow

This system automates the entire grading process using Jupyter notebooks that leverage Google's Gemini AI with comprehensive error handling and professional output generation:

1. **📋 Generate Answer Sheets**: Creates personalized answer sheets with robust PDF processing
2. **📖 Extract Marking Scheme**: AI-powered parsing of marking schemes with validation
3. **🎯 Define Answer Regions**: Intelligent bounding box detection with interactive refinement
4. **🤖 AI-Powered Scoring**: Advanced OCR and grading with caching and error recovery
5. **✅ Review and Validation**: Web interface with comprehensive checks
6. **📊 Generate Reports (Modular)**:
    - **Step 6.1 Basic**: Scoring, PDFs, sampling, and archiving
    - **Step 6.2 Advanced**: AI analytics, Word/PPTX reports
7. **📧 Email Distribution**: Personalized emails with performance analytics and attachments

### 🆕 Features

#### **Step 2 Features**
- **Multi-Sheet Excel Output**: Professional 4-sheet workbook with comprehensive analysis
- **Advanced AI Processing**: Gemini integration with structured validation
- **Multi-Agent Verification**: Sequential agents for grounding and formatting
- **Google Search Grounding**: Live fact-checking of marking schemes against real-world data
- **Comprehensive Error Handling**: Retry logic, fallback processing, and graceful degradation
- **Professional Formatting**: Stakeholder-ready reports with detailed validation

#### **Step 4 & 5 Features**
- **Comprehensive Error Handling**: Robust processing with graceful degradation
- **Intelligent Caching**: Efficient API usage with organized cache structure
- **Metadata Validation**: Metadata question handling (NAME/ID/CLASS exclusion)
- **Progress Tracking**: Visual indicators and detailed logging

#### **Step 6 Features (Modular)**
- **Notebook Splitting**: Separated into `step6_1` (Basic) and `step6_2` (AI) for flexibility.
- **PowerPoint Reports**: Automated 16:9 presentations with centered infographics and speaker notes.
- **AI-Powered Analytics**: Individual and class-level performance insights.
- **Professional Word Reports**: Embedded charts and comprehensive analysis.
- **Visual Analytics**: Question performance charts and score distributions.
- **Multi-Sheet Excel Reports**: Detailed data with audit trails.
- **PDF Generation**: Modern libraries with comprehensive validation.

#### **System-Wide Improvements**
- **Modern Libraries**: Updated to pypdf 6.5.0, removed deprecated dependencies
- **Metadata Intelligence**: Proper handling of student information fields
- **Production Reliability**: Comprehensive error handling and validation
- **Professional Output**: Stakeholder-ready reports and documentation

## 📁 Setup and Input Files

Before running the notebooks, prepare the following files. Copy examples from `sample/` directory, customize them, and place them in `data/` directory.

Let `<exam_prefix>` be your exam name (e.g., `VTC Test`).

### Required Input Files

#### 1. 📄 Scanned Student Scripts
- **File**: `data/<exam_prefix>.pdf`
- **Description**: Single PDF containing all scanned handwritten answer sheets
- **Format Support**: Supports various PDF formats with robust processing

#### 2. 👥 Student Roster  
- **File**: `data/<exam_prefix> Name List.xlsx`
- **Description**: Excel file with student information
- **Required Columns**: `ID`, `NAME`, `CLASS`
- **Template**: `sample/VTC Test Name List.xlsx`
- **Validation**: Improved validation and error handling

#### 3. 📝 Answer Sheet Template
- **File**: `data/<exam_prefix> Answer Sheet.docx`
- **Description**: Word template for generating individual answer sheets
- **Placeholders**: `Name:`, `Student ID:`, `Class:`
- **Template**: `sample/VTC Test Answer Sheet.docx`
- **Processing**: Robust formatting with error recovery

#### 4. 📋 Marking Scheme
- **File**: `data/<exam_prefix> Marking Scheme.docx`
- **Description**: Word document with questions, answers, and rubric
- **Template**: `sample/VTC Test Marking Scheme.docx`
- **Processing**: Advanced AI parsing with validation

#### 5. 📧 Email Configuration
- **File**: `smtp.config` (project root)
- **Description**: SMTP credentials for email distribution
- **Template**: `smtp-template.config` → rename and configure
- **Reliability**: Robust error handling and validation

## 📚 Workflow: Step-by-Step Guide

Run the Jupyter notebooks in `notebbooks/` directory in order. Each notebook includes comprehensive error handling, progress tracking, and validation.

### Step 1: Generate Answer Sheets
**Notebook**: `step1_generate_answer_sheet.ipynb`

- **Purpose**: Creates personalized answer sheets for printing
- **Features**: 
  - Robust PDF processing with error recovery
  - Progress tracking and validation
  - Professional formatting and layout
- **Inputs**: Name list, answer sheet template
- **Output**: `data/<exam_prefix> Answer Sheets Combined.pdf`

### Step 2: Extract Marking Scheme  
**Notebook**: `step2_generate_marking_scheme_excel.ipynb`

- **Purpose**: AI-powered parsing of marking scheme into structured Excel
- **Features**:
  - ✅ **Advanced Gemini Integration**: Structured output with Pydantic validation
  - ✅ **Comprehensive Error Handling**: Retry logic and fallback processing
  - ✅ **Multi-Sheet Excel Output**: 4 professional sheets (Marking Scheme, Summary, Question Overview, Validation)
  - ✅ **Validation**: Question completeness and data integrity checks
  - ✅ **Backup Protection**: Automatic backup of existing files
  - ✅ **Professional Formatting**: Stakeholder-ready Excel reports
- **Input**: `data/<exam_prefix> Marking Scheme.docx`
- **Output**: `data/<exam_prefix> Marking Scheme.xlsx`

### Step 3: Define Answer Regions
**Notebook**: `step3_question_annotations.ipynb`

- **Purpose**: Intelligent detection and refinement of answer regions
- **Features**:
  - AI-powered bounding box detection
  - Interactive refinement tools
  - Comprehensive validation
- **Input**: Scanned PDF scripts
- **Outputs**: 
  - `marking_form/<exam_prefix>/images/`: Page images
  - `marking_form/<exam_prefix>/annotations/annotations.json`: Bounding boxes

### Step 4: AI-Powered Scoring & Preprocessing
**Notebook**: `step4_scoring_preprocessing.ipynb`

- **Purpose**: OCR, AI grading, and web interface generation
- **Features**:
  - ✅ **Intelligent Caching**: Organized cache structure for efficiency
  - ✅ **Error Recovery**: Robust handling of API failures
  - ✅ **Progress Tracking**: Visual indicators and detailed logging
  - ✅ **Metadata Handling**: Proper exclusion of NAME/ID/CLASS fields
- **Inputs**: Images, annotations, marking scheme
- **Outputs**: 
  - Web interface at `marking_form/<exam_prefix>/`
  - Cached API responses in `cache/`
  - Question data and marks in `mark.json` files

### Step 5: Post-Scoring Validation & Checks
**Notebook**: `step5_post_scoring_checks.ipynb`

- **Purpose**: Comprehensive validation before final processing
- **Features**:
  - ✅ **Validation**: Metadata question exclusion
  - ✅ **Comprehensive Checks**: All scoring completeness verification
  - ✅ **Error Reporting**: Clear identification of issues
  - ✅ **Data Integrity**: ID validation against name lists
- **Process**: Verifies all questions scored, validates student IDs, cleans temporary files

### Step 6: Report Generation & Analysis (Modular)

**Notebook 6.1**: `step6_1_basic_reporting.ipynb`
- **Purpose**: Core scoring outputs and archiving.
- **Features**:
  - Score calculation and marks sheet generation
  - Scored script PDF creation
  - Stratified sampling
  - Backup creation

**Notebook 6.2**: `step6_2_ai_analysis.ipynb`
- **Purpose**: Advanced AI analytics and presentation.
- **Features**:
  - AI Performance Reports
  - Class & Question Analytics
  - Word Report with embedded charts
  - PowerPoint Presentation (16:9, centered, speaker notes)

### Step 7: Email Distribution
**Notebook**: `step7_email_score.ipynb`

- **Purpose**: Personalized email distribution with performance insights
- **Features**:
  - Professional email templates with AI insights
  - Robust SMTP handling with error recovery
  - Progress tracking and validation
- **Inputs**: SMTP config, reports, individual PDFs
- **Output**: Personalized emails with scores and marked scripts

## 📊 Output & Reports

All outputs are generated in `marking_form/<exam_prefix>/` with professional formatting and comprehensive analytics.

### 🆕 Excel Reports

#### **Comprehensive Multi-Sheet Workbook**
**File**: `marking_form/<exam_prefix>/marked/scripts/details_score_report.xlsx`

- **📋 Marks Sheet**: Final scores with student information
- **📝 Answers Sheet**: Captured student responses (wide format)
- **🤖 Reasoning Sheet**: AI analysis and similarity scores  
- **📊 Performance Sheet**: Individual AI-generated performance reports
- **📈 ClassOverview Sheet**: Statistical analysis with AI insights
- **📉 QuestionMetrics Sheet**: Per-question performance analysis
- **🔍 Raw Data Sheets**: Complete audit trail for transparency

#### **Summary Report**
**File**: `marking_form/<exam_prefix>/marked/scripts/score_report.xlsx`
- Concise marks-only sheet with ID, Name, Class, Total Marks

### 🆕 Word Documents

#### **Class Performance Report**
**File**: `marking_form/<exam_prefix>/marked/scripts/class_overview_report.docx`

- **📊 Embedded Charts**: Score distributions, question analysis, pass rates
- **🤖 AI-Generated Insights**: Class strengths, weaknesses, recommendations
- **📈 Visual Analytics**: Professional charts and graphs
- **📋 Data Tables**: Performance metrics and question analysis
- **🎯 Actionable Recommendations**: Specific next steps for instruction

### 🆕 PowerPoint Presentation

#### **Class Overview Presentation**
**File**: `marking_form/<exam_prefix>/marked/scripts/class_overview_presentation.pptx`

- **16:9 Format**: Professional widescreen layout (13.33" x 7.5").
- **Centered Infographics**: Visual summaries centered vertically and horizontally.
- **Deep Dive Slides**: Per-question insights with infographics.
- **Speaker Notes**: Detailed AI analysis (hurdles, keys, tips) embedded in notes.

### 📄 PDF Outputs

#### **Individual Student Scripts**
- **📁 Individual PDFs**: `marking_form/<exam_prefix>/marked/pdfs/<ID>.pdf`
  - Annotated scripts with marks and total scores
  - Professional formatting with clear mark indicators

#### **Combined & Sample Collections**
- **📚 Complete Collection**: `marking_form/<exam_prefix>/marked/scripts/all.pdf`
- **🎯 Stratified Samples**: `marking_form/<exam_prefix>/marked/scripts/sampleOf*.pdf`
  - Good, average, and weak performance samples
  - Passing-only samples (when sufficient data available)
  - Template pages separating categories

### 📊 Visual Analytics

#### **Performance Charts**
**Directory**: `marking_form/<exam_prefix>/marked/scripts/charts/`

- **📈 Score Distribution Histograms**: Class performance spread
- **📊 Question Performance Charts**: Mean scores with error bars
- **📉 Box Plots**: Score distributions per question
- **🎯 Pass Rate Analysis**: Success rates by question
- **📋 Comparative Analysis**: Strengths vs. focus areas

### 🗄️ Archives & Backups

- **📦 Complete Archive**: `marking_form/<exam_prefix>.zip`
  - Full grading website backup for archival
- **📁 Scripts Archive**: `marking_form/<exam_prefix>/marked/scripts.zip`
  - All generated reports and PDFs

### 🔍 Intermediate Data & Caching

#### **Question Data**
**Directory**: `marking_form/<exam_prefix>/questions/`
- **📊 Data Files**: `data.csv` with captured answers and AI analysis
- **✅ Mark Files**: `mark.json` with final scores and overrides
- **🌐 Web Interface**: Interactive grading interface files

#### **Intelligent Caching**
**Directory**: `cache/`
- **🗂️ Organized Structure**: Separate folders for different cache types
  - `grade_answer/`: Answer grading cache
  - `grade_moderator/`: Moderation cache
  - `ocr/`: OCR processing cache
  - `performance_report/`: Individual report cache
  - `class_overview_report/`: Class analytics cache
- **⚡ Performance**: Reduces API calls and processing time on reruns

### 🎯 Key Features

- **🤖 AI-Powered Insights**: Individual and class-level performance analysis
- **📊 Professional Formatting**: Stakeholder-ready reports and documents
- **📈 Visual Analytics**: Charts and graphs for data-driven decisions
- **🛡️ Error Resilience**: Robust processing with graceful degradation
- **⚡ Intelligent Caching**: Efficient API usage and faster reruns
- **🔍 Comprehensive Audit**: Complete data trail for transparency
- **📋 Multiple Formats**: Excel, Word, PDF, PowerPoint for different use cases

## 🛠️ System Requirements & Setup

### **Environment Options**
- **🌐 GitHub Codespaces**: Free, cloud-based development environment
- **💻 Local Installation**: Python 3.8+ with virtual environment
- **🐳 Docker**: Containerized deployment (optional)

### **Required Dependencies**
```bash
# Core libraries (automatically installed)
pip install -r requirements.txt

# Key packages include:
- pandas>=2.0.0          # Data analysis
- pypdf>=6.5.0          # Modern PDF processing  
- python-docx>=1.2.0    # Word document generation
- python-pptx>=0.6.21   # PowerPoint generation
- matplotlib>=3.7.0     # Visualization
- seaborn>=0.13.0       # Charts for visualizations
- opencv-python>=4.8.0  # Image processing
- ipywidgets>=8.0.0     # Interactive notebooks
```

### **API Configuration**

#### **1. API Key Setup (`.env` file)**
Create a `.env` file in the project root with your Google Gemini API key:

```env
# Get your API key from: https://aistudio.google.com/apikey
GOOGLE_GENAI_API_KEY=your-api-key-here
```

#### **2. Application Settings (`config.yaml` file)**
All other configuration settings are in `config.yaml`:

```yaml
# Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL
logging:
  level: INFO

# Caching configuration
caching:
  enabled: true  # Master cache control
  agents:
    ocr: true
    grading: true
    moderation: true
    marking_scheme: true
    annotation: true
    analytics: true

# AI Models for each agent
models:
  ocr: gemini-2.5-flash
  grading: gemini-3-flash-preview
  moderation: gemini-3-pro-preview
  marking_scheme: gemini-3-flash-preview
  annotation: gemini-3-flash-preview
  analytics: gemini-3-flash-preview
  analytics_image: gemini-3-pro-image-preview
```

**Quick Setup**:
```bash
python3 setup_config.py  # Creates config files from templates
python3 test_config.py   # Verifies configuration
```

**Note**: See [docs/CONFIGURATION.md](docs/CONFIGURATION.md) for complete configuration documentation.

#### **3. Email Configuration (Optional)**
For email distribution (Step 7), configure `smtp.config` in the project root.

### **Hardware Recommendations**
- **RAM**: 8GB+ (16GB recommended for large datasets)
- **Storage**: 5GB+ free space for processing and outputs
- **CPU**: Multi-core recommended for faster processing

## 📚 Documentation

### **Documentation Index**
All documentation is organized in the `docs/` directory. See **[docs/README.md](docs/README.md)** for the complete index.

### **Quick Links**
- **📖 Configuration**: [docs/CONFIGURATION.md](docs/CONFIGURATION.md) - Complete configuration guide
- **📖 Agent System**: [docs/AGENTS_README.md](docs/AGENTS_README.md) - Agent usage and API reference
- **⚙️ Cache Control**: [docs/CACHE_CONTROL.md](docs/CACHE_CONTROL.md) - Configure caching behavior
- **📊 Log Levels**: [docs/LOG_LEVEL_QUICK_REF.md](docs/LOG_LEVEL_QUICK_REF.md) - Configure logging output
- **🔧 Model Selection**: [docs/MODEL_CONFIGURATION.md](docs/MODEL_CONFIGURATION.md) - Model configuration guide

### **Getting Started**
1. **Clone Repository**: `git clone <repository-url>`
2. **Setup Environment**: Install dependencies and configure API keys
3. **Prepare Input Files**: Copy templates from `sample/` to `data/`
4. **Run Notebooks**: Execute notebooks in sequence (Step 1-7)
5. **Review Outputs**: Check generated reports and analytics

### **System Highlights**
- **🤖 AI-Powered**: Individual and class-level performance analysis with actionable insights
- **📊 Professional Output**: Multi-format reports (Excel, Word, PowerPoint, PDF) ready for stakeholders
- **🛡️ Production-Ready**: Comprehensive error handling, validation, and graceful degradation
- **⚡ Efficient**: Intelligent caching reduces API calls and speeds up reruns
- **📈 Visual Analytics**: Charts and graphs for data-driven decision making
- **🔍 Transparent**: Complete audit trail with detailed reasoning and raw data

This system transforms the grading process into a comprehensive, professional-grade assessment system that provides deep insights into student performance while maintaining the efficiency and accuracy of AI-powered automation.