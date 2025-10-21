# VWAR Scanner - Database Migration Guide
## 2-Device License Support Implementation

---

## Overview

This document provides the complete database migration steps required to support 2-device license activation in VWAR Scanner v2.0.

**Feature:** Each license key can now be activated on up to 2 devices simultaneously.

---

## Database Schema Changes

### New Columns Required

Your database needs two new columns to store the second device's hardware information:

| Column Name | Data Type | Nullable | Default | Description |
|-------------|-----------|----------|---------|-------------|
| `processor_id_2` | VARCHAR(255) | YES | NULL | Processor ID of second device |
| `motherboard_id_2` | VARCHAR(255) | YES | NULL | Motherboard ID of second device |

### Existing Columns (No Changes)

| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| `id` | INT/BIGINT | Primary key |
| `username` | VARCHAR(255) | License owner username |
| `password` | VARCHAR(255) | License key |
| `processor_id` | VARCHAR(255) | Processor ID of first device |
| `motherboard_id` | VARCHAR(255) | Motherboard ID of first device |
| `valid_till` | DATETIME | License expiration date |
| `created_at` | DATETIME | License creation date |

---

## SQL Migration Scripts

### Option 1: MySQL / MariaDB

```sql
-- Add new columns for second device
ALTER TABLE `licenses` 
ADD COLUMN `processor_id_2` VARCHAR(255) NULL DEFAULT NULL AFTER `motherboard_id`,
ADD COLUMN `motherboard_id_2` VARCHAR(255) NULL DEFAULT NULL AFTER `processor_id_2`;

-- Verify columns were added
DESCRIBE `licenses`;
```

**Expected Output:**
```
+-------------------+--------------+------+-----+---------+
| Field             | Type         | Null | Key | Default |
+-------------------+--------------+------+-----+---------+
| processor_id      | varchar(255) | YES  |     | NULL    |
| motherboard_id    | varchar(255) | YES  |     | NULL    |
| processor_id_2    | varchar(255) | YES  |     | NULL    |
| motherboard_id_2  | varchar(255) | YES  |     | NULL    |
+-------------------+--------------+------+-----+---------+
```

---

### Option 2: PostgreSQL

```sql
-- Add new columns for second device
ALTER TABLE licenses 
ADD COLUMN processor_id_2 VARCHAR(255) DEFAULT NULL,
ADD COLUMN motherboard_id_2 VARCHAR(255) DEFAULT NULL;

-- Verify columns were added
\d licenses;
```

---

### Option 3: SQLite

```sql
-- Add new columns for second device
ALTER TABLE licenses ADD COLUMN processor_id_2 TEXT;
ALTER TABLE licenses ADD COLUMN motherboard_id_2 TEXT;

-- Verify columns were added
PRAGMA table_info(licenses);
```

---

### Option 4: Microsoft SQL Server

```sql
-- Add new columns for second device
ALTER TABLE licenses 
ADD processor_id_2 NVARCHAR(255) NULL,
    motherboard_id_2 NVARCHAR(255) NULL;

-- Verify columns were added
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'licenses';
```

---

## Complete Table Structure After Migration

```
licenses
├── id (Primary Key)
├── username
├── password (License Key)
├── processor_id         ← Device 1 - Processor ID
├── motherboard_id       ← Device 1 - Motherboard ID
├── processor_id_2       ← Device 2 - Processor ID (NEW!)
├── motherboard_id_2     ← Device 2 - Motherboard ID (NEW!)
├── valid_till
├── created_at
└── [other columns...]
```

---

## PHP Backend Updates Required

### 1. Update API Endpoint (postAPI.php)

Your PHP backend must handle the `slot` parameter sent by the client:

```php
<?php
header('Content-Type: application/json');

// Get POST data
$data = json_decode(file_get_contents('php://input'), true);

$license_id = $data['id'];
$slot = isset($data['slot']) ? intval($data['slot']) : 1; // Default to slot 1
$processor_id = $data['processor_id'];
$motherboard_id = $data['motherboard_id'];

// Connect to database
$conn = new mysqli($servername, $username, $password, $dbname);

if ($conn->connect_error) {
    die(json_encode(['status' => 'error', 'message' => 'Database connection failed']));
}

// Update the correct device slot based on parameter
if ($slot == 2) {
    // Bind to Device 2 slot
    $sql = "UPDATE licenses 
            SET processor_id_2 = ?, motherboard_id_2 = ? 
            WHERE id = ?";
} else {
    // Bind to Device 1 slot (default)
    $sql = "UPDATE licenses 
            SET processor_id = ?, motherboard_id = ? 
            WHERE id = ?";
}

$stmt = $conn->prepare($sql);
$stmt->bind_param("ssi", $processor_id, $motherboard_id, $license_id);

if ($stmt->execute()) {
    echo json_encode([
        'status' => 'success',
        'message' => "Device bound to slot $slot successfully",
        'slot' => $slot
    ]);
} else {
    echo json_encode([
        'status' => 'error',
        'message' => 'Failed to bind device: ' . $stmt->error
    ]);
}

$stmt->close();
$conn->close();
?>
```

---

### 2. Update GET API (getAPI.php)

Ensure your GET endpoint returns the new columns:

```php
<?php
header('Content-Type: application/json');

// Connect to database
$conn = new mysqli($servername, $username, $password, $dbname);

if ($conn->connect_error) {
    die(json_encode(['status' => 'error', 'message' => 'Database connection failed']));
}

// Fetch all license data including new device 2 fields
$sql = "SELECT id, username, password, 
               processor_id, motherboard_id, 
               processor_id_2, motherboard_id_2, 
               valid_till, created_at 
        FROM licenses";

$result = $conn->query($sql);

$licenses = array();
if ($result->num_rows > 0) {
    while($row = $result->fetch_assoc()) {
        $licenses[] = $row;
    }
}

echo json_encode([
    'status' => 'success',
    'data' => $licenses
]);

$conn->close();
?>
```

---

## Client-Side Code Reference

The VWAR Scanner client automatically handles the 2-device logic:

### During Activation (activation/gui.py)

```python
# Client determines available slot automatically
target_slot = None
if not device1_cpu or not device1_mobo:
    target_slot = 1  # Device 1 slot is empty
elif not device2_cpu or not device2_mobo:
    target_slot = 2  # Device 2 slot is empty
else:
    # Both slots occupied - show error
    messagebox.showerror("Device Limit Reached", 
                        "This license key is already activated on 2 devices.")

# Send activation request with slot parameter
bind_payload = {
    "id": found["id"],
    "slot": target_slot,      # 1 or 2
    "processor_id": current_cpu,
    "motherboard_id": current_mobo
}

response = requests.post(API_POST, json=bind_payload)
```

### During Validation (activation/license_utils.py)

```python
# Client checks both device slots during validation
device1_cpu = found.get("processor_id")
device1_mobo = found.get("motherboard_id")
device2_cpu = found.get("processor_id_2")
device2_mobo = found.get("motherboard_id_2")

# Check if current device matches either slot
is_device1 = (current_cpu == device1_cpu and current_mobo == device1_mobo)
is_device2 = (current_cpu == device2_cpu and current_mobo == device2_mobo)

if not (is_device1 or is_device2):
    return False, "Device no longer authorized."
```

---

## Testing Procedure

### Step 1: Verify Database Migration

```sql
-- Check if new columns exist
SELECT processor_id, motherboard_id, processor_id_2, motherboard_id_2 
FROM licenses 
LIMIT 1;

-- Should return NULL values for processor_id_2 and motherboard_id_2 initially
```

### Step 2: Test API Endpoints

**Test GET API:**
```bash
curl -X GET https://your-api-url/getAPI.php
```

Expected response should include `processor_id_2` and `motherboard_id_2` fields:
```json
{
  "status": "success",
  "data": [
    {
      "id": "1",
      "processor_id": "ABC123",
      "motherboard_id": "DEF456",
      "processor_id_2": null,
      "motherboard_id_2": null
    }
  ]
}
```

**Test POST API (Slot 2):**
```bash
curl -X POST https://your-api-url/postAPI.php \
  -H "Content-Type: application/json" \
  -d '{
    "id": 1,
    "slot": 2,
    "processor_id": "XYZ789",
    "motherboard_id": "UVW012"
  }'
```

Expected response:
```json
{
  "status": "success",
  "message": "Device bound to slot 2 successfully",
  "slot": 2
}
```

### Step 3: Test Client Activation

1. **First Device:**
   - Run VWAR Scanner on Device A
   - Activate with license key
   - Should bind to slot 1

2. **Second Device:**
   - Run VWAR Scanner on Device B (different computer)
   - Activate with same license key
   - Should bind to slot 2

3. **Third Device (Should Fail):**
   - Run VWAR Scanner on Device C
   - Try to activate with same license key
   - Should show: "Device Limit Reached - This license key is already activated on 2 devices"

---

## Database Query Examples

### Check License Usage

```sql
-- Show all licenses with device occupation status
SELECT 
    id,
    password AS license_key,
    CASE 
        WHEN processor_id IS NOT NULL THEN 'Occupied'
        ELSE 'Empty'
    END AS device_1_status,
    CASE 
        WHEN processor_id_2 IS NOT NULL THEN 'Occupied'
        ELSE 'Empty'
    END AS device_2_status,
    valid_till
FROM licenses;
```

### Find Fully Occupied Licenses

```sql
-- Find licenses with both device slots occupied
SELECT 
    id,
    password AS license_key,
    processor_id AS device1_cpu,
    processor_id_2 AS device2_cpu,
    valid_till
FROM licenses
WHERE processor_id IS NOT NULL 
  AND processor_id_2 IS NOT NULL;
```

### Clear Device Slot (Deactivation)

```sql
-- Clear Device 1
UPDATE licenses 
SET processor_id = NULL, motherboard_id = NULL 
WHERE id = ?;

-- Clear Device 2
UPDATE licenses 
SET processor_id_2 = NULL, motherboard_id_2 = NULL 
WHERE id = ?;
```

---

## Rollback Procedure (If Needed)

If you need to revert the database changes:

### MySQL / MariaDB
```sql
ALTER TABLE `licenses` 
DROP COLUMN `processor_id_2`,
DROP COLUMN `motherboard_id_2`;
```

### PostgreSQL
```sql
ALTER TABLE licenses 
DROP COLUMN processor_id_2,
DROP COLUMN motherboard_id_2;
```

### SQLite
```sql
-- SQLite doesn't support DROP COLUMN directly
-- You need to recreate the table without these columns
-- (See SQLite documentation for table recreation steps)
```

---

## Migration Checklist

- [ ] **Backup Database** - Create full backup before migration
- [ ] **Add Columns** - Execute ALTER TABLE statements
- [ ] **Verify Schema** - Confirm new columns exist
- [ ] **Update PHP GET API** - Include new columns in SELECT query
- [ ] **Update PHP POST API** - Handle `slot` parameter
- [ ] **Test GET API** - Verify new columns returned in response
- [ ] **Test POST API** - Test slot 1 and slot 2 binding
- [ ] **Test Client** - Activate on 2 devices
- [ ] **Test Limit** - Verify 3rd device shows error
- [ ] **Monitor Logs** - Check for errors after deployment
- [ ] **Update Documentation** - Document new API parameters

---

## Troubleshooting

### Issue: Columns not showing in API response

**Solution:** Update your SELECT query to include the new columns:
```php
$sql = "SELECT id, username, password, 
               processor_id, motherboard_id, 
               processor_id_2, motherboard_id_2,  // Add these
               valid_till, created_at 
        FROM licenses";
```

### Issue: Client shows "Device no longer authorized"

**Cause:** Database columns exist but API is not returning them.

**Solution:** Verify GET API returns `processor_id_2` and `motherboard_id_2` fields.

### Issue: Slot parameter ignored by server

**Cause:** PHP not reading `slot` from JSON body.

**Solution:** Use `json_decode(file_get_contents('php://input'), true)` instead of `$_POST`.

---

## API Contract Specification

### POST /postAPI.php

**Request Body:**
```json
{
  "id": 123,
  "slot": 2,
  "processor_id": "ABC123XYZ",
  "motherboard_id": "DEF456UVW"
}
```

**Parameters:**
- `id` (required, integer) - License ID
- `slot` (optional, integer) - Device slot (1 or 2, default: 1)
- `processor_id` (required, string) - Processor hardware ID
- `motherboard_id` (required, string) - Motherboard hardware ID

**Response (Success):**
```json
{
  "status": "success",
  "message": "Device bound to slot 2 successfully",
  "slot": 2
}
```

**Response (Error):**
```json
{
  "status": "error",
  "message": "Failed to bind device: [error details]"
}
```

---

## Security Considerations

1. **Validate Input:** Always validate and sanitize the `slot` parameter
   ```php
   $slot = isset($data['slot']) ? intval($data['slot']) : 1;
   if ($slot < 1 || $slot > 2) {
       $slot = 1; // Force valid range
   }
   ```

2. **Use Prepared Statements:** Prevent SQL injection
   ```php
   $stmt = $conn->prepare($sql);
   $stmt->bind_param("ssi", $processor_id, $motherboard_id, $license_id);
   ```

3. **Verify License Ownership:** Ensure the license ID belongs to the requesting user

4. **Rate Limiting:** Implement rate limiting to prevent brute force attacks

---

## Support & Contact

**For Technical Support:**
- Website: https://bitss.one/contact
- GitHub: https://github.com/TM-Mehrab-Hasan/BITSS-VWAR-Software

**Version Information:**
- VWAR Scanner Version: 2.0
- Feature: 2-Device License Support
- Migration Date: October 21, 2025

---

## Document Version

**Version:** 1.0  
**Last Updated:** October 21, 2025  
**Author:** VWAR Development Team  
**Status:** Production Ready

---

**END OF DOCUMENT**
