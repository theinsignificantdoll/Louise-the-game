from louiseClient import Hand
import time
import threading

h = Hand()
continueloop = True


def handleAnnouncements(payload):
    if payload == "Delt":
        h.requestcardhand()


h.announce = handleAnnouncements
answer = ""  # For the sake of PyCharm's sanity
# noinspection PyRedeclaration
answer = None


def loop():
    while continueloop:
        h.client.loop()


def inputloop():
    global answer
    while continueloop:
        answer = input()


def getinput():
    global answer
    while answer is None:
        time.sleep(0.1)
    a = answer
    answer = None
    return a


thread = threading.Thread(None, loop)
thread.start()
inputthread = threading.Thread(None, inputloop)
inputthread.start()

time.sleep(1)
h.requestcardhand()
time.sleep(1)
print(h.cardhand)
perlinecards = 16
# noinspection PyRedeclaration
#continueloop = False


def show(string): print(string, end="")


def displayAllCards():
    global activeUI
    numofopen = len(h.opencards)
    for ind, c in enumerate(h.opencards):
        show(f"{ind}.{'' if ind > 9 else ' '}{'' if ind > 99 else ' '}{'' if ind > 999 else ' '} {c}{'' if c > 9 else ' '}      ")

        if (1+ind) % perlinecards == 0 and ind != 0:
            show("\n")

    print()

    for ind, c in enumerate(h.hiddencards):
        show(f"{ind + numofopen}.{'' if ind+numofopen > 9 else ' '}{'' if ind+numofopen > 99 else ' '}{'' if ind+numofopen > 999 else ' '} {c}{'' if c > 9 else ' '}      ")

        if (1+ind) % perlinecards == 0 and ind != 0:
            show("\n")

    print()
    if len(h.cardhand) == 0:
        print("You have no cards on your hand")
    print()
    for ind, n in enumerate(h.cardhand):
        show(f"{ind}. {n}   ")

        if (1 + ind) % perlinecards == 0 and ind != 0:
            show("\n")

    print(h.gameprogress)
    print()
    print("Next dealing:", tilldealing)
    print(f"Back  Replace  Pass")
    userin = getinput()
    if userin == "continue": return
    if userin.lower() == "back":
        activeUI = -1
    elif userin.split(" ")[0].lower() == "replace":
        try:
            num1 = int(userin.split(" ")[1])
            num2 = int(userin.split(" ")[2])
            print("replaceing")
            h.replace(num1, num2)

        except (TypeError, IndexError):
            print("Invalid Input, 'Replace [INT FROM CARDHAND] [INT FROM DECKS]")
    elif userin == "pass":
        h.dopass()
    return


tilldealing = "0"


def timeleft(seconds):
    global tilldealing
    tilldealing = seconds


def startMatch():
    global activeUI
    activeUI = -1
    h.requeststart()


def recved(e):
    global answer
    answer = "continue"


def doUI():
    global activeUI
    if activeUI == -1:
        for ind, n in enumerate(mainUI):
            print(f"{ind}.", n[0])

        while True:
            try:
                userin = getinput()
                if userin == "continue": continue
                userin = int(userin)
                if userin < len(mainUI):
                    activeUI = userin
                    break
                continue
            except TypeError:
                continue
    else:
        mainUI[activeUI][1]()
    print()


activeUI = -1
mainUI = [
    ["Display all cards", displayAllCards],
    ["Start match", startMatch],
]


h.updatefunc = recved
h.timeleftfunc = timeleft
h.requestopencards()
h.requesthiddencards()
while not h.finished:
    doUI()


print("THE GAME HAS FINISHED, YOU PLACED")
print(h.placement)
print("You had", h.get_points(), "points!")
