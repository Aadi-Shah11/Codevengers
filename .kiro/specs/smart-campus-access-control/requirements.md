# Requirements Document

## Introduction

The Smart Campus Access Control system is a comprehensive security solution designed for educational institutions to manage and monitor campus entry points. The system combines ID verification and vehicle recognition capabilities to provide real-time access control decisions. It consists of three main components: a Flutter mobile app for watchmen, a Python FastAPI backend with OCR capabilities, and a web dashboard for higher authorities. The system is designed to be demo-ready for hackathon presentation with clean, user-friendly interfaces and functional prototypes.

## Requirements

### Requirement 1

**User Story:** As a watchman, I want to verify student/staff IDs at the gate, so that I can grant or deny access based on institutional records.

#### Acceptance Criteria

1. WHEN the watchman opens the mobile app THEN the system SHALL display a clean interface with a scan button
2. WHEN the watchman taps the scan button THEN the system SHALL allow QR/barcode scanning or manual ID input
3. WHEN an ID is scanned or entered THEN the system SHALL verify it against the MySQL database within 2 seconds
4. IF the ID exists in the database THEN the system SHALL display "Access Granted" with green indicator
5. IF the ID does not exist in the database THEN the system SHALL display "Unauthorized" with red indicator and trigger an alert
6. WHEN an unauthorized attempt occurs THEN the system SHALL log the attempt with timestamp and ID details

### Requirement 2

**User Story:** As a higher authority, I want to receive real-time alerts about unauthorized access attempts, so that I can take immediate security action.

#### Acceptance Criteria

1. WHEN an unauthorized ID or vehicle is detected THEN the system SHALL send an immediate notification to the authority dashboard
2. WHEN authorities access the dashboard THEN the system SHALL display all recent alerts with timestamps and details
3. WHEN an alert is generated THEN the system SHALL include ID/vehicle information, timestamp, and access decision
4. IF multiple unauthorized attempts occur THEN the system SHALL maintain a chronological log of all incidents

### Requirement 3

**User Story:** As a student/staff member, I want to register my vehicle in the system, so that I can gain authorized access through the campus gates.

#### Acceptance Criteria

1. WHEN a user accesses the registration interface THEN the system SHALL provide a form to input vehicle details
2. WHEN vehicle registration is submitted THEN the system SHALL store license plate, owner ID, and vehicle type in MySQL database
3. WHEN registration is complete THEN the system SHALL confirm successful registration to the user
4. IF duplicate license plates are entered THEN the system SHALL prevent registration and show appropriate error message

### Requirement 4

**User Story:** As a security system, I want to automatically recognize vehicle license plates from video feeds, so that I can verify vehicle authorization without manual intervention.

#### Acceptance Criteria

1. WHEN a vehicle video is uploaded to the system THEN the backend SHALL process it using OpenCV and OCR within 5 seconds
2. WHEN license plate text is extracted THEN the system SHALL match it against the vehicle registry database
3. IF the license plate exists in the database THEN the system SHALL return "Vehicle Authorized" status
4. IF the license plate does not exist THEN the system SHALL return "Unauthorized Vehicle" and forward alert to authorities
5. WHEN OCR processing fails THEN the system SHALL return an appropriate error message

### Requirement 5

**User Story:** As a higher authority, I want to upload vehicle videos and view verification results through a web dashboard, so that I can monitor vehicle access remotely.

#### Acceptance Criteria

1. WHEN authorities access the web dashboard THEN the system SHALL display two main sections: video upload and logs
2. WHEN a video file is uploaded THEN the system SHALL show upload progress and processing status
3. WHEN video processing is complete THEN the system SHALL display detected license plate and verification result
4. WHEN viewing logs THEN the system SHALL show chronological list of all access attempts with filtering options
5. IF video upload fails THEN the system SHALL display clear error message and retry option

### Requirement 6

**User Story:** As the access control system, I want to implement decision logic that grants access when either ID or vehicle is valid, so that authorized personnel can enter through multiple verification methods.

#### Acceptance Criteria

1. WHEN both ID and vehicle verification are performed THEN the system SHALL grant access if either verification passes
2. WHEN only ID verification is available THEN the system SHALL make access decision based solely on ID status
3. WHEN only vehicle verification is available THEN the system SHALL make access decision based solely on vehicle status
4. WHEN both verifications fail THEN the system SHALL deny access and trigger security alert
5. WHEN access is granted through either method THEN the system SHALL log the successful entry with method used

### Requirement 7

**User Story:** As a system administrator, I want the system to maintain comprehensive logs of all access attempts, so that I can review security incidents and generate reports.

#### Acceptance Criteria

1. WHEN any access attempt occurs THEN the system SHALL log timestamp, ID/vehicle details, verification method, and result
2. WHEN logs are requested THEN the system SHALL return data in chronological order with filtering capabilities
3. WHEN the system starts THEN it SHALL be pre-populated with 10 mock student/staff IDs and 10 vehicle records
4. IF database connection fails THEN the system SHALL handle errors gracefully and maintain local logging
5. WHEN logs exceed storage limits THEN the system SHALL implement appropriate data retention policies

### Requirement 8

**User Story:** As a developer, I want the system to have clean, modular architecture with REST APIs, so that components can be easily integrated and maintained.

#### Acceptance Criteria

1. WHEN the backend is deployed THEN it SHALL expose REST endpoints: /verify_id, /upload_video, and /logs
2. WHEN API requests are made THEN the system SHALL return responses in consistent JSON format within 3 seconds
3. WHEN the Flutter app makes requests THEN it SHALL handle network errors gracefully with user-friendly messages
4. IF API endpoints are unavailable THEN the mobile app SHALL display appropriate offline indicators
5. WHEN the system is demonstrated THEN all components SHALL work together seamlessly for hackathon presentation