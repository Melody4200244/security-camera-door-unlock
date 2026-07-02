"""
Face recognition module for encoding and matching faces
Supports hybrid mode with IMX500 onboard AI for optimized performance
"""

import face_recognition
import numpy as np
from typing import List, Tuple, Optional, Dict
from PIL import Image
import config


class FaceRecognizer:
    """Handles face detection, encoding, and matching with optional IMX500 integration"""

    def __init__(self, use_imx500: bool = False):
        """
        Initialize the face recognizer

        Args:
            use_imx500: Whether IMX500 onboard AI is available for pre-detection
        """
        self.known_face_encodings = []
        self.known_face_ids = []
        self.known_face_names = []
        self.use_imx500 = use_imx500

    def load_known_faces(self, faces_data: List[Tuple[int, str, np.ndarray, str]]):
        """
        Load known faces from database

        Args:
            faces_data: List of tuples (id, name, face_encoding, photo_path)
        """
        self.known_face_encodings = []
        self.known_face_ids = []
        self.known_face_names = []

        for person_id, name, encoding, photo_path in faces_data:
            self.known_face_encodings.append(encoding)
            self.known_face_ids.append(person_id)
            self.known_face_names.append(name)

        if config.DEBUG_MODE:
            print(f"Loaded {len(self.known_face_encodings)} known faces")

    def detect_faces(self, frame: np.ndarray) -> List[Tuple]:
        """
        Detect faces in a frame

        Args:
            frame: Image as numpy array (RGB format)

        Returns:
            List of face locations as tuples (top, right, bottom, left)
        """
        try:
            # Detect faces using HOG model (faster) or CNN model (more accurate but slower)
            # Using HOG for real-time performance
            face_locations = face_recognition.face_locations(frame, model="hog")

            return face_locations

        except Exception as e:
            print(f"Error detecting faces: {e}")
            return []

    def encode_face(self, frame: np.ndarray,
                   face_location: Optional[Tuple] = None) -> Optional[np.ndarray]:
        """
        Generate face encoding from an image

        Args:
            frame: Image as numpy array (RGB format)
            face_location: Optional pre-detected face location (top, right, bottom, left)

        Returns:
            Face encoding as numpy array, or None if no face found
        """
        try:
            if face_location:
                # Use provided face location
                encodings = face_recognition.face_encodings(frame, [face_location])
            else:
                # Detect face first
                encodings = face_recognition.face_encodings(frame)

            if len(encodings) > 0:
                return encodings[0]
            else:
                return None

        except Exception as e:
            print(f"Error encoding face: {e}")
            return None

    def encode_face_from_image(self, image_path: str) -> Optional[np.ndarray]:
        """
        Generate face encoding from an image file

        Args:
            image_path: Path to the image file

        Returns:
            Face encoding as numpy array, or None if no face found
        """
        try:
            # Load image
            image = face_recognition.load_image_file(image_path)

            # Generate encoding
            return self.encode_face(image)

        except Exception as e:
            print(f"Error encoding face from image: {e}")
            return None

    def recognize_faces(self, frame: np.ndarray,
                       face_locations: List[Tuple]) -> List[dict]:
        """
        Recognize faces in a frame

        Args:
            frame: Image as numpy array (RGB format)
            face_locations: List of face locations from detect_faces()

        Returns:
            List of dictionaries with recognition results:
            {
                'location': (top, right, bottom, left),
                'encoding': face encoding,
                'is_match': bool,
                'person_id': int or None,
                'name': str or 'Unknown',
                'distance': float (confidence)
            }
        """
        results = []

        if len(face_locations) == 0:
            return results

        try:
            # Encode all detected faces
            face_encodings = face_recognition.face_encodings(frame, face_locations)

            # Match each face against known faces
            for location, encoding in zip(face_locations, face_encodings):
                result = {
                    'location': location,
                    'encoding': encoding,
                    'is_match': False,
                    'person_id': None,
                    'name': 'Unknown',
                    'distance': 1.0
                }

                if len(self.known_face_encodings) > 0:
                    # Compare with known faces
                    face_distances = face_recognition.face_distance(
                        self.known_face_encodings, encoding
                    )

                    # Find best match
                    best_match_index = np.argmin(face_distances)
                    best_distance = face_distances[best_match_index]

                    # Check if match is within tolerance
                    if best_distance <= config.FACE_MATCH_TOLERANCE:
                        result['is_match'] = True
                        result['person_id'] = self.known_face_ids[best_match_index]
                        result['name'] = self.known_face_names[best_match_index]
                        result['distance'] = float(best_distance)

                results.append(result)

            return results

        except Exception as e:
            print(f"Error recognizing faces: {e}")
            return results

    def process_frame(self, frame: np.ndarray) -> List[dict]:
        """
        Complete face recognition pipeline: detect and recognize faces

        Args:
            frame: Image as numpy array (RGB format)

        Returns:
            List of recognition results
        """
        # Detect faces
        face_locations = self.detect_faces(frame)

        # Recognize faces
        results = self.recognize_faces(frame, face_locations)

        return results

    def process_frame_with_imx500(self, frame: np.ndarray,
                                  imx500_detections: List[Dict]) -> List[dict]:
        """
        Process frame using IMX500 person detections as hint for face detection
        This hybrid approach uses IMX500 for fast person detection,
        then applies face detection only within those regions

        Args:
            frame: Image as numpy array (RGB format)
            imx500_detections: List of detections from IMX500 with 'bbox' and 'class_id'

        Returns:
            List of recognition results
        """
        # If no IMX500 detections or not using IMX500, fall back to standard processing
        if not imx500_detections or not self.use_imx500:
            return self.process_frame(frame)

        all_results = []

        # Filter for person detections only
        person_detections = [
            d for d in imx500_detections
            if d.get('class_id') == config.IMX500_PERSON_CLASS_ID
            and d.get('confidence', 0) >= config.IMX500_CONFIDENCE_THRESHOLD
        ]

        if not person_detections:
            # No person detected by IMX500, fall back to full frame detection
            return self.process_frame(frame)

        # Process each person detection region
        for detection in person_detections:
            bbox = detection['bbox']  # [x1, y1, x2, y2]

            # Expand bounding box slightly to ensure full face is included
            x1, y1, x2, y2 = bbox
            h, w = frame.shape[:2]

            # Add 20% padding
            padding = 0.2
            width = x2 - x1
            height = y2 - y1
            x1 = max(0, int(x1 - width * padding))
            y1 = max(0, int(y1 - height * padding))
            x2 = min(w, int(x2 + width * padding))
            y2 = min(h, int(y2 + height * padding))

            # Extract region of interest
            roi = frame[y1:y2, x1:x2]

            if roi.size == 0:
                continue

            # Detect faces within this region
            face_locations_roi = self.detect_faces(roi)

            # Adjust face locations to full frame coordinates
            face_locations = []
            for (top, right, bottom, left) in face_locations_roi:
                face_locations.append((top + y1, right + x1, bottom + y1, left + x1))

            # Recognize faces
            if face_locations:
                results = self.recognize_faces(frame, face_locations)
                all_results.extend(results)

        # If IMX500 detected persons but no faces found, try full frame as fallback
        if not all_results:
            if config.DEBUG_MODE:
                print("IMX500 detected persons but no faces found, trying full frame")
            return self.process_frame(frame)

        return all_results

    def draw_face_boxes(self, frame: np.ndarray, results: List[dict]) -> np.ndarray:
        """
        Draw bounding boxes and labels on detected faces

        Args:
            frame: Image as numpy array (RGB format)
            results: Recognition results from recognize_faces()

        Returns:
            Frame with drawn boxes
        """
        try:
            import cv2

            # Create a copy to avoid modifying original
            output_frame = frame.copy()

            for result in results:
                top, right, bottom, left = result['location']
                name = result['name']
                is_match = result['is_match']

                # Choose color based on match
                if is_match:
                    color = (50, 220, 50)  # Green for authorized
                    label = f"{name}"
                else:
                    color = (220, 50, 50)  # Red for unknown
                    label = "Unknown"

                # Draw rectangle
                cv2.rectangle(output_frame, (left, top), (right, bottom), color, 2)

                # Draw label background
                cv2.rectangle(output_frame, (left, bottom - 25), (right, bottom),
                            color, cv2.FILLED)

                # Draw label text
                cv2.putText(output_frame, label, (left + 6, bottom - 6),
                           cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)

            return output_frame

        except Exception as e:
            print(f"Error drawing face boxes: {e}")
            return frame


# Convenience function
def get_face_recognizer() -> FaceRecognizer:
    """Get a face recognizer instance"""
    return FaceRecognizer()
