Approach
The goal is to build a holistic player rating system that balances positional specialization with overall versatility. Instead of a one-size-fits-all metric, the system is designed to be role-aware, ensuring that each player’s performance is evaluated against the most relevant KPIs for their position, while still accounting for contributions across all phases of play. 
Goalkeepers: Core metrics focus on shot-stopping efficiency, command of the box, and distribution accuracy.
Defenders: Emphasis on defensive actions—tackles, interceptions, clearances, and aerial duels—along with composure under pressure.
Midfielders: A dual-threat weighting that captures both defensive disruptiveness and offensive influence
Attackers: Primary weight on goal contribution and shot volume, but with secondary visibility into defensive work rate when relevant.


Assumptions
Midfielders and forwards have position-specific performance benchmarks.
Defenders, midfielders, and forwards have distinct evaluation criteria.
Players with the role "Goalkeeper" are evaluated differently from outfielders.
All metrics are normalized to a 0-1 scale for fair comparison.
Performance metrics are weighted based on role importance.


Rating Logic - Player Rating System
Manager Rating Calculation
Rating = ((Win_Rate × 0.7) + Impact_Score) × 10
Components:
Win Rate: Points earned / (Total Matches × 3)
Impact Score:
0.3 for 2+ comebacks (trailing at half-time but winning)
0.15 for 1 comeback
0 for no comebacks
Scale: 0-10 (multiplied by 10 for readability)
Goalkeeper Rating
SV = (ISP/SP_avg + IAS/AS_avg) / 2
Final Rating = (0.85 × SV + 0.15 × SP) × 10
Components:
ISP: Individual Save Percentage (shots saved / shots faced)
SP_avg: Tournament average save percentage
IAS: Individual Average Saves (total saves / matches played)
AS_avg: Tournament average saves per match
SP: Passing Success Rate (successful passes / total passes)
Outfielder Rating (Role-Specific)
Defenders
Rating = (0.75 × DC + 0.15 × CC + 0.10 × GIR) × 10
Midfielders
Rating = (0.20 × DC + 0.30 × CC + 0.30 × TH + 0.20 × GIR) × 10
Forwards
Rating = (0.10 × DC + 0.20 × CC + 0.50 × TH + 0.20 × GIR) × 10
Component Definitions:
DC (Defending Quotient): Average of Air Duels, Ground Defending, Ground Loose Ball, and Clearances
CC (Control Confidence): Average of Passing Accuracy, Free Kick Accuracy, and Interceptions
TH (Attacking Threat): Average of Target Accuracy Ratio, Shot Conversion Ratio, and Key Passes Ratio
GIR (Goal Involvement Ratio): Individual AGP / Tournament AGI (where AGP = goals+assists per match)



Tradeoffs
The ratings generated are for all the events tracked over the tournament, not match-based.
The System rates according to the category of player, not overall as a football player.
The top 10 displayed are by default to reduce front-end rendering if there is any change in data.
Limitations
Relies on pre-loaded JSON files; not connected to live data feeds
No physical metrics (speed, strength, stamina) 
Equal weight given to performances regardless of opponent strength
Performance quantified through a limited set of indicators.
Doesn't account for performance quality within wins/losses
Weightings don't adapt to match context or opponent quality. 
Can't view match-by-match performance breakdown


Tools Used: Gemini, Deepseek, to build the solutions

Steps to run the HTML:

Save all files in a folder named Project.
Install Flask if not installed: pip install flask.
Change the directory where the file is saved. Suppose on the desktop
CD Desktop/Project
Run python app.py
Open Browser -paste  http://127.0.0.1:5000 or http://localhost:5000
