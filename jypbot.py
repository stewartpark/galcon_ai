#!/usr/bin/env python
#
"""
    Ju-yeong Park Bot for Galcon AI
    Version 0.01
"""


import logging
from PlanetWars import PlanetWars

logging.basicConfig(filename='output.log', level=logging.DEBUG)
nTurn = 0
help_requests = []
attack_requests = []

# Vote
def help(pw, p):
    global help_requests 
    help_requests.append(p)
def attack(pw, p):
    global attack_requests
    attack_requests.append(p)

# Utilities
def issueOrder(pw, source, dest, num_ships):
    if source.PlanetID() == dest.PlanetID():
        return
    if getAvailableNumShips(pw, source) <= num_ships:
        num_ships = getAvailableNumShips(pw, source)-1
    if num_ships < 1:
        return
    logging.debug('P%d[%d] --%d--> P%d[%d]', source.PlanetID(), source.NumShips(), num_ships, dest.PlanetID(), dest.NumShips())
    source.RemoveShips(num_ships)
    pw.IssueOrder(source.PlanetID(), dest.PlanetID(), num_ships)

def getAvailableNumShips(pw, p):
    rst = p.NumShips()
    if p.Owner() == 0:
        for x in pw.Fleets():
            if x.DestinationPlanet() == p.PlanetID():
                if x.Owner() == 1:
                    rst -= x.NumShips()
                elif x.Owner() == 2:
                    rst += x.NumShips()
    elif p.Owner() == 1:
        for x in pw.Fleets():
            if x.DestinationPlanet() == p.PlanetID():
                if x.Owner() == 2:
                    rst -= (x.NumShips() - ((x.TurnsRemaining()-1) * p.GrowthRate()))+1
                elif x.Owner() == 1:
                    #rst += (x.NumShips() - ((x.TurnsRemaining()-1) * p.GrowthRate()))+1
                    pass
    elif p.Owner() == 2:
        for x in pw.Fleets():
            if x.DestinationPlanet() == p.PlanetID():
                if x.Owner() == 1:
                    rst -= (x.NumShips() - ((x.TurnsRemaining()-1) * p.GrowthRate()))+1
                elif x.Owner() == 2:
                    rst += (x.NumShips() - ((x.TurnsRemaining()-1) * p.GrowthRate()))+1
    return rst
def PlanetThinks(pw, p):
    G_RATE = 20
    global help_requests, attack_requests
    if getAvailableNumShips(pw, p) <= 0:
        # Help Me!
        if not p in help_requests:
            logging.debug('P%d needs help!' % (p.PlanetID(),))
            #if p.GrowthRate() <= 1:
            #    logging.debug('Ignore, because this planet is too small to protect.')
            #else:
            help(pw, p)
    # Attack.
    best_score = -99999
    _p = None
    for x in pw.NotMyPlanets():
        score = (x.GrowthRate()*G_RATE) - (x.NumShips() + (x.GrowthRate() * pw.Distance(p.PlanetID(), x.PlanetID())))
        #logging.debug('P%d: estimated P%d, score: %d.' % (p.PlanetID(), x.PlanetID(), score))
        if score >= best_score:
            best_score = score
            _p = x
    # Help others.
    for x in help_requests:
        if x != p: # except me
            score = (x.GrowthRate()*G_RATE) - ((-getAvailableNumShips(pw,x)) - (x.GrowthRate() * pw.Distance(p.PlanetID(), x.PlanetID())))
            if score >= best_score:
                best_score = score
                _p = x
    logging.debug('P%d thinks the best target is P%d!' % (p.PlanetID(), _p.PlanetID()))
    attack(pw, _p)
def DoTurn(pw):
    if len(pw.NotMyPlanets()) == 0: return
    if len(pw.MyPlanets()) == 0: return
    global help_requests, attack_requests
    global nTurn
    logging.debug('====== Turn %d' % (nTurn,))
    nTurn += 1
    # initialize
    help_requests = []
    attack_requests = []

    planets = sorted(pw.MyPlanets(), key=lambda x: -getAvailableNumShips(pw, x))
    logging.debug('[1] Planet is voting...')
    for x in planets:
        PlanetThinks(pw, x)
    logging.debug('[2] Planet is voting...')
    for x in planets:
        PlanetThinks(pw, x)
    logging.debug('[3] Planet is voting...')
    for x in planets:
        PlanetThinks(pw, x)
    logging.debug('Planet is deciding...')
    # Get total avail
    s_avail = sum(map(lambda x: x if x >= 0 else 0, map(lambda x: min(getAvailableNumShips(pw,x), x.NumShips()), planets)))
    logging.debug('Total power: %d' % (s_avail,))
    ##### Decision ######
    votes = []
    for x in attack_requests:
        vote = 0
        for y in attack_requests:
            if x.PlanetID() == y.PlanetID():
                vote += 1
        if len(filter(lambda a: a[0] == x, votes)) == 0:
            votes.append([x, vote])
    votes = sorted(votes, key=lambda x: -x[1])
    logging.debug('Vote result: %s' % (str(votes),))
    try:
        logging.debug('Voted: P%d, %d votes.' % (votes[0][0].PlanetID(), votes[0][1]))
    except:
        logging.debug('No vote.')
    ###### Voted, Action!!! #####
    for x in votes:
        if x[0].Owner() == 1: # Planet needs help
            logging.debug('Planets decided to help P%d.' % (x[0].PlanetID(),))
            v = (-getAvailableNumShips(pw, x[0]))+1
        else: # attack
            logging.debug('Planets decided to attack P%d.' % (x[0].PlanetID(),))
            v = getAvailableNumShips(pw, x[0])+1
    
        if v < s_avail: # This is an estimation.
            logging.debug('P%d seems to be doable.' % (x[0].PlanetID(),))
            # Attack!!
            for y in planets:
                if y in help_requests:
                    logging.debug('P%d is in danger. cannot attack.' %(y.PlanetID(),))
                    continue
                vv = min(y.NumShips(), getAvailableNumShips(pw, y))
                if vv < 1: continue
                logging.debug('P%d has available ships: %d.' %(y.PlanetID(), vv))
                if v >= vv:
                    logging.debug('1')
                    issueOrder(pw, y, x[0], vv)
                    s_avail -= vv
                elif v < vv:
                    logging.debug('2')
                    issueOrder(pw, y, x[0], v)
                    s_avail -= v
                    v = -1
                if v < 0:
                    break
def main():
  map_data = ''
  while(True):
    current_line = raw_input()
    if len(current_line) >= 2 and current_line.startswith("go"):
      pw = PlanetWars(map_data)
      DoTurn(pw)
      pw.FinishTurn()
      map_data = ''
    else:
      map_data += current_line + '\n'


if __name__ == '__main__':
  try:
    import psyco
    psyco.full()
  except ImportError:
    pass
  try:
    main()
  except KeyboardInterrupt:
    print 'ctrl-c, leaving ...'
  except:
    import sys
    logging.debug(str(sys.exc_info()))
