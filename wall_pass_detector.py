import cv2
import numpy as np
import time
from collections import deque
import argparse

def parse_arguments():
    parser = argparse.ArgumentParser(description='Table Tennis Wall Pass Detection')
    parser.add_argument('--input', type=str, default='0', help='Path to video file or camera index (default: 0)')
    parser.add_argument('--ball_color', type=str, default='orange', help='Ball color (orange, white, yellow)')
    parser.add_argument('--wall_color', type=str, default='blue', help='Wall box color (blue, red, green)')
    parser.add_argument('--buffer_size', type=int, default=64, help='Size of trajectory buffer')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode with additional visualizations')
    return parser.parse_args()

class WallPassDetector:
    def __init__(self, args):
        # Initialize video capture
        self.input_source = args.input
        if self.input_source.isdigit():
            self.cap = cv2.VideoCapture(int(self.input_source))
        else:
            self.cap = cv2.VideoCapture(self.input_source)
           
        # Check if camera/video opened successfully
        if not self.cap.isOpened():
            raise ValueError(f"Error: Could not open video source {self.input_source}")
           
        # Set camera properties for better performance
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
       
        # Color ranges for detection
        self.ball_color = args.ball_color
        self.wall_color = args.wall_color
        self.setup_color_ranges()
       
        # Ball tracking parameters
        self.buffer_size = args.buffer_size
        self.ball_positions = deque(maxlen=self.buffer_size)
        self.min_ball_radius = 5
        self.max_ball_radius = 30
       
        # Wall zone parameters
        self.wall_zone = None
        self.wall_detected = False
       
        # Game stats
        self.pass_count = 0
        self.last_pass_side = None
        self.start_time = time.time()
        self.debug_mode = args.debug
       
    def setup_color_ranges(self):
        # HSV color ranges for different objects
        if self.ball_color == 'orange':
            self.ball_lower = np.array([5, 100, 150])
            self.ball_upper = np.array([15, 255, 255])
        elif self.ball_color == 'white':
            self.ball_lower = np.array([0, 0, 200])
            self.ball_upper = np.array([180, 30, 255])
        elif self.ball_color == 'yellow':
            self.ball_lower = np.array([20, 100, 100])
            self.ball_upper = np.array([30, 255, 255])
        else:
            self.ball_lower = np.array([5, 100, 150])  # Default to orange
            self.ball_upper = np.array([15, 255, 255])
           
        if self.wall_color == 'blue':
            self.wall_lower = np.array([100, 100, 100])
            self.wall_upper = np.array([130, 255, 255])
        elif self.wall_color == 'red':
            # Red wraps around the hue spectrum in HSV
            self.wall_lower = np.array([0, 100, 100])
            self.wall_upper = np.array([10, 255, 255])
            self.wall_lower2 = np.array([170, 100, 100])
            self.wall_upper2 = np.array([180, 255, 255])
        elif self.wall_color == 'green':
            self.wall_lower = np.array([40, 100, 100])
            self.wall_upper = np.array([80, 255, 255])
        else:
            self.wall_lower = np.array([100, 100, 100])  # Default to blue
            self.wall_upper = np.array([130, 255, 255])
   
    def detect_wall_zone(self, frame, hsv):
        # Create masks for wall color
        if self.wall_color == 'red':
            mask1 = cv2.inRange(hsv, self.wall_lower, self.wall_upper)
            mask2 = cv2.inRange(hsv, self.wall_lower2, self.wall_upper2)
            mask = cv2.bitwise_or(mask1, mask2)
        else:
            mask = cv2.inRange(hsv, self.wall_lower, self.wall_upper)
           
        # Apply morphological operations to clean up the mask
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.dilate(mask, kernel, iterations=2)
        mask = cv2.erode(mask, kernel, iterations=2)
       
        # Find contours in the mask
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
       
        if contours:
            # Find the largest contour (assuming it's the wall box)
            largest_contour = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest_contour)
           
            # Only proceed if the contour is large enough
            if area > 5000:
                # Get bounding rectangle
                x, y, w, h = cv2.boundingRect(largest_contour)
               
                # Define wall zone
                self.wall_zone = (x, y, x + w, y + h)
                self.wall_detected = True
               
                # Draw wall zone on frame
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, "Wall Zone", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
               
                return True
               
        return False
               
    def detect_ball(self, frame, hsv):
        # Create mask for ball color
        mask = cv2.inRange(hsv, self.ball_lower, self.ball_upper)
       
        # Apply morphological operations
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.erode(mask, kernel, iterations=1)
        mask = cv2.dilate(mask, kernel, iterations=1)
       
        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
       
        ball_detected = False
        center = None
       
        if contours:
            # Find the best circular contour
            best_circularity = 0
            best_contour = None
           
            for contour in contours:
                area = cv2.contourArea(contour)
                if area < 30:  # Ignore very small contours
                    continue
                   
                perimeter = cv2.arcLength(contour, True)
                if perimeter == 0:
                    continue
                   
                # Circularity = 4*pi*area/perimeter^2, perfect circle = 1
                circularity = 4 * np.pi * area / (perimeter * perimeter)
               
                if circularity > 0.7 and circularity > best_circularity:  # Threshold for considering it a circle
                    best_circularity = circularity
                    best_contour = contour
           
            if best_contour is not None:
                # Get minimum enclosing circle
                ((x, y), radius) = cv2.minEnclosingCircle(best_contour)
               
                # Only proceed if the radius is within reasonable range
                if self.min_ball_radius < radius < self.max_ball_radius:
                    M = cv2.moments(best_contour)
                    if M["m00"] > 0:
                        center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
                        ball_detected = True
                       
                        # Draw circle and center
                        cv2.circle(frame, (int(x), int(y)), int(radius), (0, 255, 255), 2)
                        cv2.circle(frame, center, 5, (0, 0, 255), -1)
                       
        return ball_detected, center
   
    def check_wall_pass(self, center):
        if not self.wall_detected or center is None:
            return False
           
        # Get wall boundaries
        x1, y1, x2, y2 = self.wall_zone
       
        # Check which side of the wall the ball is on
        current_side = 'left' if center[0] < (x1 + x2) // 2 else 'right'
       
        # If this is the first detection, just record the side
        if self.last_pass_side is None:
            self.last_pass_side = current_side
            return False
           
        # Check if the ball has crossed from one side to the other
        if current_side != self.last_pass_side:
            # Valid pass detected
            self.pass_count += 1
            self.last_pass_side = current_side
            return True
           
        return False
   
    def draw_trajectory(self, frame):
        # Draw the trajectory points
        for i in range(1, len(self.ball_positions)):
            if self.ball_positions[i] is None or self.ball_positions[i-1] is None:
                continue
               
            # Calculate the thickness based on the position in the queue
            thickness = int(np.sqrt(self.buffer_size / float(i + 1)) * 2.5)
           
            # Draw the connecting lines
            cv2.line(frame, self.ball_positions[i-1], self.ball_positions[i], (0, 0, 255), thickness)
   
    def draw_stats(self, frame):
        # Calculate elapsed time
        elapsed_time = time.time() - self.start_time
        minutes = int(elapsed_time // 60)
        seconds = int(elapsed_time % 60)
       
        # Create a semi-transparent overlay for stats
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (300, 100), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
       
        # Display stats
        cv2.putText(frame, f"Passes: {self.pass_count}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(frame, f"Time: {minutes:02d}:{seconds:02d}", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
       
        # If wall isn't detected, show warning
        if not self.wall_detected:
            cv2.putText(frame, "WARNING: Wall zone not detected!", (frame.shape[1]//2 - 200, 40),
                      cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
   
    def run(self):
        try:
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    print("Failed to grab frame")
                    break
                   
                # Resize for faster processing
                frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
               
                # Convert to HSV color space
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
               
                # Detect wall zone (if not already detected or in debug mode)
                if not self.wall_detected or self.debug_mode:
                    self.detect_wall_zone(frame, hsv)
               
                # Detect ball
                ball_detected, center = self.detect_ball(frame, hsv)
               
                # Add position to trajectory deque
                self.ball_positions.appendleft(center if ball_detected else None)
               
                # Check for wall pass if ball is detected
                if ball_detected:
                    pass_detected = self.check_wall_pass(center)
                    if pass_detected:
                        # Flash the screen briefly to indicate a successful pass
                        overlay = frame.copy()
                        cv2.rectangle(overlay, (0, 0), (frame.shape[1], frame.shape[0]), (0, 255, 0), -1)
                        cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)
               
                # Draw ball trajectory
                self.draw_trajectory(frame)
               
                # Draw stats overlay
                self.draw_stats(frame)
               
                # Show debug info if enabled
                if self.debug_mode:
                    # Create masks for visualization
                    ball_mask = cv2.inRange(hsv, self.ball_lower, self.ball_upper)
                    if self.wall_color == 'red':
                        wall_mask1 = cv2.inRange(hsv, self.wall_lower, self.wall_upper)
                        wall_mask2 = cv2.inRange(hsv, self.wall_lower2, self.wall_upper2)
                        wall_mask = cv2.bitwise_or(wall_mask1, wall_mask2)
                    else:
                        wall_mask = cv2.inRange(hsv, self.wall_lower, self.wall_upper)
                   
                    # Resize masks for display
                    display_height = 120
                    ball_mask_small = cv2.resize(ball_mask, (int(display_height * ball_mask.shape[1] / ball_mask.shape[0]), display_height))
                    wall_mask_small = cv2.resize(wall_mask, (int(display_height * wall_mask.shape[1] / wall_mask.shape[0]), display_height))
                   
                    # Convert masks to BGR for display
                    ball_mask_bgr = cv2.cvtColor(ball_mask_small, cv2.COLOR_GRAY2BGR)
                    wall_mask_bgr = cv2.cvtColor(wall_mask_small, cv2.COLOR_GRAY2BGR)
                   
                    # Add masks to the main frame
                    frame[10:10+display_height, frame.shape[1]-10-ball_mask_small.shape[1]:frame.shape[1]-10] = ball_mask_bgr
                    frame[10+display_height+10:10+display_height+10+display_height, frame.shape[1]-10-wall_mask_small.shape[1]:frame.shape[1]-10] = wall_mask_bgr
                   
                    # Add labels
                    cv2.putText(frame, "Ball Mask", (frame.shape[1]-10-ball_mask_small.shape[1], 10-5),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                    cv2.putText(frame, "Wall Mask", (frame.shape[1]-10-wall_mask_small.shape[1], 10+display_height+10-5),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
               
                # Display the resulting frame
                cv2.imshow('Table Tennis Wall Pass Detection', frame)
               
                # Quit on 'q' press
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                   
        finally:
            # Release resources
            self.cap.release()
            cv2.destroyAllWindows()


if __name__ == "__main__":
    args = parse_arguments()
    detector = WallPassDetector(args)
    detector.run()