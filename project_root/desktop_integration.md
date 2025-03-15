# Desktop App Integration Guide

This document provides instructions for integrating the proctoring desktop application with the CheatWall admin dashboard.

## Overview

The proctoring desktop application runs on students' computers during tests and collects monitoring data. After a test is completed, the desktop app submits the collected data to the admin portal, where it is displayed on the Completed Tests Dashboard.

## API Endpoints

### Submit Test Results

**Endpoint:** `/api/submit-test-results`
**Method:** `POST`
**Content Type:** `application/json`

This endpoint allows the desktop app to submit completed test session data, including student information, screenshots, and detected risk flags.

#### Request Format

```json
{
    "access_code": "TEST123",
    "student_id": "S12345",
    "end_time": "2023-07-15T15:30:00Z",
    "start_time": "2023-07-15T14:00:00Z",
    "screenshots": [
        {
            "timestamp": "2023-07-15T14:05:00Z",
            "image_link": "https://your-storage.example.com/screenshots/test123_1.jpg",
            "risk_score": 0.1
        },
        {
            "timestamp": "2023-07-15T14:30:00Z",
            "image_link": "https://your-storage.example.com/screenshots/test123_2.jpg",
            "risk_score": 0.8
        }
    ],
    "risk_flags": [
        {
            "type": "multiple_faces",
            "timestamp": "2023-07-15T14:30:00Z",
            "severity": "high",
            "details": "2 faces detected in frame"
        },
        {
            "type": "gaze_direction",
            "timestamp": "2023-07-15T14:45:00Z",
            "severity": "medium",
            "details": "Looking away from screen"
        }
    ]
}
```

**Alternative with Base64 Image Data:**
```json
{
    "access_code": "TEST123",
    "student_id": "S12345",
    "end_time": "2023-07-15T15:30:00Z",
    "start_time": "2023-07-15T14:00:00Z",
    "screenshots": [
        {
            "timestamp": "2023-07-15T14:05:00Z",
            "image_data": "base64_encoded_image_data_here",
            "risk_score": 0.1
        }
    ],
    "risk_flags": [...]
}
```

#### Response Format (Success)

```json
{
    "success": true,
    "message": "Test results submitted successfully",
    "session_id": 123
}
```

#### Response Format (Error)

```json
{
    "success": false,
    "message": "Error message describing what went wrong"
}
```

## Integration Steps

1. **Collect Monitoring Data**: The desktop app should collect screenshots and monitor for suspicious activities during the test.

2. **Calculate Risk Scores**: For each screenshot and detected suspicious activity, assign a risk score between 0.0 (low risk) and 1.0 (high risk).

3. **Store Data Locally**: Save all collected data locally in case of connectivity issues.

4. **Submit Data on Test Completion**:
   - When the test ends, prepare the data payload according to the format above.
   - Submit the data to the admin portal API.
   - Handle any errors and retry if necessary.

5. **Confirmation**: Show a confirmation message to the student when the data has been successfully submitted.

## Risk Flag Types

The system recognizes the following risk flag types:

- `multiple_faces`: Multiple faces detected in the camera feed
- `no_face`: No face detected in the camera feed
- `phone_detected`: Mobile phone or similar device detected
- `looking_away`: Student looking away from the screen
- `unauthorized_process`: Unauthorized application or process running
- `screen_sharing`: Screen sharing or remote access detected
- `audio_anomaly`: Suspicious audio detected
- `browser_navigation`: Unauthorized browser navigation

## Screenshot Guidelines

- Take screenshots at regular intervals (e.g., every 5 minutes)
- Take additional screenshots when suspicious activity is detected
- **Option 1 - Using Screenshot Links (Recommended)**:
  - Upload screenshots to your secure storage (cloud storage, CDN, etc.)
  - Provide the URL/link to the screenshot in the API request
  - Ensure the links are accessible to the admin system but secured from unauthorized access
- **Option 2 - Using Base64 Encoding** (for smaller payloads):
  - Compress and encode screenshots as base64 strings
  - Include the base64 data directly in the API request
  - Consider the payload size limitations of your server
- Include a timestamp and calculated risk score with each screenshot

## Implementation Example

Here's a pseudocode example for submitting test results:

```javascript
async function submitTestResults(testData) {
    try {
        const response = await fetch('https://your-admin-portal.com/api/submit-test-results', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(testData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            console.log('Test results submitted successfully!');
            return true;
        } else {
            console.error('Error submitting test results:', result.message);
            return false;
        }
    } catch (error) {
        console.error('Network error:', error);
        return false;
    }
}
```

## Data Security Considerations

- All sensitive data should be transmitted over HTTPS
- Large payloads may need to be split into smaller chunks
- Consider implementing a retry mechanism for failed submissions
- Store data locally until a successful submission is confirmed

## Testing the Integration

To test the integration:

1. Create a test using the admin portal
2. Use the test access code in the desktop app
3. Complete a mock test session
4. Submit the results using the API
5. Verify the data appears on the Completed Tests Dashboard

For development and testing, you can use sample data with the following access code and student ID:

- Access Code: `TEST123`
- Student ID: `STUDENT123`

## Support

For integration support, please contact our development team:

- Email: support@cheatwall.com
- Documentation: https://docs.cheatwall.com/api 