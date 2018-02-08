# -*- coding: utf-8 -*-
# Copyright (C) Scott Coughlin (2017)
#
# This file is part of aCOSMIC.
#
# aCOSMIC is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# aCOSMIC is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with astro-traj.  If not, see <http://www.gnu.org/licenses/>.

"""`sample`
"""

import numpy as np
import math
import random

__author__ = 'Katelyn Breivik <katie.breivik@gmail.com>'
__credits__ = 'Scott Coughlin <scott.coughlin@ligo.org>'
__all__ = 'Sample'


G = 6.67384*math.pow(10, -11.0)
c = 2.99792458*math.pow(10, 8.0)
parsec = 3.08567758*math.pow(10, 16)
Rsun = 6.955*math.pow(10, 8)
Msun = 1.9891*math.pow(10,30)
day = 86400.0
rsun_in_au = 215.0954
day_in_year = 365.242
sec_in_day = 86400.0
sec_in_hour = 3600.0
hrs_in_day = 24.0
sec_in_year = 3.15569*10**7.0
Tobs = 3.15569*10**7.0
geo_mass = G/c**2


class Sample:
    def __init__(self, metallicity, size=None):
        '''
        initialize samples
        '''
        self.metallicity = np.asarray(metallicity).repeat(size)


    # sample primary masses
    def sample_primary(self, kstar1_final, model='kroupa93', size=None):
        '''
        kroupa93 follows Kroupa (1993), normalization comes from
        `Hurley (2002) <https://arxiv.org/abs/astro-ph/0201220>`_ between 0.1 and 100 Msun
        salpter55 follows Salpeter (1955) <http://adsabs.harvard.edu/abs/1955ApJ...121..161S>`_ between 0.1 and 100 Msun
        '''

        if model=='kroupa93':
            # If the final binary contains a compact object (BH or NS),
            # we want to evolve 'size' binaries that could form a compact
            # object so we over sample the initial population
            if kstar1_final > 14.0:
                a_0 = np.random.uniform(0.0, 0.9999797, size*500)
            elif kstar1_final > 12.0:
                a_0 = np.random.uniform(0.0, 0.9999797, size*50)
            else:   
                a_0 = np.random.uniform(0.0, 0.9999797, size)
            
            low_cutoff = 0.740074
            high_cutoff=0.908422
     
            lowIdx, = np.where(a_0 <= low_cutoff)
            midIdx, = np.where((a_0 > low_cutoff) & (a_0 < high_cutoff)) 
            highIdx, = np.where(a_0 >= high_cutoff)
     
            a_0[lowIdx] = ((0.1) ** (-3.0/10.0) - (a_0[lowIdx] / 0.968533)) ** (-10.0/3.0)
            a_0[midIdx] = ((0.5) ** (-6.0/5.0) - ((a_0[midIdx] - low_cutoff) / 0.129758)) ** (-5.0/6.0)
            a_0[highIdx] = (1 - ((a_0[highIdx] - high_cutoff) / 0.0915941)) ** (-10.0/17.0)
            
            total_sampled_mass = np.sum(a_0)
            if kstar1_final > 13.0:
                a_0 = a_0[a_0 > 15.0]
            elif kstar1_final > 12.0: 
                a_0 = a_0[a_0 > 8.0]
            return a_0, total_sampled_mass
        
        elif model=='salpeter55':
            # If the final binary contains a compact object (BH or NS),
            # we want to evolve 'size' binaries that could form a compact
            # object so we over sample the initial population
            if kstar1_final > 14.0:
                mSamp = np.random.power(-1.3, size*500)
            elif kstar1_final > 12.0:
                mSamp = np.random.power(-1.3, size*50)
            else:
                mSamp = np.random.power(-1.3, size*500)
            
            # Transform sample from 0 to 1 to be between 0.1 and 100 Msun
            a_0 = mSamp*(100.0-0.1)+0.1

            total_sampled_mass = np.sum(a_0)
            if kstar1_final > 13.0:
                a_0 = a_0[a_0 > 15.0]
            elif kstar1_final > 12.0:
                a_0 = a_0[a_0 > 8.0]
            return a_0, total_sampled_mass 
                   
    # sample secondary mass
    def sample_secondary(self, primary_mass):
        '''
        Secondary mass is computed from uniform mass ratio distribution draws motivated by
        `Mazeh et al. (1992) <http://adsabs.harvard.edu/abs/1992ApJ...401..265M>`_
        and `Goldberg & Mazeh (1994) <http://adsabs.harvard.edu/abs/1994ApJ...429..362G>`_
        '''
        
        a_0 = np.random.uniform(0.001, 1, primary_mass.size)
        secondary_mass = primary_mass*a_0        

        return secondary_mass


    def binary_select(self, primary_mass, model='vanHaaften'):
        '''
        Binary fraction is set by `van Haaften et al.(2009)<http://adsabs.harvard.edu/abs/2013A%26A...552A..69V>`_ in appdx
        '''
        
        if model=='vanHaaften':
            binary_fraction = 1/2.0 + 1/4.0 * np.log10(primary_mass)
            binary_choose =  np.random.uniform(0, 1.0, binary_fraction.size)
     
            binaryIdx, = np.where(binary_fraction > binary_choose)
            singleIdx, = np.where(binary_fraction < binary_choose)
     
            return primary_mass[binaryIdx], primary_mass[singleIdx]


    def sample_porb(self, mass1, mass2, model='Han', size=None):
        '''
        If model='Han', separation is sampled according to `Han (1998)<http://adsabs.harvard.edu/abs/1998MNRAS.296.1019H>`_
        If model='log_normal', Use (ref from Aaron Geller) to sample a log normal distributed orbital period
        with mu=1e5.03 days and sigma=1e2.28 days; converts period from days to seconds.
        Separation is then converted to orbital period in seconds
        '''
        
        if model=='Han': 
            a_0 = np.random.uniform(0, 1, size)
            low_cutoff = 0.0583333
            lowIdx, = np.where(a_0 <= low_cutoff)
            hiIdx, = np.where(a_0 > low_cutoff)
            
            a_0[lowIdx] = (a_0[lowIdx]/0.00368058)**(5/6.0)
            a_0[hiIdx] = np.exp(a_0[hiIdx]/0.07+math.log(10.0))
            
            # convert to meters
            a_0 = a_0*Rsun
            
            # convert to orbital period in seconds
            porb_sec = (4*np.pi**2.0/(G*(mass1+mass2)*Msun)*(a_0**3.0))**0.5           
            return porb_sec
     
        if model=='log_normal':
            #sample orbital period in days, return in seconds
            porb = np.random.lognormal(np.pow(10,5.03), np.pow(10.0,2.28), size)

            return porb*sec_in_day


    def sample_ecc(self, model='thermal', size=None):
        '''
        If model=='thermal', thermal eccentricity distribution following `Heggie (1975)<http://adsabs.harvard.edu/abs/1975MNRAS.173..729H>`_ 
        
        If model=='uniform', Sample eccentricities uniformly between 0 and 1 following ref ref from Aaron Geller '''
        
        if model=='thermal':
            a_0 = np.random.uniform(0.0, 1.0, size)
 
            return a_0**0.5

        if model=='uniform':
            ecc = np.random.uniform(0.0, 1.0, size)

            return ecc


    def sample_SFH(self, model='const', size=None):
        '''
        'const': Assign an evolution time assuming a constant star formation rate over the age of the MW disk: 10,000 [Myr]
        'burst': Assign an evolution time assuming constant star formation rate for 1Gyr starting at 't_component' 10,000 [Myr] in the past
        '''

        if model=='const':

            tphys = np.random.uniform(0, 10000.0, size)
            return tphys
 
        if model=='burst':
            tphys = 10000.0 - np.random.uniform(0, 1000, size)
            return tphys
     
     
    def set_kstar(self, mass):
        '''
        Initialize all stars according to: kstar=1 if M>=0.7 Msun; kstar=0 if M<0.7
        '''
         
        kstar = np.zeros(mass.size)
        low_cutoff = 0.7
        lowIdx, = np.where(mass < low_cutoff)
        hiIdx, = np.where(mass >= low_cutoff)

        kstar[lowIdx] = 0
        kstar[hiIdx] = 1

        return kstar


class MultiDimSample:

    def __init__(self, metallicity, size=None):
        '''
        initialize samples
        '''
        self.metallicity = np.asarray(metallicity).repeat(size)

    #-----------------------------------
    # Belows is the adapted version of Maxwell Moe's IDL code 
    # that generates a population of single and binary stars 
    # based on the paper Mind your P's and Q's
    # By Maxwell Moe and Rosanne Di Stefano
    #
    # The python code has been adopted by Mads Sørensen
    #-----------------------------------
    # Version history:
    # V. 0.1; 2017/02/03
    # By Mads Sørensen
    # - This is a pure adaption from IDL to Python.
    # - The function idl_tabulate is similar to
    # the IDL function int_tabulated except, this function seems to be slightly
    # more exact in its solution.
    # Therefore, relative to the IDL code, there are small numerical differences.
    #-----------------------------------

    #
    # Comments below beginning with ; is the original nodes by Maxwell Moe.
    # Please read these careful for understanding the script.
    #; NOTE - This version produces only the statistical distributions of
    #;        single stars, binaries, and inner binaries in hierarchical triples.
    #;        Outer tertiaries in hierarchical triples are NOT generated.
    #;        Moreover, given a set of companions, all with period P to
    #;        primary mass M1, this version currently uses an approximation to
    #;        determine the fraction of those companions that are inner binaries
    #;        vs. outer triples. Nevertheless, this approximation reproduces
    #;        the overall multiplicity statistics.
    #; Step 1 - Tabulate probably density functions of periods,
    #;          mass ratios, and eccentricities based on
    #;          analytic fits to corrected binary star populations.
    #; Step 2 - Implement Monte Carlo method to generate stellar
    #;          population from those density functions.
    #;
    #
    #

    def idl_tabulate(x, f, p=5) :
        def newton_cotes(x, f) :
            if x.shape[0] < 2 :
                return 0
            rn = (x.shape[0] - 1) * (x - x[0]) / (x[-1] - x[0])
            weights = scipy.integrate.newton_cotes(rn)[0]
            return (x[-1] - x[0]) / (x.shape[0] - 1) * numpy.dot(weights, f)
        ret = 0
        for idx in xrange(0, x.shape[0], p - 1) :
            ret += newton_cotes(x[idx:idx + p], f[idx:idx + p])
        return ret

    def populate_pdfs():
        '''Tabulate probably density functions of periods,
        mass ratios, and eccentricities based on
        analytic fits to corrected binary star populations.
        '''

        numM1 = 101 
        numlogP=158
        numq = 91
        nume = 100

        #; Vector of primary masses M1 (Msun), logarithmic orbital period P (days),
        #; mass ratios q = Mcomp/M1, and eccentricities e
        #
        #; 0.8 < M1 < 40 (where we have statistics corrected for selection effects)
        M1_lo = 0.8
        M1_hi = 40
       
        M1v = np.logspace(np.log10(M1_lo), np.log10(M1_hi), num1M1)
       
        #; 0.15 < log P < 8.0
        log10_porb_lo = 0.15
        log10_porb_hi = 8.0
        logP = np.linspace(log10_porb_lo, log10_porb_hi, numlogP)
        #; 0.10 < q < 1.00
        q_lo = 0.1
        q_hi = 1.0
        qv = np.linspace(q_lo, q_hi, numq)
        #; 0.0001 < e < 0.9901
        #; set minimum to non-zero value to avoid numerical errors
        e_lo = 0.0
        e_hi = 0.99
        ev = np.linspace(e_lo, e_hi, nume)+0.0001
        #; Note that companions outside this parameter space (e.g., q < 0.1,
        #; log P (days) > 8.0 are not constrained in M+D16 and therefore
        #; not considered.

        #; Distribution functions - define here, but evaluate within for loops.
    
        #; Frequency of companions with q > 0.1 per decade of orbital period.
        #; Bottom panel in Fig. 37 of M+D17
        flogP_sq = np.zeros([numlogP, numM1])
    
        #; Given M1 and P, the cumulative distribution of mass ratios q
        cumqdist = np.zeros([numq, numlogP, numM1])
    
        #; Given M1 and P, the cumulative distribution of eccentricities e
        cumedist = np.zeros([nume, numlogP, numM1])
    
        #; Given M1 and P, the probability that the companion
        #; is a member of the inner binary (currently an approximation).
        #; 100% for log P < 1.5, decreases with increasing P
        probbin = np.zeros([numlogP, numM1])
    
    
        #; Given M1, the cumulative period distribution of the inner binary
        #; Normalized so that max(cumPbindist) = total binary frac. (NOT unity)
        cumPbindist = np.zeros([numlogP, numM1])
        #; Slope alpha of period distribution across intermediate periods
        #; 2.7 - DlogP < log P < 2.7 + DlogP, see Section 9.3 and Eqn. 23.
        #; Slightly updated from version 1.
        alpha = 0.018
        DlogP = 0.7
    
        #; Heaviside function for twins with 0.95 < q < 1.00
        H = np.zeros(numq)
        ind = np.where(qv >= 0.95)
        H[ind] = 1.0
        H= H / idl_tabulate(qv, H) #;normalize so that integral is unity
    
    
        #; Relevant indices with respect to mass ratio
        indlq = np.where(qv >= 0.3)
        indsq = np.where(qv < 0.3)
        indq0p3 = np.min(indlq)
        
        # FILL IN THE MULTIDIMENSIONAL DISTRIBUTION FUNCTIONS
        #; Loop through primary mass
        for i in range(0, numM1):
            myM1 = M1v[i]
            #; Twin fraction parameters that are dependent on M1 only; section 9.1
            FtwinlogPle1 = 0.3 - 0.15 * np.log10(myM1)#; Eqn. 6
            logPtwin = 8.0 - myM1                       #; Eqn. 7a
            if (myM1 >= 6.5):
                logPtwin = 1.5                       #; Eqn. 7b
            #; Frequency of companions with q > 0.3 at different orbital periods
            #; and dependent on M1 only; section 9.3 (slightly modified since v1)
            flogPle1   = 0.020 + 0.04 * np.log10(myM1) + \
                         0.07 * (np.log10(myM1))**2.   #; Eqn. 20
            flogPeq2p7 = 0.039 + 0.07 * np.log10(myM1) + \
                         0.01 * (np.log10(myM1))**2.   #; Eqn. 21
            flogPeq5p5 = 0.078 - 0.05 * np.log10(myM1) + \
                         0.04 * (np.log10(myM1))**2.   #; Eqn. 22
            #; Loop through orbital period P
            for j in range(0, numlogP):
                mylogP = logPv[j]
                #; Given M1 and P, set excess twin fraction; section 9.1 and Eqn. 5
                if(mylogP <= 1.0):
                    Ftwin = FtwinlogPle1
                else:
                    Ftwin = FtwinlogPle1 * (1.0 - (mylogP - 1.0) / (logPtwin - 1.0))
                if(mylogP >= logPtwin):
                    Ftwin = 0.0
       
       
                #; Power-law slope gamma_largeq for M1 < 1.2 Msun and various P; Eqn. 9
                if(mylogP <= 5.0):
                    gl_1p2 = -0.5
                if(mylogP > 5.0):
                    gl_1p2 = -0.5 - 0.3 * (mylogP - 5.0)
       
                #; Power-law slope gamma_largeq for M1 = 3.5 Msun and various P; Eqn. 10
                if(mylogP <= 1.0):
                    gl_3p5 = -0.5
                if((mylogP > 1.0)and(mylogP <= 4.5)):
                    gl_3p5 = -0.5 - 0.2 * (mylogP - 1.0)
                if((mylogP > 4.5)and(mylogP <= 6.5)):
                    gl_3p5 = -1.2 - 0.4 * (mylogP - 4.5)
                if(mylogP > 6.5):
                    gl_3p5 = -2.0
                
                #; Power-law slope gamma_largeq for M1 > 6 Msun and various P; Eqn. 11
                if(mylogP <= 1.0):
                    gl_6 = -0.5
                if((mylogP > 1.0)and(mylogP <= 2.0)):
                    gl_6 = -0.5 - 0.9 * (mylogP - 1.0)
                if((mylogP > 2.0)and(mylogP <= 4.0)):
                    gl_6 = -1.4 - 0.3 * (mylogP - 2.0)

                if(mylogP > 4.0):
                    gl_6 = -2.0
                
                #; Given P, interpolate gamma_largeq w/ respect to M1 at myM1
                if(myM1 <= 1.2):
                    gl = gl_1p2
                if((myM1 > 1.2)and(myM1 <= 3.5)):
                    gl = np.interp(np.log10(myM1), np.log10([1.2, 3.5]), [gl_1p2, gl_3p5])
                if((myM1 > 3.5)and(myM1 <= 6.0)):
                    gl = np.interp(np.log10(myM1), np.log10([3.5, 6.0]), [gl_3p5, gl_6])
                if(myM1 > 6.0):
                    gl = gl_6
                
                #; Power-law slope gamma_smallq for M1 < 1.2 Msun and all P; Eqn. 13
                gs_1p2 = 0.3
                
                #; Power-law slope gamma_smallq for M1 = 3.5 Msun and various P; Eqn. 14
                if(mylogP <= 2.5):
                    gs_3p5 = 0.2
                if((mylogP > 2.5)and(mylogP <= 5.5)):
                    gs_3p5 = 0.2 - 0.3 * (mylogP - 2.5)
                if(mylogP > 5.5):
                    gs_3p5 = -0.7 - 0.2 * (mylogP - 5.5)

                #; Power-law slope gamma_smallq for M1 > 6 Msun and various P; Eqn. 15
                if(mylogP <= 1.0):
                    gs_6 = 0.1
                if((mylogP > 1.0)and(mylogP <= 3.0)):
                    gs_6 = 0.1 - 0.15 * (mylogP - 1.0)
                if((mylogP > 3.0)and(mylogP <= 5.6)):
                    gs_6 = -0.2 - 0.50 * (mylogP - 3.0)
                if(mylogP > 5.6):
                    gs_6 = -1.5
                
                #; Given P, interpolate gamma_smallq w/ respect to M1 at myM1
                if(myM1 <= 1.2):
                    gs = gs_1p2
                if((myM1 > 1.2)and(myM1 <= 3.5)):
                    gs = np.interp(np.log10(myM1), np.log10([1.2, 3.5]),[gs_1p2, gs_3p5])
                if((myM1 > 3.5)and(myM1 <= 6.0)):
                   gs = np.interp(np.log10(myM1), np.log10([3.5, 6.0]),[gs_3p5, gs_6])
                if(myM1 > 6.0):
                    gs = gs_6

                #; Given Ftwin, gamma_smallq, and gamma_largeq at the specified M1 & P,
                #; tabulate the cumulative mass ratio distribution across 0.1 < q < 1.0
                fq = qv**gl                                   #; slope across 0.3 < q < 1.0
                fq = fq / idl_tabulate(qv[indlq], fq[indlq])   #; normalize to 0.3 < q < 1.0
                fq = fq * (1.0 - Ftwin) + H * Ftwin                   #; add twins
                fq[indsq] = fq[indq0p3] * (qv[indsq] / 0.3)**gs   #; slope across 0.1 < q < 0.3
                cumfq = np.cumsum(fq) - fq[0]          #; cumulative distribution
                cumfq = cumfq / np.max(cumfq)                     #; normalize cumfq(q=1.0) = 1
                cumqdist[:,j,i] = cumfq                      #; save to grid

                #; Given M1 and P, q_factor is the ratio of all binaries 0.1 < q < 1.0
                #; to those with 0.3 < q < 1.0
                q_factor = idl_tabulate(qv, fq)


                #; Given M1 & P, calculate power-law slope eta of eccentricity dist.
                if(mylogP >= 0.7):
                    #; For log P > 0.7 use fits in Section 9.2.
                    #; Power-law slope eta for M1 < 3 Msun and log P > 0.7
                    eta_3 = 0.6 - 0.7 / (mylogP - 0.5)  #; Eqn. 17
                    #; Power-law slope eta for M1 > 7 Msun and log P > 0.7
                    eta_7 = 0.9 - 0.2 / (mylogP - 0.5)  #; Eqn. 18
                else:
                    #; For log P < 0.7, set eta to fitted values at log P = 0.7
                    eta_3 = -2.9
                    eta_7 = -0.1

                #; Given P, interpolate eta with respect to M1 at myM1
                if(myM1 <= 3.):
                    eta = eta_3
                if((myM1 > 3.)and(myM1 <= 7.)):
                    eta = np.interp(np.log10(myM1), np.log10([3., 7.]), [eta_3, eta_7])
                if(myM1 > 7.):
                    eta = eta_7


                #; Given eta at the specified M1 and P, tabulate eccentricity distribution
                if(10**mylogP <= 2.):
                    #; For P < 2 days, assume all systems are close to circular
                    #; For adopted ev (spacing and minimum value), eta = -3.2 satisfies this
                    fe = ev**(-3.2)
                else:
                    fe = ev**eta
                    e_max = 1.0 - (10**mylogP / 2.0)**(-2.0/3.0) #; maximum eccentricity for given P
                    ind = np.where(ev >= e_max)
                    fe[ind] = 0.0                       #; set dist. = 0 for e > e_max
                    #; Assume e dist. has power-law slope eta for 0.0 < e / e_max < 0.8 and
                    #; then linear turnover between 0.8 < e / e_max < 1.0 so that dist.
                    #; is continuous at e / e_max = 0.8 and zero at e = e_max
                    ind = np.where((ev >= 0.8*e_max)&(ev <= 1.0*e_max))
                    ind_cont = np.min(ind) - 1
                    fe[ind] = np.interp(ev[ind], [0.8*e_max, 1.0*e_max], [fe[ind_cont], 0.])

                cumfe = np.cumsum(fe) - fe[0]  #; cumulative distribution
                cumfe = cumfe / np.max(cumfe)             #; normalize cumfe(e=e_max) = 1
                cumedist[:,j,i] = cumfe              #; save to grid


                #; Given constants alpha and DlogP and
                #; M1 dependent values flogPle1, flogPeq2p7, and flogPeq5p5,
                #; calculate frequency flogP of companions with q > 0.3 per decade
                #; of orbital period at given P (Section 9.3 and Eqn. 23)
                if(mylogP <= 1.):
                    flogP = flogPle1
                if((mylogP > 1.0)and(mylogP <= 2.7 - DlogP)):
                    flogP = flogPle1 + (mylogP - 1.0) / (1.7 - DlogP) * \
                            (flogPeq2p7 - flogPle1 - alpha*DlogP)
                if((mylogP > 2.7 - DlogP)and(mylogP <= 2.7 + DlogP)):
                    flogP = flogPeq2p7 + alpha*(mylogP - 2.7)
                if((mylogP > 2.7 + DlogP)and(mylogP <= 5.5)):
                    flogP = flogPeq2p7 + alpha*DlogP + \
                            (mylogP - 2.7 - DlogP)/(2.8 - DlogP) * \
                            (flogPeq5p5 - flogPeq2p7 - alpha*DlogP)
                if(mylogP > 5.5):
                    flogP = flogPeq5p5 * np.exp(-0.3 * (mylogP - 5.5))


                #; Convert frequency of companions with q > 0.3 to frequency of
                #; companions with q > 0.1 according to q_factor; save to grid
                flogP_sq[j,i] = flogP*q_factor


                #; Calculate prob. that a companion to M1 with period P is the
                #; inner binary.  Currently this is an approximation.
                #; 100% for log P < 1.5
                #; For log P > 1.5 adopt functional form that reproduces M1 dependent
                #; multiplicity statistics in Section 9.4, including a
                #; 41% binary star faction (59% single star fraction) for M1 = 1 Msun and
                #; 96% binary star fraction (4% single star fraction) for M1 = 28 Msun
                if(mylogP <= 1.5):
                    probbin[j,i] = 1.0
                else:
                    probbin[j,i] = 1.0 - 0.11*(mylogP - 1.5)**1.43 * (myM1 / 10.0)**0.56
                if(probbin[j,i] <= 0.0):
                    probbin[j,i]=0.0

            #; Given M1, calculate cumulative binary period distribution
            mycumPbindist = np.cumsum(flogP_sq[:,i] * probbin[:,i]) - \
                            flogP_sq[0,i] * probbin[0,i]
            #; Normalize so that max(cumPbindist) = total binary star fraction (NOT 1)
            mycumPbindist = mycumPbindist / np.max(mycumPbindist) * \
                            idl_tabulate(logPv, flogP_sq[:,i]*probbin[:,i])
            cumPbindist[:,i] = mycumPbindist  #;save to grid

        return cumqdist, cumedist, cumPbindist

    def initial_sample(self, M1min=0.08, size=None):
        '''
        Sample initial binary distribution according to Moe & Di Stefano (2017)   
        <http://adsabs.harvard.edu/abs/2017ApJS..230...15M>`_
        '''
        
        #; Step 2
        #; Implement Monte Carlo method / random number generator to select
        #; single stars and binaries from the grids of distributions


        #; Create vector for PRIMARY mass function, which is the mass distribution
        #; of single stars and primaries in binaries.
        #; This is NOT the IMF, which is the mass distribution of single stars,
        #; primaries in binaries, and secondaries in binaries.

        primary_mass_list = []
        secondary_mass_list = []
        porb_list = []
        ecc_list = []

        cumqdist, cumedist, cumPbindist = populate_pdfs()

        #; Full primary mass vector across 0.08 < M1 < 150
        M1 = np.linspace(0,150,150000) + 0.08
        #; Slope = -2.3 for M1 > 1 Msun
        fM1 = M1**(-2.3)
        #; Slope = -1.6 for M1 = 0.5 - 1.0 Msun
        ind = np.where(M1 <= 1.0)
        fM1[ind] = M1[ind]**(-1.6)
        #; Slope = -0.8 for M1 = 0.15 - 0.5 Msun
        ind = np.where(M1 <= 0.5)
        fM1[ind] = M1[ind]**(-0.8) / 0.5**(1.6 - 0.8)
        #; Cumulative primary mass distribution function
        cumfM1 = np.cumsum(fM1) - fM1[0]
        cumfM1 = cumfM1 / np.max(cumfM1)

        #; Value of primary mass CDF where M1 = M1min
        #; Minimum primary mass to generate (must be >0.080 Msun
        cumf_M1min = np.interp(M1min, M1, cumfM1)

        for i in range(0,int(size)):

            #; Select primary M1 > M1min from primary mass function
            myM1 = np.interp(cumf_M1min + (1.0 - cumf_M1min) * np.random.rand(), cumfM1, M1)

            # ; Find index of M1v that is closest to myM1.
            #     ; For M1 = 40 - 150 Msun, adopt binary statistics of M1 = 40 Msun.
            #     ; For M1 = 0.08 - 0.8 Msun, adopt P and e dist of M1 = 0.8Msun,
            #     ; scale and interpolate the companion frequencies so that the
            #     ; binary star fraction of M1 = 0.08 Msun primaries is zero,
            #     ; and truncate the q distribution so that q > q_min = 0.08/M1
            indM1 = np.where(abs(myM1 - M1v) == min(abs(myM1 - M1v)))
            indM1 = indM1[0]


            # ; Given M1, determine cumulative binary period distribution
            mycumPbindist = (cumPbindist[:, indM1]).flatten
            #; If M1 < 0.8 Msun, rescale to appropriate binary star fraction
            if(myM1 <= 0.8):
                mycumPbindist = mycumPbindist() * np.interp(np.log10(myM1), np.log10([0.08, 0.8]), [0.0, 1.0])

             # ; Given M1, determine the binary star fraction
             mybinfrac = np.max(mycumPbindist())
         
         
             # ; Generate random number myrand between 0 and 1
             myrand = np.random.rand()
             #; If random number < binary star fraction, generate a binary
             if(myrand < mybinfrac):
                 #; Given myrand, select P and corresponding index in logPv
                 mylogP = np.interp(myrand, mycumPbindist(), logPv)
                 indlogP = np.where(abs(mylogP - logPv) == min(abs(mylogP - logPv)))
                 indlogP = indlogP[0]
         
         
                 #; Given M1 & P, select e from eccentricity distribution
                 mye = np.interp(np.random.rand(), cumedist[:, indlogP, indM1].flatten(), ev)
         
         
                 #; Given M1 & P, determine mass ratio distribution.
                 #; If M1 < 0.8 Msun, truncate q distribution and consider
                 #; only mass ratios q > q_min = 0.08 / M1
                 mycumqdist = cumqdist[:, indlogP, indM1].flatten()
                 if(myM1 < 0.8):
                     q_min = 0.08 / myM1
                     #; Calculate cumulative probability at q = q_min
                     cum_qmin = np.interp(q_min, qv, mycumqdist)
                     #; Rescale and renormalize cumulative distribution for q > q_min
                     mycumqdist = mycumqdist - cum_qmin
                     mycumqdist = mycumqdist / max(mycumqdist)
                     #; Set probability = 0 where q < q_min
                     indq = np.where(qv <= q_min)
                     mycumqdist[indq] = 0.0
         
                 #; Given M1 & P, select q from cumulative mass ratio distribution
                 myq = np.interp(np.random.rand(), mycumqdist, qv)
         
         
                 primary_mass_list.append(myM1)
                 secondary_mass_list.append(myq * myM1)
                 porb_list.append(10**logP * sec_in_day)
                 ecc_list.append(mye)
         
                 total_mass += myM1
                 total_mass += myq * myM1 
             else:
                 total_mass += myM1    
        return np.array(primary_mass_list), np.array(secondary_mass_list), porb_list, ecc_list, total_mass      
                   
    def sample_SFH(self, model='const', size=None):
        '''
        'const': Assign an evolution time assuming a constant star formation rate over the age of the MW disk: 10,000 [Myr]
        'burst': Assign an evolution time assuming constant star formation rate for 1Gyr starting at 't_component' 10,000 [Myr] in the past
        '''

        if model=='const':

            tphys = np.random.uniform(0, 10000.0, size)
            return tphys

        if model=='burst':
            tphys = 10000.0 - np.random.uniform(0, 1000, size)
            return tphys

    def set_kstar(self, mass):
        '''
        Initialize all stars according to: kstar=1 if M>=0.7 Msun; kstar=0 if M<0.7
        '''

        kstar = np.zeros(mass.size)
        low_cutoff = 0.7
        lowIdx, = np.where(mass < low_cutoff)
        hiIdx, = np.where(mass >= low_cutoff)

        kstar[lowIdx] = 0
        kstar[hiIdx] = 1

        return kstar

    
