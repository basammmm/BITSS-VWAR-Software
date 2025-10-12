# Drag & Drop Scanning Guide

## Feature Overview
VWAR Scanner now supports drag-and-drop functionality for quick file and folder scanning directly from Windows Explorer.

## How to Use

### Single File/Folder
1. Open VWAR Scanner and navigate to the **Scanning** page
2. Locate the green drop zone labeled **"📁 Drag & Drop Files or Folders Here"**
3. Drag any file or folder from Windows Explorer
4. Drop it onto the green zone
5. The scan will **automatically start** immediately
6. Progress will be shown in the progress bar below

### Multiple Files/Folders
- Drop multiple items at once
- Each item will be scanned sequentially
- Results appear in the "MATCHED FILES" and "TESTED FILES" sections

### Visual Feedback
- **Turquoise (#1ABC9C)**: Ready to accept drop
- **Green (#27AE60)**: File/folder received, scan starting
- Filename displayed in drop zone after successful drop

## Technical Details

### Implementation
- Uses `tkinterdnd2` library for cross-platform drag-and-drop support
- Automatically detects file vs folder and handles accordingly
- Integrates with existing YARA scanning engine
- Supports Windows file path formats (including UNC paths)

### File Types
- All file types supported by YARA rules
- No size restrictions (follows existing scan logic)
- Respects user-defined exclusions from settings

### Error Handling
- Invalid paths are filtered out automatically
- Error messages logged to the Load Log box
- Failed drops revert drop zone to ready state

## Requirements
- Python package: `tkinterdnd2==0.3.0` (included in requirements.txt)
- Windows 10/11 with File Explorer drag support
- Administrator privileges (same as main app)

## Known Limitations
- Multiple items scanned sequentially (not parallel)
- Brief 0.5s delay between multi-item scans
- Drop zone must be visible (cannot drag to minimized app)

## Troubleshooting

### Drop not working
1. Ensure VWAR is running with administrator privileges
2. Check that `tkinterdnd2` is installed: `pip list | findstr tkinterdnd2`
3. Restart the application after installation

### Files not scanning
- Check the Load Log box for error messages
- Verify file path is valid and accessible
- Ensure file is not in exclusion list (Settings → Manage Exclusions)

### Performance
- Large folders may take time to scan recursively
- Use the "Stop" button to cancel long-running scans
- Monitor progress in the progress bar

## Benefits
- **Faster workflow**: Skip file/folder selection dialogs
- **Intuitive**: Familiar Windows drag-and-drop interaction
- **Batch scanning**: Drop multiple items at once
- **Visual feedback**: Clear indication of scan status
- **Auto-start**: No need to click "Scan" button

## Future Enhancements
- Parallel scanning for multiple dropped items
- Visual drop indicators (hover effects)
- Drag from other sources (email attachments, web browsers)
- Progress indicator per-file for batch drops
