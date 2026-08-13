"""
Output directory management and permission handling.
Ensures /output directory exists and is writable.
"""
import os
import sys
import stat
import logging
import tempfile
import errno
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class OutputDirectoryError(Exception):
    """Exception raised when output directory cannot be created or is not writable."""
    pass


class OutputManager:
    """Manages the output directory creation and permission verification."""
    
    def __init__(self, output_path: str = "/output"):
        self.output_path = Path(output_path)
        self.actual_user: Optional[str] = None
        self.actual_group: Optional[str] = None
        
    def ensure_directory_exists(self) -> Path:
        """
        Ensure the output directory exists and is writable.
        
        Returns:
            Path object to the output directory
            
        Raises:
            OutputDirectoryError: If directory cannot be created or is not writable
        """
        logger.info(f"Ensuring output directory exists: {self.output_path}")
        
        try:
            # Create directory if it doesn't exist
            self.output_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Output directory created/exists: {self.output_path}")
            
            # Get current user/group information
            self._get_current_user_info()
            
            # Try to fix permissions if we own the directory
            self._fix_permissions_if_needed()
            
            # Verify directory is writable
            self._verify_writable()
            
            # Test with a temporary file
            self._test_write_access()
            
            logger.info(f"Output directory ready: {self.output_path}")
            return self.output_path
            
        except OSError as e:
            error_msg = f"Cannot create output directory {self.output_path}: {e}"
            logger.error(error_msg)
            raise OutputDirectoryError(error_msg)
    
    def _get_current_user_info(self):
        """Get current user and group information."""
        try:
            import pwd
            import grp
            
            uid = os.getuid()
            gid = os.getgid()
            
            try:
                self.actual_user = pwd.getpwuid(uid).pw_name
            except KeyError:
                self.actual_user = str(uid)
                
            try:
                self.actual_group = grp.getgrgid(gid).gr_name
            except KeyError:
                self.actual_group = str(gid)
                
            logger.debug(f"Running as user: {self.actual_user}, group: {self.actual_group}")
            
        except ImportError:
            # Windows or minimal environment
            self.actual_user = "unknown"
            self.actual_group = "unknown"
    
    def _fix_permissions_if_needed(self):
        """Fix directory permissions if we own the directory."""
        if not self.output_path.exists():
            return
            
        try:
            stat_info = os.stat(self.output_path)
            
            # Check if directory is owned by current user
            if os.getuid() == stat_info.st_uid:
                # We own the directory, ensure proper permissions
                current_mode = stat_info.st_mode
                desired_mode = (current_mode | stat.S_IWUSR | stat.S_IRUSR | stat.S_IXUSR)
                
                # Add group permissions if not world-writable
                if not (current_mode & stat.S_IWOTH):
                    desired_mode = desired_mode | stat.S_IWGRP | stat.S_IRGRP | stat.S_IXGRP
                
                if current_mode != desired_mode:
                    os.chmod(self.output_path, desired_mode)
                    logger.info(f"Fixed directory permissions: {oct(desired_mode)}")
                    
        except OSError as e:
            logger.warning(f"Cannot fix directory permissions: {e}")
    
    def _verify_writable(self):
        """
        Verify that the directory is writable.
        
        Raises:
            OutputDirectoryError: If directory is not writable
        """
        if not os.access(self.output_path, os.W_OK):
            # Try to get detailed permission information
            try:
                stat_info = os.stat(self.output_path)
                mode = stat_info.st_mode
                uid = os.getuid()
                
                error_details = []
                error_details.append(f"Directory: {self.output_path}")
                error_details.append(f"Owner UID: {stat_info.st_uid}, Current UID: {uid}")
                error_details.append(f"Mode: {oct(mode)}")
                
                if uid == stat_info.st_uid:
                    error_details.append("User owns directory but cannot write")
                elif os.getgid() == stat_info.st_gid and (mode & stat.S_IWGRP):
                    error_details.append("Group write permission exists")
                elif mode & stat.S_IWOTH:
                    error_details.append("World write permission exists")
                else:
                    error_details.append("No write permission for user/group/others")
                
                error_msg = "\n".join(error_details)
                logger.error(f"Directory not writable:\n{error_msg}")
                
            except OSError:
                pass
                
            raise OutputDirectoryError(f"Output directory is not writable: {self.output_path}")
    
    def _test_write_access(self):
        """
        Test write access by creating a temporary file.
        
        Raises:
            OutputDirectoryError: If cannot write test file
        """
        test_file = None
        try:
            # Create a temporary test file
            with tempfile.NamedTemporaryFile(
                mode='w',
                dir=self.output_path,
                prefix='write_test_',
                suffix='.txt',
                delete=False
            ) as f:
                test_file = f.name
                f.write("Write test - this file will be deleted\n")
            
            # Verify we can read it back
            with open(test_file, 'r') as f:
                content = f.read()
                if "Write test" not in content:
                    raise OutputDirectoryError("Cannot read back test file content")
            
            # Delete the test file
            os.unlink(test_file)
            logger.debug("Successfully tested write access to output directory")
            
        except (OSError, IOError) as e:
            if test_file and os.path.exists(test_file):
                try:
                    os.unlink(test_file)
                except OSError:
                    pass
                    
            raise OutputDirectoryError(f"Cannot write test file to output directory: {e}")
    
    def get_recommended_systemd_config(self) -> str:
        """
        Generate recommended systemd configuration for the service.
        
        Returns:
            String with systemd service configuration
        """
        return f"""[Unit]
Description=FFmpeg Video Renderer API
After=network.target

[Service]
Type=simple
User={self.actual_user or 'video-renderer'}
Group={self.actual_group or 'video-renderer'}
WorkingDirectory={self.output_path.parent}
ExecStart=/usr/local/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

# Directory and permission settings
ReadWritePaths={self.output_path}
StateDirectory=ffmpeg-api
RuntimeDirectory=ffmpeg-api
RuntimeDirectoryMode=0755

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true

[Install]
WantedBy=multi-user.target
"""
    
    def get_docker_permission_instructions(self) -> str:
        """
        Get Docker permission setup instructions.
        
        Returns:
            String with Docker permission instructions
        """
        return f"""Docker Permission Setup:

1. Volume Mount Permissions:
   - Ensure host directory has correct ownership
   - On host, run: sudo chown 1000:1000 {self.output_path}

2. Docker Compose Configuration:
   environment:
     - PUID=1000
     - PGID=1000
   user: "1000:1000"

3. Docker run command:
   docker run -v {self.output_path}:/output \
     -e PUID=1000 -e PGID=1000 \
     --user 1000:1000 \
     ffmpeg-api

4. Alternative: Use Docker named volumes:
   volumes:
     ffmpeg-output:
       driver: local
       driver_opts:
         type: none
         o: bind
         device: {self.output_path}
"""


def check_output_directory(output_path: str = "/output") -> bool:
    """
    Quick check if output directory exists and is writable.
    
    Args:
        output_path: Path to output directory
        
    Returns:
        True if directory is writable, False otherwise
    """
    try:
        manager = OutputManager(output_path)
        manager.ensure_directory_exists()
        return True
    except OutputDirectoryError:
        return False


def setup_output_directory(output_path: str = "/output") -> Path:
    """
    Setup output directory with proper permissions.
    
    Args:
        output_path: Path to output directory
        
    Returns:
        Path object to the output directory
        
    Raises:
        OutputDirectoryError: If setup fails
    """
    manager = OutputManager(output_path)
    return manager.ensure_directory_exists()
