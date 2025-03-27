# Rock-Paper-Scissors Giveaway Analysis

![Rock-Paper-Scissors Giveaway Logo](https://raw.githubusercontent.com/rps-on-chain/rps-giveaway/main/header.png)

A transparent system for managing X (Twitter) giveaways with bot detection through blockchain verification.
[Rock Paper Scissors](https://rock-paper-scissors.game) is a blockchain-based game that allows play with any ERC20 tokens in your wallet.

## Instructions to reproduce

- pip install -r requirements.txt
- echo "ALCHEMY_API_KEY=...your_api_key_here..." > .env
- Download results from X (export as CSV)
- Run parser with: `python parser.py your_replies.csv`
- Run validator: `python validator.py replies_filtered.csv`

### Results Validation

#### 1. Parse replies from X using plugin...
The output format is the following:
```csv
ID,Name,Handle,TweetText,TweetCreateTime,TweetURL,ReplyCount,QuoteCount,RetweetCount,LikeCount,BookmarkCount,Views,AllImageURL,VideoURL,Bio,CanDM,AccountCreateDate,Location,FollowersCount,FollowingCount,TotalFavouritesByUser,MediaCount,ProfileBannerURL,ProfileURL,AvatarURL,PostCount,Verified,IsBlueVerified
1902696649656557630,Rock Paper Scissors,@rps_chain,"🚀 Retweet &amp; Earn! Twitter USDT Storm 🌪️Stay, grow, and WIN!

💰 How to participate?

✅ Follow [@rps_chain]
❤️ Like &amp; Retweet this post
💬 Comment with your Arbitrum wallet address

🎁 Prize Pool: $150 USDT split among 10 random winners!
⏳ Duration: 1 week

🎲 Winners will be https://t.co/OIM1mDCZX8",2025-03-20 05:20:06,https://x.com/rps_chain/status/1902696649656557630,3734,7,3157,3332,24,21294,https://pbs.twimg.com/media/Gme738GboAAlLXL.jpg,,"🤝 1 vs 1 Battles: Think, Analyze, and Win! Powered by @ethereum.
🎮 Classic game on the blockchain.
🌍 Join community: https://t.co/iYRsgkiBWG",true,2024-10-09 02:59:24,,3962,75,112,25,https://pbs.twimg.com/profile_banners/1843954364731609088/1742472791,https://x.com/rps_chain,https://pbs.twimg.com/profile_images/1843957143206289408/7qpTwtes_normal.jpg,172,false,true
```

#### 2. Parse replies
The parser performs several key operations to ensure valid participant entries:
1. **Column Validation**: Checks for required fields like Tweet ID, Handle, and Tweet content
2. **Address Extraction**: Uses regex pattern `0x[a-fA-F0-9]{40}` to find ERC20 addresses in tweet text
3. **Duplicate Removal**: Ensures each wallet address only appears once, even if tweeted multiple times
4. **Data Sanitization**: Maintains only essential fields (ID, Handle, Timestamp, Tweet URL, and Address)

```bash
> python parser.py replies.csv
Detected columns: ['ID', 'Name', 'Handle', 'TweetText', 'TweetCreateTime', 'TweetURL', 'ReplyCount', '
QuoteCount', 'RetweetCount', 'LikeCount', 'BookmarkCount', 'Views', 'AllImageURL', 'VideoURL', 'Bio', 
'CanDM', 'AccountCreateDate', 'Location', 'FollowersCount', 'FollowingCount', 'TotalFavouritesByUser',
 'MediaCount', 'ProfileBannerURL', 'ProfileURL', 'AvatarURL', 'PostCount', 'Verified', 'IsBlueVerified
']                                                                                                    
Successfully wrote 2879 records to replies_filtered.csv                                               
Unique addresses found: 2879                                                                          
Duplicate addresses skipped: 20   
```

#### 3. Run validator
The validator checks which addresses have been funded on Arbitrum network using Alchemy's blockchain API. It verifies each address by:
1. Querying transaction history in chronological order
2. Checking for any external (on-chain) transfers received
3. Validating the first transaction timestamp
4. Filtering out addresses with no transaction history

This ensures participants actually used the Arbitrum network prior to the giveaway, preventing fake accounts. The script uses concurrent requests (up to 20 simultaneous) for fast verification while maintaining API rate limits.

```bash
> python validator.py replies_filtered.csv
Starting validation for 2879 addresses...
Processed 100/2879 addresses (40.0/sec)
Processed 200/2879 addresses (49.5/sec)
...
Processed 2800/2879 addresses (63.8/sec)
Processed 2879/2879 addresses (64.1/sec)
Found 90 funded addresses (3.1%)
Wrote 90 funded addresses to replies_filtered_funded.csv
```

The output file (`*_funded.csv`) includes the first transaction hash for transparency, allowing anyone to independently verify the blockchain record.

