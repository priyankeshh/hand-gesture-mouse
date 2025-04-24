# Hand Gesture Control System

A computer vision application that uses hand gestures to control various computer functions including:

- **Volume Control**: Adjust system volume by pinching thumb and index finger
- **Cursor Control**: Move and click your mouse using hand gestures
- **Scroll Control**: Scroll up and down web pages with simple finger movements

## Features

- Real-time hand tracking and gesture recognition
- Multiple control modes (Volume, Cursor, Scroll)
- Intuitive gesture-based interactions
- Visual feedback with on-screen indicators

## Requirements

- Python 3.6+
- Webcam

## Installation

1. Clone this repository
2. Install required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

Run the main application:
```
python Main.py
```

### Gesture Controls

- **Neutral Mode**: Close all fingers (fist)
- **Volume Mode**: Extend thumb and index finger, adjust volume by changing distance
- **Cursor Mode**: Extend all fingers, move index finger to control cursor position
- **Scroll Mode**: Extend index finger to scroll up, index and middle to scroll down

Exit the application by pressing 'q'.

## Project Structure

- `Main.py`: Main application with gesture recognition and control logic
- `HandTrackingModule.py`: Custom module for hand detection and tracking

## License



