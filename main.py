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
    parser = argparse.ArgumentParser(description='Normalizes generic location type words by default (Street, Ave, Road, Rd, Blvd become Road; City, Town become Region). Specific names such as street names and city names are replaced only when they are supplied in a custom mappings file (--mappings).')
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
    # A custom file replaces the defaults outright, it does not extend
    # them: supply one pair and the Street to Road and City to Region
    # normalization is gone from the run unless the file repeats it.

    import json  # Import here to avoid unnecessary import if not used
    try:
        with open(mappings_file, 'r') as f:
            mappings = json.load(f)
        return mappings
    except FileNotFoundError:
        logging.error(f"Mappings file not found: {mappings_file}")
        sys.exit(1)
    except json.JSONDecodeError:
        logging.error(f"Invalid JSON format in mappings file: {mappings_file}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error loading mappings: {e}")
        sys.exit(1)



def replace_location_names(text, location_mappings):
    """
    Replaces location names in the text with broader categories using regex.
    """
    total = 0
    try:
        # Patterns apply in the order the mapping gives them, each over
        # the output of the ones before, so replacement text is itself
        # fair game for a later pattern: a custom pair that maps City to
        # Town and Town to Region lands City at Region in one pass. The
        # defaults are safe from that only because Road and Region appear
        # in no later left hand side. Matching is case insensitive but the
        # replacement is written exactly as configured, so STREET and
        # street both come out as the one cased word Road.
        for pattern, replacement in location_mappings.items():
            text, count = re.subn(pattern, replacement, text, flags=re.IGNORECASE)
            total += count
        return text, total
    except Exception as e:
        logging.error(f"Error replacing location names: {e}")
        # On error the partially worked text is returned with a count of
        # zero, whatever earlier patterns already changed in it. The
        # caller reads zero as nothing replaced and writes no output, so
        # one bad pattern in a custom file, which is never named in the
        # log, discards the whole run rather than just its own matches.
        return text, 0  # Return original text in case of error

def process_file(input_file, output_file, location_mappings):
    """
    Reads the input file, replaces location names, and writes to the output file.
    """
    try:
        encoding = detect_encoding(input_file)
        # Read the whole input before any output is opened, so an output
        # path that reaches the input can never truncate it mid read.
        with open(input_file, 'r', encoding=encoding) as infile:
            lines = infile.readlines()
        total = 0
        sanitized_lines = []
        for line in lines:
            sanitized_line, count = replace_location_names(line, location_mappings)
            total += count
            sanitized_lines.append(sanitized_line)
        if total == 0:
            logging.error(f"Nothing was replaced in file: {input_file}; no output written.")
            return False
        with open(output_file, 'w', encoding=encoding) as outfile:
            outfile.writelines(sanitized_lines)
        logging.info(f"Successfully processed file: {input_file} and saved to: {output_file} ({total} replacement(s))")
        return True

    except FileNotFoundError:
        logging.error(f"Input file not found: {input_file}")
        return False
    except Exception as e:
        logging.error(f"Error processing file: {e}")
        return False


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

    # Refuse in place runs: the output must not resolve to the input file.
    if os.path.realpath(args.input_file) == os.path.realpath(args.output_file):
        logging.error("Output file must differ from the input file; refusing to overwrite the input.")
        sys.exit(1)

    # Load location mappings
    location_mappings = load_location_mappings(args.mappings)

    # Process the file
    if not process_file(args.input_file, args.output_file, location_mappings):
        sys.exit(1)


if __name__ == "__main__":
    main()


# Usage Examples:
# 1.  Basic usage:  Normalize generic location type words in input.txt and save to output.txt
#     python main.py input.txt output.txt

# 2.  Using a custom mappings file:
#     python main.py input.txt output.txt --mappings custom_mappings.json

# 3.  Setting the log level to DEBUG:
#     python main.py input.txt output.txt --log_level DEBUG