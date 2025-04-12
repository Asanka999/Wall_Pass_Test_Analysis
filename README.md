# Wall_Pass_Test_Analysis

1. Input Feed (Camera/Video)
The system captures live video from a webcam (default) or a pre-recorded video file.

The frame is resized to 640x360 (50% of 1280x720) for faster processing.

2. Color Detection (HSV Space)
The frame is converted from BGR to HSV for better color segmentation.

Ball Detection (Orange/White/Yellow):

A mask isolates the ball using predefined HSV ranges.

Morphological operations (erosion + dilation) clean up noise.

Contour detection finds circular objects (high circularity = ball).

Wall Zone Detection (Blue/Red/Green):

Another mask identifies the marked wall area.

The largest contour is selected as the "wall zone" (must be >5000 pixels).

3. Ball Tracking & Trajectory
Ball Position: The centroid (center) of the detected ball is recorded.

Trajectory Buffer: A deque (max length = 64) stores recent ball positions.

Trajectory Drawing:

A fading red line connects past positions (thicker for recent points).

If the ball is lost, gaps appear in the trajectory.

4. Wall Pass Logic
The wall zone is split into left and right halves.

A "pass" is counted when:

The ball crosses from left → right or right → left.

The ball must be detected on both sides (no false positives).

Visual Feedback:

On a successful pass, the screen flashes green briefly.

5. Game Stats Overlay
A semi-transparent black box (top-left) displays:

Pass Count: Total wall passes detected.

Time Elapsed: In MM:SS format.

If the wall zone is not detected, a red warning appears.

6. Debug Mode (Optional)
Ball & Wall Masks are shown in small previews (top-right).

Helps calibrate color thresholds if detection fails.

7. Output Display
The final output shows:

Live video with ball tracking (yellow circle + red center).

Wall zone (green rectangle).

Trajectory path (red line).

Stats overlay (pass count, time).

Press Q to quit.
