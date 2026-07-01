from flask import Flask, render_template, jsonify
import json
from collections import defaultdict

app = Flask(__name__)

# --- DATA LOADING FUNCTIONS ---
def load_coach_data():
    with open('coaches.json', 'r', encoding='utf-8') as f:
        coaches = json.load(f)
    with open('matches_World_Cup.json', 'r', encoding='utf-8') as f:
        matches = json.load(f)
    return coaches, matches

def load_player_data():
    with open('players.json', 'r', encoding='utf-8') as f:
        players = json.load(f)
    with open('matches_World_Cup.json', 'r', encoding='utf-8') as f:
        matches = json.load(f)
    with open('events_World_Cup.json', 'r', encoding='utf-8') as f:
        events = json.load(f)
    return players, matches, events

# --- METRIC CALCULATION FUNCTIONS ---
def calculate_coach_metrics(coaches, matches):
    coach_stats = defaultdict(lambda: {
        'matches': [], 'wins': 0, 'draws': 0, 'losses': 0, 'points': 0, 'comebacks': 0
    })
    coach_info = {}
    for coach in coaches:
        coach_info[coach['wyId']] = {
            'name': coach.get('shortName', 'Unknown'),
            'nationality': coach.get('birthArea', {}).get('name', 'Unknown')
        }
    
    for match in matches:
        if match['status'] != 'Played': continue
        home_coach_id, away_coach_id = None, None
        home_score, away_score, home_ht_score, away_ht_score = 0, 0, 0, 0
        
        for team_id, team_data in match['teamsData'].items():
            if team_data['side'] == 'home':
                home_coach_id = team_data.get('coachId')
                home_score = team_data.get('score', 0)
                home_ht_score = team_data.get('scoreHT', 0)
            else:
                away_coach_id = team_data.get('coachId')
                away_score = team_data.get('score', 0)
                away_ht_score = team_data.get('scoreHT', 0)
        
        if not home_coach_id or not away_coach_id or home_coach_id == 0 or away_coach_id == 0:
            continue
            
        match_id = match['wyId']
        if home_score > away_score:
            coach_stats[home_coach_id]['matches'].append(match_id)
            coach_stats[home_coach_id]['wins'] += 1
            coach_stats[home_coach_id]['points'] += 3
            coach_stats[away_coach_id]['matches'].append(match_id)
            coach_stats[away_coach_id]['losses'] += 1
            if home_ht_score < away_ht_score: coach_stats[home_coach_id]['comebacks'] += 1
        elif away_score > home_score:
            coach_stats[away_coach_id]['matches'].append(match_id)
            coach_stats[away_coach_id]['wins'] += 1
            coach_stats[away_coach_id]['points'] += 3
            coach_stats[home_coach_id]['matches'].append(match_id)
            coach_stats[home_coach_id]['losses'] += 1
            if away_ht_score < home_ht_score: coach_stats[away_coach_id]['comebacks'] += 1
        else:
            coach_stats[home_coach_id]['matches'].append(match_id)
            coach_stats[home_coach_id]['draws'] += 1
            coach_stats[home_coach_id]['points'] += 1
            coach_stats[away_coach_id]['matches'].append(match_id)
            coach_stats[away_coach_id]['draws'] += 1
            coach_stats[away_coach_id]['points'] += 1
    
    results = []
    for coach_id, stats in coach_stats.items():
        total_matches = len(stats['matches'])
        if total_matches == 0: continue
            
        win_rate = stats['points'] / (total_matches * 3) if total_matches > 0 else 0
        impact_score = 0.3 if stats['comebacks'] >= 2 else (0.15 if stats['comebacks'] == 1 else 0)
        coach_rating = ((win_rate * 0.7) + impact_score) * 10
        info = coach_info.get(coach_id, {})
        
        results.append({
            'coachId': coach_id, 'name': info.get('name', 'Unknown'),
            'nationality': info.get('nationality', 'Unknown'),
            'matches': total_matches, 'wins': stats['wins'], 'draws': stats['draws'],
            'losses': stats['losses'], 'points': stats['points'], 'maxPoints': total_matches * 3,
            'winRate': round(win_rate * 100, 2), 'comebacks': stats['comebacks'],
            'impactScore': impact_score, 'rating': round(coach_rating, 2)
        })
    results.sort(key=lambda x: x['rating'], reverse=True)
    return results

def calculate_player_metrics(players, matches, events):
    player_info = {p['wyId']: {'name': p.get('shortName', ''), 'role': p.get('role', {}).get('name', 'Unknown')} for p in players}
    player_matches = defaultdict(set)
    
    # Track goals and assists directly from match data
    player_goals = defaultdict(int)
    player_assists = defaultdict(int)
    total_tournament_gi = 0
    total_tournament_matches = len([m for m in matches if m['status'] == 'Played'])

    # First pass: collect match appearances and goals/assists from match lineup data
    for match in matches:
        if match['status'] != 'Played': continue
        match_id = match['wyId']
        
        for team_id, team_data in match['teamsData'].items():
            formation = team_data.get('formation', {})
            
            # Process lineup (starters)
            for p in formation.get('lineup', []):
                pid = p['playerId']
                player_matches[pid].add(match_id)
                
                # Count goals - handle null values
                goals = p.get('goals')
                if goals and goals != 'null':
                    try:
                        g = int(goals)
                        if g > 0:
                            player_goals[pid] += g
                            total_tournament_gi += g
                    except (ValueError, TypeError):
                        pass
                
                # Count assists - handle null values
                assists = p.get('assists')
                if assists and assists != 'null':
                    try:
                        a = int(assists)
                        if a > 0:
                            player_assists[pid] += a
                            total_tournament_gi += a
                    except (ValueError, TypeError):
                        pass
            
            # Process substitutions (players who came on)
            for sub in formation.get('substitutions', []):
                pid_in = sub['playerIn']
                player_matches[pid_in].add(match_id)
                # Goals and assists for substitutes might be in a different field
                # Some match data formats have goals in the substitution object
                if 'goals' in sub and sub['goals'] and sub['goals'] != 'null':
                    try:
                        g = int(sub['goals'])
                        if g > 0:
                            player_goals[pid_in] += g
                            total_tournament_gi += g
                    except (ValueError, TypeError):
                        pass
                if 'assists' in sub and sub['assists'] and sub['assists'] != 'null':
                    try:
                        a = int(sub['assists'])
                        if a > 0:
                            player_assists[pid_in] += a
                            total_tournament_gi += a
                    except (ValueError, TypeError):
                        pass
            
            # Also check bench players who might have scored
            for p in formation.get('bench', []):
                pid = p['playerId']
                # Only count if they actually played (appeared in lineup or as sub)
                if pid in player_matches and match_id in player_matches[pid]:
                    goals = p.get('goals')
                    if goals and goals != 'null':
                        try:
                            g = int(goals)
                            if g > 0:
                                player_goals[pid] += g
                                total_tournament_gi += g
                        except (ValueError, TypeError):
                            pass
                    assists = p.get('assists')
                    if assists and assists != 'null':
                        try:
                            a = int(assists)
                            if a > 0:
                                player_assists[pid] += a
                                total_tournament_gi += a
                        except (ValueError, TypeError):
                            pass

    tourney_stats = defaultdict(float)
    role_tourney_stats = {'Midfielder': defaultdict(float), 'Forward': defaultdict(float)}
    player_stats = defaultdict(lambda: defaultdict(float))

    for ev in events:
        pid = ev['playerId']
        if pid == 0: continue
        
        role = player_info.get(pid, {}).get('role', 'Unknown')
        tags = [t['id'] for t in ev.get('tags', [])]
        ev_id, sub_id = ev.get('eventId'), ev.get('subEventId')
        is_accurate = 1801 in tags
        
        if ev_id == 9: 
            tourney_stats['TS'] += 1
            player_stats[pid]['ITS'] += 1
            if is_accurate: 
                tourney_stats['SS'] += 1
                player_stats[pid]['ISS'] += 1
        if ev_id == 8:
            player_stats[pid]['Pass_Attempted'] += 1
            if is_accurate: 
                player_stats[pid]['Pass_Accurate'] += 1
            if 302 in tags: 
                player_stats[pid]['Key_Passes'] += 1
                if role in role_tourney_stats: 
                    role_tourney_stats[role]['Total_Key_Passes'] += 1
        if sub_id == 10:
            player_stats[pid]['Air_Attempted'] += 1
            if is_accurate: 
                player_stats[pid]['Air_Won'] += 1
        if sub_id == 12:
            player_stats[pid]['GD_Attempted'] += 1
            if is_accurate: 
                player_stats[pid]['GD_Won'] += 1
        if sub_id == 13:
            player_stats[pid]['GL_Attempted'] += 1
            if is_accurate: 
                player_stats[pid]['GL_Won'] += 1
        if sub_id == 71:
            player_stats[pid]['Clear_Attempted'] += 1
            if is_accurate: 
                player_stats[pid]['Clear_Won'] += 1
        if ev_id == 3:
            player_stats[pid]['FK_Attempted'] += 1
            if is_accurate: 
                player_stats[pid]['FK_Accurate'] += 1
        if 1401 in tags:
            player_stats[pid]['Int_Attempted'] += 1
            if is_accurate: 
                player_stats[pid]['Int_Accurate'] += 1
        if sub_id == 100:
            player_stats[pid]['Shots_Attempted'] += 1
            if role in role_tourney_stats: 
                role_tourney_stats[role]['Shots_Attempted'] += 1
            
            if is_accurate: 
                player_stats[pid]['Shots_Accurate'] += 1
                if role in role_tourney_stats: 
                    role_tourney_stats[role]['Shots_Accurate'] += 1
            
            # Count goals from events too (as a secondary source)
            if 101 in tags: 
                player_stats[pid]['Goals_From_Events'] += 1
                if role in role_tourney_stats: 
                    role_tourney_stats[role]['Goals_Scored'] += 1

    # Global Tourney Stats
    tourney_SP = tourney_stats['SS'] / tourney_stats['TS'] if tourney_stats['TS'] > 0 else 0
    tourney_AS = tourney_stats['SS'] / total_tournament_matches if total_tournament_matches > 0 else 0
    tourney_AGI = total_tournament_gi / total_tournament_matches if total_tournament_matches > 0 else 0

    # Role-filtered Baselines (Midfielder and Forward specific)
    role_baselines = {}
    for r in ['Midfielder', 'Forward']:
        rt = role_tourney_stats[r]
        TP = rt['Shots_Accurate'] / rt['Shots_Attempted'] if rt['Shots_Attempted'] > 0 else 0
        SC = rt['Goals_Scored'] / rt['Shots_Accurate'] if rt['Shots_Accurate'] > 0 else 0
        AKP = rt['Total_Key_Passes'] / total_tournament_matches if total_tournament_matches > 0 else 0
        role_baselines[r] = {'TP': TP, 'SC': SC, 'AKP': AKP}

    results = []
    for pid, info in player_info.items():
        role = info['role']
        matches_played = len(player_matches[pid])
        if matches_played == 0: 
            continue 
        
        ps = player_stats[pid]
        rating, SV, succ_pass, DC, CC, TH, GIR = 0, 0, 0, 0, 0, 0, 0
        AD, GD, GL, CS, PA, FK, IN, ITP, ISC, KP, TR, SR, KPR, AGP = [0]*14
        ISP, IAS = 0, 0
        
        # Determine the correct baseline for the role
        if role in ['Midfielder', 'Forward']:
            active_TP = role_baselines[role]['TP']
            active_SC = role_baselines[role]['SC']
            active_AKP = role_baselines[role]['AKP']
        else:
            active_TP, active_SC, active_AKP = 0, 0, 0
        
        if role == 'Goalkeeper':
            ITS, ISS = ps['ITS'], ps['ISS']
            ISP = ISS / ITS if ITS > 0 else 0
            IAS = ISS / matches_played
            p_att, p_acc = ps['Pass_Attempted'], ps['Pass_Accurate']
            succ_pass = p_acc / p_att if p_att > 0 else 0
            
            part1 = ISP / tourney_SP if tourney_SP > 0 else 0
            part2 = IAS / tourney_AS if tourney_AS > 0 else 0
            SV = min((part1 + part2) / 2, 1)
            succ_pass = min(succ_pass, 1)
            rating = ((0.85 * SV) + (0.15 * succ_pass)) * 10
            
        elif role in ['Defender', 'Midfielder', 'Forward']:
            AD = ps['Air_Won'] / ps['Air_Attempted'] if ps['Air_Attempted'] > 0 else 0
            GD = ps['GD_Won'] / ps['GD_Attempted'] if ps['GD_Attempted'] > 0 else 0
            GL = ps['GL_Won'] / ps['GL_Attempted'] if ps['GL_Attempted'] > 0 else 0
            CS = ps['Clear_Won'] / ps['Clear_Attempted'] if ps['Clear_Attempted'] > 0 else 0
            DC = (AD + GD + GL + CS) / 4
            
            PA = ps['Pass_Accurate'] / ps['Pass_Attempted'] if ps['Pass_Attempted'] > 0 else 0
            FK = ps['FK_Accurate'] / ps['FK_Attempted'] if ps['FK_Attempted'] > 0 else 0
            IN = ps['Int_Accurate'] / ps['Int_Attempted'] if ps['Int_Attempted'] > 0 else 0
            CC = (PA + FK + IN) / 3
            
            ITP = ps['Shots_Accurate'] / ps['Shots_Attempted'] if ps['Shots_Attempted'] > 0 else 0
            ISC = ps['Goals_From_Events'] / ps['Shots_Accurate'] if ps['Shots_Accurate'] > 0 else 0
            KP = ps['Key_Passes'] / matches_played
            
            TR = ITP / active_TP if active_TP > 0 else 0
            SR = ISC / active_SC if active_SC > 0 else 0
            KPR = KP / active_AKP if active_AKP > 0 else 0
            TH = (TR + SR + KPR) / 3
            
            # Use goals and assists from match lineup data (more reliable)
            goals_scored = player_goals[pid]
            assists_made = player_assists[pid]
            GI = goals_scored + assists_made
            AGP = GI / matches_played
            GIR = AGP / tourney_AGI if tourney_AGI > 0 else 0
            
            # Clamp all metrics to max 1
            DC = min(DC, 1)
            CC = min(CC, 1)
            TH = min(TH, 1)
            GIR = min(GIR, 1)
            
            # Final rating formulas
            if role == 'Defender': 
                rating = ((0.75 * DC) + (0.15 * CC) + (0.1 * GIR)) * 10
            elif role == 'Midfielder': 
                rating = ((0.2 * DC) + (0.3 * CC) + (0.3 * TH) + (0.2 * GIR)) * 10
            elif role == 'Forward': 
                rating = ((0.1 * DC) + (0.2 * CC) + (0.5 * TH) + (0.2 * GIR)) * 10

        final_rating = min(max(rating, 0), 10)
        
        # Display stats - use goals and assists from match data
        goals_scored = player_goals[pid]
        assists_made = player_assists[pid]
        shots_on_target = int(ps['Shots_Accurate'])
        avg_passes_per_match = round(ps['Pass_Accurate'] / matches_played, 2) if matches_played > 0 else 0
        total_key_passes = int(ps['Key_Passes'])
        shots_saved = int(ps['ISS'])
        avg_saves_per_match = round(IAS, 2)

        results.append({
            'playerId': pid, 
            'name': info['name'], 
            'role': role,
            'matches': matches_played, 
            'rating': round(final_rating, 2),
            'displayStats': {
                'goals': goals_scored,
                'assists': assists_made,
                'shotsOnTarget': shots_on_target,
                'avgPassesPerMatch': avg_passes_per_match,
                'keyPasses': total_key_passes,
                'shotsSaved': shots_saved,
                'avgSavesPerMatch': avg_saves_per_match,
            },
            'stats': {
                'SV': round(SV, 3), 'SP': round(succ_pass, 3), 'DC': round(DC, 3), 'CC': round(CC, 3),
                'TH': round(TH, 3), 'GIR': round(GIR, 3), 'AD': round(AD, 3), 'GD': round(GD, 3),
                'GL': round(GL, 3), 'CS': round(CS, 3), 'PA': round(PA, 3), 'FK': round(FK, 3),
                'IN': round(IN, 3), 'ITP': round(ITP, 3), 'ISC': round(ISC, 3), 'KP': round(KP, 3),
                'TR': round(TR, 3), 'SR': round(SR, 3), 'KPR': round(KPR, 3), 
                'GI': goals_scored + assists_made,
                'AGP': round(AGP, 3), 'ISP': round(ISP, 3), 'IAS': round(IAS, 3),
                't_SP': round(tourney_SP, 3), 't_AS': round(tourney_AS, 3), 't_AGI': round(tourney_AGI, 3),
                't_TP': round(active_TP, 3), 't_SC': round(active_SC, 3), 't_AKP': round(active_AKP, 3)
            }
        })

    results.sort(key=lambda x: x['rating'], reverse=True)
    return results

# --- ROUTES ---
@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/coaches')
def get_coaches():
    coaches, matches = load_coach_data() 
    return jsonify(calculate_coach_metrics(coaches, matches))

@app.route('/api/players')
def get_players():
    players, matches, events = load_player_data() 
    return jsonify(calculate_player_metrics(players, matches, events))

if __name__ == '__main__':
    app.run(debug=True, port=5000)