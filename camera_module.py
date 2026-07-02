"""
Camera module for Raspberry Pi AI Camera with IMX500
Handles camera initialization, frame capture, and onboard AI inference
"""

import numpy as np
from picamera2 import Picamera2
from PIL import Image
import config
import os

# Try to import IMX500 for onboard AI
try:
    from picamera2.devices import IMX500
    from picamera2.devices.imx500 import NetworkIntrinsics
    IMX500_AVAILABLE = True
except ImportError:
    print("WARNING: IMX500 not available. AI Camera features disabled.")
    IMX500_AVAILABLE = False


class Camera:
    """Manages Raspberry Pi AI Camera operations with IMX500 onboard AI"""

    def __init__(self):
        """Initialize the camera"""
        self.camera = None
        self.imx500 = None
        self.is_running = False
        self.use_imx500 = False
        self.intrinsics = None
        self._initialize_camera()

    def _initialize_camera(self):
        """Initialize Picamera2 with IMX500 if available"""
        try:
            self.camera = Picamera2()

            # Check if IMX500 model is configured and available
            if IMX500_AVAILABLE and config.IMX500_MODEL_PATH and os.path.exists(config.IMX500_MODEL_PATH):
                self._initialize_with_imx500()
            else:
                self._initialize_standard()

        except Exception as e:
            print(f"Error initializing camera: {e}")
            # Fallback to standard mode
            if not self.camera:
                self.camera = Picamera2()
            self._initialize_standard()

    def _initialize_with_imx500(self):
        """Initialize camera with IMX500 onboard AI"""
        try:
            # Create IMX500 instance
            self.imx500 = IMX500(config.IMX500_MODEL_PATH)
            self.intrinsics = self.imx500.network_intrinsics

            # Configure camera with IMX500
            camera_config = self.camera.create_preview_configuration(
                main={"size": (config.CAMERA_WIDTH, config.CAMERA_HEIGHT),
                      "format": "RGB888"},
                controls={"FrameRate": config.CAMERA_FPS}
            )

            self.camera.configure(camera_config)
            self.use_imx500 = True

            if config.DEBUG_MODE:
                print(f"Camera initialized with IMX500: {config.CAMERA_WIDTH}x{config.CAMERA_HEIGHT}")
                print(f"IMX500 model loaded: {config.IMX500_MODEL_PATH}")
                if self.intrinsics:
                    print(f"Model input size: {self.intrinsics.input_width}x{self.intrinsics.input_height}")

        except Exception as e:
            print(f"Error initializing IMX500: {e}")
            print("Falling back to standard camera mode")
            self._initialize_standard()

    def _initialize_standard(self):
        """Initialize camera in standard mode (without IMX500 AI)"""
        # Configure camera for optimal face recognition
        camera_config = self.camera.create_preview_configuration(
            main={"size": (config.CAMERA_WIDTH, config.CAMERA_HEIGHT),
                  "format": "RGB888"}
        )
        self.camera.configure(camera_config)
        self.use_imx500 = False

        if config.DEBUG_MODE:
            print(f"Camera initialized (standard mode): {config.CAMERA_WIDTH}x{config.CAMERA_HEIGHT}")
            print("IMX500 AI not available - using CPU-based detection")

    def start(self):
        """Start the camera"""
        try:
            if not self.is_running:
                self.camera.start()
                self.is_running = True
                if config.DEBUG_MODE:
                    print("Camera started")
        except Exception as e:
            print(f"Error starting camera: {e}")
            raise

    def stop(self):
        """Stop the camera"""
        try:
            if self.is_running:
                self.camera.stop()
                self.is_running = False
                if config.DEBUG_MODE:
                    print("Camera stopped")
        except Exception as e:
            print(f"Error stopping camera: {e}")

    def capture_frame(self) -> np.ndarray:
        """
        Capture a single frame from the camera

        Returns:
            numpy array representing the frame in RGB format
        """
        try:
            if not self.is_running:
                self.start()

            # Capture frame as numpy array
            frame = self.camera.capture_array()

            return frame

        except Exception as e:
            print(f"Error capturing frame: {e}")
            return None

    def capture_frame_with_inference(self) -> tuple:
        """
        Capture a frame with IMX500 inference results (if available)

        Returns:
            Tuple of (frame, inference_results) or (frame, None) if IMX500 not available
            inference_results format depends on the model loaded
        """
        try:
            if not self.is_running:
                self.start()

            # Capture frame
            frame = self.camera.capture_array()

            # Get inference results if IMX500 is available
            inference_results = None
            if self.use_imx500 and self.imx500:
                try:
                    # Get the last inference result from IMX500
                    metadata = self.camera.capture_metadata()
                    if metadata and 'imx500' in metadata:
                        inference_results = metadata['imx500']
                except Exception as e:
                    if config.DEBUG_MODE:
                        print(f"Error getting IMX500 inference: {e}")

            return frame, inference_results

        except Exception as e:
            print(f"Error capturing frame with inference: {e}")
            return None, None

    def get_detections_from_inference(self, inference_results) -> list:
        """
        Parse IMX500 inference results into detection list

        Args:
            inference_results: Raw inference results from IMX500

        Returns:
            List of detection dictionaries with 'bbox', 'confidence', 'class_id'
        """
        detections = []

        if not inference_results or not self.use_imx500:
            return detections

        try:
            # Parse based on model type
            # This is a generic parser - adjust based on your specific model
            if hasattr(inference_results, 'boxes'):
                # Object detection model format
                boxes = inference_results.boxes
                for box in boxes:
                    detection = {
                        'bbox': box[:4],  # [x1, y1, x2, y2]
                        'confidence': box[4] if len(box) > 4 else 1.0,
                        'class_id': int(box[5]) if len(box) > 5 else 0
                    }
                    detections.append(detection)

        except Exception as e:
            if config.DEBUG_MODE:
                print(f"Error parsing IMX500 inference: {e}")

        return detections

    def capture_image(self, save_path: str = None) -> Image.Image:
        """
        Capture a single image from the camera

        Args:
            save_path: Optional path to save the image

        Returns:
            PIL Image object
        """
        try:
            frame = self.capture_frame()
            if frame is None:
                return None

            # Convert numpy array to PIL Image
            image = Image.fromarray(frame)

            # Save if path provided
            if save_path:
                image.save(save_path)
                if config.DEBUG_MODE:
                    print(f"Image saved to: {save_path}")

            return image

        except Exception as e:
            print(f"Error capturing image: {e}")
            return None

    def get_frame_for_display(self) -> np.ndarray:
        """
        Get a frame optimized for display

        Returns:
            numpy array in RGB format suitable for pygame/display
        """
        return self.capture_frame()

    def is_using_imx500(self) -> bool:
        """
        Check if camera is using IMX500 onboard AI

        Returns:
            True if IMX500 is active, False otherwise
        """
        return self.use_imx500

    def close(self):
        """Close the camera and release resources"""
        try:
            self.stop()
            if self.camera:
                self.camera.close()
                if config.DEBUG_MODE:
                    print("Camera closed")

            # Clean up IMX500 if used
            if self.imx500:
                self.imx500 = None

        except Exception as e:
            print(f"Error closing camera: {e}")

    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

    def __del__(self):
        """Destructor - ensure camera is closed"""
        self.close()


# Convenience function for quick camera access
def get_camera() -> Camera:
    """Get a camera instance"""
    return Camera()
