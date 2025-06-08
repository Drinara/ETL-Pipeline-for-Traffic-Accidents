import os
import sys
import logging
import traceback
import subprocess  # Use subprocess instead of os.system
from pathlib import Path
from datetime import datetime
from send_email import send_email

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("pipeline.log")
    ]
)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent

SCRIPTS = [
    "pipeline_files/01_Data_Cleaning_Traffic_Accidents.py",
    "pipeline_files/02_Data_Storage_Traffic_Accidents.py",
    "ml_modeling/04_ml_predict_injury.py"
]

def run_script(script_path):
    """Execute a pipeline script with proper path handling"""
    try:
        full_path = BASE_DIR / script_path
        logger.info(f"🚀 Running {full_path}")
        
        # Capture start time
        start_time = datetime.now()
        
        # Use subprocess to handle paths with spaces properly
        result = subprocess.run(
            ["python", str(full_path)],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Log script output
        if result.stdout:
            logger.info(f"Output from {script_path}:\n{result.stdout}")
        if result.stderr:
            logger.error(f"Errors from {script_path}:\n{result.stderr}")
        
        # Log execution time
        duration = datetime.now() - start_time
        logger.info(f"✅ {script_path} completed in {duration.total_seconds():.2f} seconds")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Script failed with exit code {e.returncode}")
        logger.error(f"Command: {e.cmd}")
        logger.error(f"Error output:\n{e.stderr}")
        logger.error(f"Standard output:\n{e.stdout}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error running {script_path}: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def main():
    """Main pipeline execution with email notifications"""
    pipeline_start = datetime.now()
    logger.info("⏳ Starting ETL Pipeline")
    
    success = True
    failed_scripts = []
    
    # Execute each script in sequence
    for script in SCRIPTS:
        if not run_script(script):
            success = False
            failed_scripts.append(script)
            break  # Stop pipeline on first failure
    
    # Prepare email notification
    pipeline_duration = datetime.now() - pipeline_start
    status = "SUCCESS" if success else "FAILED"
    subject = f"ETL Pipeline {status}"
    
    # Build email body
    body_lines = [
        "ETL Pipeline Report",
        "===================",
        f"Status: {status}",
        f"Start Time: {pipeline_start.strftime('%Y-%m-%d %H:%M:%S')}",
        f"Duration: {pipeline_duration}"
    ]
    
    if success:
        body_lines.append("\nAll stages completed successfully!")
    else:
        body_lines.append(f"\nPipeline failed at stage: {failed_scripts[0]}")
        body_lines.append(f"Error details available in logs: {BASE_DIR}/pipeline.log")
    
    body_lines.append(f"\nLog Location: {BASE_DIR}/pipeline.log")
    body = "\n".join(body_lines)
    
    # Send notification email
    try:
        email_sent = send_email(subject, body)
        if email_sent:
            logger.info("📧 Status email sent successfully")
        else:
            logger.warning("⚠️ Failed to send status email")
    except Exception as e:
        logger.error(f"⚠️ Email sending failed: {str(e)}")
    
    # Final status
    if success:
        logger.info(f"✅ Pipeline completed successfully in {pipeline_duration.total_seconds():.2f} seconds")
        sys.exit(0)
    else:
        logger.error(f"❌ Pipeline failed after {pipeline_duration.total_seconds():.2f} seconds")
        sys.exit(1)

if __name__ == "__main__":
    main()