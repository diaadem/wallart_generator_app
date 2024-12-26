# WallArtAI

An AI-powered web application that helps users choose and generate perfect wall art based on their room's color scheme and personal preferences. The app analyzes room photos using GPT-4 Vision and generates customized artwork suggestions using Stability AI.

## 🎥 Demo
[https://www.youtube.com/watch?v=DwhR4Tal1Jg]

## ✨ Features

- 📸 Room photo analysis using GPT-4 Vision
- 🎨 Custom artwork generation based on room colors
- 🖼️ Interactive artwork selection and refinement
- 📏 Custom sizing options for printing
- 💾 High-resolution artwork downloads
- 🎯 Personalized style preferences

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- OpenAI API key
- Stability AI API key

### Installation

1. Clone the repository:
```bash
git clone [your-repo-url]
cd wall-decorator
```

2. Create and activate a virtual environment:

Using pip:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Or using conda:
```bash
conda env create -f environment.yml
conda activate wall-decorator
```

3. Set up your environment variables:
- Copy `.env.example` to `.env`
- Add your API keys to `.env`:
```plaintext
OPENAI_API_KEY=your_openai_api_key_here
STABILITY_API_KEY=your_stability_api_key_here
FLASK_SECRET_KEY=your_secret_key_here
```

4. Run the application:
```bash
python app.py
```

The app will be available at `http://localhost:5000`

## 🛠️ Technologies Used

- Flask (Backend)
- OpenAI GPT-4 Vision (Room Analysis)
- Stability AI (Artwork Generation)
- Bootstrap 5 (Frontend)
- HTML5 Canvas (Image Processing)

## 📝 Usage

1. Upload a photo of your room
2. Add any style preferences (optional)
3. View and select from generated artwork suggestions
4. Generate more options based on your selections
5. Download artwork in your preferred size and resolution
