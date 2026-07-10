# -*- coding: utf-8 -*-
"""
Created on Sun Sep  1 15:38:24 2019

@author: robert.culver
"""
import numpy as np
import os

def valToSigFigStr(val, sf):
    assert (sf%1 == 0) and (sf >= 1), 'Invalid number of significant figures'
    return "{val:1.{sf}e}".format(val=val, sf=sf-1)

def portionOutList(bigList,nThreads):
    '''Separates bigList out into nThreads portions.'''
    assert np.iterable(bigList), 'iterable type expected'
    assert isinstance(nThreads, int), 'N must be integer'
    nJobs = len(bigList)
    if nThreads > nJobs:
        nThreads = nJobs
    boundaries = np.linspace(0,nJobs,nThreads+1).astype(int)
    starts, stops = boundaries[:-1], boundaries[1:]
    sublists = [bigList[s:e] for s,e in zip(starts,stops)]
    return sublists

def _signal_handler(signal, frame):
    import pdb, sys
    #doctest._OutputRedirectingPdb not needed - pdb.Pdb seems to do the job already
    realStdoutPdb = pdb.Pdb(stdout=sys.__stdout__)
    dbg = realStdoutPdb.set_trace
    realStdoutPdb.stdout.write('caught Ctrl-C in signal_handler\n')
    dbg(frame=frame)

def runDoctest(local, moduleName=None):
    'give dict(locals()) as the arg for local. that will pass in the scope from the caller.'
    import sys, doctest, signal
    notTested = ('profile',)
    signal.signal(signal.SIGINT, _signal_handler)
    if '-g' in sys.argv:
        for k,v in list(local.items()):
            if hasattr(v, '__module__') and v.__module__ == '__main__' and not k in notTested and not v.__doc__ is None:
                print('Testing ', k)
                doctest.debug(sys.modules['__main__'], '__main__.'+k, pm=True)
    elif '-p' in sys.argv:
        sys.modules['__main__'].dbg = lambda : None #disable breakpoints
        import cProfile
        try:
            fname=sys.argv[sys.argv.index('-p')+1] #filename is argument after -p flag
        except IndexError:
            fname='temp_profile_stats'
        cProfile.run('import doctest; doctest.testmod()',fname)
        import pstats
        ps=pstats.Stats(fname)
        ps.sort_stats('time').print_stats(15)
    else:
        sys.modules['__main__'].dbg = lambda : None #disable breakpoints
        #setupDebug()
        doctest.testmod()
    print('tests finished')
    
def emailNotification(msg=None,subject=None,recipient=None):
    '''Email self a notification msg'''
    recipient = os.environ['username']+'@the-mtc.org' if (recipient is None) else recipient
    assert (msg is not None) or (subject is not None),'At least one of msg & subject required as input'
    if msg is None:
        msg = ''
    else:
        assert type(msg) is str,'string expected'
    if subject is None:
        subject = 'Python notification'
    else:
        assert type(subject) is str,'string expected'
    import smtplib
    from email.mime.text import MIMEText
    me = 'nicks.app@the-mtc.org'
    msg = MIMEText(msg)
    msg['Subject'] = subject
    msg['From'] = me
    msg['To'] = recipient
    try:
        server = smtplib.SMTP('arcexch01.mtc.local')
        server.sendmail(me,[recipient],msg.as_string())
        server.quit()
    except: #silently fails if server unreachable or similar
        pass