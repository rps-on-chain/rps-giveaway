# This script verifies which cryptocurrency addresses received their first 
# transaction (funding) on Arbitrum network. Used to validate giveaway eligibility.

# Imported libraries breakdown:
# - argparse: Handles command-line arguments for input/output files
# - aiohttp: Enables fast asynchronous HTTP requests to blockchain node
# - asyncio: Manages concurrency for high-performance address checking
# - csv: Reads input addresses and writes validated results
# - datetime: Converts blockchain timestamps to human-readable format
# - dotenv: Loads environment variables from .env file
import argparse
import aiohttp
import asyncio
import csv
import json
from datetime import datetime
import os
from dotenv import load_dotenv

async def get_funding(session, semaphore, row, api_key):
    """Checks if an address received initial funding through Alchemy's blockchain API.
    
    Uses semaphore to prevent overwhelming the API with too many concurrent requests.
    Processes one address at a time with error handling for reliability."""
    
    async with semaphore:  # Limits concurrent requests (max 50 at once)
        try:
            # API request payload formatted for Alchemy's specific JSON-RPC requirements
            payload = json.dumps({
                "id": 1,
                "jsonrpc": "2.0",
                "method": "alchemy_getAssetTransfers",
                "params": [{
                    "toAddress": row['Address'],  # The cryptocurrency address to check
                    "category": ["external"],     # Only look at external transactions (not internal)
                    "order": "asc",               # Get earliest transaction first
                    "maxCount": "0x1",            # Only need the first transaction
                    "withMetadata": True          # Include block timestamp information
                }]
            })

            # Send the API request using our connection pool
            async with session.post(
                f"https://arb-mainnet.g.alchemy.com/v2/{api_key}",
                data=payload,
                headers={'Content-Type': 'application/json'}
            ) as response:
                data = await response.json()
                
                # Successful response will contain 'result' with transfer data
                if 'result' in data and data['result']['transfers']:
                    transfer = data['result']['transfers'][0]  # Get first transaction
                    
                    # Convert blockchain timestamp to Unix format for easier analysis
                    timestamp = int(datetime.fromisoformat(
                        transfer['metadata']['blockTimestamp'].replace('Z', '+00:00')
                    ).timestamp())
                    
                    # Return enriched address data with funding details
                    return {
                        **row,  # Preserve original data
                        'funded': True,
                        'firstTxHash': transfer['hash'],  # Transaction ID on blockchain
                        'funder': transfer['from'],       # Address that sent funds
                        'timestamp': timestamp,           # When funding occurred
                        'block': int(transfer['blockNum'], 16)  # Blockchain block number
                    }
                # Add rate limit cushion (50ms delay after each successful call)
                # Insurance against rate limits, more info https://docs.alchemy.com/reference/throughput
                await asyncio.sleep(0.05)
                return {**row, 'funded': False}
        except Exception as e:
            print(f"Error processing address {row['Address']}: {e}")
            # Safely handle any API errors by marking as unfunded
            return {**row, 'funded': False}

async def main():
    """Orchestrates the validation process with progress tracking and result output."""
    load_dotenv()  # Load environment variables from .env file
    
    # Configure command-line interface
    parser = argparse.ArgumentParser(description='Validate giveaway participants')
    parser.add_argument('input_file', help='CSV containing participant addresses')
    parser.add_argument('output_file', nargs='?', 
                       help='Optional output path for results (default: input_funded.csv)')
    args = parser.parse_args()

    # Read all addresses at once for batch processing
    with open(args.input_file, 'r') as f:
        reader = csv.DictReader(f)
        original_fields = reader.fieldnames  # Preserve original CSV structure
        rows = list(reader)  # Load all data into memory for parallel processing

    # Get API key from environment variables for security
    api_key = os.getenv('ALCHEMY_API_KEY')
    
    # Create concurrency limiter (20 concurrent requests max)
    semaphore = asyncio.Semaphore(20)
    
    print(f"Starting validation for {len(rows)} addresses...")
    
    # Create HTTP session with connection pooling
    async with aiohttp.ClientSession() as session:
        # Create all validation tasks up front
        tasks = [get_funding(session, semaphore, row, api_key) for row in rows]
        
        # Progress tracking setup
        completed = 0
        start_time = asyncio.get_event_loop().time()
        results = []
        
        # Process results as they complete (out-of-order OK)
        for future in asyncio.as_completed(tasks):
            result = await future
            results.append(result)
            completed += 1
            
            # Progress updates every 100 addresses
            if completed % 100 == 0 or completed == len(rows):
                elapsed = asyncio.get_event_loop().time() - start_time
                req_per_sec = completed / elapsed if elapsed > 0 else 0
                print(f"Processed {completed}/{len(rows)} addresses "
                      f"({req_per_sec:.1f}/sec)")

    # Filter and analyze results
    funded = [result for result in results if result['funded']]
    print(f"Found {len(funded)} funded addresses ({len(funded)/len(rows):.1%})")
    
    # Output structure adds blockchain transaction ID to original data
    fieldnames = original_fields + ['firstTxHash']
    
    # Generate output path: input_funded.csv if none specified
    output_path = args.output_file or f"{os.path.splitext(args.input_file)[0]}_funded.csv"

    # Write validated results with new transaction ID column
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        # Automatically filters extra fields from API response
        writer.writerows({k: v for k, v in row.items() if k in fieldnames} 
                        for row in funded)

    print(f"Wrote {len(funded)} funded addresses to {output_path}")

if __name__ == "__main__":
    # Start the async event loop
    asyncio.run(main())