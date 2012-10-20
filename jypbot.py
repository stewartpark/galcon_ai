#!/usr/bin/env python
#
"""
    Ju-yeong Park Bot for Galcon AI
    Version 0.01
"""
import math

LOGGING = True

if LOGGING:
    import logging
else:
    class logging:
        DEBUG=0
        FATAL=0
        ERROR=0
        INFO=0
        @staticmethod
        def basicConfig(filename, level):
            pass
        @staticmethod
        def debug(*kwarg):
            pass
        @staticmethod
        def fatal(*kwarg):
            pass
        @staticmethod
        def info(*kwarg):
            pass
        @staticmethod
        def error(*kwarg):
            pass
    
from PlanetWars import PlanetWars

logging.basicConfig(filename='output.log', level=logging.DEBUG)
nTurn = 0
help_requests = []
attack_requests = []

# Vote
def help(pw, p, amount):
    global help_requests 
    help_requests.append([p, amount])
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
    logging.debug('P%d[%d] --%d--> P%d[%d]' % (source.PlanetID(), source.NumShips(), num_ships, dest.PlanetID(), dest.NumShips()))
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
                    rst -= (x.NumShips())# - ((x.TurnsRemaining()-1) * p.GrowthRate()))+1
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
    RISK_D = 12
    global help_requests, attack_requests
    giveUpVote = False
    gAv = getAvailableNumShips(pw, p)
    if gAv <= 0: # Will die
        giveUpVote = True
        # Help Me!
        danger = map(lambda x: x[0], help_requests)
        if not p in danger:
            logging.debug('P%d needs help! <--%d--' % (p.PlanetID(),gAv))
            help(pw, p, gAv)
    else: # not yet, but possible to die
        # Risk management
        amount = 0
        keep_so = 0
        for x in pw.EnemyPlanets():
            d = pw.Distance(x.PlanetID(), p.PlanetID())
            #logging.debug('P%d: enemy P%d is near(%d).' % (p.PlanetID(), x.PlanetID(), d))
            if d < RISK_D:
                tmp = int(x.NumShips() - (gAv+(d*p.GrowthRate())))
                if tmp > 0: 
                    logging.debug('P%d: is afraid of P%d.', p.PlanetID(), x.PlanetID())
                    amount += tmp

                if tmp < 0:
                    logging.debug('P%d: is uncomfortable with P%d.', p.PlanetID(), x.PlanetID())
                    keep_so += -tmp
        if p.NumShips() < keep_so:
            # need help
            amount += keep_so - p.NumShips()
            keep_so = p.NumShips() # should keep all of them
        if keep_so > 0:
            logging.debug('P%d decides how many sodilers should stay for their safety.: %d/%d', p.PlanetID(), keep_so, p.NumShips())
            p._num_ships = keep_so
        if amount > 0:
            logging.debug('P%d needs reinforcement! <--%d--' % (p.PlanetID(),amount))
            help(pw, p, amount)
    #### Decision ####
    attack_list = []
    # Attack.
    for x in pw.NotMyPlanets():
        score = (x.GrowthRate()*G_RATE) - (x.NumShips() + (x.GrowthRate() * pw.Distance(p.PlanetID(), x.PlanetID())))
        attack_list.append([x, score]) 
    # Help others.
    for x in help_requests:
        if x[0] != p: # except me
            score = (x[0].GrowthRate()*G_RATE*2) - ((-getAvailableNumShips(pw,x[0])) - (x[0].GrowthRate() * pw.Distance(p.PlanetID(), x[0].PlanetID())))
            attack_list.append([x[0], score]) 
    # Select highest score.
    attack_list = sorted(attack_list, key=lambda x: -x[1])
    logging.debug("P%d: results; %s" , p.PlanetID(), str(map(lambda x: ['P%d' % (x[0].PlanetID(),), x[1]], attack_list)))
    if giveUpVote:
        logging.debug('P%d gives up vote.' %(p.PlanetID(),))
        return
    try:
        logging.debug('P%d thinks the best target is P%d!' % (p.PlanetID(), attack_list[0][0].PlanetID()))
        #gen = (x for x in atttack_list)
        for _ in xrange(4):
            attack(pw, attack_list[0][0]) # Best vote: weight 4
        for _ in xrange(2):
            attack(pw, attack_list[1][0]) # Second vote: weight 2
        for _ in xrange(1):
            attack(pw, attack_list[2][0]) # Last vote 1
    except:
        logging.debug('P%d thinks there\'s no target anymore.' % (p.PlanetID()))
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
    attack_requests = [] # Think once more!
    logging.debug('[2] Planet is voting...')
    for x in planets:
        PlanetThinks(pw, x)
    #logging.debug('[3] Planet is voting...')
    #for x in planets:
    #    PlanetThinks(pw, x)
    logging.debug('Planet is deciding...')
    # Get total avail
    s_avail = sum(map(lambda x: x if x >= 0 else 0, map(lambda x: getAvailableNumShips(pw,x) if getAvailableNumShips(pw,x) > 1 else 0, planets)))
    logging.debug('Total power: %d' % (s_avail,))
    ##### Decision ######
    vote_r = {}
    for x in attack_requests: #initialization
        vote_r[x.PlanetID()] = 0
    for x in attack_requests:
        vote_r[x.PlanetID()] += 1
    votes = sorted(map(lambda x: [x, vote_r[x.PlanetID()]], attack_requests), key=lambda x: -x[1])
    
    logging.debug('Vote result: %s' % (str(map(lambda x: ['P%d' % (x[0].PlanetID(),), x[1]], votes),)))
    try:
        logging.debug('Voted: P%d, %d votes.' % (votes[0][0].PlanetID(), votes[0][1]))
    except:
        logging.debug('No vote.')
    # Remove redundancy
    r_votes = votes
    votes = []
    for x in r_votes:
        if not x in votes:
            votes.append(x)
    # utilities
    danger = map(lambda x: x[0], help_requests)
    ###### Voted, Action!!! #####
    for x in votes:
        must_action = False
        if x[0].Owner() == 1: # Planet needs help
            logging.debug('Planets decided to help P%d.' % (x[0].PlanetID(),))
            v = (-getAvailableNumShips(pw, x[0]))+1
            # Should we must help the planet?
            if x[0].GrowthRate() > 3:
                must_action = True # if it is big planet, yes.
        else: # attack
            logging.debug('Planets decided to attack P%d.' % (x[0].PlanetID(),))
            v = getAvailableNumShips(pw, x[0])+1
        if v < s_avail: # This is an estimation.
            #logging.debug('P%d seems to be doable. - estimation' % (x[0].PlanetID(),))
            # Attack!!
            attackers = []
            for y in planets:
                vv = min(y.NumShips(), getAvailableNumShips(pw, y))
                #if y in danger or vv < 1:
                if vv < 1:
                    logging.debug('P%d is in danger. cannot attack.' % (y.PlanetID(),))
                    continue
                logging.debug('P%d has available ships: %d.' % (y.PlanetID(), vv))
                # Actual damage 
                if x[0].Owner() == 2:
                    bubu = v + (x[0].GrowthRate()*pw.Distance(y.PlanetID(), x[0].PlanetID()))
                else:
                    bubu = v
                if bubu >= vv:
                    attackers.append([y, vv])
                elif bubu < vv:
                    attackers.append([y, bubu])
                if v < 0:
                    break
            if v <= sum(map(lambda x: x[1], attackers)):
                # available to attack.
                logging.debug('P%d seems to be doable.' % (x[0].PlanetID(),))
                # attack order (1st amount 2nd distance)
                attackers = sorted(attackers, key=lambda xx: xx[1] + (pw.Distance(x[0].PlanetID(), xx[0].PlanetID()) * 10) )
                for y in attackers:
                    issueOrder(pw, y[0], x[0], y[1])
                    s_avail -= y[1] 
            else:
                logging.debug('P%d is stronger than we thought.' % (x[0].PlanetID(),))
                if must_action:
                    break # try again in next turn
        else:
            logging.debug('P%d is too strong to attack or help.' % (x[0].PlanetID(),))
            if must_action:
                break # try again in next turn
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
  #except:
  #  import sys
  #  logging.debug(str(sys.exc_info()))
