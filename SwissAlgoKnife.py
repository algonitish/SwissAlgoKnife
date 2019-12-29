import os
import PySimpleGUI as sg


def getFileList():
    l = [f[:-3] for f in os.listdir(os.getcwd()+'/SAKModules') if '.py' in f]
    l.sort()
    return l
col =[
        [sg.Image(os.getcwd()+'/SAK_none.png')], 
        [sg.Button('Launch', size=(12,1))]
    ]
layout = [
            [sg.Listbox(getFileList(), size=(25,16), key='_LB_'), sg.Column(col)],
            [sg.Button('Exit')]
         ]

win_SAK = sg.Window('Swiss Algo Knife').Layout(layout)

while True:             # Event Loop
    event, values = win_SAK.Read()
    if event is None or event == 'Exit':
        break
    if event == 'Launch':
        try:
            exec(open(os.getcwd()+'/SAKModules/'+values["_LB_"][0]+".py").read())
        except (ValueError,IndexError):
            sg.popup("Nothing selected!")

win_SAK.Close()
