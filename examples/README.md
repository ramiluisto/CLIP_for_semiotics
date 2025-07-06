# Examples Directory

This directory contains comprehensive examples demonstrating the capabilities of CLIP for Humanists.

## 📁 Available Examples

### 1. **Basic Demonstrations**
- `demo_with_sample_data.py` - Basic CLIP and spatial analysis with sample images
- `basic_autocorrelation_demo.py` - Focused spatial autocorrelation analysis
- `multimodal_analysis_demo.py` - Full multimodal analysis demonstration

### 2. **Japanese Poster Analysis (New)**
- `japanese_poster_analysis_demo.py` - **Comprehensive poster analysis demo**
- `run_poster_analysis_with_openai.py` - Full multimodal analysis with GPT-4o

## 🎌 Japanese Poster Analysis

The Japanese poster analysis examples demonstrate the full capabilities of CLIP for Humanists using a real dataset of 156 Japanese manner posters from 2011-2024.

### Dataset
- **Location**: `./data/japanese_example_posters/`
- **Content**: 156 Japanese transit etiquette posters
- **Years**: 2011-2024
- **Research Value**: Excellent for studying visual communication strategies and cultural norms

### Analysis Features

#### `japanese_poster_analysis_demo.py` (Free - CLIP Only)
```bash
python examples/japanese_poster_analysis_demo.py
```

**What it does:**
- ✅ CLIP similarity analysis with 48 culturally-relevant keywords
- ✅ Temporal trend analysis across poster years
- ✅ Statistical analysis and visualization
- ✅ Comprehensive markdown report generation
- ✅ No API costs - runs entirely locally

**Keywords analyzed:**
- **Character Types**: businessman, student, elderly person, etc.
- **Behaviors**: seat monopolization, helping others, patient waiting, etc.
- **Cultural Concepts**: social harmony, politeness, Japanese transit culture, etc.
- **Visual Elements**: cartoon style, manga aesthetic, bright colors, etc.

**Generated outputs:**
- Detailed markdown report with findings
- Statistical visualizations (bar charts, correlation matrix, temporal trends)
- JSON data for further analysis
- Professional figures for presentations

#### `run_poster_analysis_with_openai.py` (Paid - Full Multimodal)
```bash
export OPENAI_API_KEY=your_key_here
python examples/run_poster_analysis_with_openai.py
```

**What it adds:**
- 🔬 OpenAI GPT-4o vision analysis for deep cultural interpretation
- 📊 Cross-analysis correlation between CLIP and Vision API results
- 🎯 Qualitative cultural context and semiotic analysis
- 📈 Enhanced reporting with multimodal insights

**Cost**: ~$0.15 per image with GPT-4o (demo limited to 10 images = ~$1.50)

### Example Results

**Top CLIP findings from actual analysis:**
1. **manner poster** (similarity: 0.636) - Highest scoring theme
2. **instructional poster** (similarity: 0.633) - Clear instructional design
3. **Japanese transit culture** (similarity: 0.632) - Cultural specificity
4. **cartoon style** (similarity: 0.580) - Visual approach
5. **social harmony** (similarity: 0.565) - Cultural values

**Analysis insights:**
- Strong representation of positive behavioral themes
- Consistent visual style emphasizing approachability
- Cultural values of harmony and collective responsibility
- Temporal stability in messaging approach

## 🚀 Quick Start

### 1. Run Basic Demo (Free)
```bash
# Install dependencies
pip install -r requirements.txt

# Run CLIP-only analysis
python examples/japanese_poster_analysis_demo.py
```

### 2. Run Full Analysis (Requires OpenAI API)
```bash
# Set API key
export OPENAI_API_KEY=your_key_here

# Run multimodal analysis (costs ~$1.50 for demo)
python examples/run_poster_analysis_with_openai.py
```

### 3. View Results
```bash
# Check generated report
open output/japanese_poster_analysis/japanese_poster_analysis_report.md

# View visualizations  
open output/japanese_poster_analysis/figures/
```

## 📊 Research Applications

This poster analysis framework can be adapted for:

### **Cultural Studies**
- Visual communication strategies across cultures
- Evolution of public messaging approaches
- Cross-cultural comparison of social norms

### **Digital Humanities**
- Large-scale analysis of visual archives
- Temporal studies of visual culture
- Computational approaches to art history

### **Public Policy Research**
- Effectiveness of visual communication campaigns
- Cultural adaptation of public messaging
- Behavioral change communication strategies

### **Urban Studies**
- Transit culture and public behavior
- Visual rhetoric in public spaces
- Cultural geography of transportation

## 🔧 Customization

### Adapt for Your Dataset
1. **Place your images** in `./data/your_dataset/`
2. **Modify keywords** in the analyzer class based on your research questions
3. **Customize vision template** for domain-specific analysis
4. **Run analysis** with your specific parameters

### Example Adaptations
- **Art History**: Analyze visual themes across art movements
- **Advertising Research**: Study commercial visual strategies
- **Social Media**: Analyze visual culture in social platforms
- **Historical Documents**: Study evolution of visual communication

## 📚 Documentation

Each script includes comprehensive docstrings and comments explaining:
- Methodology and theoretical framework
- Cultural context and keyword selection
- Statistical analysis approaches
- Visualization techniques
- Report generation process

## 🎯 Next Steps

After running the demos:
1. **Explore the generated reports** to understand the methodology
2. **Examine the visualizations** to see pattern analysis
3. **Review the raw data** for detailed insights
4. **Adapt the scripts** for your own research questions
5. **Scale up analysis** for larger datasets

The Japanese poster analysis serves as a comprehensive template for applying CLIP for Humanists to real research questions in digital humanities and cultural studies.