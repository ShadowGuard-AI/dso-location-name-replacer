import argparse
import logging
import os
import sys
import re
import chardet  # Added as per dependencies
from faker import Faker  # Added as per dependencies

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define default location name mappings.  Can be extended or overridden.
DEFAULT_LOCATION_MAPPINGS = {
    r'\b(Street|Ave|Road|Rd|Blvd)\b': 'Road',
    r'\b(City|Town)\b': 'Region',
    # Add more mappings as needed
}


def setup_argparse():
    """
    Sets up the argument parser for the command-line interface.
    """
    parser = argparse.ArgumentParser(description='Replaces specific location names with broader geographical categories.')
    parser.add_argument('input_file', type=str, help='Path to the input file.')
    parser.add_argument('output_file', type=str, help='Path to the output file.')
    parser.add_argument('--mappings', type=str, help='Path to a custom location mappings file (JSON format).', default=None)  # Allow custom mappings
    parser.add_argument('--log_level', type=str, default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Set the logging level (default: INFO)')
    return parser

def detect_encoding(file_path):
    """
    Detects the encoding of a file.
    """
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read()
        result = chardet.detect(raw_data)
        return result['encoding']
    except Exception as e:
        logging.error(f"Error detecting encoding: {e}")
        return 'utf-8'  # Default to utf-8 if detection fails


def load_location_mappings(mappings_file):
    """
    Loads location mappings from a file.
    """
    if mappings_file is None:
        return DEFAULT_LOCATION_MAPPINGS  # Use default mappings if no file specified
    
    import json  # Import here to avoid unnecessary import if not used
    try:
        with open(mappings_file, 'r') as f:
            mappings = json.load(f)
        return mappings
    except FileNotFoundError:
        logging.error(f"Mappings file not found: {mappings_file}")
        return DEFAULT_LOCATION_MAPPINGS
    except json.JSONDecodeError:
        logging.error(f"Invalid JSON format in mappings file: {mappings_file}")
        return DEFAULT_LOCATION_MAPPINGS
    except Exception as e:
        logging.error(f"Error loading mappings: {e}")
        return DEFAULT_LOCATION_MAPPINGS



def replace_location_names(text, location_mappings):
    """
    Replaces location names in the text with broader categories using regex.
    """
    try:
        for pattern, replacement in location_mappings.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        return text
    except Exception as e:
        logging.error(f"Error replacing location names: {e}")
        return text  # Return original text in case of error

def process_file(input_file, output_file, location_mappings):
    """
    Reads the input file, replaces location names, and writes to the output file.
    """
    try:
        encoding = detect_encoding(input_file)
        with open(input_file, 'r', encoding=encoding) as infile, open(output_file, 'w', encoding=encoding) as outfile:
            for line in infile:
                sanitized_line = replace_location_names(line, location_mappings)
                outfile.write(sanitized_line)
        logging.info(f"Successfully processed file: {input_file} and saved to: {output_file}")

    except FileNotFoundError:
        logging.error(f"Input file not found: {input_file}")
    except Exception as e:
        logging.error(f"Error processing file: {e}")


def main():
    """
    Main function to parse arguments and process the file.
    """
    parser = setup_argparse()
    args = parser.parse_args()

    # Set logging level
    logging.getLogger().setLevel(args.log_level.upper())

    # Input validation
    if not os.path.isfile(args.input_file):
        logging.error(f"Input file does not exist: {args.input_file}")
        sys.exit(1)  # Exit with an error code

    # Load location mappings
    location_mappings = load_location_mappings(args.mappings)

    # Process the file
    process_file(args.input_file, args.output_file, location_mappings)


if __name__ == "__main__":
    main()


# Usage Examples:
# 1.  Basic usage:  Replace default location names in input.txt and save to output.txt
#     python main.py input.txt output.txt

# 2.  Using a custom mappings file:
#     python main.py input.txt output.txt --mappings custom_mappings.json

# 3.  Setting the log level to DEBUG:
#     python main.py input.txt output.txt --log_level DEBUG