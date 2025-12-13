# PTV Display Screen

A Pygame-based display application for real-time public transport departure information from the Public Transport Victoria (PTV) API.

## What This Project Does

PTV Display Screen creates a digital signage display for train stations or transit hubs that shows real-time departure information. The application:

- **Fetches live departure data** from the PTV (Public Transport Victoria) API
- **Displays platform-specific information** including routes, destinations, and departure times
- **Supports multiple display modes** for different information layouts
- **Handles station searches** with intelligent fuzzy matching for station names
- **Uses GTFS data** for route color mapping and static transit information
- **Targets embedded displays** (480×320 resolution) and desktop monitors

The application is designed to run on embedded display devices (e.g., Raspberry Pi) or desktop systems, providing real-time countdown timers and transit information for passengers.

## Key Features

- **Real-Time Updates**: Automatic polling of PTV API with configurable refresh rates
- **Multiple Display Modes**: Platform view and alternative display layouts
- **Station Lookup**: Fuzzy matching algorithm to find stations by partial names
- **Route-Specific Colors**: Uses GTFS route data to display authentic transit colors
- **Timezone Support**: Configurable timezone handling for accurate local times
- **API Caching**: Request caching to minimize API calls and improve performance
- **Responsive UI**: Handles mouse/touch input for display switching

## Getting Started

### Prerequisites

- Python 3.7+
- Pygame 1.9.6
- Internet connection (for PTV API)
- PTV API credentials (Developer ID and API Key)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/JaidenMcD/PTV-Display-Screen.git
   cd PTV-Display-Screen
   ```

2. **Create a virtual environment** (optional but recommended)
   ```bash
   python -m venv .venv
   # On Windows
   .venv\Scripts\activate
   # On Linux/Mac
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   Create a `.env` file in the project root with the following variables:
   ```env
   # PTV API Credentials (get from https://www.ptv.vic.gov.au/footer/data-and-reporting/datasets/ptv-timetable-api/)
   USER_ID=your_user_id
   API_KEY=your_api_key

   # Display Configuration
   DEVICE=0              # 0 for desktop, 1 for embedded Linux display
   TIMEZONE=Australia/Melbourne
   TRAIN_STOP_ID=optional_default_stop_id
   ```

### Running the Application

```bash
python app/run.py
```

When prompted, enter the station name:
```
Enter station: Flinders Street
```

The application will:
1. Search for the station using the PTV API
2. Display departure information on your screen
3. Update in real-time

### Controls

- **Click/Tap**: Switch between display modes (Platform View ↔ Alternative View)

## Project Structure

```
PTV-Display-Screen/
├── app/
│   ├── config.py              # Display configuration and colors
│   ├── run.py                 # Main application entry point
│   ├── utils.py               # Utility functions
│   ├── stop_class.py          # Stop-related functionality
│   ├── api/
│   │   └── ptv_api.py         # PTV API client with signing
│   ├── models/
│   │   ├── stop.py            # Stop data model
│   │   └── route.py           # Route data model
│   ├── displays/
│   │   ├── base.py            # Base display class
│   │   ├── platform.py        # Platform departure display
│   │   └── altdisplay.py      # Alternative display layout
│   ├── data/
│   │   ├── gtfs_loader.py     # GTFS data loader
│   │   ├── routes.txt         # Route reference data
│   │   ├── trips.txt          # Trip reference data
│   │   └── gtfs_static/       # Static GTFS dataset
│   └── assets/
│       └── fonts/             # Display fonts
├── testing/                    # Test scripts
├── requirements.txt            # Python dependencies
└── README.md
```

## Configuration

### Screen Resolution

Modify `config.py` to adjust display resolution:
```python
SCREEN_RES = (480, 320)  # Change as needed
```

### Display Colors

The application uses:
- **Route Colors**: From GTFS route data (`data/gtfs_static/routes.txt`)
- **UI Colors**: Configured in `config.py` (Network grey, light warm grey, etc.)

### API Caching

Request caching is enabled by default to minimize API calls. Disable via environment variable:
```env
PTV_CACHE_DISABLED=1
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `USER_ID` | PTV API user ID | Required |
| `API_KEY` | PTV API key | Required |
| `DEVICE` | 0=desktop, 1=embedded Linux | `0` |
| `TIMEZONE` | Timezone for time display | `Australia/Melbourne` |
| `TRAIN_STOP_ID` | Default stop ID | Optional |

## API Integration

The application integrates with the **PTV Timetable API v3**:

- **Base URL**: `https://timetableapi.ptv.vic.gov.au`
- **Authentication**: HMAC-SHA1 signing
- **Key Endpoints**:
  - `/v3/search/{query}` - Station/stop search
  - `/v3/departures/route_type/{type}/stop/{id}` - Get departures
  - `/v3/routes/{id}` - Route information

For more information, visit: https://www.ptv.vic.gov.au/footer/data-and-reporting/datasets/ptv-timetable-api/

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

## Development

### Project Dependencies

- **pygame** (1.9.6): Graphics and display rendering
- **python-dotenv**: Environment variable management
- **requests**: HTTP client for API calls
- **pytz**: Timezone handling
- **gtfs-realtime-bindings**: GTFS real-time protocol support
- **requests-cache**: Response caching for API calls

### Adding New Displays

1. Create a new class in `app/displays/` inheriting from `base.Display`
2. Implement required methods: `update()`, `draw()`, `on_show()`
3. Register in `run.py`:
   ```python
   displays = [
       PlatformDisplay(ctx),
       AltDisplay(ctx),
       MyNewDisplay(ctx)  # Add here
   ]
   ```

### Extending Station Search

The Stop class includes intelligent fuzzy matching:
- Exact name match: 100 points
- Name starts with query: 70 points
- Query substring in name: 40 points
- Suburb match: +20 points bonus

Modify scoring in [app/models/stop.py](app/models/stop.py) to customize matching behavior.

## Troubleshooting

### API Authentication Issues
- Verify `USER_ID` and `API_KEY` in `.env` file
- Check that credentials are properly registered at PTV developer portal
- Ensure no extra whitespace in environment variables

### Station Not Found
- Try partial station names (e.g., "Flinders" instead of "Flinders Street")
- Check for spelling and include suburb for disambiguation
- Verify the station exists in PTV's database

### Display Not Updating
- Check internet connection for API calls
- Verify API credentials and rate limits
- Check application logs for errors
- Ensure Pygame display can access screen (check DISPLAY environment variable on Linux)


## Support

For issues, questions, or suggestions:

- **GitHub Issues**: [Report an issue](https://github.com/JaidenMcD/PTV-Display-Screen/issues)
- **PTV API Help**: https://www.ptv.vic.gov.au/footer/data-and-reporting/datasets/ptv-timetable-api/

## Acknowledgments

- Public Transport Victoria (PTV) for the Timetable API
- Pygame community for the graphics library
- GTFS community for transit data standards
