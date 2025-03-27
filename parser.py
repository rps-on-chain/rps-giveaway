# Import necessary libraries for CSV handling, regex, and system operations
import csv
import sys
import re
import os
import argparse

def extract_erc_address(text):
    """
    Finds and extracts the first ERC20 cryptocurrency address from text.
    ERC20 addresses follow the pattern: '0x' followed by 40 hexadecimal characters.
    Example: 0x71C7656EC7ab88b098defB751B7401B5f6d8976F
    """
    # Regular expression pattern matching for ERC20 addresses
    match = re.search(r'0x[a-fA-F0-9]{40}', text)
    return match.group(0) if match else None

def process_csv(input_path, output_path):
    """
    Processes Twitter data CSV to filter for unique cryptocurrency addresses.
    Steps:
    1. Reads input CSV with tweet data
    2. Validates required columns exist
    3. Extracts unique addresses from tweets
    4. Writes cleaned data to new CSV
    """
    with open(input_path, 'r', encoding='utf-8-sig') as f:  # Handle BOM if present
        reader = csv.DictReader(f)  # Read as dictionary for column access
        
        # Debug output to help identify column mismatch issues
        print("Detected columns:", reader.fieldnames)
        
        # Ensure CSV contains all required columns for processing
        required_columns = ['ID', 'Name', 'Handle', 'TweetText', 
                          'TweetCreateTime', 'TweetURL']
        missing_columns = [col for col in required_columns 
                         if col not in reader.fieldnames]
        if missing_columns:
            print(f"Error: Missing required columns: {', '.join(missing_columns)}")
            sys.exit(1)
            
        output_rows = []
        # Simplified output columns (exclude long text fields for readability)
        keep_columns = ['ID', 'Handle', 'TweetCreateTime', 'TweetURL']
        
        # Track unique addresses to avoid duplicates
        seen_addresses = set()
        duplicate_count = 0
        
        for row in reader:
            tweet_text = row['TweetText']
            if tweet_text:
                # Attempt to find crypto address in tweet text
                if address := extract_erc_address(tweet_text):
                    # Only add new unique addresses
                    if address not in seen_addresses:
                        seen_addresses.add(address)
                        # Create simplified record with essential info
                        new_entry = {col: row[col] for col in keep_columns}
                        new_entry['Address'] = address
                        output_rows.append(new_entry)
                    else:
                        duplicate_count += 1

    if output_rows:
        # Write results to new CSV file
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keep_columns + ['Address'])
            writer.writeheader()  # Column headers
            writer.writerows(output_rows)  # Actual data
            
        print(f"Successfully wrote {len(output_rows)} records to {output_path}")
        print(f"Unique addresses found: {len(seen_addresses)}")
        print(f"Duplicate addresses skipped: {duplicate_count}")
    else:
        print("No valid ERC20 addresses found in input data")

def main():
    """
    Command line interface setup and execution.
    Handles input/output file paths and starts processing.
    """
    # Configure command line arguments
    parser = argparse.ArgumentParser(
        description='Filter Twitter CSV data for ERC20 addresses'
    )
    parser.add_argument('input_file', help='Path to Twitter data CSV file')
    parser.add_argument('output_file', nargs='?', 
                      help='Optional: Custom output file path')
    
    args = parser.parse_args()
    
    # Set default output filename if not provided
    if not args.output_file:
        base_name = os.path.splitext(args.input_file)[0]
        output_path = f"{base_name}_filtered.csv"
    else:
        output_path = args.output_file
    
    # Start the CSV processing workflow
    process_csv(args.input_file, output_path)

if __name__ == "__main__":
    # This runs when executing the script directly (not when imported)
    main()
