#!/usr/bin/env python
# licence.py - display GPL licence

# Copyright (c) 2010-2011 Algis Kabaila. All rights reserved.
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public Licence as published
# by the Free Software Foundation, either version 2 of the Licence, or
# version 3 of the Licence, or (at your option) any later version. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public Licence for more details.
'''
Reference:  http://docs.enthought.com/mayavi/mayavi/
To do:

0. Manage old_values and motion beyond bounds
1. Move dot smoothly
2. Draw nice lines smoothly
3. Erase lines
4. Strip down
'''
from PySide.QtGui import QApplication, QMainWindow, QWidget
from ui_PVE_control import Ui_Form as PVE_control
class variable:
    '''A class that collects, for a single variable, the spin box, slider
    and button widgets and their service routines.
    '''
    def __init__(
            self,    # variable instance
            spin,    # Qt spin box widget
            slide,   # Qt slider widget
            button,  # Qt radio button widget
            name,    # On character string that is one of PvES
            factor,  # (variable value)/(spin box value)
            state):  # Link to other variables
        assert name in 'PvES'
        self.spin = spin
        self.slide = slide                    # Goes 0 to 99
        self.button = button
        self.name = name
        self.factor = factor
        self.state = state
        self.min = float(self.spin.minimum())
        self.max = float(self.spin.maximum())
        self.value = spin.value()*factor
    def spin_move(self,  # variable instance
                    f):  # value from spin box
        '''Interrupt service routine for spin box value change.  Sends new
        value to slider and calls state.update().
        '''
        self.value = f*self.factor
        frac = (f - self.min)/(self.max - self.min)
        i = max(0, min(99, int(frac*99)))
        self.slide.blockSignals(True) # So setValue won't trigger slide_move
        self.slide.setValue(i)
        self.slide.blockSignals(False)
        self.state.update(self.name, value=self.value)
    def slide_move(self, # variable instance
                    i):    # value from slider
        '''Interrupt service routine for slider value change.  Sends new
        value to spin box and calls state.update().
        '''
        frac = float(i)/float(99)
        f = self.min + frac*(self.max - self.min)
        self.spin.blockSignals(True) # So setValue won't trigger spin_move
        self.spin.setValue(f)
        self.spin.blockSignals(False)
        self.value = f*self.factor
        self.state.update(self.name, value=self.value)
    def set_value(self, v, force=False):
        '''Called by state.update().  Sets self.value, slider and spin,
        and returns quantized number from spin.
        '''
        if self.value != v or force:
            self.value = v
            f = v/self.factor
            self.spin.blockSignals(True) # So setValue won't trigger spin_move
            self.spin.setValue(f)
            self.spin.blockSignals(False)
            frac = (f - self.min)/(self.max - self.min)
            i = max(0, min(99, int(frac*99)))
            self.slide.blockSignals(True)
            self.slide.setValue(i)
            self.slide.blockSignals(False)
        return self.spin.value()*self.factor # Return a quantized value
class state:
    '''Contains links to GUI and present and past values of state variables.
    Has methods for moving on the EOS sub-manifold.
    '''
    def initial_values(self,  # state instance
                       ):
        '''Set  3 value dictionaries using P and v values from self.var_dict.
        This is separate from __init__ because var_dict isn't ready when
        __init__ is called.
        '''
        self.values = {}
        self.displayed_values = {}
        for s, var in self.var_dict.items():
            self.values[s] = var.value
        self.vP(None, None)  # Set values['E'] to be consistent with v and P
        for s, var in self.var_dict.items():
            if self.var_dict[s].button.isChecked():
                self.constant = s
                self.displayed_values['constant'] = s
                self.values['constant'] = s
            v = self.values[s]
            self.displayed_values[s] = var.set_value(v, force=True)
        self.old_values = self.values.copy()
    def __init__(self, var_dict):
        import ideal_eos
        self.EOS = ideal_eos.EOS()
        self.var_dict = var_dict
        self.dispatch = {
            #(Moved, constant): Method,
            ('v',    'P'):      self.vP,
            ('E',    'P'):      self.EP,
            ('P',    'v'):      self.vP,
            ('E',    'v'):      self.Ev,
            ('P',    'E'):      self.EP,
            ('v',    'E'):      self.Ev,
            ('P',    'S'):      self.PS,
            ('v',    'S'):      self.vS,
            ('E',    'S'):      self.ES
            }
    def PS(self, s, button):
        P = self.values['P']
        v = self.values['v']
        E = self.values['E']
        v_new, E_new = self.EOS.isentrope_P(P, v, E)
        self.values['v'] = v_new
        self.values['E'] = E_new
    def vS(self, s, button):
        P = self.values['P']
        v = self.values['v']
        E = self.values['E']
        P_new, E_new = self.EOS.isentrope_v(v, P, E)
        self.values['P'] = P_new
        self.values['E'] = E_new
    def ES(self, s, button):
        P = self.values['P']
        v = self.values['v']
        E = self.values['E']
        P_new, v_new = self.EOS.isentrope_E(E, P, v)
        self.values['P'] = P_new
        self.values['v'] = v_new
    def Ev(self, s, button):
        E = self.values['E']
        v = self.values['v']
        P = self.EOS.Ev2P(E, v)
        self.values['P'] = P
    def EP(self, s, button):
        E = self.values['E']
        P = self.values['P']
        v = self.EOS.PE2v(P, E)
        self.values['v'] = v
    def vP(self, s, button):
        v = self.values['v']
        P = self.values['P']
        E = self.EOS.Pv2E(P, v)
        self.values['E'] = E
    def new_constant(self):
        '''Find which radio button is checked and then do update
        '''
        for s in 'PvES':
            if self.var_dict[s].button.isChecked():
                self.constant = s
                self.update(s, button=True)
                return
        assert False
    def display(self,     # state instance
                skip=None # Value of s to skip
                ):
        '''Make sliders and spin boxes match self.values.  Put the quantized
        values from the spin boxers in self.displayed_values.
        '''
        for s in self.var_dict:
            if s == skip: continue
            assert s in self.values
            v = self.values[s]
            var = self.var_dict[s]
            self.displayed_values[s] = var.set_value(v)
            
    def update(self,            # state instance
               s,               # key for manipulated variable
               value = None,
               button = False   # Flag for button event
               ):
        '''Called when GUI manipulated.  Put new value in self.values[s] and set
        new values of other variables that follow from that change.
        '''
        if button:
            for t, var in self.var_dict.items():
                self.displayed_values[t] = var.set_value(self.values[t])
            return
        key = (s, self.constant)
        if key not in self.dispatch:
            print('Pushing %s with constant %s has no effect'%key)
            self.var_dict[s].set_value(self.values[s]) # Return to last value
            return
        self.values[s] = value
        self.dispatch[key](s, button) # Calculate effect on other variables
        for t, var in self.var_dict.items():
            if t == s: continue
            self.displayed_values[t] = var.set_value(self.values[t])
        return
        
class PVE_widget(QWidget, PVE_control):
    def __init__(self, parent=None):
        '''Mandatory initialisation of a class.'''
        super(PVE_widget, self).__init__(parent)
        self.setupUi(self)
        var_dict = {}
        self.state = state(var_dict)
        for spin, slide, button, name, factor in (
# spin                 slide                  button             name  factor
(self.doubleSpinBox_P, self.verticalSlider_P, self.radioButton_P, 'P', 1e10),
(self.doubleSpinBox_v, self.verticalSlider_v, self.radioButton_v, 'v', 1e-6),
(self.doubleSpinBox_E, self.verticalSlider_E, self.radioButton_E, 'E', 1e3),
(self.doubleSpinBox_S, self.verticalSlider_S, self.radioButton_S, 'S', 1.0)):
            var = variable(spin, slide, button, name, factor, self.state)
            var_dict[name] = var
            slide.valueChanged.connect(var.slide_move)
            spin.valueChanged.connect(var.spin_move)
            button.clicked.connect(self.state.new_constant)
        self.state.initial_values() # Set up state information from var_dict

import surf
from ui_ideal_qt import Ui_MainWindow
class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        '''Mandatory initialisation of a class.'''
        super(MainWindow, self).__init__(parent)
        self.setupUi(self, surf.MayaviQWidget, PVE_widget)

if __name__ == '__main__':
    app = QApplication.instance() # traitsui.api has created app
    frame = MainWindow()
    frame.show()
    app.exec_()
