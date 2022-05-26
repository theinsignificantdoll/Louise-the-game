from paho.mqtt import client as mclient
import random
import time
import threading

broker = "192.168.3.41"
port = 1883
topic = "/"
client_id = "MasterDealer"

players = {}

cards = 2  # each player will have this many hidden AND this many open cards. If this value is 512 each player will
# have a total of 1024 cards, half hidden and half open.
replacedCards = []


class Dealer:
    def __init__(self):
        self.lastRound = False

    def tick(self):
        AnnounceDealing()
        for P in players:
            if players[P].hiddencards == 0 and not self.lastRound:
                AnnounceLastRound()
                self.lastRound = True
                setgameprogress("Last round")

            players[P].passed = True
            if players[P].recentlyplayed:
                self.dealCard(P, True)
                players[P].recentlyplayed = False
                players[P].passed = False

            updateplayerall(P)
        AnnounceDelt()

    def dealCard(self, P, useReplaced=False):
        if useReplaced and len(replacedCards) != 0:
            print("replaced")
            players[P].cardhand.append(replacedCards.pop(random.randrange(0, len(replacedCards))))
        else:
            print("random")
            players[P].cardhand.append(get_card())


def AnnounceLastRound():
    global client
    client.publish("Announcements", "LastRound")


def AnnounceDealing():
    print("DDDD")
    client.publish("Announcements", "Dealing")


def AnnounceDelt():
    client.publish("Announcements", "Delt")


def sorter(e):
    return e[1]


def announceWinner():
    lst = [[n, 0] for n in players]
    for ind, n in enumerate(lst):
        lst[ind][1] = players[n[0]].calculatepoints()

    lead = ""
    lst.sort(key=sorter)
    for ind, n in enumerate(lst):
        client.publish(f"placementRecv{n[0]}", f"{ind}-{n[1]}")
        lead += str(n[0]) + "/" + str(n[1]) + "\n"

    client.publish("Leaderboard", lead.rstrip())


gameprogress = ""


def setgameprogress(a):
    global gameprogress
    gameprogress = a
    client.publish("GameProgress", gameprogress)


class Card:
    def __init__(self, value, hidden=False, tangible=True):
        self.hidden = hidden
        self.value = value
        self.tangible = tangible

    def replace(self, new_value):
        if not self.tangible:
            raise Exception("Non-tangible cards cannot be replaced")

        old_value = self.value
        self.value = new_value
        if self.hidden:
            self.tangible = False
        self.hidden = False
        return old_value

    def get_value(self):
        if self.hidden:
            return 0
        else:
            return self.value


def get_card():
    return random.randint(1, 13)


class Player:
    def __init__(self, playername):
        global cards
        self.playername = playername
        self.cardhand = []
        self.openarray = []
        self.hiddenarray = []
        self.hiddencards = cards
        self.recentlyplayed = True
        self.passed = False
        for n in range(cards):  # Deals the player their cards
            self.openarray.append(Card(get_card()))
            self.hiddenarray.append(Card(get_card(), hidden=True))

    def replace(self, handInd, cardsInd):
        print("replacing", handInd, cardsInd)
        self.recentlyplayed = True
        if cardsInd >= cards:
            self.hiddencards -= 1
            return self.hiddenarray[cardsInd - cards].replace(self.cardhand[handInd])
        else:
            return self.openarray[cardsInd].replace(self.cardhand[handInd])

    def calculatepoints(self):
        points = 0
        for n in self.openarray:
            points += n.value
        for n in self.hiddenarray:
            points += n.value
        return points

    def dopass(self):
        if len(self.cardhand) == 0:
            return
        if self.passed:
            print("passed", "true")
            replacedCards.append(self.cardhand.pop())
            self.cardhand.clear()
            return
        self.passed = True
        replacedCards.append(self.cardhand.pop())
        dealer.dealCard(self.playername, False)


def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mclient.Client(client_id)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def updateplayerhand(P):
    client.publish(f"HandRecv{P}", joinnums(",", players[P].cardhand))


def updateplayeropen(P):
    client.publish(f"OpenRecv{P}", joincards(",", players[P].openarray))


def updateplayerhidden(P):
    client.publish(f"HiddenRecv{P}", joincards(",", players[P].hiddenarray))


def updateplayerall(P):
    updateplayerhand(P)
    updateplayeropen(P)
    updateplayerhidden(P)


def joinnums(string, lst):
    out = ""
    for n in lst:
        out += f"{str(n)}{string}"

    return out.rstrip(string)


def joincards(string, lst):
    out = ""
    for n in lst:
        out += f"{str(n.get_value())}{string}"

    return out.rstrip(string)


def subscribe(client: mclient):
    def on_message(client, userdata, msg):
        global queuestart
        global players
        topic = msg.topic
        payload = msg.payload.decode()
        print(topic, payload)
        if topic == "RegisterPlayer":
            players[payload] = Player(payload)
            print(f"Registered Player {payload}")
            client.subscribe(payload)
            return
        try:
            if payload == "Get/CardHand":
                client.publish(f"HandRecv{topic}", joinnums(",", players[topic].cardhand))
                print(f"HandRecv{topic}")
            elif payload == "Get/OpenCards":
                print(joincards(",", players[topic].openarray))
                client.publish(f"OpenRecv{topic}", joincards(",", players[topic].openarray))
            elif payload == "Get/HiddenCards":
                client.publish(f"HiddenRecv{topic}", joincards(",", players[topic].hiddenarray))
            elif payload.split(",")[0] == "Replace":
                sp = payload.split(",")
                replacedCards.append(players[topic].replace(int(sp[1]), int(sp[2])))
                players[topic].cardhand.pop(int(sp[1]))
                updateplayerall(topic)
            elif payload == "Do/Pass":
                print("dopass")
                players[topic].dopass()
                updateplayerall(topic)
            elif payload == "StartMatch":
                print("Starting")
                queuestart = True

        except KeyError as e:
            print("KeyError", e)
            print(players)
            client.publish("Announcements", "Unrecognized Player")

    client.subscribe("RegisterPlayer")
    client.on_message = on_message


client = connect_mqtt()
subscribe(client)
dealer = Dealer()
ticks = 0
dealLoopSeconds = 60
loopdelay = 0.01
tickspersecond = 1 / loopdelay
started = False
starttime = -1
queuestart = False
continueloop = True
gamespeed = 60  # How often, in seconds, the dealer should deal.


endnext = False


def loop():
    global ticks
    global starttime
    global queuestart
    global started
    global endnext
    while True:
        time.sleep(loopdelay)
        ticks += 1
        if started:
            if (ticks % tickspersecond) == 0:
                client.publish("Timeleft", int(gamespeed - ((ticks + starttime) // tickspersecond) % gamespeed))
            if (ticks + starttime) % (tickspersecond * gamespeed) == 0:
                queuestart = False
                print("Dealing")
                dealer.tick()
        else:
            if queuestart:
                started = True
                starttime = ticks - 20 * tickspersecond
                queuestart = False
        if endnext:
            break
        if dealer.lastRound:
            endnext = True
    announceWinner()


loopthread = threading.Thread(None, loop)
loopthread.start()


while continueloop:
    client.loop()
