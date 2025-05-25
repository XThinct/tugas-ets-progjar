# file_generator.py
import os
import random
import logging
from glob import glob

class FileGenerator:
    @staticmethod
    def generate_file(filename, size_mb):
        """Generate a random file of specified size in MB"""
        size = size_mb * 1024 * 1024  
        chunk_size = 1024 * 1024  
        chunks = size // chunk_size
        remainder = size % chunk_size
        
        try:
            with open(filename, 'wb') as f:
                for _ in range(chunks):
                    data = bytes([random.randint(0, 255) for _ in range(chunk_size)])
                    f.write(data)
                if remainder:
                    data = bytes([random.randint(0, 255) for _ in range(remainder)])
                    f.write(data)
            
            logging.info(f"Successfully generated file: {filename} ({size_mb}MB)")
            return True
        except Exception as e:
            logging.error(f"Error generating file {filename}: {str(e)}")
            return False

    @staticmethod
    def generate_test_files(directory="files"):
        """Generate standard test files for stress testing"""
        test_files = {
            'test_1mb': 1,
            'test_10mb': 10,
            'test_50mb': 50,
            'test_100mb': 100
        }
        os.makedirs(directory, exist_ok=True)
        
        for name, size in test_files.items():
            filename = os.path.join(directory, f"{name}.dat")
            if not os.path.exists(filename):
                logging.info(f"Generating test file: {filename}")
                FileGenerator.generate_file(filename, size)
            else:
                actual_size = os.path.getsize(filename) / (1024 * 1024)
                if abs(actual_size - size) > 0.1: 
                    logging.warning(f"Existing file {filename} has wrong size ({actual_size}MB), regenerating...")
                    FileGenerator.generate_file(filename, size)
                else:
                    logging.info(f"Test file already exists with correct size: {filename}")

    @staticmethod
    def cleanup_test_files(directory=""):
        """Remove all generated test files"""
        try:
            for filename in glob(os.path.join(directory, "*.dat")):
                os.remove(filename)
                logging.info(f"Removed test file: {filename}")
            return True
        except Exception as e:
            logging.error(f"Error cleaning up test files: {str(e)}")
            return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    FileGenerator.generate_test_files()