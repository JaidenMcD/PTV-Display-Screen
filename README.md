# PTV Display Screen

A Pygame-based display application for real-time public transport departure information from the Public Transport Victoria (PTV) API.

## Setup

### Prerequisites
- Python 3.7+
- Pygame 1.9.6+
- PTV API credentials

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/JaidenMcD/PTV-Display-Screen.git
   cd PTV-Display-Screen

2. **Install dependencies** (optional but recommended)
   pip install -r requirements.txt

3. **Create a .env file with your PTV API credentials**
   ``` env
   USER_ID=your_user_id
   API_KEY=your_api_key
   TIMEZONE=Australia/Melbourne
   DEVICE=0
   ```

### Running
   ```python app/run.py


## Project Structure

```
app/
├── config.py              # Configuration and colors
├── run.py                 # Main entry point
├── utils.py               # Utility functions
├── fonts.py               # Font management
├── api/                   # API clients
├── models/                # Data models
├── displays/              # Display components
├── data/                  # GTFS data
└── assets/                # Fonts and icons
```


##

## Hardware Compatibility

### Desktop
- Windows, Linux, or macOS with Pygame support
- Any monitor (configurable resolution)

### Embedded Displays
- Raspberry Pi or similar single-board computers
- 480×320 displays (standard for transit displays)
- Requires X11 display server for Linux

For embedded setup, ensure display environment variables are set:
```python
os.environ["DISPLAY"] = ":0"
os.environ["XAUTHORITY"] = "/home/admin/.Xauthority"
```

