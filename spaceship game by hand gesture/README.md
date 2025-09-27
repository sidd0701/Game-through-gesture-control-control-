Spaceship Gesture Control

"Spaceship Gesture Control" is a single-player, arcade-style shooter game that uses a webcam and computer vision to interpret hand gestures for gameplay.

Getting Started

To run this game, you'll need Python installed on your computer. You also need to install the following libraries using pip:
pygame: For creating the game window and handling game logic.
opencv-python: For accessing the webcam and processing video frames.
mediapipe: For robust hand tracking and gesture recognition.
numpy: For numerical operations with the video frames.


Bash

pip install pygame opencv-python mediapipe numpy
Once all dependencies are installed, save the provided Python code as a .py file (e.g., spaceship_game.py) and run it from your terminal:

Bash

python spaceship_game.py


How to Play
The game runs in a full-screen window with a live feed from your webcam displayed in the top-right corner. You use your right hand to control the spaceship.

Movement: Move your hand horizontally left and right to steer the spaceship. The spaceship's movement is accelerated, giving it a realistic feel.

Firing: To fire projectiles, make a quick "thumb tap" gesture by touching your thumb to your index finger.

Power-Up: Form a closed fist to activate a temporary power-up, which increases your spaceship's firing rate. A yellow highlight will appear on the ship when the power-up is active.

Restart: If your spaceship is hit and the game is over, show a middle finger gesture to the webcam or press the Enter key to restart.



Known Issues

Webcam Detection: The game will attempt to open your webcam by trying a few different device indices. If it still fails, ensure your webcam is not in use by another application and that its drivers are up to date.

Latency: Performance and gesture recognition can vary depending on your computer's processing power and the quality of your webcam.
