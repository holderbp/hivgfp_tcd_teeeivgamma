#!/usr/bin/env python

from __future__ import print_function
import sys
import math
import numpy as np
import scipy as sp
from scipy import integrate


class _Par:
    """Contains parameter values for both the ODE and its ICs"""
    # Strings of help output for each variable    
    class _help: pass
    # ODE Parameters
    #   Be sure to enter decimal representations (not integers)
    #--- cell culture death parameters
    N = 3e5 # cells
    _help.N = "Initial culture population size (at t = -tprior) (cells)"
    tauT = 6.0 # h
    _help.tauT = "Lifespan of uninfected, average (h)"
    sigmaT = 3.0 # h
    _help.sigmaT = "Lifespan of uninfected, StdDev (h)"
    _nT = int(round((tauT/sigmaT)**2)); sigmaT = math.sqrt(tauT**2/_nT)
    s = 0.0 # 1/h
    _help.s = "Exponential rate of growth of T cells (1/h)"
    dD = 1e-3 # h
    _help.dD = "Exponential rate of dead cell disintegration (1/h)"
    #--- virus/attachment parameters
    beta = 1e-2 # 1/h/[V]
    _help.beta = "Rate constant for infection (1/[V]/h)"
    V0 = 1e-3 # [V]
    _help.V0 = "Initial value of virus (Virus added at t=0) ([V])"    
    c = 0.1 # 1/h
    _help.c = "Virus decay (clearance) rate (1/h)"
    onedaydilution = 0 # yes/no
    _help.onedaydilution = "Virus conc reduced at 24h by 1mL of media (y/n)"
    #--- infection parameters: prior to reverse-transcription ("entered") 
    tauEE = 6.0 # h
    _help.tauEE = "Eclipse phase EE (fusion through RT, \"entered\"), Avg (h)"
    sigmaEE = 3.0 # h
    _help.sigmaEE = "Eclipse phase EE (fusion through RT), StdDev (h)"
    _nEE = int(round((tauEE/sigmaEE)**2)); sigmaEE = math.sqrt(tauEE**2/_nEE)
    dEE = 1e-3 # 1/h
    _help.dEE = "Exponential rate of infection-induced death in the EE phase (1/h)"
    fEE = 1e-3 # 1/h
    _help.fEE = "Exponential rate of infection failure within the EE phase (1/h)"
    EFAV_time = 1e6 #
    _help.EFAV_time = "The time of efavirenz (reverse transcriptase) action (h)"
    #--- infection parameters: prior to integration ("reverse-transcribed") 
    tauER = 6.0 # h
    _help.tauER = "Eclipse phase ER (RT through INT, \"reverse-transcribed\"), Avg (h)"
    sigmaER = 3.0 # h
    _help.sigmaER = "Eclipse phase ER (RT through INT), StdDev (h)"
    _nER = int(round((tauER/sigmaER)**2)); sigmaER = math.sqrt(tauER**2/_nER)
    dER = 1e-3 # 1/h
    _help.dER = "Exponential rate of infection-induced death in the ER phase (1/h)"
    fER = 1e-3 # 1/h
    _help.fER = "Exponential rate of infection failure within the ER phase (1/h)"
    RALT_time = 1e6 #
    _help.RALT_time = "The time of raltegravir (integrase) action (h)"
    #--- infection parameters: prior to viral production ("integrated")
    tauEI = 6.0 # h
    _help.tauEI = "Eclipse phase EI (INT through Vir Prod, \"integrated\"), Avg (h)"
    sigmaEI = 3.0 # h
    _help.sigmaEI = "Eclipse phase EI (INT through Vir Prod), StdDev (h)"
    _nEI = int(round((tauEI/sigmaEI)**2)); sigmaEI = math.sqrt(tauEI**2/_nEI)
    dEI = 1e-3 # 1/h
    _help.dEI = "Exponential rate of infection-induced death in the EI phase (1/h)"
    fEI = 1e-3 # 1/h
    _help.fEI = "Exponential rate of infection failure within the EI phase (1/h)"
    #--- infection-induced-death parameters
    deathtype = 'exp'
    _help.deathtype = "Type of infected cell death (exp or gamma)"
    tauP = 6.0 # h
    _help.tauP = "Infected phase (viral prod through cell death), Avg (h)"
    sigmaP = 3.0 # h
    _help.sigmaP = "Infected phase (viral prod through death), StdDev (h)"
    _nP = int(round((tauP/sigmaP)**2)); sigmaP = math.sqrt(tauP**2/_nP)
    dP = 1e-3 # 1/h
    _help.dP = "Additional hazard for death in viral prod phase (1/h)"
    #--- integration parameters
    tprior = 24.0 # [h]
    _help.tprior = "Culture isolation time prior to infection (h)"
    tend = 7*24.0 # [h]
    _help.tend = "End time of numerical integration (h)"
    Nsteps = 1000
    _help.Nsteps = "Number of timesteps to return in [-tprior, tend] (unless timepoints specified with gettimes())"
    _onset_time = 0.1 # (time for virus or drug to ramp up; 0.01h ~ 30s)

def setpars(**kwdargs):
    """Allows user to set parameter values for ODEand ICs"""
    for kw in kwdargs.keys():
        setattr(_Par,kw,float(kwdargs[kw]))
    checkpars()
        
def checkpars():
    """CHECKPARS() --- after setting parameters, adjust model
    """
    # tauT
    _Par._nT = int(max(1,round((_Par.tauT/_Par.sigmaT)**2)))
    _Par.sigmaT = math.sqrt(_Par.tauT**2/_Par._nT)
    # tauEE
    _Par._nEE = int(max(1,round((_Par.tauEE/_Par.sigmaEE)**2)))
    _Par.sigmaEE = math.sqrt(_Par.tauEE**2/_Par._nEE)
    # tauER
    _Par._nER = int(max(1,round((_Par.tauER/_Par.sigmaER)**2)))
    _Par.sigmaER = math.sqrt(_Par.tauER**2/_Par._nER)
    # tauEI
    _Par._nEI = int(max(1,round((_Par.tauEI/_Par.sigmaEI)**2)))
    _Par.sigmaEI = math.sqrt(_Par.tauEI**2/_Par._nEI)
    # tauP
    if (_Par.deathtype == 'exp'):
        _Par._nP = 1
        _Par.sigmaP = _Par.tauP
    elif (_Par.deathtype == 'gamma'):
        _Par._nP = int(max(1,round((_Par.tauP/_Par.sigmaP)**2)))
        _Par.sigmaP = math.sqrt(_Par.tauP**2/_Par._nP)
    else:
        sys.exit()

def _ode_expP(X, t):
    """Definition of the TEEEIV ODE (gamma-distributed tEs, exponential tP)"""
    #--- convert times to rates for cell death and eclipse
    deltaT = _Par._nT / _Par.tauT
    deltaEI = _Par._nEI / _Par.tauEI
    nT = _Par._nT; nEE = _Par._nEE; nER = _Par._nER; nEI = _Par._nEI
    # and take into account drug application
    if (t < _Par.EFAV_time):
        deltaEE = _Par._nEE / _Par.tauEE
    else:
        # halt reverse-transcription if EFAV applied
        deltaEE = _Par._nEE / _Par.tauEE \
                  * np.exp(-(t - _Par.EFAV_time)**2/(2.0*_Par._onset_time**2))
    if (t < _Par.RALT_time):
        deltaER = _Par._nER / _Par.tauER
    else:
        # halt integration if RALT applied
        deltaER = _Par._nER / _Par.tauER \
                  * np.exp(-(t - _Par.RALT_time)**2/(2.0*_Par._onset_time**2))
    #--- get current virus value (exponential decay from t=0)
    if t<0:
        # rather than a discontinuous addition of virus at t=0, use a
        # rapidly increasing function as t->0-:  Gaussian with
        # sigma = 1/100h ~ 30s.
        Virus = _Par.V0*np.exp(-t*t/(2.0*_Par._onset_time**2))
    elif t<24.0:
        Virus = _Par.V0*np.exp(-_Par.c*t)
    else:
        if _Par.onedaydilution:    # dilution at one day?
            # add 1mL --> Virus down by mult factor ~ 310/1310 ~ 0.25
            Virus = 0.25*_Par.V0*np.exp(-_Par.c*t)
        else:
            Virus = _Par.V0*np.exp(-_Par.c*t)
    #--- forbid negative values
    X[X<0] = 0
    #--- create array of live-cell populations
    # rows are: segments of T cell death 
    # columns are: uninf, EE1, EE2, ..., EEnEE,      <-- 0 to nEE
    #                     ER1, ER2, ..., ERnER,      <-- nEE+1 to nEE+nER
    #                     EI1, EI2, ..., EInEI, P.   <-- nEE+nER+1 to nEE+nER+nEI+1
    # Extra (first) row of zeros to allow for, e.g., T[i-1,j]=0
    live = np.zeros((nT+1,nEE+nER+nEI+2))
    live[1:,:] = np.reshape(X[:-2],(nT,nEE+nER+nEI+2))
    #--- create return array :
    #    last two elements are dead (uninf and inf, respectively) 
    #    remaining values are an unwrapped "live" array (see above)
    dXdt = np.zeros(nT*(nEE+nER+nEI+2)+2)
    #
    #--- the ODE
    #
    ncolL = nEE+nER+nEI+2 # number of columns in live array
    for i in range(nT):
        # uninfected
        dXdt[ncolL*i+0] = -_Par.beta*live[i+1,0]*Virus/_Par.N \
                       + _Par.s*live[i+1,0] + deltaT*(live[i,0] - live[i+1,0]) \
                       + _Par.fEE*np.sum(live[i+1,1:(nEE+1)]) \
                       + _Par.fER*np.sum(live[i+1,(nEE+1):(nEE+nER+1)]) \
                       + _Par.fEI*np.sum(live[i+1,(nEE+nER+1):(nEE+nER+nEI+1)])
        # eclipse entered (EE) [1:nEE+1]
        dXdt[ncolL*i+1] = +_Par.beta*live[i+1,0]*Virus/_Par.N \
                       + deltaT*(live[i,1] - live[i+1,1]) - deltaEE*live[i+1,1] \
                       + (_Par.s - _Par.fEE)*live[i+1,1] \
                       - _Par.dEE*live[i+1,1]
        for j in (np.arange(nEE-1)+2):
            dXdt[ncolL*i+j] = + deltaT*(live[i,j] - live[i+1,j]) \
                           + deltaEE*(live[i+1,j-1] - live[i+1,j]) \
                           + (_Par.s - _Par.fEE)*live[i+1,j] \
                           - _Par.dEE*live[i+1,j]
        # eclipse RTed (ER)  [nEE+1:nEE+nER+1]
        j=nEE+1
        dXdt[ncolL*i+j] = + deltaEE*live[i+1,j-1] \
                       + deltaT*(live[i,j] - live[i+1,j]) \
                       - deltaER*live[i+1,j] \
                       + (_Par.s - _Par.fER)*live[i+1,j] \
                       - _Par.dER*live[i+1,j]
        for j in (np.arange(nER-1)+nEE+2):
            dXdt[ncolL*i+j] = + deltaT*(live[i,j] - live[i+1,j]) \
                           + deltaER*(live[i+1,j-1] - live[i+1,j]) \
                           + (_Par.s - _Par.fER)*live[i+1,j] \
                           - _Par.dER*live[i+1,j]
        # eclipse INTed (EI)  [nEE+nER+1:nEE+nER+nEI+1]
        j=nEE+nER+1
        dXdt[ncolL*i+j] = + deltaER*live[i+1,j-1] \
                       + deltaT*(live[i,j] - live[i+1,j]) \
                       - deltaEI*live[i+1,j] \
                       + (_Par.s - _Par.fEI)*live[i+1,j] \
                       - _Par.dEI*live[i+1,j]
        for j in (np.arange(nEI-1)+nEE+nER+2):
            dXdt[ncolL*i+j] = + deltaT*(live[i,j] - live[i+1,j]) \
                           + deltaEI*(live[i+1,j-1] - live[i+1,j]) \
                           + (_Par.s - _Par.fEI)*live[i+1,j] \
                           - _Par.dEI*live[i+1,j]
        # viral productive cells (P)  [nEE+nER+nEI+1]
        j=nEE+nER+nEI+1
        dXdt[ncolL*i+j] = + deltaEI*live[i+1,j-1] \
                          + deltaT*(live[i,j] - live[i+1,j]) \
                          + _Par.s*live[i+1,j] \
                          - _Par.dP*live[i+1,j] 
    # uninfected dead cells
    dXdt[-2] = + _Par.dEE*np.sum(live[1:,1:(nEE+1)]) \
               + _Par.dER*np.sum(live[1:,(nEE+1):(nEE+nER+1)]) \
               + _Par.dEI*np.sum(live[1:,(nEE+nER+1):(nEE+nER+nEI+1)]) \
               + deltaT*np.sum(live[nT,0:(nEE+nER+nEI+1)]) \
               - _Par.dD*X[-2]
    # infected dead cells
    dXdt[-1] = + _Par.dP*np.sum(live[1:,nEE+nER+nEI+1]) \
               + deltaT*live[nT,nEE+nER+nEI+1] \
               - _Par.dD*X[-1]
    return dXdt

def _ode_gammaP(X, t):
    """Definition of the TEEEIV ODE (gamma-distributed tEs, exponential tP)"""
    #--- convert times to rates for cell death, eclipse phases and vir prod phase
    deltaT = _Par._nT / _Par.tauT
    deltaEE = _Par._nEE / _Par.tauEE
    deltaER = _Par._nER / _Par.tauER
    deltaEI = _Par._nEI / _Par.tauEI
    deltaP = _Par._nP / _Par.tauP
    nT = _Par._nT
    nEE = _Par._nEE; nER = _Par._nER; nEI = _Par._nEI
    nP = _Par._nP
    #--- get current virus value (exponential decay from t=0)
    if t<0:
        # rather than a discontinuous addition of virus at t=0, use a
        # rapidly increasing function as t->0-:  Gaussian with
        # sigma = 1/100h ~ 30s.
        Virus = _Par.V0*np.exp(-t*t/(2.0*_Par._onset_time**2))
    elif t<24.0:
        Virus = _Par.V0*np.exp(-_Par.c*t)
    else:
        if _Par.onedaydilution:    # dilution at one day?
            # add 1mL --> Virus down by mult factor ~ 310/1310 ~ 0.25
            Virus = 0.25*_Par.V0*np.exp(-_Par.c*t)
        else:
            Virus = _Par.V0*np.exp(-_Par.c*t)
    #--- forbid negative values
    X[X<0] = 0
    #--- create array of live-cell populations
    # rows are: segments of T cell death 
    # columns are: uninf, EE1, EE2, ..., EEnEE,      <-- 0 to nEE
    #                     ER1, ER2, ..., ERnER,      <-- nEE+1 to nEE+nER
    #                     EI1, EI2, ..., EInEI, P.   <-- nEE+nER+1 to nEE+nER+nEI+1
    # Extra (first) row of zeros to allow for, e.g., T[i-1,j]=0
    live = np.zeros((nT+1,1+nEE+nER+nEI+nP))
    live[1:,:] = np.reshape(X[:-2],(nT,1+nEE+nER+nEI+nP))
    #--- create return array :
    #    last two elements are dead (uninf and inf, respectively) 
    #    remaining values are an unwrapped "live" array (see above)
    dXdt = np.zeros(nT*(1+nEE+nER+nEI+nP)+2)
    #
    #--- the ODE
    #
    ncolL = 1+nEE+nER+nEI+nP # number of columns in live array
    for i in range(nT):
        # uninfected
        dXdt[ncolL*i+0] = -_Par.beta*live[i+1,0]*Virus/_Par.N \
                       + _Par.s*live[i+1,0] + deltaT*(live[i,0] - live[i+1,0]) \
                       + _Par.fEE*np.sum(live[i+1,1:(nEE+1)]) \
                       + _Par.fER*np.sum(live[i+1,(nEE+1):(nEE+nER+1)]) \
                       + _Par.fEI*np.sum(live[i+1,(nEE+nER+1):(nEE+nER+nEI+1)])
        # eclipse entered (EE) [1:nEE+1]
        dXdt[ncolL*i+1] = +_Par.beta*live[i+1,0]*Virus/_Par.N \
                       + deltaT*(live[i,1] - live[i+1,1]) - deltaEE*live[i+1,1] \
                       + (_Par.s - _Par.fEE)*live[i+1,1] \
                       - _Par.dEE*live[i+1,1]
        for j in (np.arange(nEE-1)+2):
            dXdt[ncolL*i+j] = + deltaT*(live[i,j] - live[i+1,j]) \
                           + deltaEE*(live[i+1,j-1] - live[i+1,j]) \
                           + (_Par.s - _Par.fEE)*live[i+1,j] \
                           - _Par.dEE*live[i+1,j]
        # eclipse RTed (ER)  [nEE+1:nEE+nER+1]
        j=nEE+1
        dXdt[ncolL*i+j] = + deltaEE*live[i+1,j-1] \
                       + deltaT*(live[i,j] - live[i+1,j]) \
                       - deltaER*live[i+1,j] \
                       + (_Par.s - _Par.fER)*live[i+1,j] \
                       - _Par.dER*live[i+1,j]
        for j in (np.arange(nER-1)+nEE+2):
            dXdt[ncolL*i+j] = + deltaT*(live[i,j] - live[i+1,j]) \
                           + deltaER*(live[i+1,j-1] - live[i+1,j]) \
                           + (_Par.s - _Par.fER)*live[i+1,j] \
                           - _Par.dER*live[i+1,j]
        # eclipse INTed (EI)  [nEE+nER+1:nEE+nER+nEI+1]
        j=nEE+nER+1
        dXdt[ncolL*i+j] = + deltaER*live[i+1,j-1] \
                       + deltaT*(live[i,j] - live[i+1,j]) \
                       - deltaEI*live[i+1,j] \
                       + (_Par.s - _Par.fEI)*live[i+1,j] \
                       - _Par.dEI*live[i+1,j]
        for j in (np.arange(nEI-1)+nEE+nER+2):
            dXdt[ncolL*i+j] = + deltaT*(live[i,j] - live[i+1,j]) \
                           + deltaEI*(live[i+1,j-1] - live[i+1,j]) \
                           + (_Par.s - _Par.fEI)*live[i+1,j] \
                           - _Par.dEI*live[i+1,j]
        # viral productive cells (P)  [nEE+nER+nEI+1]
        j=nEE+nER+nEI+1
        dXdt[ncolL*i+j] = + deltaEI*live[i+1,j-1] \
                          + deltaT*(live[i,j] - live[i+1,j]) \
                          - deltaP*live[i+1,j] \
                          + _Par.s*live[i+1,j] \
                          - _Par.dP*live[i+1,j] 
        for j in (np.arange(nP-1) + nEE+nER+nEI+2):
            dXdt[ncolL*i+j] = + deltaT*(live[i,j] - live[i+1,j]) \
                              + deltaP*(live[i+1,j-1] - live[i+1,j]) \
                              + _Par.s*live[i+1,j] \
                              - _Par.dP*live[i+1,j]
    # uninfected dead cells
    dXdt[-2] = + _Par.dEE*np.sum(live[1:,1:(nEE+1)]) \
               + _Par.dER*np.sum(live[1:,(nEE+1):(nEE+nER+1)]) \
               + _Par.dEI*np.sum(live[1:,(nEE+nER+1):(nEE+nER+nEI+1)]) \
               + deltaT*np.sum(live[nT,0:(nEE+nER+nEI+1)]) \
               - _Par.dD*X[-2]
    # infected dead cells
    dXdt[-1] = + _Par.dP*np.sum(live[1:,(nEE+nER+nEI+1):(nEE+nER+nEI+nP+1)]) \
               + deltaT*np.sum(live[nT,(nEE+nER+nEI+1):(nEE+nER+nEI+nP+1)]) \
               + deltaP*np.sum(live[1:,nEE+nER+nEI+nP]) \
               - _Par.dD*X[-1]
    return dXdt

def getICs():
    """Returns an array of initial conditions for ODE evolution
    """
    if (_Par.deathtype == 'gamma'):
        nlive = 1 + _Par._nEE + _Par._nER + _Par._nEI + _Par._nP
        x=np.r_[np.zeros(_Par._nT*nlive + 2)]
        x[0]=_Par.N
        return x
    else:
        nlive = 1 + _Par._nEE + _Par._nER + _Par._nEI + 1
        x=np.r_[np.zeros(_Par._nT*nlive + 2)]
        x[0]=_Par.N
        return x

def gettimes(arr=None):
    """Returns an array of times for ODE evolution
    """
    if arr is None:
        tpoints = np.linspace(-1.0*_Par.tprior, _Par.tend, num=_Par.Nsteps)
    else:
        tpoints = np.array(arr)
    return tpoints

def evolve(times, X0):
    """Evolve the ODE from X0 and return array of values at times
    
    (Just a wrapper for scipy.integrate.odeint)
    """
    if (_Par.deathtype == 'gamma'):
        X = sp.integrate.odeint(_ode_gammaP, X0, times)
    else:
        #X = sp.integrate.odeint(_ode_expP, X0, times)
        X = sp.integrate.odeint(_ode_expP, X0, times, mxstep=500000)
    return X

def getsummarydata(times, X):
    """Returns [total, dead, fracinf, frac-dead-of-inf]
    """
    XX = np.zeros([times.size,4])
    nT = _Par._nT
    nEE = _Par._nEE; nER = _Par._nER; nEI = _Par._nEI
    if (_Par.deathtype == 'gamma'):
        nP = _Par._nP
    else:
        nP = 1
    ncolL = 1+nEE+nER+nEI+nP
    ncolE = nEE+nER+nEI
    for i in range(times.size):
        XX[i,0] = np.sum(X[i,:]).clip(0) # total
        XX[i,1] = np.sum(X[i,-2:]).clip(0) # dead
        deadinf =  X[i,-1].clip(0)
        liveinf = 0.0
        for j in range(nT):
            liveinf = liveinf \
                + np.sum(X[i,(j*ncolL+(1+ncolE)):(j*ncolL+(1+ncolE+nP))])
        XX[i,2] = (deadinf+liveinf)/XX[i,0]
        if (liveinf+deadinf)>0:
            XX[i,3] = deadinf/(liveinf+deadinf)
        else:
            XX[i,3] = 0.0
    return XX            

def outputdata(times, X):
    """Output data to user with header of parameter values"""
    print ("# This is data from the hiv_tcp_teivgamma model\n#\n" 
           + "# Parameters are:\n#")
    # list all parameters and their help string
    sortedlist = _Par.__dict__.items()
    sortedlist.sort()
    for key, value in sortedlist:
        if not key.startswith("_"):
            print("# {0} = {1} [{2}]".format(key, value, getattr(_Par._help,key)))
    # also print nT, nE and nP (these are preceded by _)
    print("# Equation numbers: nT={} nEE={} nER={} nEI={} nP={}".format(_Par._nT, _Par._nEE, _Par._nER, _Par._nEI, _Par._nP))
    # --- output data ---
    print("#\n# t  total  dead  frac-inf  dead-frac-of-inf")
    XX = getsummarydata(times,X)
    for i in range(times.size):
        print(times[i], XX[i,0], XX[i,1], XX[i,2], XX[i,3])

#====== When run as a script ======
# --- Parse cmd-line args, set parameters, run ode --- 
if __name__ == "__main__":
    import argparse
    #--- Parse the commandline flags ---
    parser = argparse.ArgumentParser(
        description = 'A routine to integrate the single-cycle HIV-GFP viral infection ' 
        + 'model with gamma-distributed timing for the eclipse phase and an '
        + 'exponentially-distributed infectious phase.',
        epilog = 'When utilized as a module, the following functions are available:\n'
        + '[setpars(**kwd) --- set parameter values by keyword]; '
        + '[checkpars() --- make sure that the number of eqns is an integer]; '
        + '[getICs() --- returns vector of initial conditions]; '
        + '[gettimes() --- returns vector of times for integration evaluation]; '
        + '[evolve(times,X0) --- evolves ODE from X0, returning X(t) at times].')
    # Create an optional argument for each ODE parameter
    sortedlist = _Par.__dict__.items()
    sortedlist.sort()
    for key, value in sortedlist:
        if not key.startswith("_"):   # omit system/private variables
            parser.add_argument("-" + key, 
                                help = ('{0} ({1})'.format(getattr(_Par._help,key), value)))
    # Parse the input arguments
    args = parser.parse_args()
    # If flag raised on commandline, set parameter value (convert string to float)
    for key, value in sortedlist:
        if not key.startswith("_"):
            if (getattr(args,key)):
                setattr(_Par, key, float(getattr(args,key)))

    ######==== RUNNING ONCE ====######
    #--- Check the parameter values ---
    checkpars()
    #--- Integrate the ODE ---
    X0 = getICs()
    tpoints = gettimes()
    X = evolve(tpoints,X0)
    #--- Output header and data --- 
    outputdata(tpoints,X)
